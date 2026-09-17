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
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start or end > len(doc['text']):
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


def anchor_location(anchor):
    """Stable occurrence identity shared by full anchors and syntax spans."""
    return tuple(anchor[name] for name in ('doc_id', 'reading_id', 'start', 'end'))


def semantic_output_address(packet, definition_anchor, construction_anchor, construction_role,
                            output_port, branch_id='main', invocation_path=(), semantic_role=None):
    """Persistent semantic output address; runtime AST/event/value ids are excluded."""
    if not construction_role or not output_port or not branch_id or not semantic_role:
        raise ValueError('semantic_output_address_requires_role_port_branch')
    return {'schema': 'SemanticOutputAddress', 'schema_version': '1.0',
            'definition_anchor': validate_anchor(packet, definition_anchor),
            'construction_anchor': validate_anchor(packet, construction_anchor),
            'construction_role': construction_role, 'semantic_role': semantic_role, 'output_port': output_port,
            'invocation_path': list(invocation_path), 'branch_id': branch_id}


def validate_semantic_output_address(packet, address):
    required = {'definition_anchor', 'construction_anchor', 'construction_role', 'semantic_role', 'output_port', 'branch_id'}
    if not isinstance(address, dict) or not required.issubset(address):
        raise ValueError('invalid_semantic_output_address')
    return semantic_output_address(packet, address['definition_anchor'], address['construction_anchor'],
                                   address['construction_role'], address['output_port'],
                                   address['branch_id'], address.get('invocation_path', ()),
                                   address['semantic_role'])


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
