"""Validation gates that human decisions cannot bypass."""
from .anchors import overlaps
from .registry import validate_manual_structure, validate_quantity_semantics


def validate_effective_decisions(effective):
    issues = []
    for payload in effective.get('parameters', {}).values():
        if payload.get('derived_role') or payload.get('root_input') is False:
            issues.append({'kind': 'invalid_parameter_declaration', 'decision_id': payload['decision_id'],
                           'reason': 'derived quantities cannot be converted into parameters'})
    for payload in effective.get('quantity_semantics', {}).values():
        try:
            if 'facets' in payload:
                from .quantity_targets import validate_quantity_facets
                validate_quantity_facets(payload['facets'])
            else:
                validate_quantity_semantics(payload)
        except ValueError as error:
            issues.append({'kind': 'invalid_quantity_semantics', 'decision_id': payload['decision_id'], 'reason': str(error)})
        if payload.get('conversion') and not payload.get('conversion_evidence'):
            issues.append({'kind': 'requires_conversion_evidence', 'decision_id': payload['decision_id']})
    for payload in effective.get('manual_structures', []):
        try:
            validate_manual_structure(payload)
        except ValueError as error:
            issues.append({'kind': 'schema_extension_required', 'decision_id': payload['decision_id'], 'reason': str(error)})
    for payload in effective.get('candidate_selection_metadata', {}).values():
        if not payload.get('candidate_set_complete', True):
            issues.append({'kind': 'truncated_candidate_set', 'decision_id': payload['decision_id'],
                           'reason': 'candidate list was truncated and cannot close review'})
    return issues


def validate_root_parameters(program, effective):
    """A root is legal only when the compiled procedure has no producer for it."""
    produced = {name for definition in program.definitions
                for name in definition.get('defined_values', {})}
    formal_inputs = {name for definition in program.definitions
                     for name in definition.get('formal_inputs', {})}
    issues = []
    for name, payload in effective.get('parameters', {}).items():
        if not payload.get('root_input', True):
            continue
        if name in produced:
            issues.append({'kind': 'invalid_parameter_declaration', 'decision_id': payload['decision_id'],
                           'reason': 'source_derived_value_cannot_be_root_input'})
        elif formal_inputs and name not in formal_inputs:
            issues.append({'kind': 'invalid_parameter_declaration', 'decision_id': payload['decision_id'],
                           'reason': 'root_input_not_a_required_formal'})
    return issues


def validate_comparison_operands(left, right):
    """Reject equality/order comparisons across incompatible time origins/scales."""
    if left.get('unit') != right.get('unit'):
        return {'valid': False, 'kind': 'incompatible_units'}
    if left.get('time_frame') != right.get('time_frame') or left.get('epoch') != right.get('epoch'):
        return {'valid': False, 'kind': 'incompatible_time_origin'}
    return {'valid': True, 'kind': 'compatible'}


def validate_control_coverage(graph, effective):
    controls = [event for event in graph.get('events', []) if event.get('kind') in ('threshold', 'branch', 'condition')]
    invalid = []
    for decision in effective.get('noncomputational', []):
        for control in controls:
            if any(overlaps(decision['target'], span) for span in control.get('source_spans', [])):
                invalid.append({'kind': 'required_control_marked_noncomputational',
                                'decision_id': decision['decision_id'], 'event_id': control['id']})
    return invalid


def validate_graph_closure(graph, ledger, effective):
    issues = validate_effective_decisions(effective) + validate_control_coverage(graph, effective)
    if ledger['graph_status'] != 'closed':
        issues.append({'kind': 'graph_not_closed', 'graph_status': ledger['graph_status']})
    return {'valid_for_complete_export': not issues, 'issues': issues}
