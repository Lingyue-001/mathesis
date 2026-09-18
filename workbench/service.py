"""Narrow corpus → compiler → executor orchestration shared by HTTP and tests."""
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from adjudication import append_decision, compile_reviewed, create_branch, new_session
from adjudication.bundle import make_bundle
from source_adapters.corpus import build_source_packet
from workbench.projection import project_graph
from workbench.presentation import build_presentation
from source_adapters.dependencies import artifact


def _artifacts(packet, graph):
    parser = artifact('parser', graph, packet=packet)
    return [parser, artifact('graph', graph, parents=[parser])]


def analyze_procedure(root, procedure_id):
    source = build_source_packet(root, procedure_id)
    graph = parse_packet(source['source_packet'])
    projection = project_graph(graph)
    return {
        **source, 'graph': graph, 'projection': projection,
        'artifacts': _artifacts(source['source_packet'], graph),
        'summary': {
            'graph_status': 'issues' if projection['issues'] else 'compiled',
            'execution_status': 'not_run',
            'event_count': len(graph['events']),
            'value_count': len(graph['value_instances']),
        },
    }


def compile_procedure(root, procedure_id, inputs):
    source = analyze_procedure(root, procedure_id)
    contract = {item['name']: item for item in source['procedure']['inputs']}
    if not isinstance(inputs, dict) or set(inputs) - set(contract):
        raise ValueError('invalid_inputs: use declared input names')
    for name, value in inputs.items():
        spec = contract[name]
        if (spec['type'] != 'integer' or type(value) is not int
                or not spec['minimum'] <= value <= spec['maximum']):
            raise ValueError(f"invalid_input: {name} must be an integer in {spec['minimum']}–{spec['maximum']}")
    graph = source['graph']
    execution = execute(graph, inputs)
    unresolved = {
        'compiler': graph.get('unresolved', []),
        'diagnostics': graph.get('diagnostics', []),
        'unparsed_spans': graph.get('coverage', {}).get('unparsed_spans', []),
        'execution': execution.get('unresolved', []),
    }
    missing = any(row.get('cause') == 'requires_explicit_input' for row in unresolved['execution'])
    graph_issues = bool(source['projection']['issues'])
    return {
        **source,
        'summary': {
            'graph_status': 'issues' if graph_issues else 'compiled',
            'execution_status': 'missing_inputs' if missing else 'unresolved' if unresolved['execution'] else 'executed',
            'event_count': len(graph['events']),
            'value_count': len(graph['value_instances']),
        },
        'unresolved': unresolved,
        'graph': graph,
        'execution': execution,
        'artifacts': [*source['artifacts'], artifact('execution', {'inputs': inputs, 'execution': execution},
                                                   parents=[source['artifacts'][-1]])],
    }


def _stage_records(source, bundle):
    """Describe completed compiler products; this is not a progress simulation."""
    graph = bundle['graph']
    queue = bundle['review_queue']['items']
    coverage = bundle['coverage_ledger']
    status = lambda needed: 'needs_review' if needed else 'completed'
    blocked = coverage['graph_status'] == 'invalid'
    return [
        {'id': 'source_scope', 'label': '来源与范围核验', 'status': 'completed',
         'inputs': ['canonical corpus', 'procedure registry'],
         'artifacts': [{'kind': 'source_packet', 'packet_id': source['source_packet']['packet_id']},
                       {'kind': 'documents', 'count': len(graph.get('documents', []))}],
         'rules': ['source_adapter_hash_and_section_validation'], 'affected_stages': ['lexical_syntax']},
        {'id': 'lexical_syntax', 'label': '词项／构式候选',
         'status': status(bool(graph.get('syntax', {}).get('diagnostics'))),
         'inputs': ['SourcePacket documents'],
         'artifacts': [{'kind': 'tokens', 'count': len(graph.get('tokens', []))},
                       {'kind': 'construction_candidates', 'count': len(graph.get('construction_candidates', []))}],
         'rules': ['analysis_parser.lexical', 'analysis_parser.construction_ir'],
         'affected_stages': ['procedure_control', 'quantity_binding']},
        {'id': 'procedure_control', 'label': '过程与控制结构',
         'status': status(bool(graph.get('program', {}).get('diagnostics'))),
         'inputs': ['syntax candidates'],
         'artifacts': [{'kind': 'definitions', 'count': len(graph.get('program', {}).get('definitions', []))}],
         'rules': ['analysis_parser.program_ir'], 'affected_stages': ['quantity_binding', 'graph_coverage']},
        {'id': 'quantity_binding', 'label': '数量／来源／端口绑定',
         'status': status(any(item['kind'] in ('missing_input', 'producer_or_port_ambiguity', 'quantity_semantics') for item in queue)),
         'inputs': ['program definitions', 'binding constraints'],
         'artifacts': [{'kind': 'values', 'count': len(graph.get('value_instances', []))},
                       {'kind': 'events', 'count': len(graph.get('events', []))}],
         'rules': ['analysis_parser.link_entry', 'adjudication.binding_constraints'],
         'affected_stages': ['graph_coverage', 'review']},
        {'id': 'graph_coverage', 'label': '图与覆盖检查',
         'status': 'blocked' if blocked else status(coverage['graph_status'] != 'closed'),
         'inputs': ['typed graph', 'coverage ledger'],
         'artifacts': [{'kind': 'graph_status', 'value': coverage['graph_status']},
                       {'kind': 'unresolved_required_spans', 'count': len(coverage['unresolved_required_spans'])}],
         'rules': ['SourceStructureCoverageLedger'], 'affected_stages': ['review']},
        {'id': 'review', 'label': '待审定或审定完成', 'status': status(bool(queue)),
         'inputs': ['review queue', 'replay status'],
         'artifacts': [{'kind': 'review_questions', 'count': len(queue)}],
         'rules': ['adjudication.review_queue'], 'affected_stages': []},
    ]


