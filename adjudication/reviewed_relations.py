"""Resolve the bounded Han Si-fen month-to-day claim against source operations.

An approval supplies meaning for existing multiply/divmod ports. This module
never creates arithmetic or accepts a graph diagnostic as a review choice.
"""

from analysis_parser.audit import audit

from .anchors import anchor_for, anchor_location, document_for, validate_anchor


_ANCHORS = (
    'definition_anchor', 'month_input_anchor', 'month_producer_anchor', 'multiply_anchor',
    'division_anchor', 'quotient_anchor', 'remainder_anchor',
    'numerator_parameter_anchor', 'denominator_parameter_anchor',
)


def validate_relation_payload(packet, payload):
    """Validate durable evidence addresses without consulting runtime IDs."""
    if not isinstance(payload, dict) or payload.get('kind') != 'month_to_day':
        raise ValueError('unsupported_reviewed_relation')
    for name in _ANCHORS:
        validate_anchor(packet, payload.get(name))
    path = payload.get('invocation_path')
    if not isinstance(path, list) or not path:
        raise ValueError('relation_invocation_path_required')
    for anchor in path:
        validate_anchor(packet, anchor)
    if (payload.get('tradition'), payload.get('task'), payload.get('query')) != (
            'Han_Si_fen_li', 'new_moon', 'main'):
        raise ValueError('relation_scope_not_supported')
    if not isinstance(payload.get('evidence_refs'), list) or not all(
            isinstance(ref, str) and ref.strip() for ref in payload['evidence_refs']):
        raise ValueError('relation_evidence_required')
    if not payload['evidence_refs']:
        raise ValueError('relation_evidence_required')
    return payload


def _at(row, anchor):
    return any(anchor_location(span) == anchor_location(anchor)
               for span in row.get('source_spans', ()))


def _one(rows, reason):
    if len(rows) != 1:
        raise ValueError('relation_' + reason)
    return rows[0]


def _event(graph, kind, anchor, call_id):
    return _one([row for row in graph.get('events', ())
                 if row['kind'] == kind and row.get('scope', {}).get('call_id') == call_id
                 and _at(row, anchor)], 'operation_or_call_changed:' + kind)


def _value(graph, value_id):
    return _one([row for row in graph.get('value_instances', ()) if row['id'] == value_id],
                'value_missing')


def _parameter(graph, value_id, anchor, label):
    value = _value(graph, value_id)
    event = _one([row for row in graph['events'] if row['id'] == value['producer']],
                 'parameter_producer_missing')
    declarations = [row for row in graph.get('context', {}).get('declarations', ())
                    if row.get('label') == label and _at(row, anchor)]
    declaration = _one(declarations, 'parameter_source_changed:' + label)
    if (event['kind'] != 'parameter' or event['writes'].get('result') != value_id
            or not _at(event, anchor) or label not in value.get('labels', ())
            or value.get('role') != 'parameter'
            or event.get('attributes', {}).get('value') != declaration['value']):
        raise ValueError('relation_parameter_identity_changed:' + label)
    return declaration['value']


