"""Stable, source-character addresses for reviewed compiler inputs."""
import hashlib
import json


def _documents(packet):
    return [doc for category in ('primary_documents', 'context_documents')
            for doc in packet.get(category, [])]


def document_for(packet, doc_id, reading_id=None):
    found = [doc for doc in _documents(packet) if doc.get('doc_id') == doc_id]
    if len(found) != 1:
        raise ValueError('unknown_or_ambiguous_document')
    doc = found[0]
    if reading_id is not None and doc.get('reading_id', doc_id + '.declared') != reading_id:
        raise ValueError('reading_id_mismatch')
    return doc


def source_sha256(doc):
    return hashlib.sha256(doc['text'].encode('utf-8')).hexdigest()


def anchor_for(packet, doc_id, start, end, reading_id=None):
    doc = document_for(packet, doc_id, reading_id)
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start or end > len(doc['text']):
        raise ValueError('invalid_source_range')
    return {
        'doc_id': doc_id,
        'reading_id': doc.get('reading_id', doc_id + '.declared'),
        'source_sha256': source_sha256(doc),
        'start': start,
        'end': end,
        'quote': doc['text'][start:end],
        'offset_unit': 'unicode_code_point',
    }


def validate_anchor(packet, anchor):
    required = {'doc_id', 'reading_id', 'source_sha256', 'start', 'end', 'quote'}
    if not isinstance(anchor, dict) or not required.issubset(anchor):
        raise ValueError('invalid_anchor_shape')
    expected = anchor_for(packet, anchor['doc_id'], anchor['start'], anchor['end'], anchor['reading_id'])
    for key in ('source_sha256', 'quote'):
        if anchor[key] != expected[key]:
            raise ValueError('stale_source_anchor:' + key)
    return expected


def anchor_key(anchor):
    value = {key: anchor[key] for key in ('doc_id', 'reading_id', 'source_sha256', 'start', 'end', 'quote')}
    return 'anchor-' + hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                                  separators=(',', ':')).encode('utf-8')).hexdigest()[:24]


def overlaps(left, right):
    return (left['doc_id'] == right['doc_id'] and left['reading_id'] == right['reading_id']
            and left['start'] < right['end'] and right['start'] < left['end'])


def packet_identity(packet):
    documents = []
    for doc in _documents(packet):
        documents.append({
            'doc_id': doc['doc_id'],
            'reading_id': doc.get('reading_id', doc['doc_id'] + '.declared'),
            'source_sha256': source_sha256(doc),
            'length': len(doc['text']),
        })
    canonical = json.dumps({'packet_id': packet.get('packet_id'), 'documents': documents},
                           ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return {'packet_id': packet.get('packet_id'), 'documents': documents,
            'sha256': hashlib.sha256(canonical.encode('utf-8')).hexdigest()}
