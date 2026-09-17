"""Persist falsification evidence on captured real source graphs (not fresh text)."""
import argparse
import copy
from pathlib import Path
from run_suite import load, write, local_module, PACKAGE


def run_faults(captured, out):
    captured, out = Path(captured), Path(out)
    cards = [c for c in load(PACKAGE / 'reference/civil_cards.json') if c['card_id'].endswith('_ST')]
    packet = load(captured / 'N3_01-input.json')['packet']
    original = load(captured / 'N3_01-runtime.json')['report']
    policy = local_module('civil_policy').build_policy(load(PACKAGE / 'reference/civil_cards.json'))
    grader = local_module('civil_contracts')
    rows = []

    def evaluate(case_id, report, target_ids, expected_status='parser_error'):
        result = grader.evaluate_cards(packet, report, cards, policy)
        statuses = {o['id']: o['status'] for c in result['cards'] for o in c['obligations']}
        passed = all(statuses.get(oid) == expected_status for oid in target_ids)
        write(out / (case_id + '-mutated-graph.json'), report)
        write(out / (case_id + '-score.json'), result)
        rows.append({'id': case_id, 'classification': 'fault_injection_on_development_source_graph',
                     'targets': target_ids, 'expected_status': expected_status,
                     'actual_statuses': {oid: statuses.get(oid) for oid in target_ids}, 'passed': passed})

    report = copy.deepcopy(original)
    additions = [e for e in report['events'] if e['kind'] == 'add' and e['scope'].get('task') in ('nodes', 'qi')
                 and e.get('attributes', {}).get('receiver') == '小餘' and e.get('attributes', {}).get('increment')]
    nodes = next(e for e in additions if e['scope']['task'] == 'nodes')
    qi = next(e for e in additions if e['scope']['task'] == 'qi')
    nodes['reads']['right'], qi['reads']['right'] = qi['reads']['right'], nodes['reads']['right']
    evaluate('B29', report, ['C4_ST.01', 'C4_ST.04'])

    report = copy.deepcopy(original); graph = grader.Graph(packet, report)
    months = graph.root(report['task_exports']['new_moon']['months'])
    division = graph.events[graph.values[months]['producer']]
    consumer = next(e for e in report['events'] if e['kind'] == 'multiply' and e['scope'].get('task') == 'new_moon'
                    and graph.root(e['reads'].get('right')) == months)
    consumer['reads']['right'] = division['writes']['remainder']
    evaluate('B31', report, ['C2_ST.04'])

    report = copy.deepcopy(original)
    call = next(e for e in report['events'] if e['kind'] == 'method_call' and e['scope'].get('task') == 'winter')
    definition = copy.deepcopy(next(m for m in report['method_library'] if m['id'] == call['attributes']['target']))
    definition['id'] = 'fault_wrong_unit_same_body'; definition['formal_inputs']['offset']['unit'] = 'du'
    report['method_library'].append(definition)
    call['attributes']['target'] = definition['id']; call['method_binding']['definition_id'] = definition['id']
    call['method_binding']['formal_inputs'] = definition['formal_inputs']
    evaluate('B16', report, ['C3_ST.03'])

    report = copy.deepcopy(original)
    repeat = next(e for e in report['events'] if e['kind'] == 'repeat')
    repeat['attributes']['control']['stop']['operator'] = 'ge'
    evaluate('B20_control_mutation', report, ['C5_ST.02'])

    report = copy.deepcopy(original)
    event = next(e for e in report['events'] if e['kind'] == 'multiply' and e['scope'].get('task') == 'qi')
    event['kind'] = 'new_numeral_operation_not_yet_supported_by_grader'
    evaluate('B30', report, ['C4_ST.02'], 'evaluator_unsupported')

    report = copy.deepcopy(original)
    rescale = next(e for e in report['events'] if e['kind'] == 'rescale' and e['scope'].get('task') == 'qi')
    rescale['attributes']['transition']['status'] = 'inconsistent_representation'
    evaluate('B05_rate_evidence_mutation', report, ['C4_ST.03'])

    report = copy.deepcopy(original)
    value = next(v for v in report['value_instances'] if v['id'] == report['task_exports']['new_moon']['intercalation_remainder'])
    value['unit'] = 'day_fraction'; value['scale'] = {'denominator': 'wrong-denominator', 'value': 81}
    evaluate('review_quantity_scale', report, ['C2_ST.02'])

    report = copy.deepcopy(original)
    call = next(e for e in report['events'] if e['kind'] == 'method_call' and e['scope'].get('task') == 'winter')
    call['method_binding']['formal_inputs']['offset']['unit'] = 'month'
    evaluate('review_binding_signature', report, ['C3_ST.03'])

    report = copy.deepcopy(original)
    anchor = next(o['anchor'] for c in cards for o in c['obligations'] if o['id'] == 'C2_ST.03')
    source = next(d['text'] for d in packet['primary_documents'] if d['doc_id'] == anchor['doc_id'])
    span = dict(anchor, start=anchor['start'] - 1, end=anchor['start'] + 1,
                quote=source[anchor['start'] - 1:anchor['start'] + 1])
    target = next(e for e in report['events'] if e['kind'] == 'threshold' and e['writes']['result'] == report['task_exports']['new_moon']['has_intercalation'])
    target['source_spans'] = [span]
    evaluate('review_crossing_span', report, ['C2_ST.03'])

    report = copy.deepcopy(original)
    div = next(e for e in report['events'] if e['kind'] == 'divmod' and e.get('attributes', {}).get('quantity_transition', {}).get('rate', {}).get('from_unit') == 'month')
    div['attributes'].pop('quantity_transition')
    evaluate('review_missing_unit_rate', report, ['C2_ST.04'])

    report = load(captured / 'N3_03-runtime.json')['report']
    sf_packet = load(captured / 'N3_03-input.json')['packet']
    sf_cards = [c for c in load(PACKAGE / 'reference/civil_cards.json') if c['card_id'].endswith('_SF')]
    events = {e['id']: e for e in report['events']}; values = {v['id']: v for v in report['value_instances']}
    predicate = events[values[report['task_exports']['new_moon']['has_intercalation']]['producer']]
    events[values[predicate['reads']['lower']]['producer']]['attributes']['value'] = 13
    score = grader.evaluate_cards(sf_packet, report, sf_cards, policy)
    item = next(o for c in score['cards'] for o in c['obligations'] if o['id'] == 'C2_SF.02')
    write(out / 'review_sf_threshold-mutated-graph.json', report)
    write(out / 'review_sf_threshold-score.json', score)
    rows.append({'id': 'review_sf_threshold', 'targets': ['C2_SF.02'], 'expected_status': 'parser_error',
                 'actual_statuses': {'C2_SF.02': item['status']}, 'passed': item['status'] == 'parser_error'})

    summary = {'faults': rows, 'passed': all(row['passed'] for row in rows),
               'classification': 'Development evaluator falsification; not new-material performance'}
    write(out / 'summary.json', summary)
    return summary


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('--captured', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_faults(args.captured, args.out), ensure_ascii=False, indent=2))
