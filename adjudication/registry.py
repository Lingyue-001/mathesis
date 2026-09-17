"""Versioned signatures for existing lowerer primitives only."""
import hashlib
import json
from analysis_parser.resources import PROFILES


OPERATION_CONTRACTS = {
    'task_marker': {'required': {'marker': ('source_anchor',), 'target': ('source_anchor',)}, 'optional': {}, 'outputs': ()},
    'query_marker': {'required': {'target': ('source_anchor',)}, 'optional': {}, 'outputs': ()},
    'load': {'required': {'value': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor')}, 'optional': {'decrement': ('literal',)}, 'outputs': ('result',)},
    'multiply': {'required': {'left': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor', 'literal'), 'right': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor', 'literal')}, 'optional': {}, 'outputs': ('result',)},
    'divide': {'required': {'value': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor'), 'divisor': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor', 'literal')}, 'optional': {}, 'outputs': ('quotient', 'remainder')},
    'name': {'required': {'label': ('source_anchor',)}, 'optional': {}, 'outputs': ('result',)},
    'remainder_name': {'required': {'label': ('source_anchor',)}, 'optional': {}, 'outputs': ('remainder',)},
    'threshold': {'required': {'value': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor'), 'lower': ('literal', 'quantity_ref', 'context_declaration')}, 'optional': {}, 'outputs': ('result',)},
    'judgment': {'required': {}, 'optional': {}, 'outputs': ()},
    'add': {'required': {'amount': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor', 'literal')}, 'optional': {}, 'outputs': ('result',)},
    'subtract': {'required': {'left': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor', 'literal'), 'right': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor', 'literal')}, 'optional': {}, 'outputs': ('result',)},
    'declaration': {'required': {'label': ('source_anchor',), 'value': ('literal',)}, 'optional': {}, 'outputs': ('result',)},
    'update': {'required': {'receiver': ('quantity_ref', 'source_anchor'), 'amount': ('quantity_ref', 'root_input', 'context_declaration', 'source_anchor', 'literal')}, 'optional': {}, 'outputs': ('result',)},
    'receiver_add': {'required': {'receiver': ('quantity_ref', 'source_anchor')}, 'optional': {}, 'outputs': ('result',)},
    'count_origin': {'required': {'origin': ('source_anchor',)}, 'optional': {}, 'outputs': ('result',)},
    'count_command': {'required': {'origin': ('source_anchor',)}, 'optional': {}, 'outputs': ('result',)},
    'reuse_operation': {'required': {'receiver': ('quantity_ref', 'source_anchor')}, 'optional': {}, 'outputs': ('result',)},
}
SUPPORTED_OPERATIONS = set(OPERATION_CONTRACTS)
QUANTITY_UNITS = {'integer', 'year', 'year_ordinal', 'month', 'month_fraction',
                  'day', 'day_fraction', 'du', 'du_fraction', 'boolean', 'status',
                  'opaque', 'product', 'unknown'}


def validate_manual_structure(structure):
    candidates = structure.get('candidates')
    if not isinstance(candidates, list) or not candidates:
        raise ValueError('manual_structure_requires_candidates')
    for candidate in candidates:
        contract = OPERATION_CONTRACTS.get(candidate.get('kind'))
        if contract is None:
            raise ValueError('unsupported_existing_operation:' + str(candidate.get('kind')))
        slots = candidate.get('slots', {})
        if not isinstance(slots, dict):
            raise ValueError('manual_structure_slots_required')
        unexpected = set(slots) - set(contract['required']) - set(contract['optional'])
        missing = set(contract['required']) - set(slots)
        if unexpected or missing:
            raise ValueError('manual_operation_signature:' + candidate['kind'])
        for name, reference in slots.items():
            if not isinstance(reference, dict) or reference.get('ref_kind') not in contract['required'].get(name, contract['optional'].get(name, ())):
                raise ValueError('invalid_manual_slot:' + candidate['kind'] + ':' + name)
    return True


def validate_quantity_semantics(payload):
    if payload.get('unit') not in QUANTITY_UNITS:
        raise ValueError('unknown_quantity_unit')
    if payload.get('resolution_status') is not None:
        raise ValueError('resolution_status_is_derived')
    if not isinstance(payload.get('semantic_output'), dict):
        raise ValueError('semantic_output_address_required')
    return True


def registry_identity():
    encoded = json.dumps(OPERATION_CONTRACTS, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'version': '1.0', 'sha256': hashlib.sha256(encoded).hexdigest()}


def validate_profile(profile_id):
    if profile_id not in PROFILES:
        raise ValueError('unknown_existing_profile')
    return True
