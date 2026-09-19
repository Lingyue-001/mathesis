"""Thin calls to the real parser stages, with unchanged JSON outputs."""
import json
from pathlib import Path
import sys
from threading import Lock
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis_parser.inputs import documents
from analysis_parser.lexical import tokenize_candidates
from analysis_parser.construction_ir import parse_syntax
from analysis_parser.pipeline import parse_packet
from source_adapters.dependencies import artifact, validate
from source_adapters.corpus_review import _atomic

OUTPUT = Path(__file__).resolve().parent / 'output' / 'current'
FILES = (
    'packet.json', 'documents.json', 'lexical_candidates.json', 'syntax.json',
    'construction_candidates.json', 'construction_selection.json', 'events.json',
    'values.json', 'diagnostics.json', 'unresolved.json', 'program.json',
    'compiler_report.json', 'run.json',
)
_LOCK = Lock()


def text_packet(text):
    """Wrap pasted text without editing it or supplying semantic assumptions."""
    return {
        'schema_version': '3.0',
        'packet_id': 'inspector:pasted',
        'input_mode': 'edition_transcription_only',
        'primary_documents': [{'doc_id': 'pasted', 'text': text}],
        'context_documents': [],
    }


def run(packet, stage, *, root=ROOT, include_term_semantics=False, term_regions=None):
    """Run up to a stage. Null files mean not run, never an empty result.

    SyntaxResult.to_dict()/candidates() are parser-owned serializers. Selection
    is only reported from normal parse_packet lowering. No inspector projection,
    token filtering, diagnostic merging, or semantic inference is performed.
    """
    if stage not in ('lexical', 'constructions', 'compile'):
        raise ValueError('Unknown parser stage')
    with _LOCK:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        result = {}
        candidate_filename = "term_semantic_candidates.json"
        (OUTPUT / candidate_filename).unlink(missing_ok=True)

        def save(filename, value):
            (OUTPUT / filename).write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            result[filename] = value

        # Reset every owned artifact before starting, including on failed runs.
        for filename in FILES:
            save(filename, None)
        progress = {'requested_stage': stage, 'completed_stages': [], 'status': 'running',
                    'corpus_root': str(Path(root).resolve())}
        save('run.json', progress)
        if include_term_semantics:
            save(candidate_filename, None)
        try:
            save('packet.json', packet)
            docs = documents(packet)
            save('documents.json', docs)
            token_streams = {doc['doc_id']: tokenize_candidates(doc, {}) for doc in docs}
            save('lexical_candidates.json', [token for stream in token_streams.values() for token in stream])
            progress['completed_stages'].append('lexical')
            if stage in ('constructions', 'compile'):
                syntaxes = {doc['doc_id']: parse_syntax(token_streams[doc['doc_id']], doc) for doc in docs}
                save('syntax.json', {doc_id: syntax.to_dict() for doc_id, syntax in syntaxes.items()})
                save('construction_candidates.json', [candidate for syntax in syntaxes.values() for candidate in syntax.candidates()])
                progress['completed_stages'].append('constructions')
            if stage == 'compile':
                report = parse_packet(packet)
                save('compiler_report.json', report)
                for filename, key in (
                    ('construction_selection.json', 'construction_candidates'),
                    ('events.json', 'events'), ('values.json', 'value_instances'),
                    ('diagnostics.json', 'diagnostics'), ('unresolved.json', 'unresolved'),
                    ('program.json', 'program'),
                ):
                    save(filename, report[key])
                progress['completed_stages'].append('compile')
            parser = artifact('parser', {name: value for name, value in result.items()
                                         if name not in ('run.json', 'packet.json', candidate_filename)}, packet=packet)
            progress['artifacts'] = [parser]
            if stage == 'compile':
                progress['artifacts'].append(artifact('graph', report, parents=[parser]))
            progress['freshness'] = validate(root, progress['artifacts'])
            progress['status'] = 'complete'
        except Exception:
            progress.update(status='error', error=traceback.format_exc())
        if include_term_semantics:
            if progress['status'] != 'complete':
                progress['term_semantics'] = {'status': 'blocked', 'reason': 'Native stage failed.'}
            else:
                try:
                    from domain_kernel.engine import suggest_packet_semantics
                    candidates = suggest_packet_semantics(packet, term_regions=term_regions)
                    candidate_artifact = artifact('term_semantics', candidates, packet=packet)
                    save(candidate_filename, candidates)
                    progress['term_semantics'] = {'status': 'complete', 'artifact': candidate_artifact}
                except Exception:
                    save(candidate_filename, None)
                    progress['term_semantics'] = {'status': 'error', 'error': traceback.format_exc()}
        save('run.json', progress)
        return result


def refresh_dependencies(root=ROOT):
    """Refresh only metadata; raw parser output files remain byte-for-byte native."""
    with _LOCK:
        path = OUTPUT / 'run.json'
        if not path.is_file():
            return None
        progress = json.loads(path.read_bytes())
        if not isinstance(progress, dict):
            return progress
        if progress.get('corpus_root') != str(Path(root).resolve()):
            return progress
        freshness = validate(root, progress['artifacts']) if progress.get('artifacts') else []
        if progress.get('freshness') != freshness:
            progress['freshness'] = freshness
            _atomic(path, progress)
        return progress
