"""Finite M2 vocabulary mapped only to already supported lowering kinds."""
from analysis_parser.resources import PROFILES


SUPPORTED_OPERATIONS = {
    'task_marker', 'query_marker', 'load', 'multiply', 'divide', 'name',
    'remainder_name', 'threshold', 'judgment', 'add', 'subtract', 'declaration',
    'update', 'receiver_add', 'count_origin', 'count_command', 'reuse_operation',
}
QUANTITY_UNITS = {'integer', 'year', 'year_ordinal', 'month', 'month_fraction',
                  'day', 'day_fraction', 'du', 'du_fraction', 'boolean', 'status',
                  'opaque', 'product', 'unknown'}


def validate_manual_structure(structure):
    candidates = structure.get('candidates')
    if not isinstance(candidates, list) or not candidates:
        raise ValueError('manual_structure_requires_candidates')
    for candidate in candidates:
        if candidate.get('kind') not in SUPPORTED_OPERATIONS:
            raise ValueError('unsupported_existing_operation:' + str(candidate.get('kind')))
        if not isinstance(candidate.get('slots', {}), dict):
            raise ValueError('manual_structure_slots_required')
    return True


def validate_quantity_semantics(payload):
    if payload.get('unit') not in QUANTITY_UNITS:
        raise ValueError('unknown_quantity_unit')
    if payload.get('output_port', 'result') == '':
        raise ValueError('output_port_required')
    return True


def validate_profile(profile_id):
    if profile_id not in PROFILES:
        raise ValueError('unknown_existing_profile')
    return True