def resolve_reviewed_relation(packet, graph, payload):
    """Return preflight proof and semantic port hooks for the current call."""
    validate_relation_payload(packet, payload)
    if packet.get('provided_scope', {}).get('tradition') != payload['tradition']:
        raise ValueError('relation_scope_changed')
    calls = [call for call in graph.get('program', {}).get('calls', ())
             if _at(call, payload['definition_anchor'])
             and all(_at(call, anchor) for anchor in payload['invocation_path'])
             and any(_at(call, payload[name]) for name in (
                 'month_input_anchor', 'multiply_anchor', 'division_anchor'))]
    call = _one(calls, 'call_changed_or_ambiguous')
    call_id = call['call_id']
    load = _event(graph, 'load', payload['month_input_anchor'], call_id)
    multiply = _event(graph, 'multiply', payload['multiply_anchor'], call_id)
    division = _event(graph, 'divmod', payload['division_anchor'], call_id)
    whole_name = _event(graph, 'alias', payload['quotient_anchor'], call_id)
    remainder_name = _event(graph, 'alias', payload['remainder_anchor'], call_id)
    involved = (load, multiply, division, whole_name, remainder_name)
    if any(any(event.get('scope', {}).get(key) != payload[key]
               for key in ('tradition', 'task', 'query')) for event in involved):
        raise ValueError('relation_scope_changed')
    call_events = set(call.get('event_ids', ()))
    if not all(event['id'] in call_events for event in involved):
        raise ValueError('relation_call_membership_changed')
    if (load['writes'].get('result') not in multiply['reads'].values()
            or multiply['writes'].get('result') != division['reads'].get('dividend')):
        raise ValueError('relation_source_operation_chain_changed')
    month_source = call.get('formal_bindings', {}).get('入蔀積月')
    imports = [row for row in graph.get('program', {}).get('linked', {}).get('imports', ())
               if row.get('consumer_definition_id') == call['definition_id']
               and row.get('formal') == '入蔀積月']
    imported = _one(imports, 'month_source_binding_missing')
    if (month_source != load['reads'].get('value')
            or imported.get('actual_value_id') != month_source
            or not imported.get('selected_definition_id')
            or imported.get('selected_port') != '積月'):
        raise ValueError('relation_month_source_changed')
    month_value = _value(graph, month_source)
    month_producer = _one([row for row in graph['events']
                           if row['id'] == month_value['producer']],
                          'month_source_producer_missing')
    if (month_producer['kind'] != 'alias'
            or month_producer['writes'].get('result') != month_source
            or not _at(month_producer, payload['month_producer_anchor'])
            or month_producer.get('scope', {}).get('definition_id') != imported['selected_definition_id']):
        raise ValueError('relation_month_source_changed')
    numerator_id = _one([value_id for value_id in multiply['reads'].values()
                         if value_id != load['writes']['result']], 'numerator_operand_changed')
    denominator_id = division['reads'].get('divisor')
    numerator = _parameter(graph, numerator_id, payload['numerator_parameter_anchor'], '蔀日')
    denominator = _parameter(graph, denominator_id, payload['denominator_parameter_anchor'], '蔀月')
    quotient_id = division['writes'].get('quotient')
    remainder_id = division['writes'].get('remainder')
    if (not quotient_id or not remainder_id
            or whole_name['reads'].get('value') != quotient_id
            or remainder_name['reads'].get('value') != remainder_id):
        raise ValueError('relation_quotient_remainder_ports_changed')
    for port, value_id in (('quotient', quotient_id), ('remainder', remainder_id)):
        value = _value(graph, value_id)
        if value.get('producer') != division['id'] or value.get('output_port') != port:
            raise ValueError('relation_output_port_invariant_failed')
    relevant = {row['id'] for row in involved}
    violations = [row for row in audit(graph) if row.get('event_id') in relevant]
    if violations:
        raise ValueError('relation_graph_invariant_failed:' + violations[0]['kind'])
    construction = _one([row for row in graph.get('construction_candidates', ())
                         if row['kind'] == 'divide' and _at(row, payload['division_anchor'])],
                        'division_construction_changed')
    quotient = {'unit': 'day', 'quantity_kind': 'duration', 'representation': {'kind': 'whole'}}
    remainder = {'unit': 'day_fraction', 'quantity_kind': 'duration',
                 'representation': {'kind': 'fraction_numerator', 'denominator_id': denominator_id}}
    return {
        'kind': 'month_to_day', 'call_id': call_id,
        'multiply_event_id': multiply['id'], 'division_event_id': division['id'],
        'source_division': {'multiply_event_id': multiply['id'], 'division_event_id': division['id']},
        'parameters': {'numerator': numerator, 'denominator': denominator},
        'numerator_value_id': numerator_id, 'denominator_value_id': denominator_id,
        'month_value_id': load['writes']['result'],
        'quotient_value_id': quotient_id, 'remainder_value_id': remainder_id,
        'quotient': quotient, 'remainder': remainder,
        'preflight_event_count': len(graph['events']),
        'output_hooks': [
            {'kind': 'output', 'syntax_node_id': construction['node_id'], 'port': 'quotient',
             'semantic_role': 'divmod', 'call_id': call_id, 'metadata': quotient},
            {'kind': 'output', 'syntax_node_id': construction['node_id'], 'port': 'remainder',
             'semantic_role': 'divmod', 'call_id': call_id, 'metadata': remainder},
        ],
        'operation_hook': {
            'kind': 'operation', 'syntax_node_id': construction['node_id'], 'semantic_role': 'divmod',
            'call_id': call_id,
            'metadata': {
                'transition': 'reviewed_month_to_day_relation',
                'ports': {'quotient': quotient, 'remainder': remainder},
            },
        },
    }


