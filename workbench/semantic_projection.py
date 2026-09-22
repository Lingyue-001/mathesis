"""Project compiled closure onto existing Scholar identities; no inference."""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import json


def _key(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def _id(value):
    return 'semantic:' + sha256(_key(value).encode()).hexdigest()[:24]


def attach_semantic_closure(projection, compilation):
    graph = compilation['graph']
    closure = compilation.get('semantic_closure', {'schema': 'SemanticClosure/1', 'assertions': [], 'conflicts': [], 'unresolved': [], 'rules': {}})
    steps = {e['event_id']: s['id'] for s in projection['steps'] for e in s.get('evidence', []) if e.get('event_id')}
    constructions = {c['_candidate']['node_id']: c['id'] for c in projection['constructions'] if c.get('_candidate', {}).get('node_id')}
    events, ordinal = {}, defaultdict(int)
    for event in graph.get('events', []):
        spans = event.get('source_spans', [])
        base = [event['kind'], spans]
        key = _key(base)
        events[event['id']] = {'object_id': steps.get(event['id']) or constructions.get(event.get('syntax_node_id')),
                               'operation': event['kind'], 'source_anchors': deepcopy(spans), 'occurrence': ordinal[key]}
        ordinal[key] += 1
    values = {v['id']: v for v in graph.get('value_instances', [])}

    def event_target(ident, port=None, kind='graph_event'):
        result = dict(kind=kind, **deepcopy(events.get(ident, {'object_id': None})))
        if port is not None:
            result['port'] = port
        return result

    def target(raw):
        if raw['kind'] == 'term':
            a = raw['anchor']
            return {'kind': 'term', 'object_id': f"term:{a['doc_id']}:{a['start']}-{a['end']}", 'anchor': deepcopy(a)}
        if raw.get('value_id'):
            v = values.get(raw['value_id'], {})
            return event_target(v.get('producer'), v.get('output_port'), 'quantity')
        if raw.get('event_id'):
            return event_target(raw['event_id'], raw.get('port'), raw['kind'])
        return deepcopy(raw)

    identities = {a['id']: _id([target(a['target']), a['facet'], a['value'], a['authority'],
        sorted(d['id'] for d in a['depends_on'] if d['kind'] == 'review_decision')]) for a in closure['assertions']}

    def dependency(ref):
        if ref['kind'] == 'assertion':
            return {**ref, 'id': identities[ref['id']]}
        if ref['kind'] in ('graph_event', 'graph_port'):
            return event_target(ref['id'], ref.get('port'), ref['kind'])
        return deepcopy(ref)

    public = {'schema': 'SemanticClosure/1', 'assertions': [], 'conflicts': [], 'unresolved': [], 'rules': deepcopy(closure.get('rules', {}))}
    for a in closure['assertions']:
        item = {**deepcopy(a), 'id': identities[a['id']], 'target': target(a['target']),
                'depends_on': sorted([dependency(d) for d in a['depends_on']], key=_key),
                'proofs': sorted([{'rule_id': p['rule_id'], 'usable': p.get('usable', a['usable']), 'depends_on': sorted([dependency(d) for d in p['depends_on']], key=_key)} for p in a['proofs']], key=_key)}
        item['object_refs'] = [item['target']['object_id']] if item['target'].get('object_id') else []
        public['assertions'].append(item)
    for c in closure['conflicts']:
        item = {**deepcopy(c), 'target': target(c['target']), 'assertion_ids': sorted(identities[i] for i in c['assertion_ids'])}
        item['id'] = _id([item['target'], item['facet'], item['reason']])
        public['conflicts'].append(item)
    for row in closure['unresolved']:
        public['unresolved'].append({**deepcopy(row), 'target': target(row['target'])})
    for key in ('assertions', 'conflicts', 'unresolved'):
        public[key].sort(key=_key)
    projection['semantic_closure'] = public
    projection['derived_assertions'] = [a for a in public['assertions'] if a['authority'] == 'derived' and a['usable']]
    for row in [*projection['terms'], *projection['constructions'], *projection['steps']]:
        owned = [a for a in public['assertions'] if a['target'].get('object_id') == row['id']]
        row['semantic_assertions'] = owned
        row['derived_assertions'] = [a for a in owned if a['authority'] == 'derived' and a['usable']]
        row['semantic_conflicts'] = [c for c in public['conflicts'] if c['target'].get('object_id') == row['id']]
    for step in projection['steps']:
        for output in step['outputs']:
            facts = [a for a in step['semantic_assertions'] if a['target']['kind'] == 'quantity' and a['target'].get('port') == output['port']]
            if facts:
                output['semantic_assertions'] = facts
