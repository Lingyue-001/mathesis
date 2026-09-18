"""Content-addressed corpus dependencies, shared by Inspector and Workbench.

Freshness is checked on read, without a second result store or parser imports.
Records travel with saved results; graph/execution/comparison depend on parent
artifact IDs. `valid` means current inputs, not scholarly or semantic validity.
"""
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode('utf-8')).hexdigest()


def unit_hash(unit):
    """Review/actor/detection changes are not changes to compiler input."""
    return digest({**{key: unit.get(key) for key in
        ('id', 'sections', 'source_spans', 'text_original', 'text_effective', 'type')},
        'relations': [{key: value for key, value in relation.items()
                       if key not in ('basis', 'actor', 'time', 'note')}
                      for relation in unit.get('relations', [])]})


def artifact(kind, value, *, packet=None, parents=()):
    units = {}
    for parent in parents:
        for unit in parent['units']:
            units[(unit['source_id'], unit['unit_id'], unit['hash'])] = unit
    for group in ('primary_documents', 'context_documents'):
        for doc in (packet or {}).get(group, []):
            source = doc.get('source', {})
            if source.get('unit_id'):
                unit = {'source_id': source['source_id'], 'unit_id': source['unit_id'],
                        'hash': source['unit_index_sha256'], 'hash_schema': 'effective-unit/1'}
                units[(unit['source_id'], unit['unit_id'], unit['hash'])] = unit
    record = {'schema': 'CorpusArtifactDependencies/1', 'kind': kind,
              'content_hash': digest(value), 'parents': [p['id'] for p in parents],
              'units': [units[k] for k in sorted(units)]}
    return {**record, 'id': kind + ':' + digest(record)}


def validate(root, records):
    """Return per-artifact status; missing parents/cycles/units fail closed.

    No whole-corpus review hash is used. The source integrity lock is still
    enforced: an externally edited original needs explicit source revalidation.
    """
    from .corpus_review import load
    if not isinstance(records, list) or len(records) > 256 or any(
            not isinstance(r, dict) or r.get('schema') != 'CorpusArtifactDependencies/1'
            or not isinstance(r.get('kind'), str)
            or not isinstance(r.get('id'), str) or not isinstance(r.get('parents'), list)
            or not all(isinstance(p, str) for p in r['parents'])
            or not isinstance(r.get('units'), list) or any(
                not isinstance(u, dict) or not all(isinstance(u.get(k), str)
                for k in ('source_id', 'unit_id', 'hash')) for u in r['units']) for r in records):
        raise ValueError('invalid_artifact_dependencies')
    if len({r['id'] for r in records}) != len(records):
        raise ValueError('duplicate_artifact_id')
    by_id = {r['id']: r for r in records}
    sources, checked = {}, {}

    def check(artifact_id, visiting):
        if artifact_id in checked:
            return checked[artifact_id]
        if artifact_id not in by_id or artifact_id in visiting:
            return {'id': artifact_id, 'status': 'stale', 'reasons': ['missing_or_cyclic_parent']}
        record = by_id[artifact_id]
        reasons = []
        for parent in record['parents']:
            if check(parent, visiting | {artifact_id})['status'] != 'valid':
                reasons.append('upstream_stale:' + parent)
        for unit in record['units']:
            source_id = unit['source_id']
            if source_id not in sources:
                try:
                    state = load(root, source_id)
                    sources[source_id] = {} if state['stale'] else {
                        u['id']: unit_hash(u) for u in state['effective']['units']}
                except (OSError, ValueError):
                    sources[source_id] = {}
            if unit.get('hash_schema') != 'effective-unit/1' or sources[source_id].get(unit['unit_id']) != unit['hash']:
                reasons.append('unit_changed_or_missing:' + unit['unit_id'])
        checked[artifact_id] = {'id': artifact_id, 'kind': record['kind'],
                               'status': 'stale' if reasons else 'valid', 'reasons': reasons}
        return checked[artifact_id]

    return [check(r['id'], set()) for r in records]