def _full_anchor(packet, span):
    return anchor_for(packet, span['doc_id'], span['start'], span['end'], span['reading_id'])


def _proposed_claim(packet, graph, division, events, values, calls):
    scope = division.get('scope', {})
    if (scope.get('tradition'), scope.get('task'), scope.get('query')) != (
            'Han_Si_fen_li', 'new_moon', 'main'):
        return None
    source = division.get('source_spans', ())
    if (len(source) != 1 or
            document_for(packet, source[0]['doc_id'], source[0]['reading_id'])
            .get('source', {}).get('section') != 39):
        return None
    call_id = scope.get('call_id')
    call = _one([row for row in calls if row['call_id'] == call_id], 'call_missing')
    multiply = events[values[division['reads']['dividend']]['producer']]
    if multiply['kind'] != 'multiply':
        return None
    denominator = values[division['reads']['divisor']]
    factors = [values[vid] for vid in multiply['reads'].values()]
    numerator = _one([value for value in factors if value.get('role') == 'parameter'
                      and '蔀日' in value.get('labels', ())], 'numerator_missing')
    month = _one([value for value in factors if value['id'] != numerator['id']],
                 'month_operand_missing')
    load = events[month['producer']]
    if load['kind'] != 'load':
        return None
    month_producer = events[values[load['reads']['value']]['producer']]
    quotient_name = _one([row for row in graph['events']
                          if row['kind'] == 'alias' and row.get('scope', {}).get('call_id') == call_id
                          and row['reads'].get('value') == division['writes']['quotient']
                          and row.get('attributes', {}).get('label') == '積日'], 'quotient_name_missing')
    remainder_name = _one([row for row in graph['events']
                           if row['kind'] == 'alias' and row.get('scope', {}).get('call_id') == call_id
                           and row['reads'].get('value') == division['writes']['remainder']
                           and row.get('attributes', {}).get('label') == '小餘'], 'remainder_name_missing')
    if not all(row.get('source_spans') for row in (
            call, load, month_producer, multiply, division, quotient_name,
            remainder_name, numerator, denominator)):
        return None
    claim = {
        'kind': 'month_to_day',
        'definition_anchor': _full_anchor(packet, call['source_spans'][0]),
        'invocation_path': [_full_anchor(packet, call['source_spans'][0])],
        'month_input_anchor': _full_anchor(packet, load['source_spans'][0]),
        'month_producer_anchor': _full_anchor(packet, month_producer['source_spans'][0]),
        'multiply_anchor': _full_anchor(packet, multiply['source_spans'][0]),
        'division_anchor': _full_anchor(packet, division['source_spans'][0]),
        'quotient_anchor': _full_anchor(packet, quotient_name['source_spans'][0]),
        'remainder_anchor': _full_anchor(packet, remainder_name['source_spans'][0]),
        'numerator_parameter_anchor': _full_anchor(packet, numerator['source_spans'][0]),
        'denominator_parameter_anchor': _full_anchor(packet, denominator['source_spans'][0]),
        'tradition': 'Han_Si_fen_li', 'task': 'new_moon', 'query': 'main',
        'evidence_refs': ['Cullen Proc. 3.6, §39'],
    }
    resolve_reviewed_relation(packet, graph, claim)
    return claim


def propose_reviewed_relations(packet, graph):
    """Offer this bounded claim only when the current typed graph proves it."""
    if not graph:
        return []
    events = {row['id']: row for row in graph.get('events', ())}
    values = {row['id']: row for row in graph.get('value_instances', ())}
    calls = graph.get('program', {}).get('calls', ())
    proposals = []
    for division in graph.get('events', ()):
        if division['kind'] != 'divmod':
            continue
        try:
            claim = _proposed_claim(packet, graph, division, events, values, calls)
        except (KeyError, ValueError, TypeError):
            continue
        if claim is not None:
            proposals.append(claim)
    return proposals
