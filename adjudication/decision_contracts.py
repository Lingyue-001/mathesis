"""One versioned contract for decision payloads and semantic targets.

Source anchors remain the evidence for a decision.  This module separately
derives the object a decision changes, so replay conflict detection and the
effective reducer cannot disagree about identity.
"""
import json

from .anchors import anchor_location, validate_anchor, validate_semantic_output_address, validate_semantic_input_address


CONTRACT_VERSION = '1.0'


def _anchor_identity(anchor):
    location = list(anchor_location(anchor))
    return [*location, anchor['definition_kind']] if anchor.get('definition_kind') else location


def _require(payload, *names):
    missing = [name for name in names if payload.get(name) in (None, '', [])]
    if missing:
        raise ValueError('decision_payload_missing:' + ','.join(missing))


def normalize_decision_target(action, payload, targets):
    """Return the canonical, serializable semantic target for one action."""
    evidence = targets[0]
    if action == 'attach_context':
        return {'kind': 'context_document', 'doc_id': payload['document']['doc_id']}
    if action in ('bind_value', 'bind_call'):
        return {'kind': 'binding', 'consumer': _anchor_identity(payload['consumer_definition_anchor']),
                'formal': payload.get('formal') or payload.get('input_slot'),
                'scope': _anchor_identity(payload['scope_anchor']) if payload.get('scope_anchor') else None}
    if action == 'set_quantity_semantics':
        direction = 'input' if 'semantic_input' in payload else 'output'
        address = payload['semantic_' + direction]
        return {'kind': 'semantic_' + direction, 'definition': _anchor_identity(address['definition_anchor']),
                'construction': _anchor_identity(address['construction_anchor']),
                'construction_role': address['construction_role'], 'semantic_role': address['semantic_role'],
                **({'input_slot': address['input_slot'], 'formal': address['formal']} if direction == 'input'
                   else {'output_port': address['output_port']}),
                'invocation_path': address.get('invocation_path') or [],
                'branch_id': address['branch_id']}
    if action in ('set_term_boundary', 'set_term_interpretation'):
        return {'kind': action.removeprefix('set_'), 'source': _anchor_identity(evidence)}
    if action == 'approve_reviewed_relation':
        return {'kind': 'reviewed_relation', 'source': _anchor_identity(payload['division_anchor']),
                'invocation_path': payload['invocation_path']}
    if action in ('set_scope',):
        return {'kind': 'definition_scope', 'definition': _anchor_identity(payload['definition_anchor'])}
    if action in ('select_candidate', 'reject_candidate'):
        return {'kind': 'candidate_resolution', 'source': _anchor_identity(evidence)}
    return {'kind': 'source_occurrence', 'action': action, 'source': _anchor_identity(evidence)}


def semantic_target_key(action, payload, targets):
    return json.dumps(normalize_decision_target(action, payload, targets), ensure_ascii=False,
                      sort_keys=True, separators=(',', ':'))


def validate_action_payload(packet, action, payload, targets):
    """Validate fields and stable addresses that do not need a compiler snapshot."""
    if action == 'select_candidate':
        _require(payload, 'selected_candidate_id')
    elif action == 'reject_candidate':
        _require(payload, 'candidate_id')
    elif action == 'resegment':
        _require(payload, 'segments')
        if not isinstance(payload['segments'], list):
            raise ValueError('resegment_segments_must_be_list')
        for segment in payload['segments']:
            validate_anchor(packet, segment)
    elif action == 'set_scope':
        _require(payload, 'definition_anchor')
        validate_anchor(packet, payload['definition_anchor'])
        if payload.get('procedure_role') not in (None, 'independent', 'followup'):
            raise ValueError('invalid_procedure_role')
        if payload.get('procedure_role') == 'followup':
            _require(payload, 'parent_definition_anchor', 'query_base_anchor')
        if payload.get('procedure_role') == 'independent' and any(
                payload.get(key) for key in ('parent_definition_anchor', 'query_base_anchor')):
            raise ValueError('independent_procedure_has_no_parent_or_base')
        for name in ('parent_definition_anchor', 'query_base_anchor'):
            if payload.get(name) is not None:
                validate_anchor(packet, payload[name])
    elif action in ('bind_value', 'bind_call'):
        _require(payload, 'consumer_definition_anchor', 'producer_definition_anchor')
        if not (payload.get('formal') or payload.get('input_slot')):
            raise ValueError('binding_requires_formal_or_input_slot')
        validate_anchor(packet, payload['consumer_definition_anchor'])
        validate_anchor(packet, payload['producer_definition_anchor'])
        if payload.get('scope_anchor') is not None:
            validate_anchor(packet, payload['scope_anchor'])
    elif action == 'set_quantity_semantics':
        if bool(payload.get('semantic_input')) == bool(payload.get('semantic_output')):
            raise ValueError('quantity_requires_one_semantic_address')
        if 'semantic_input' in payload:
            validate_semantic_input_address(packet, payload['semantic_input'])
        else:
            validate_semantic_output_address(packet, payload.get('semantic_output'))
        if 'facets' in payload:
            from .quantity_targets import validate_quantity_facets
            validate_quantity_facets(payload['facets'])
    elif action == 'set_term_boundary':
        from .term_claims import validate_term_boundary
        validate_term_boundary(packet, targets[0], payload.get('branch_id', 'main'))
    elif action == 'set_term_interpretation':
        _require(payload, 'claim')
        claim = payload['claim']
        if claim.get('schema') != 'TermInterpretationClaim/1':
            raise ValueError('unsupported_term_interpretation_contract')
        from .anchors import anchor_key
        validate_anchor(packet, claim.get('anchor'))
        if anchor_key(claim['anchor']) != anchor_key(targets[0]):
            raise ValueError('term_interpretation_target_mismatch')
    elif action == 'approve_reviewed_relation':
        from .reviewed_relations import validate_relation_payload
        validate_relation_payload(packet, payload)
        from .anchors import anchor_key
        if anchor_key(payload['division_anchor']) != anchor_key(targets[0]):
            raise ValueError('relation_target_must_be_attested_division')
    elif action == 'select_profile':
        _require(payload, 'profile_id')
    elif action == 'attach_context':
        document = payload.get('document')
        if not isinstance(document, dict) or not document.get('doc_id') or not document.get('text'):
            raise ValueError('attach_context_requires_complete_document')
    elif action == 'declare_parameter':
        _require(payload, 'name', 'unit', 'role', 'evidence_basis')
        if payload.get('role') not in ('root_input', 'parameter'):
            raise ValueError('parameter_role_and_evidence_required')
    elif action == 'assemble_known_structure':
        _require(payload, 'candidates')
        if not isinstance(payload['candidates'], list):
            raise ValueError('manual_structure_candidates_must_be_list')
    elif action == 'defer':
        if not (payload.get('unresolved') or payload.get('schema_extension_required')):
            raise ValueError('defer_requires_unresolved_or_extension_reason')
    elif action == 'retract':
        _require(payload, 'decision_id')
    return normalize_decision_target(action, payload, targets)
