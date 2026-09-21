"""Read-only quantity/data-flow view of ScholarSourceProjection/1.

No parsing, compilation, Kernel queries or review-state writes. Ontology is
read only for authored display labels. Graph IDs derive from Scholar IDs and
ports; internal value/event/definition IDs are deliberately not exported.
"""
from copy import deepcopy
import json
from pathlib import Path

from analysis_parser.ontology import entry


FLOW_LABELS = {
    'unresolved_source': 'Source unresolved',
    'ambiguous_source': 'Source ambiguous',
    'runtime_value_permitted': 'Runtime value permitted · source unresolved',
    'linked_source': 'Linked historical source',
}


def _authored(category, code):
    try:
        record = entry(category, code)
    except ValueError:
        record = {}
    return (record.get('label_en') or code,
            record.get('definition_en') or record.get('definition') or 'No authored description registered')


def _unique(values):
    return list({json.dumps(v, sort_keys=True, ensure_ascii=False): deepcopy(v) for v in values}.values())


def _anchors(row):
    return deepcopy(row.get('source_anchors') or ([row['source_anchor']] if row.get('source_anchor') else []))


def _public_source(row):
    if row is None:
        return None
    return {key: deepcopy(row[key]) for key in
            ('source_id', 'unit_id', 'doc_id', 'reading_id', 'sections', 'source_spans', 'source_anchors', 'text_sha256')
            if key in row}


