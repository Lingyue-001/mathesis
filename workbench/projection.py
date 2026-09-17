"""Read-only IR → researcher view. No parsing, inference, execution or repair.

Definition/body order is the hierarchy; event reads/writes are the graph edges.
Source-overlap links are explicitly distinguished from compiler node-ID links.
Unknown types and diagnostics from every IR layer remain visible.
"""
from copy import deepcopy


def _overlap(left, right):
    return any(a.get('doc_id') == b.get('doc_id')
               and a.get('reading_id') == b.get('reading_id')
               and a['start'] < b['end'] and b['start'] < a['end']
               for a in left for b in right)


def _layer_rows(graph, bundle, steps):
    """Expose source evidence by research layer without imposing one label per character."""
    ledger = (bundle or {}).get('coverage_ledger', {})
    accounts = ledger.get('accounts', [])
    layers = {
        'L0': [{'kind': 'source_reading', 'span': {'doc_id': doc['doc_id'], 'reading_id': doc['reading_id'],
                                                    'start': 0, 'end': len(doc['text'])},
                'evidence_basis': 'source'} for doc in graph.get('documents', [])],
        'L1': [], 'L2': [], 'L3': [],
    }
    for account in accounts:
        layer = {'procedure': 'L1', 'stage': 'L1', 'context': 'L1', 'operation': 'L2',
                 'control': 'L2', 'quantity': 'L3', 'unresolved': 'L3'}.get(account['layer'])
        if layer:
            layers[layer].append({'kind': account['layer'], 'span': account['span'],
                                  'object_id': account.get('graph_node_id') or account.get('definition_id'),
                                  'decision_refs': account.get('decision_refs', []),
                                  'evidence_basis': 'compiler_or_reviewed_graph'})
    for candidate in graph.get('construction_candidates', []):
        for span in candidate.get('source_spans', []):
            layers['L3'].append({'kind': 'construction_candidate', 'span': span,
                                 'object_id': candidate.get('node_id'), 'production_id': candidate.get('production_id'),
                                 'evidence_basis': 'parser_rule'})
    return layers


def _review_questions(graph, bundle):
    queue = (bundle or {}).get('review_queue', {'items': []})
    candidates = graph.get('construction_candidates', [])
    questions = []
    for index, item in enumerate(queue.get('items', [])):
        spans = item.get('source_anchors') or item.get('source_spans') or []
        options = [{'id': row.get('node_id'), 'kind': row.get('kind'), 'surface': row.get('text'),
                    'production_id': row.get('production_id'), 'source_spans': row.get('source_spans', [])}
                   for row in candidates if any(_overlap(row.get('source_spans', []), [span]) for span in spans)]
        questions.append({**item, 'id': item.get('id', f'review-{index + 1}'),
                          'candidate_options': options,
                          'evidence': [{'basis': option.get('production_id'), 'source_spans': option['source_spans']}
                                       for option in options]})
    return questions


def project_graph(report, bundle=None):
    graph = deepcopy(report)
    syntax = graph.get('syntax', {})
    program = graph.get('program', {})
    ast = {node['id']: node for node in syntax.get('nodes', [])}
    definitions = {frame['id']: frame for frame in program.get('definitions', [])}
    quantities = graph.get('value_instances', [])
    values = {value['id']: value for value in quantities}
    events = graph.get('events', [])
    steps = []
    # Program bodies can refer to operations inside a composed syntax root.
    step_ids = list(dict.fromkeys([*syntax.get('roots', []),
                                  *(ident for frame in definitions.values() for ident in frame.get('body', []) if ident in ast)]))
    for ident in step_ids:
        node = ast[ident]
        owners = [f['id'] for f in definitions.values() if ident in f.get('body', [])]
        steps.append({
            'id': ident, 'kind': node['kind'], 'surface': node.get('surface', ''),
            'frame_ids': owners, 'source_spans': node.get('source_spans', []),
            'slots': {key: {'node_id': ref, 'surface': ast.get(ref, {}).get('surface', '')}
                      for key, ref in node.get('slots', {}).items()},
            'event_ids': [], 'graph_links': [], 'issue_ids': [],
        })
    frames = []
    for frame in definitions.values():
        frames.append({
            **frame,
            'label': frame.get('goal_surface') or ('Context' if frame.get('source_role') == 'context' else frame['kind']),
            'body': [{'type': 'frame' if ident in definitions else 'step', 'id': ident}
                     for ident in frame.get('body', [])],
        })

    nodes = []
    edges = []
    for event in events:
        linked = []
        for step in steps:
            direct = event.get('syntax_node_id') == step['id']
            shared = _overlap(event.get('source_spans', []), step['source_spans'])
            if direct or shared:
                step['event_ids'].append(event['id'])
                step['graph_links'].append({'event_id': event['id'], 'basis': 'syntax_node_id' if direct else 'shared_source_span'})
                linked.append(step['id'])
        nodes.append({**event, 'step_ids': linked})
        for port, value_id in event.get('reads', {}).items():
            value = values.get(value_id, {})
            edges.append({
                'producer': value.get('producer'), 'output_port': value.get('output_port'),
                'value_id': value_id, 'consumer': event['id'], 'input_port': port,
            })

    issues = []
    channels = [
        ('compiler', graph.get('unresolved', [])),
        ('diagnostics', graph.get('diagnostics', [])),
        ('coverage', graph.get('coverage', {}).get('unparsed_spans', [])),
        ('syntax', syntax.get('diagnostics', [])),
        ('program', program.get('diagnostics', [])),
        ('linker', program.get('linked', {}).get('diagnostics', [])),
    ]
    for origin, records in channels:
        for record in records:
            issues.append({**record, 'origin': origin, 'kind': record.get('kind', record.get('cause', 'unresolved'))})
    for value in quantities:
        status = value.get('resolution_status')
        if status != 'resolved':
            issues.append({'origin': 'quantity', 'kind': 'quantity_unresolved', 'value_id': value['id'],
                           'event_id': value.get('producer'), 'status': status or 'not_recorded',
                           'source_spans': value.get('source_spans', [])})
    for i, issue in enumerate(issues):
        issue['id'] = f'issue-{i + 1}'
        spans = issue.get('source_spans', [])
        if not spans and 'doc_id' in issue and 'start' in issue and 'end' in issue:
            spans = [issue]
        for step in steps:
            if (issue.get('node_id') == step['id'] or issue.get('event_id') in step['event_ids']
                    or _overlap(spans, step['source_spans'])):
                step['issue_ids'].append(issue['id'])

    review_questions = _review_questions(graph, bundle)
    return {
        'projection_version': 2,
        'frames': frames, 'steps': steps, 'nodes': nodes, 'edges': edges,
        'quantities': quantities, 'issues': issues,
        'calls': program.get('calls', []), 'imports': program.get('imports', []),
        'branches': graph.get('branches', []),
        'layers': _layer_rows(graph, bundle, steps),
        'coverage': (bundle or {}).get('coverage_ledger'),
        'review_queue': {'schema': 'ReviewQueue', 'schema_version': '1.0', 'items': review_questions},
        'trace': (bundle or {}).get('trace'),
    }