def _reviewed_response(source, session, branch_id):
    compilation = compile_reviewed(source['source_packet'], session, branch_id)
    bundle = make_bundle(compilation, session)
    graph = bundle.get('graph')
    projection = project_graph(graph, bundle) if graph is not None else {
        'projection_version': 2, 'frames': [], 'steps': [], 'nodes': [], 'edges': [], 'quantities': [],
        'issues': [], 'layers': {}, 'coverage': None, 'review_queue': bundle['review_queue'], 'trace': None,
    }
    response = {
        **source, 'session': session, 'branch_id': branch_id, 'bundle': bundle, 'graph': graph,
        'projection': projection,
        'stages': _stage_records(source, bundle) if graph is not None else [
            {'id': 'source_scope', 'label': '来源与范围核验', 'status': 'stale', 'inputs': [],
             'artifacts': [], 'rules': [], 'affected_stages': []}],
        'summary': {
            'graph_status': bundle['coverage_ledger']['graph_status'] if graph is not None else 'invalid',
            'review_status': ('needs_revalidation' if graph is None else
                              'needs_review' if bundle['review_queue']['items'] else 'completed'),
            'execution_status': 'not_run',
            'comparison_status': 'unavailable',
        },
    }
    if graph is None:
        # A blocked replay is not an empty successful analysis. Keep its session
        # and graph=None; provide a separately labelled, decision-free reference
        # through the same compiler so the current source remains inspectable.
        reference = _reviewed_response(source, new_session(source['source_packet'],
                                       f"workbench:{source['procedure']['id']}"), 'main')
        response['reference_analysis'] = {
            'kind': 'current_automatic_reference',
            **{key: reference[key] for key in ('graph', 'projection', 'stages', 'summary')},
        }
    response['presentation'] = build_presentation(response)
    response['artifacts'] = _artifacts(source['source_packet'], graph) if graph is not None else []
    bundle['artifacts'] = response['artifacts']
    return response


def open_adjudication(root, procedure_id, session=None, branch_id='main'):
    """Open a real reviewed compiler session for one registered corpus procedure."""
    source = build_source_packet(root, procedure_id)
    session = session or new_session(source['source_packet'], f'workbench:{procedure_id}')
    return _reviewed_response(source, session, branch_id)


def compile_adjudication(root, procedure_id, session, branch_id='main'):
    """Recompile a supplied session; all graph changes flow through the reviewed compiler."""
    if not isinstance(session, dict) or session.get('schema') != 'AdjudicationSession':
        raise ValueError('invalid_adjudication_session')
    return _reviewed_response(build_source_packet(root, procedure_id), session, branch_id)


def execute_adjudication(root, procedure_id, session, branch_id, inputs):
    """Run the numerical check against the reviewed graph currently on screen."""
    result = compile_adjudication(root, procedure_id, session, branch_id)
    contract = {item['name']: item for item in result['procedure']['inputs']}
    if not isinstance(inputs, dict) or set(inputs) - set(contract):
        raise ValueError('invalid_inputs: use declared input names')
    for name, value in inputs.items():
        spec = contract[name]
        if (spec['type'] != 'integer' or type(value) is not int
                or not spec['minimum'] <= value <= spec['maximum']):
            raise ValueError(f"invalid_input: {name} must be an integer in {spec['minimum']}–{spec['maximum']}")
    if result['graph'] is None:
        raise ValueError('reviewed_graph_unavailable')
    execution = execute(result['graph'], inputs)
    missing = any(row.get('cause') == 'requires_explicit_input' for row in execution.get('unresolved', []))
    result['execution'] = execution
    result['artifacts'] = [*result['artifacts'], artifact('execution', {'inputs': inputs, 'execution': execution},
                                                       parents=[result['artifacts'][-1]])]
    result['bundle']['artifacts'] = result['artifacts']
    result['summary'] = {**result['summary'], 'execution_graph': 'reviewed',
                         'execution_status': 'missing_inputs' if missing else 'unresolved' if execution.get('unresolved') else 'executed'}
    result['presentation'] = build_presentation(result)
    return result


def apply_adjudication_decision(root, procedure_id, session, decision, branch_id='main'):
    """Append one validated human decision, then recompile the affected reviewed model."""
    source = build_source_packet(root, procedure_id)
    append_decision(session, decision, packet=source['source_packet'])
    return _reviewed_response(source, session, branch_id)


def branch_adjudication(root, procedure_id, session, branch_id, from_branch='main'):
    """Create an explicit interpretation branch without overwriting its parent."""
    create_branch(session, branch_id, from_branch)
    return _reviewed_response(build_source_packet(root, procedure_id), session, branch_id)
