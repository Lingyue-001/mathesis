"""Turn reviewed corpus-unit selections into unchanged SourcePacket 3.x input.

The unit index supplies exact source material and reviewable selection IDs. It
does not supply parser candidates, construction choices, or graph semantics.
"""
import hashlib
import json
from pathlib import Path

from .corpus_index import read_registered_source
from .dependencies import unit_hash


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def list_procedures(root):
    return _json(Path(root) / 'config/workbench-procedures.json')['procedures']


def _load_effective_index(root, source_id):
    """Load the reviewed material library and verify every retained anchor."""
    root = Path(root).resolve()
    path = root / 'corpus-review' / source_id / 'effective.json'
    if not path.is_file():
        raise FileNotFoundError(f'effective_corpus_index_missing: run scripts/corpus/extract_sifen_units.py --source-id {source_id}')
    from .corpus_review import load
    state = load(root, source_id)
    if state['stale']:
        if state['stale_reason'] == 'source_changed':
            raise ValueError('corpus_index_source_hash_mismatch')
        raise ValueError(f'corpus_index_not_current: {state["stale_reason"]}')
    index = state['effective']
    source, _, raw, text = read_registered_source(root, source_id)
    if index.get('source', {}).get('source_id') != source_id or index['source'].get('sha256') != hashlib.sha256(raw).hexdigest():
        raise ValueError('corpus_index_source_hash_mismatch')
    for unit in index.get('units', []):
        spans = unit.get('source_spans', [])
        if not spans or unit.get('text_original') != ''.join(span.get('text', '') for span in spans):
            raise ValueError(f'corpus_index_unit_integrity_error: {unit.get("id", "unknown")}')
        for span in spans:
            start, end = span.get('start'), span.get('end')
            if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start <= end <= len(text) or text[start:end] != span.get('text'):
                raise ValueError(f'corpus_index_span_mismatch: {unit.get("id", "unknown")}')
    return source, index


def _document_from_unit(source, index, selection):
    unit_id = selection['unit_id']
    unit = next((item for item in index['units'] if item['id'] == unit_id), None)
    if unit is None:
        raise ValueError(f'missing_source_section: {unit_id}')
    if unit['text_effective'] != unit['text_original']:
        raise ValueError(f'unit_requires_reading_mapping: {unit_id}')
    text = unit['text_effective']
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != selection['sha256']:
        raise ValueError(f'source_changed: {source["id"]} unit {unit_id}')
    spans = [{'section': span['section'], 'start': span['start'], 'end': span['end'], 'quote': span['text']}
             for span in unit['source_spans']]
    # Keep existing document identities for single numbered sections.  Unit IDs
    # are source-selection metadata; changing doc IDs would invalidate stable
    # anchors and reviewed sessions without changing the selected source text.
    suffix = str(unit['sections'][0]) if len(unit['sections']) == 1 else f'{unit["sections"][0]}-{unit["sections"][-1]}'
    if '@' in unit_id or ':span:' in unit_id:
        suffix = unit_id.split(':', 1)[1]
    doc_id = f'{source["id"]}:{suffix}'
    return {
        'doc_id': doc_id,
        'reading_id': f'{doc_id}.{digest[:12]}',
        'text': text,
        'text_sha256': digest,
        'edition_transcription': text,
        'edition_edits': [],
        'source': {
            'path': index['source']['path'], 'source_id': source['id'], 'unit_id': unit_id,
            'section': unit['sections'][0], 'sections': unit['sections'],
            'reconstruction_span_id': selection.get('reconstruction_span_id'),
            'start': spans[0]['start'], 'end': spans[-1]['end'],
            'is_contiguous': len(spans) == 1,
            'source_spans': spans,
            'offset_unit': index['source']['offset_unit'],
            'corpus_sha256': index['source']['sha256'],
            'unit_index_sha256': unit_hash(unit),
            'unit_hash_schema': 'effective-unit/1',
        },
    }


def build_source_packet(root, procedure_id):
    root = Path(root).resolve()
    procedure = next((item for item in list_procedures(root) if item['id'] == procedure_id), None)
    if procedure is None:
        raise ValueError('unknown_procedure')
    source, index = _load_effective_index(root, procedure['source_id'])
    primary = procedure.get('primary_units')
    context = procedure.get('context_units')
    if not isinstance(primary, list) or not isinstance(context, list):
        raise ValueError('procedure_requires_unit_manifest')
    return {
        'procedure': procedure,
        'source_packet': {
            'schema_version': '3.0',
            'packet_id': f'repo:{procedure_id}',
            'input_mode': 'edition_transcription_only',
            'provided_scope': procedure['provided_scope'],
            'provenance': procedure['provenance'],
            'primary_documents': [_document_from_unit(source, index, item) for item in primary],
            'context_documents': [_document_from_unit(source, index, item) for item in context],
        },
    }
