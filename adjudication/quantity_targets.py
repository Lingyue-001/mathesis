"""Resolve reviewed quantity addresses to narrow, invocation-local read hooks."""
import copy

from .anchors import anchor_for, overlaps, validate_anchor
from .registry import OPERATION_CONTRACTS, QUANTITY_UNITS, validate_quantity_semantics


QUANTITY_FACETS = frozenset({'unit', 'quantity_kind', 'representation', 'coordinate_kind',
                           'index_base', 'reference_origin', 'counting_boundary',
                           'step_unit', 'scale', 'binding'})
REFERENCE_ORIGINS = frozenset({'current_bu_start', 'current_cycle_start'})
COUNTING_BOUNDARIES = frozenset({'start_of_current_year', 'start_of_current_month'})


def quantity_compatibility_issues(facets):
    """Report the finite incompatible facet pairs, retaining assertion atomicity."""
    issues = []
    unit, step = facets.get('unit'), facets.get('step_unit')
    if unit and step and unit not in ('unknown', 'opaque', 'product'):
        if unit.removesuffix('_ordinal').removesuffix('_fraction') != step:
            issues.append(('incompatible_quantity_unit_step_unit', {'unit', 'step_unit'}))
    boundary_unit = {'start_of_current_year': 'year', 'start_of_current_month': 'month'}.get(facets.get('counting_boundary'))
    if boundary_unit and step and boundary_unit != step:
        issues.append(('incompatible_counting_boundary_step_unit', {'counting_boundary', 'step_unit'}))
    coordinate, base = facets.get('coordinate_kind'), facets.get('index_base')
    if coordinate == 'elapsed' and base not in (None, 0):
        issues.append(('elapsed_quantity_requires_zero_base', {'coordinate_kind', 'index_base'}))
    if coordinate == 'ordinal' and base not in (None, 0, 1):
        issues.append(('ordinal_quantity_requires_supported_base', {'coordinate_kind', 'index_base'}))
    if facets.get('quantity_kind') in ('angle', 'predicate', 'status') and step in ('year', 'month', 'day'):
        issues.append(('incompatible_quantity_kind_step_unit', {'quantity_kind', 'step_unit'}))
    return issues


def combined_quantity_compatibility(facets):
    """Validate the merged state, without requiring undecided facets to exist."""
    issues = quantity_compatibility_issues(facets)
    if issues:
        raise ValueError(issues[0][0])
    return True


def validate_quantity_facets(facets):
    if not isinstance(facets, dict) or not facets:
        raise ValueError('quantity_facets_required')
    if set(facets) - QUANTITY_FACETS:
        raise ValueError('unsupported_quantity_facet')
    if 'unit' in facets and facets['unit'] not in QUANTITY_UNITS | {'month_ordinal'}:
        raise ValueError('unknown_quantity_unit')
    if 'quantity_kind' in facets and facets['quantity_kind'] not in {'count', 'duration', 'angle', 'predicate', 'status', 'reference', 'sequence', 'unknown'}:
        raise ValueError('unknown_quantity_kind')
    if 'coordinate_kind' in facets and facets['coordinate_kind'] not in {'ordinal', 'elapsed', 'cardinal', 'cyclic', 'unknown'}:
        raise ValueError('unknown_coordinate_kind')
    if 'index_base' in facets and (type(facets['index_base']) is not int or facets['index_base'] not in (0, 1)):
        raise ValueError('unsupported_index_base')
    if 'step_unit' in facets and facets['step_unit'] not in {'year', 'month', 'day', 'du', 'integer'}:
        raise ValueError('unsupported_step_unit')
    for key, registry in (('reference_origin', REFERENCE_ORIGINS), ('counting_boundary', COUNTING_BOUNDARIES)):
        if key in facets and facets[key] not in registry:
            raise ValueError('unsupported_' + key)
    if 'representation' in facets and (not isinstance(facets['representation'], dict) or facets['representation'].get('kind') not in {'whole', 'integer', 'fraction_numerator', 'rational'}):
        raise ValueError('unsupported_quantity_representation')
    if 'scale' in facets and not (isinstance(facets['scale'], dict) or type(facets['scale']) in (int, float) and facets['scale'] > 0):
        raise ValueError('invalid_quantity_scale')
    if 'binding' in facets:
        raise ValueError('quantity_binding_requires_reviewed_source_binding')
    return combined_quantity_compatibility(facets)


def _anchor(packet, address):
    if isinstance(address, dict):
        return validate_anchor(packet, address)
    if isinstance(address, (list, tuple)) and len(address) in (4, 5):
        doc_id, reading_id, start, end = address[:4]
        return anchor_for(packet, doc_id, start, end, reading_id)
    raise ValueError('invalid_stable_quantity_anchor')


def _definition(packet, program, anchor):
    kind = anchor.get('definition_kind') if isinstance(anchor, dict) else anchor[4] if isinstance(anchor, (list, tuple)) and len(anchor) == 5 else None
    anchor = _anchor(packet, anchor)
    definitions = [d for d in program.definitions if (not kind or d['kind'] == kind)
                   and any(overlaps(s, anchor) for s in d['source_spans'])]
    if len(definitions) != 1:
        raise ValueError('ambiguous_quantity_definition')
    return definitions[0]['id']


