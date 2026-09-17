"""Narrow corpus → compiler → executor orchestration shared by HTTP and tests."""
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from source_adapters.corpus import build_source_packet
from workbench.projection import project_graph


def analyze_procedure(root, procedure_id):
    source = build_source_packet(root, procedure_id)
    graph = parse_packet(source['source_packet'])
    projection = project_graph(graph)
    return {
        **source, 'graph': graph, 'projection': projection,
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
    }
