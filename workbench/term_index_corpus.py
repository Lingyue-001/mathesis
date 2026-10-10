"""Read-only baseline corpus inputs for the local Term Index view."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from adjudication import compile_reviewed, new_session
from adjudication.session import _hash_files, runtime_identity
from source_adapters.corpus import build_source_packet_from_units
from source_adapters import corpus_index, corpus_review
from workbench.annotation_projection import project_scholar_source
from workbench.question_presenter import build_questions
from workbench.service import _review_forms
from workbench.term_index import build_term_index


_TERM_INDEX_PRODUCER_ROOTS = (
    'analysis_parser', 'adjudication', 'domain_kernel', 'source_adapters', 'workbench', 'config',
)
_TERM_INDEX_PRODUCER_SUFFIXES = {'.py', '.json'}


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def fingerprint_effective_units(units):
    """Fingerprint only the effective units that are actually admitted."""
    rows = [{key: deepcopy(row.get(key)) for key in
             ('source_id', 'unit_id', 'source_spans', 'effective_revision', 'source_sha256')}
            for row in units]
    rows.sort(key=lambda row: (row['source_id'], row['unit_id'], _canonical(row['source_spans'])))
    return hashlib.sha256(_canonical(rows).encode('utf-8')).hexdigest()


def term_index_producer_files():
    """Return the deterministic active code/configuration boundary for the build."""
    root = Path(__file__).resolve().parents[1]
    names = []
    for relative_root in _TERM_INDEX_PRODUCER_ROOTS:
        directory = root / relative_root
        for path in directory.rglob('*'):
            if path.is_file() and path.suffix in _TERM_INDEX_PRODUCER_SUFFIXES:
                names.append(path.relative_to(root).as_posix())
    return tuple(sorted(names))


def term_index_producer_identity():
    """Identity of the existing analysis and read-only Index producer chain."""
    return {
        'runtime': runtime_identity({'selected_profiles': []}),
        'producer_sha256': _hash_files(term_index_producer_files()),
    }


def current_effective_units(root):
    """Return current effective corpus units and explicit unavailable sources."""
    root = Path(root)
    included, unavailable = [], []
    for source in corpus_index.list_review_sources(root):
        source_id = source['id']
        try:
            state = corpus_review._load(root, source_id)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            unavailable.append({'source_id': source_id, 'reason': str(error)})
            continue
        if state['stale']:
            unavailable.append({'source_id': source_id, 'reason': state['stale_reason']})
            continue
        for row in state['effective'].get('units', []):
            included.append({
                'source_id': source_id,
                'unit_id': row['id'],
                'source_spans': deepcopy(row.get('source_spans', [])),
                'effective_revision': state['revision'],
                'source_sha256': state['auto']['source']['sha256'],
            })
    return included, unavailable


def baseline_corpus_inputs(root='.'):
    """Read the cache key inputs without compiling any Projection.

    The returned rows are precisely the admitted baseline corpus candidates.
    Inspector focus, ReviewJobs, and branches are intentionally absent.
    """
    units, unavailable = current_effective_units(root)
    corpus_fingerprint = fingerprint_effective_units(units)
    producer_identity = term_index_producer_identity()
    fingerprint = hashlib.sha256(_canonical({
        'corpus_fingerprint': corpus_fingerprint,
        'producer_identity': producer_identity,
    }).encode('utf-8')).hexdigest()
    return {'units': deepcopy(units), 'unavailable': deepcopy(unavailable),
            'corpus_fingerprint': corpus_fingerprint,
            'producer_identity': producer_identity, 'fingerprint': fingerprint}


def project_baseline_unit(root, item):
    """Generate one current-effective Projection in memory, without a ReviewJob."""
    packet = build_source_packet_from_units(root, item['source_id'], [item['unit_id']], [], {})
    session = new_session(packet, 'term-index-baseline')
    compilation = compile_reviewed(packet, session)
    questions = build_questions(packet, compilation, _review_forms(packet, compilation))
    return project_scholar_source(packet, compilation, questions,
                                  session['decisions'], compilation['replay']['decision_status'])


def collect_baseline_term_index(root='.', *, inputs=None):
    """Collect all current effective baseline Projections into one TermIndex/1."""
    inputs = baseline_corpus_inputs(root) if inputs is None else inputs
    units = deepcopy(inputs.get('units', []))
    unavailable = deepcopy(inputs.get('unavailable', []))
    fingerprint = inputs.get('fingerprint', fingerprint_effective_units(units))
    if not units:
        return {'kind': 'baseline_corpus', 'index': None, 'fingerprint': fingerprint,
                'included': [], 'unavailable': deepcopy(unavailable)}
    projections, included, identities = [], [], set()
    for item in sorted(units, key=lambda row: (row['source_id'], row['unit_id'])):
        try:
            projection = project_baseline_unit(root, item)
        except Exception as error:
            raise ValueError('term_index_baseline_projection_failed: ' + item['unit_id']) from error
        source = projection.get('source', {})
        identity = tuple(source.get(key) for key in ('source_id', 'unit_id', 'doc_id', 'reading_id'))
        if None in identity or identity in identities:
            raise ValueError('term_index_duplicate_projection_source_identity')
        identities.add(identity)
        projections.append(projection)
        included.append({**deepcopy(item), 'projection_source_identity': {
            key: deepcopy(source[key]) for key in ('source_id', 'unit_id', 'doc_id', 'reading_id')}})
    return {'kind': 'baseline_corpus', 'index': build_term_index(projections),
            'fingerprint': fingerprint, 'included': included,
            'unavailable': deepcopy(unavailable)}
