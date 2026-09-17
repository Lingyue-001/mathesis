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


def project_graph(report):
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

    return {
        'projection_version': 1,
        'frames': frames, 'steps': steps, 'nodes': nodes, 'edges': edges,
        'quantities': quantities, 'issues': issues,
        'calls': program.get('calls', []), 'imports': program.get('imports', []),
        'branches': graph.get('branches', []),
    }