def resolve_quantity_target(packet, program, address, direction):
    definition = _definition(packet, program, address.get('definition_anchor', address.get('definition')))
    anchor = _anchor(packet, address.get('construction_anchor', address.get('construction')))
    candidates = [c for stream in program.syntaxes.values() for c in stream
                  if c.get('definition_id') == definition and c['kind'] == address['construction_role']
                  and any(overlaps(s, anchor) for s in c['source_spans'])]
    if len(candidates) != 1:
        raise ValueError('ambiguous_semantic_' + direction + '_address')
    candidate = candidates[0]
    port = address.get('input_slot') if direction == 'input' else address.get('output_port')
    contract = OPERATION_CONTRACTS.get(candidate['kind'], {})
    if direction == 'input':
        if port not in contract.get('required', {}) and port not in contract.get('optional', {}):
            raise ValueError('semantic_input_slot_not_supported')
        if address.get('formal') and candidate['slots'].get(port, {}).get('text') != address['formal']:
            raise ValueError('semantic_input_formal_mismatch')
        supported = {'load': {'load': {'value'}},
                     'multiply': {'multiply': {'left', 'right'}},
                     'subtract': {'subtract': {'left', 'right'}},
                     'divide': {'divmod': {'value', 'divisor'}}}
        if port not in supported.get(candidate['kind'], {}).get(address['semantic_role'], set()):
            raise ValueError('semantic_input_role_not_supported')
    elif port not in contract.get('outputs', ()):
        raise ValueError('semantic_output_port_not_supported')
    path = tuple(_definition(packet, program, entry) for entry in address.get('invocation_path', []))
    if path and path != (definition,):
        # Current linked bodies are invoked once per definition. Reject a path
        # that this graph cannot actually execute instead of silently ignoring it.
        raise ValueError('quantity_invocation_path_not_in_current_graph')
    return candidate['node_id'], port, address['semantic_role'], path


def install_quantity_semantics(parser, packet, program, payloads, management=()):
    """Install validated constraints before lowering; return invalid decisions.

    Runtime IDs occur only in these ephemeral lookup keys. Source addresses and
    decision provenance remain in the public evidence projection.
    """
    parser.review_input_metadata = getattr(parser, 'review_input_metadata', {})
    parser.review_output_metadata = getattr(parser, 'review_output_metadata', {})
    scopes = parser.report.setdefault('managed_scopes', [])
    issues = []
    for payload in payloads:
        try:
            direction = 'input' if payload.get('semantic_input') else 'output'
            address = payload['semantic_' + direction]
            key = resolve_quantity_target(packet, program, address, direction)
            facets = payload.get('facets', {k: v for k, v in payload.items() if k in QUANTITY_FACETS})
            reviewed = direction == 'input' or 'facets' in payload
            if reviewed:
                validate_quantity_facets(facets)
            else:
                validate_quantity_semantics(payload)
            refs = payload.get('decision_refs') or [payload.get('decision_id')]
            metadata = dict(copy.deepcopy(facets), decision_refs=[r for r in refs if r],
                            decision_id=payload.get('decision_id'), reviewed_quantity=reviewed,
                            evidence_basis=payload.get('evidence_basis', 'scholarship'),
                            decision_origin='human_selection', semantic_target=copy.deepcopy(address))
            if payload.get('role') is not None:
                metadata['role'] = payload['role']
            mapping = getattr(parser, 'review_' + direction + '_metadata')
            previous = mapping.get(key, {})
            combined = {**previous, **metadata}
            combined['decision_refs'] = sorted(set(previous.get('decision_refs', []) + metadata['decision_refs']))
            combined_quantity_compatibility({k: v for k, v in combined.items() if k in QUANTITY_FACETS})
            mapping[key] = combined
        except (ValueError, KeyError, TypeError) as error:
            issues.append({'kind': 'invalid_quantity_semantics', 'decision_id': payload.get('decision_id'), 'reason': str(error)})
    for row in management:
        if not row.get('managed', row.get('action') == 'manage'):
            continue
        address = row.get('semantic_input') or row.get('semantic_output') or row.get('semantic_target')
        if not address or row.get('facet') not in QUANTITY_FACETS or row.get('facet') == 'binding':
            continue
        direction = 'input' if row.get('semantic_input') or address.get('kind') == 'semantic_input' or 'input_slot' in address else 'output'
        evidence = {'target': copy.deepcopy(address), 'facet': row['facet'], 'event_id': row.get('event_id')}
        try:
            key = resolve_quantity_target(packet, program, address, direction)
            mapping = getattr(parser, 'review_' + direction + '_metadata')
            metadata = mapping.setdefault(key, copy.deepcopy(mapping.get(key[:3], {'reviewed_quantity': True, 'decision_refs': []})))
            metadata['reviewed_quantity'] = True
            metadata.setdefault('managed_facets', []).append(row['facet'])
            value = metadata.get(row['facet'])
            if value is None or isinstance(value, str) and value in ('unknown', 'opaque', 'product'):
                metadata.setdefault('unresolved_facets', []).append(row['facet'])
            evidence['status'] = 'unresolved' if row['facet'] in metadata.get('unresolved_facets', []) else 'resolved'
        except (ValueError, KeyError, TypeError) as error:
            evidence.update(status='needs_revalidation', reason=str(error))
        scopes.append(evidence)
    for mapping in (parser.review_input_metadata, parser.review_output_metadata):
        for metadata in mapping.values():
            if metadata.get('coordinate_kind') == 'ordinal':
                missing = [key for key in ('index_base', 'step_unit', 'reference_origin', 'counting_boundary') if key not in metadata]
                if missing:
                    metadata['unresolved_facets'] = sorted(set(metadata.get('unresolved_facets', []) + missing))
    return issues
