"""Public adapter checking every reference step against emitted dependencies.

Reference IDs exist only in this evaluator. The map is derived in source order
from actual events; an absent relation fails instead of being repaired.
"""
from graph_checks import Graph
from semantic_checks import validate_method, validate_dual, validate_threshold, validate_count, validate_year_scan, validate_external_call

KINDS = {
    'multiply': 'multiply', 'multiply_and_name': 'multiply',
    'count_full_units': 'divmod', 'name_result': 'alias',
    'name_remainder': 'alias', 'delayed_remainder_name': 'alias',
    'threshold_predicate': 'threshold', 'bounded_predicate': 'threshold',
    'query_offset': 'add', 'reduce_cycle': 'cycle_reduce',
    'cyclic_count': 'count', 'count_month_ordinal': 'count',
    'carry_to_receiver': 'add', 'add_to_prior_product': 'add',
    'add_to_named_quantity': 'add', 'subtract': 'subtract',
    'set_then_subtract': 'subtract', 'import_named_quantity': 'load',
    'reuse_count_reduce': 'method_call', 'external_constraint_call': 'external_constraint_call',
    'scan_years_with_branch': 'year_scan', 'dual_count_origin': 'count',
    'paired_increment': 'add', 'double_interval_from_base': 'interval_scale',
    'read_intercalation_schedule': 'schedule'}


def assess_steps(report, reference):
    g = Graph(report)
    quantities = {q['quantity_id']: q for q in reference['quantities']}
    mapping, rows = {}, []
    for qid, q in quantities.items():
        label = q.get('source_label')
        if not label:
            continue
        role = q['role']
        kinds = {'parameter', 'input'} if 'parameter' in role else {'input'} if role.startswith('external_') else set()
        if not kinds:
            continue
        labels = label.split('／')
        if qid == 'boundary_data':
            labels.append('boundary_data')
        values = [v['id'] for v in g.values.values()
                  if any(s in v.get('labels', []) for s in labels)
                  and g.producer(v['id'])['kind'] in kinds]
        if len(values) == 1:
            mapping[qid] = values[0]

    def equivalent(ref, actual):
        if ref.startswith('lit:'):
            return g.scalar(actual) == int(ref[4:])
        return ref in mapping and g.same(mapping[ref], actual)

    for node in reference['nodes']:
        action = node['action']
        matches = []
        for anchor in node['source_spans']:
            matches += g.at(anchor['quote'], KINDS.get(action, '__unsupported_reference_action__'), anchor['passage_id'])
        matches = list({e['id']: e for e in matches}.values())
        evidence = [e['id'] for e in matches]
        errors, relations, outputs = [], [], []
        try:
            assert matches, 'no event with required action and source anchor'
            if action == 'read_intercalation_schedule':
                schedules = [e['attributes']['schedule'] for e in matches]
                assert schedules and all(s == schedules[0] for s in schedules)
                mapping[node['outputs'][0]] = {'schedule': schedules[0]}
            elif action in ('paired_increment', 'double_interval_from_base') and len(node['outputs']) == 3:
                # Compound query includes inferred reuse of a previously parsed method.
                query = matches[0]['scope']['query']
                group = [e for e in g.events.values() if e['scope']['query'] == query]
                evidence = [e['id'] for e in group]
                outputs = [g.named('大餘', query), g.named('小餘', query), g.named('朔日', query)]
                assert any(e['kind'] == 'divmod' for e in group), 'fraction carry absent'
                assert any(e['kind'] == 'method_call' for e in group), 'count/reduce reuse absent'
                for call in group:
                    if call['kind'] == 'method_call': validate_method(g, call)
                reads = [v for e in group if e['kind'] != 'query' for v in e['reads'].values()]
                for ref in node['inputs']:
                    ok = any(equivalent(ref, v) for v in reads)
                    relations.append({'reference_quantity': ref, 'status': 'pass' if ok else 'fail'})
                    assert ok, f'query required dependency {ref} absent'
            elif action == 'paired_increment':
                assert len(matches) == 2, 'paired increments require two additions'
                # Source-order addition events correspond to greater then fractional component.
                outputs = [g.output(e) for e in matches]
                reads = [v for e in matches for v in e['reads'].values()]
                for ref in node['inputs']:
                    ok = any(equivalent(ref, v) for v in reads)
                    relations.append({'reference_quantity': ref, 'status': 'pass' if ok else 'fail'})
                    assert ok, f'paired increment input {ref} absent'
            elif action == 'dual_count_origin':
                validate_dual(g, matches)
                for e in matches:
                    assert equivalent(node['inputs'][0], e['reads']['offset'])
                outputs = [g.output(e) for e in matches]
            else:
                # A fused multiplication/name can emit two events; choose the action,
                # then verify the associated alias shares its actual value below.
                assert len(matches) == 1, f'ambiguous action selection: {evidence}'
                event = matches[0]
                if event['kind'] == 'threshold': validate_threshold(g, event)
                if event['kind'] == 'count': validate_count(g, event)
                if event['kind'] == 'year_scan': validate_year_scan(g, event)
                if event['kind'] == 'external_constraint_call': validate_external_call(g, event)
                reads = list(event['reads'].values())
                for ref in node['inputs']:
                    if ref == 'intercalation.schedule':
                        ok = mapping.get(ref, {}).get('schedule') == event['attributes'].get('cumulative_schedule')
                    elif action == 'scan_years_with_branch' and ref in ('lit:12', 'lit:13'):
                        field = 'ordinary_year_months' if ref == 'lit:12' else 'intercalary_year_months'
                        ok = event['attributes'].get(field) == int(ref[4:])
                    else:
                        ok = any(equivalent(ref, v) for v in reads)
                    relations.append({'reference_quantity': ref, 'status': 'pass' if ok else 'fail',
                                      'actual_read_ids': reads})
                    assert ok, f'required dependency {ref} absent or misbound'
                if action in ('subtract', 'set_then_subtract'):
                    assert equivalent(node['inputs'][0], event['reads']['left'])
                    assert equivalent(node['inputs'][1], event['reads']['right'])
                if action in ('count_full_units', 'reduce_cycle'):
                    assert equivalent(node['inputs'][0], event['reads']['dividend'])
                    assert equivalent(node['inputs'][1], event['reads']['divisor'])
                    outputs = [g.output(event, 'quotient'), g.output(event, 'remainder')]
                elif action == 'reuse_count_reduce':
                    outputs = [g.output(event, 'remainder'), g.output(event)]
                    validate_method(g, event)
                elif action == 'scan_years_with_branch':
                    outputs = [g.output(event, 'years'), g.output(event, 'remainder')]
                    validate_year_scan(g, event)
                else:
                    outputs = [g.output(event)]
            if outputs:
                assert len(outputs) == len(node['outputs'])
                for ref, actual in zip(node['outputs'], outputs):
                    mapping[ref] = actual
            if action == 'multiply_and_name':
                label = quantities[node['outputs'][0]]['source_label']
                assert g.same(g.named(label), outputs[0]), 'multiply result has no associated named output'
        except (AssertionError, KeyError, TypeError, IndexError) as e:
            errors.append(str(e) or 'required structural relation failed')
        rows.append({'reference_node': node['node_id'], 'action': action, 'source_spans': node['source_spans'],
                     'status': 'fail' if errors else 'pass', 'event_ids': evidence,
                     'read_relations': relations, 'output_value_ids': outputs, 'errors': errors})
    return {'window': reference['window_id'], 'rows': rows, 'quantity_mapping': mapping,
            'note': 'Required reference relations checked; alternate graph decompositions allowed. See assess_layers for annotated-unit TP/FP/FN.'}
