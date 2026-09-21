"""Pure document catalogue derived from base source and active attachments."""
import copy

from .anchors import validate_anchor


def derive_packet(base, contexts):
    packet = copy.deepcopy(base)
    docs = packet.setdefault('context_documents', [])
    known = {d['doc_id']: d for group in ('primary_documents', 'context_documents')
             for d in packet.get(group, [])}
    for attachment in contexts:
        doc = attachment.get('document')
        if not isinstance(doc, dict) or not isinstance(doc.get('doc_id'), str) or not isinstance(doc.get('text'), str) or not doc['text']:
            raise ValueError('attach_context_requires_complete_document')
        previous = known.get(doc['doc_id'])
        if previous is not None:
            keys = ('text', 'reading_id', 'text_sha256', 'edition_transcription', 'edition_edits', 'editorial_trace')
            if any(previous.get(k) != doc.get(k) for k in keys):
                raise ValueError('attach_context_document_identity_conflict')
            continue
        known[doc['doc_id']] = copy.deepcopy(doc)
        docs.append(known[doc['doc_id']])
    return packet


def decision_anchors(row):
    """Semantic addresses inside payloads need the same checks as evidence targets."""
    def walk(value):
        if isinstance(value, dict):
            if {'doc_id', 'start', 'end'}.issubset(value):
                yield value
            else:
                for key, child in value.items():
                    if key != 'document':
                        yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)
    yield from walk(row.get('targets', []))
    yield from walk(row.get('payload', {}))


def validate_context_dependencies(base, catalog, row, contexts):
    original = {d['doc_id'] for group in ('primary_documents', 'context_documents') for d in base.get(group, [])}
    for anchor in decision_anchors(row):
        if anchor['doc_id'] not in original:
            providers = {c['decision_id'] for c in contexts if c['document']['doc_id'] == anchor['doc_id']}
            if not providers.intersection(row.get('depends_on', [])):
                raise ValueError('context_target_requires_attachment_dependency')
        validate_anchor(catalog, anchor)
