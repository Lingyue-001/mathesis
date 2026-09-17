"""ReviewedProcedureBundle 1.x export; distinct from SourcePacket 3.x."""
from .metrics import decision_metrics
from .validation import validate_graph_closure


def make_bundle(compilation, session):
    graph = compilation.get('graph')
    if graph is None:
        return {**compilation, 'validation': {'valid_for_complete_export': False,
                                               'issues': [{'kind': 'stale_source'}]},
                'metrics': decision_metrics(session)}
    validation = validate_graph_closure(graph, compilation['coverage_ledger'], compilation['replay']['effective'])
    return {**compilation, 'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0',
            'validation': validation, 'metrics': decision_metrics(session)}
