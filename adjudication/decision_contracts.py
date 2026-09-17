"""One versioned contract for decision payloads and semantic targets.

Source anchors remain the evidence for a decision.  This module separately
derives the object a decision changes, so replay conflict detection and the
effective reducer cannot disagree about identity.
"""
import json

from .anchors import anchor_location, validate_anchor, validate_semantic_output_address


CONTRACT_VERSION = '1.0'


def _anchor_identity(anchor):
    return anchor_location(anchor)


def _require(payload, *names):
    missing = [name for name in names if payload.get(name) in (None, '', [])]
    if missing:
        raise ValueError('decision_payload_missing:' + ','.join(missing))


def normalize_decision_target(action, payload, targets):
    """Return the canonical, serializable semantic target for one action."""
    evidence = targets[0]
    if action in ('bind_value', 'bind_call'):
        return {'kind': 'binding', 'consumer': _anchor_identity(payload['consumer_definition_anchor']),
                'formal': payload.get('formal') or payload.get('input_slot'),
                'scope': _anchor_identity(payload['scope_anchor']) if payload.get('scope_anchor') else None}
    if action == 'set_quantity_semantics':
        address = payload['semantic_output']
        return {'kind': 'semantic_output', 'definition': _anchor_identity(address['definition_anchor']),
                'construction': _anchor_identity(address['construction_anchor']),
                'construction_role': address['construction_role'], 'semantic_role': address['semantic_role'],
                'output_port': address['output_port'], 'invocation_path': address.get('invocation_path'),
                'branch_id': address['branch_id']}
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
        validate_semantic_output_address(packet, payload.get('semantic_output'))
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
