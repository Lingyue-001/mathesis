"""Compiler pause questions, produced without a UI dependency."""

def build_review_queue(graph, replay, uncovered=()):
    items = []
    diagnostics = list(graph.get('diagnostics', []))
    diagnostics.extend(graph.get('program', {}).get('linked', {}).get('diagnostics', []))
    for diagnostic in diagnostics:
        kind = diagnostic.get('kind')
        if kind in ('missing_import', 'ambiguous_import', 'ambiguous_operation_import', 'missing_operation_import'):
            items.append({'kind': 'missing_input' if kind == 'missing_import' else 'producer_or_port_ambiguity',
                          'severity': 'blocking', 'source_spans': diagnostic.get('source_spans', []),
                          'source_anchors': diagnostic.get('source_spans', []), 'reason': kind,
                          'affected_outputs': diagnostic.get('uses', []),
                          'details': diagnostic, 'suggested_actions': ['declare_parameter', 'bind_value', 'bind_call']})
        elif kind in ('UnsupportedConstruction', 'unclassified'):
            items.append({'kind': 'no_legal_candidate', 'severity': 'blocking', 'source_spans': diagnostic.get('source_spans', []), 'source_anchors': diagnostic.get('source_spans', []), 'reason': kind, 'affected_outputs': [],
                          'details': diagnostic, 'suggested_actions': ['resegment', 'assemble_known_structure', 'defer']})
        elif kind == 'invalid_review_binding':
            items.append({'kind': 'invalid_review_binding', 'severity': 'blocking',
                          'source_spans': diagnostic.get('source_spans', []),
                          'source_anchors': diagnostic.get('source_spans', []),
                          'reason': 'binding_not_structurally_compatible', 'affected_outputs': [],
                          'details': diagnostic, 'suggested_actions': ['set_scope', 'bind_value', 'retract']})
    for issue in graph.get('unresolved', []):
        cause = issue.get('cause')
        kind = 'missing_context_or_profile' if cause in ('requires_external_data', 'missing_query_base') else 'no_legal_candidate'
        queue_kind = 'ontology_extension_required' if cause == 'schema_extension_required' else kind
        items.append({'kind': queue_kind, 'severity': 'blocking', 'source_spans': issue.get('source_spans', []), 'source_anchors': issue.get('source_spans', []), 'reason': cause, 'affected_outputs': [],
                      'details': issue, 'suggested_actions': ['attach_context', 'select_profile', 'defer']})
    for value in graph.get('value_instances', []):
        if value.get('resolution_status') == 'unknown' or (value.get('unit') in ('unknown', 'opaque', 'product')
                                                            and value.get('resolution_status') != 'resolved'):
            items.append({'kind': 'quantity_semantics', 'severity': 'review', 'source_spans': value.get('source_spans', []), 'source_anchors': value.get('source_spans', []), 'reason': 'unknown_quantity_semantics', 'affected_outputs': [value['id']],
                          'details': {'value_id': value['id'], 'unit': value.get('unit')},
                          'suggested_actions': ['set_quantity_semantics', 'defer']})
    for decision_id, state in replay.get('decision_status', {}).items():
        if state['status'] in ('needs_revalidation', 'conflicted'):
            items.append({'kind': 'stale_decision' if state['status'] == 'needs_revalidation' else 'decision_conflict',
                          'severity': 'blocking', 'source_spans': [], 'source_anchors': [], 'reason': state['reasons'], 'affected_outputs': [], 'details': {'decision_id': decision_id, **state},
                          'suggested_actions': ['retract', 'bind_value', 'resegment']})
    for anchor in uncovered:
        items.append({'kind': 'uncovered_source', 'severity': 'blocking', 'source_spans': [anchor],
                      'source_anchors': [anchor], 'reason': 'necessary_source_not_accounted',
                      'affected_outputs': [], 'details': {}, 'suggested_actions': ['resegment', 'assemble_known_structure', 'defer']})
    return {'schema': 'ReviewQueue', 'schema_version': '1.0', 'items': items}
