"""Resolve registered corpus sections into unchanged SourcePacket 3.x documents.

Ranges are zero-based, end-exclusive Unicode code-point offsets in the UTF-8
file decoded without newline conversion. No heuristic matching or saved graph
participates in this adapter.
"""
import hashlib
import json
from pathlib import Path
import re


def _json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def list_procedures(root):
    return _json(Path(root) / 'config/workbench-procedures.json')['procedures']


def build_source_packet(root, procedure_id):
    root = Path(root).resolve()
    procedure = next((p for p in list_procedures(root) if p['id'] == procedure_id), None)
    if procedure is None:
        raise ValueError('unknown_procedure')
    sources = _json(root / 'config/calendrical-ir-pipeline.json')['inputs']['source_texts']
    source = next(s for s in sources if s['id'] == procedure['source_id'])
    path = (root / source['path']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('source_outside_repository')
    raw = path.read_bytes()
    text = raw.decode('utf-8')
    sections = {}
    for match in re.finditer(r'^(\d+)[ \t]+([^\r\n]+)', text, re.MULTILINE):
        sections.setdefault(int(match[1]), []).append(match)

    def document(spec):
        matches = sections.get(spec['section'], [])
        if not matches:
            raise ValueError(f"missing_source_section: {spec['section']}")
        if len(matches) != 1:
            raise ValueError(f"ambiguous_source_section: {spec['section']}")
        match = matches[0]
        excerpt = match[2]
        digest = hashlib.sha256(excerpt.encode('utf-8')).hexdigest()
        if digest != spec['sha256']:
            raise ValueError(f"source_changed: {source['id']} section {spec['section']}")
        doc_id = f"{source['id']}:{spec['section']}"
        return {
            'doc_id': doc_id,
            'reading_id': f'{doc_id}.{digest[:12]}',
            'text': excerpt,
            'text_sha256': digest,
            'edition_transcription': excerpt,
            'edition_edits': [],
            'source': {
                'path': path.relative_to(root).as_posix(),
                'source_id': source['id'],
                'section': spec['section'],
                'reconstruction_span_id': spec['reconstruction_span_id'],
                'start': match.start(2),
                'end': match.end(2),
                'offset_unit': 'unicode_code_point',
                'corpus_sha256': hashlib.sha256(raw).hexdigest(),
            },
        }

    return {
        'procedure': procedure,
        'source_packet': {
            'schema_version': '3.0',
            'packet_id': f'repo:{procedure_id}',
            'input_mode': 'edition_transcription_only',
            'provided_scope': procedure['provided_scope'],
            'provenance': procedure['provenance'],
            'primary_documents': [document(s) for s in procedure['primary_sections']],
            'context_documents': [document(s) for s in procedure['context_sections']],
        },
    }