def build_procedure_model(scholar_projection):
    """Return portable JSON records without modifying the supplied projection.

    source_anchors are copied canonical anchors. anchor_scope distinguishes an
    object's own anchor from a supporting Step anchor (not exact literal text).
    Complete describes only the recorded data-flow, never historical validity.
    """
    if scholar_projection.get('schema') != 'ScholarSourceProjection/1':
        raise ValueError('procedure_model_requires_scholar_source_projection_v1')
    p = scholar_projection
    terms = {r['id']: r for r in p.get('terms', [])}
    steps = {r['id']: r for r in p.get('steps', [])}
    constructions = {r['id']: r for r in p.get('constructions', [])}
    flows = {r['id']: r for r in p.get('flows', [])}
    nodes, edges, gaps = {}, [], []
    output_nodes = {}

    def add_node(ident, kind, label, owners, anchors, refs=(), **extra):
        node = {'id': ident, 'type': kind, 'label': label,
                'scholar_object_ids': list(dict.fromkeys(owners)),
                'selection_object_id': next(iter(owners), None),
                'source_anchors': _unique(anchors), 'anchor_scope': 'object',
                'decision_refs': _unique(refs), **extra}
        nodes[ident] = node
        return node

    def add_edge(origin, target, role, owners, **extra):
        label, definition = _authored('port', role) if role else ('Input', 'No authored description registered')
        # Generic reading labels; raw ordered ports remain in role/Evidence.
        if role in ('left', 'right', 'value'):
            label = _authored('port', 'value')[0]
        edges.append({'from': origin, 'to': target, 'role': role, 'label': label,
                      'definition': definition,
                      'source_object_ids': list(dict.fromkeys(owners)), **extra})

    def term_anchors(ids):
        return _unique(a for ident in ids if ident in terms for a in _anchors(terms[ident]))

    def term_refs(ids):
        return _unique(ref for ident in ids if ident in terms for ref in terms[ident].get('decision_refs', []))

    def interpretations(ids):
        # Preserve explicit state; do not infer authorship from a transition.
        return [{'object_id': ident,
                 'reviewed_claim_count': len(terms[ident].get('reviewed_claims', [])),
                 'candidate_statuses': _unique(c['status'] for c in terms[ident].get('semantic_candidates', []) if c.get('status'))}
                for ident in ids if ident in terms]

    for step in steps.values():
        label, definition = _authored('operation', step['operation'])
        add_node(step['id'], 'operation', label, [step['id']], _anchors(step),
                 step.get('decision_refs', []), operation=step['operation'], definition=definition)

    # Name separate output ports explicitly. Unnamed single results can be
    # drawn as direct operation dependencies without inventing quantity names.
    for step in steps.values():
        for output in step.get('outputs', []):
            port = output['port']
            term_ids = output.get('label_term_ids', [])
            labels = output.get('labels', [])
            judgment = step.get('judgment') if output.get('quantity_kind') == 'predicate' else None
            if labels or term_ids or judgment or len(step.get('outputs', [])) > 1:
                ident = 'output:' + step['id'] + ':' + port
                owners = [ident for ident in term_ids if ident in terms]
                anchors = term_anchors(owners)
                refs = term_refs(owners) + output.get('decision_refs', [])
                kind = 'named_quantity' if labels or owners else 'quantity'
                label = ' / '.join(labels or [terms[t]['surface'] for t in owners]) or _authored('port', port)[0]
                if judgment:
                    kind, label = 'judgment', judgment
                    supports = [constructions[c] for c in step.get('construction_ids', []) if c in constructions
                                and constructions[c].get('construction_kind') == 'judgment']
                    owners = [r['id'] for r in supports]
                    anchors = [a for row in supports for a in _anchors(row)]
                    refs = [ref for row in supports for ref in row.get('decision_refs', [])]
                add_node(ident, kind, label, owners or [step['id']], anchors or _anchors(step), refs,
                         output_port=port, producer_step_id=step['id'], quantity_kind=output.get('quantity_kind'),
                         anchor_scope='object' if anchors else 'supporting_step',
                         interpretations=interpretations(term_ids))
                output_nodes[step['id'], port] = ident
                add_edge(step['id'], ident, port, [step['id'], *owners], output_port=port)

    def producer(step_id, port, consumer):
        source = steps.get(step_id)
        outputs = source.get('outputs', []) if source else []
        if port is None and len(outputs) == 1:
            port = outputs[0]['port']
        if source and any(row['port'] == port for row in outputs):
            return output_nodes.get((step_id, port), step_id), port
        gaps.append({'kind': 'unresolved_output_port', 'step_id': consumer,
                     'producer_step_id': step_id, 'output_port': port})
        return None, port

    for flow in flows.values():
        uses = [i for step in steps.values() for i in step.get('inputs', []) if i.get('flow_id') == flow['id']]
        term_ids = list(dict.fromkeys(i['term_id'] for i in uses if i.get('term_id') in terms))
        anchors = term_anchors(term_ids)
        status = flow.get('status', 'unresolved_source')
        add_node(flow['id'], 'input_quantity' if status == 'linked_source' else 'unresolved_input',
                 flow['formal'], [*term_ids, flow['id']], anchors or _anchors(flow), flow.get('decision_refs', []),
                 status=status, status_label=FLOW_LABELS.get(status, status),
                 producer_source=_public_source(flow.get('producer_source')),
                 interpretations=interpretations(term_ids), term_decision_refs=term_refs(term_ids))
        if status != 'linked_source':
            gaps.append({'kind': status, 'flow_id': flow['id']})
        elif not flow.get('producer_source') and flow.get('producer_step_id') not in steps:
            gaps.append({'kind': 'linked_source_identity_unavailable', 'flow_id': flow['id']})
        if flow.get('producer_step_id') in steps:
            origin, port = producer(flow['producer_step_id'], flow.get('output_port'), flow['id'])
            if origin:
                add_edge(origin, flow['id'], port, [flow['id'], flow['producer_step_id']], output_port=port)

    def unresolved(step, item, ordinal):
        ident = 'input:' + step['id'] + ':' + str(item.get('role')) + ':' + str(ordinal)
        add_node(ident, 'unresolved_input', item.get('surface_reference') or item.get('label') or 'Unresolved input',
                 [step['id']], _anchors(step), status='unresolved_source', status_label='Source unresolved',
                 anchor_scope='supporting_step')
        gaps.append({'kind': 'unresolved_input', 'node_id': ident, 'step_id': step['id'], 'role': item.get('role')})
        return ident

    for step in steps.values():
        for ordinal, item in enumerate(step.get('inputs', [])):
            role, origin, port = item.get('role'), None, None
            owners = [step['id']]
            if item.get('from_step_id'):
                origin, port = producer(item['from_step_id'], item.get('output_port'), step['id'])
                owners.append(item['from_step_id'])
            elif item.get('flow_id') in nodes:
                origin = item['flow_id']
                owners.append(origin)
            elif 'literal' in item:
                origin = 'literal:' + step['id'] + ':' + str(role) + ':' + str(ordinal)
                anchors = _anchors(item)
                add_node(origin, 'literal', str(item['literal']), [step['id']], anchors or _anchors(step),
                         item.get('decision_refs', []), literal=deepcopy(item['literal']),
                         anchor_scope='object' if anchors else 'supporting_step')
            elif item.get('term_id') in terms:
                term = terms[item['term_id']]
                origin = term['id']
                if origin not in nodes:
                    add_node(origin, 'unresolved_input', term['surface'], [origin], _anchors(term),
                             term.get('decision_refs', []), status='not_recorded', status_label='Source status not recorded',
                             interpretations=interpretations([origin]))
                    gaps.append({'kind': 'source_status_not_recorded', 'node_id': origin})
            if not origin:
                origin = unresolved(step, item, ordinal)
            add_edge(origin, step['id'], role, owners, **({'output_port': port} if port is not None else {}))

    # Preserve flow relations even when a Step input did not carry a flow_id.
    for flow in flows.values():
        for ref in flow.get('input_refs', []):
            if ref['step_id'] in steps and not any(e['from'] == flow['id'] and e['to'] == ref['step_id']
                                                  and e['role'] == ref.get('role') for e in edges):
                add_edge(flow['id'], ref['step_id'], ref.get('role'), [flow['id'], ref['step_id']])
        for consumer in flow.get('consumer_step_ids', []):
            if consumer in steps and not any(e['from'] == flow['id'] and e['to'] == consumer for e in edges):
                add_edge(flow['id'], consumer, None, [flow['id'], consumer])

    for diagnostic in p.get('projection_diagnostics', []):
        gaps.append({k: deepcopy(diagnostic[k]) for k in
                     ('kind', 'message', 'formal', 'construction_id', 'step_id', 'flow_id', 'slot', 'consumer_step_ids')
                     if k in diagnostic})
    if not steps:
        gaps.append({'kind': 'no_projected_steps'})
    edges = _unique(edges)
    # Keep all recorded edges, including malformed/cyclic dependencies, but do
    # not advertise them as a complete DAG. No semantic repair is attempted.
    pending = {ident: 0 for ident in nodes}
    outgoing = {ident: [] for ident in nodes}
    for edge in edges:
        pending[edge['to']] += 1
        outgoing[edge['from']].append(edge['to'])
    ready = [ident for ident, count in pending.items() if count == 0]
    for ident in ready:
        for target in outgoing[ident]:
            pending[target] -= 1
            if pending[target] == 0:
                ready.append(target)
    if len(ready) != len(nodes):
        gaps.append({'kind': 'cyclic_dependencies', 'node_ids': [ident for ident, count in pending.items() if count]})
    source_index = {}
    for node in nodes.values():
        for ident in node['scholar_object_ids']:
            row = source_index.setdefault(ident, {'node_ids': [], 'source_anchors': []})
            row['node_ids'].append(node['id'])
            row['source_anchors'] = _unique([*row['source_anchors'], *node['source_anchors']])
    return {'schema': 'ProcedureModel/1', 'source': deepcopy(p.get('source', {})),
            'status': 'incomplete' if gaps else 'complete', 'nodes': list(nodes.values()),
            'edges': edges, 'source_index': source_index, 'gaps': _unique(gaps),
            'summary': {'node_count': len(nodes), 'edge_count': len(edges), 'step_count': len(steps),
                        'unresolved_flow_count': sum(f.get('status') != 'linked_source' for f in flows.values()),
                        'supporting_anchor_node_count': sum(n['anchor_scope'] == 'supporting_step' for n in nodes.values())}}


def serialize_procedure_model(model):
    """Deterministic, readable UTF-8 JSON for downloads and static snapshots."""
    if model.get('schema') != 'ProcedureModel/1':
        raise ValueError('procedure_model_serializer_requires_v1')
    return json.dumps(model, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def export_procedure_model(model, path):
    """Explicit export only; building or viewing a model never writes files."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize_procedure_model(model), encoding='utf-8', newline='\n')
    return target
