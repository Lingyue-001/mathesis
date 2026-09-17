"""Source-to-structure coverage and graph closure checks."""
from .anchors import anchor_for
from analysis_parser.audit import audit


def _span_key(span):
    return span['doc_id'], span.get('reading_id'), span['start'], span['end']


def build_coverage_ledger(packet, graph, effective=None, replay=None):
    effective = effective or {}
    accounts = []
    for definition in graph.get('program', {}).get('definitions', []):
        layer = 'procedure' if definition.get('kind') == 'ProcedureDef' else 'stage' if definition.get('kind') == 'QueryDef' else 'context'
        for span in definition.get('source_spans', []):
            accounts.append({'span': span, 'layer': layer, 'definition_id': definition['id'],
                             'source_role': definition.get('source_role')})
    for event in graph.get('events', []):
        for span in event.get('source_spans', []):
            accounts.append({'span': span, 'layer': 'control' if event['kind'] in ('threshold', 'branch', 'condition') else 'operation',
                             'graph_node_id': event['id'], 'syntax_node_id': event.get('syntax_node_id'),
                             'decision_refs': event.get('adjudication_decision_refs', [])})
    for value in graph.get('value_instances', []):
        for span in value.get('source_spans', []):
            accounts.append({'span': span, 'layer': 'quantity', 'graph_node_id': value['id'],
                             'producer': value.get('producer'), 'decision_refs': value.get('adjudication_decision_refs', [])})
    # A declaration does not establish that an apparent gap is non-computational.
    # It remains visible until compiler evidence proves it does not hide a needed node.
    for row in effective.get('deferred', []):
        accounts.append({'span': row['target'], 'layer': 'unresolved', 'decision_refs': [row['decision_id']]})
    unresolved_required_spans = []
    for category in ('primary_documents', 'context_documents'):
        for doc in packet.get(category, []):
            covered = [account['span'] for account in accounts if account['span']['doc_id'] == doc['doc_id']]
            for offset, char in enumerate(doc['text']):
                if char.isspace() or char in '，。；、,.!?！？：:（）()':
                    continue
                if not any(span['start'] <= offset < span['end'] for span in covered):
                    unresolved_required_spans.append(anchor_for(packet, doc['doc_id'], offset, offset + 1))
    events = {event['id']: event for event in graph.get('events', [])}
    values = {value['id']: value for value in graph.get('value_instances', [])}
    missing_node_evidence = [event['id'] for event in events.values() if not event.get('source_spans')]
    missing_producers = [value['id'] for value in values.values()
                         if value.get('role') not in ('parameter', 'input', 'literal', 'missing_upstream')
                         and value.get('producer') not in events]
    unresolved_quantities = [value['id'] for value in values.values()
                             if value.get('resolution_status') == 'unknown']
    legal_inputs = set((effective.get('parameters') or {}).keys())
    # Re-run structural audit on the graph being judged. The ledger must not
    # trust a diagnostic list that may have been created before a later graph
    # transformation or test corruption.
    # Lightweight fixture graphs may intentionally omit their source-document
    # inventory. In that case audit cannot judge span validity; the ledger
    # still reports coverage, but does not manufacture an invalid-source error.
    structural_diagnostics = audit(graph) if graph.get('documents') else []
    diagnostics = list(graph.get('diagnostics', []))
    diagnostics.extend(graph.get('program', {}).get('linked', {}).get('diagnostics', []))
    missing_inputs = []
    for diagnostic in diagnostics:
        if diagnostic.get('kind') == 'missing_import' and diagnostic.get('formal') not in legal_inputs:
            missing_inputs.append(diagnostic)
    invalid = structural_diagnostics + [row for row in diagnostics
               if row.get('kind') in ('type_error', 'invalid_unit_transition', 'dependency_cycle', 'invalid_review_binding')]
    decision_states = (replay or {}).get('decision_status', {})
    unstable_decisions = [decision_id for decision_id, state in decision_states.items()
                          if state.get('status') in ('needs_revalidation', 'conflicted')]
    noncomputational_unvalidated = [row['decision_id'] for row in effective.get('noncomputational', [])]
    if invalid:
        graph_status = 'invalid'
    elif (unresolved_required_spans or missing_node_evidence or missing_producers or unresolved_quantities or missing_inputs
          or graph.get('unresolved') or effective.get('deferred') or unstable_decisions or noncomputational_unvalidated):
        graph_status = 'partial'
    else:
        graph_status = 'closed'
    return {'schema': 'SourceStructureCoverageLedger', 'schema_version': '1.0',
            'accounts': accounts, 'unresolved_required_spans': unresolved_required_spans,
            'node_without_source_evidence': missing_node_evidence, 'derived_without_producer': missing_producers,
            'quantities_needing_semantics': unresolved_quantities,
            'necessary_inputs_without_legal_origin': missing_inputs,
            'structural_diagnostics': structural_diagnostics,
            'unstable_decisions': unstable_decisions,
            'noncomputational_needing_validation': noncomputational_unvalidated,
            'graph_status': graph_status}
