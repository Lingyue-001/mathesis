"""Read-only grading of actual graphs and isolated epoch-input executions.

References are opened by this parent process only, never by the parser worker.
The numerical field map projects value IDs; it contains no calendar arithmetic.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PACKAGE = ROOT / 'handoff_v3'
GROUP_FIELDS = {
    'era_entry': ('origin_remainder', 'origin_index', 'concordance_index', 'era_index',
                  'obscuration_row', 'years_into_obscuration', 'local_elapsed_years',
                  'head_day', 'head_year', 'current_year_name'),
    'new_moon': ('months', 'intercalation_remainder', 'whole_days', 'small_remainder',
                 'day_offset', 'new_moon_day', 'month_long', 'next_moon_day',
                 'next_moon_remainder', 'has_intercalation'),
    'winter': ('winter_whole_residual', 'winter_remainder1539', 'winter_remainder32',
               'winter_day', 'winter_absolute_whole_days'),
    'nodes': ('first_node_day', 'first_node_remainder1539', 'first_node_absolute_whole_days'),
    'qi': ('qi_base_remainder4617', 'first_qi_day', 'first_qi_remainder4617',
           'first_qi_remainder32', 'first_qi_absolute_whole_days'),
    'intercalation': ('loop_count', 'loop_final_lag', 'nominal_leap_celestial_label',
                      'nominal_leap_civil_label', 'intercalation_complement',
                      'placement_q', 'placement_r', 'adjusted_count', 'nominal_leap_slot'),
}
FIELD_MAP = {field: task for task, fields in GROUP_FIELDS.items() for field in fields}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def runtime_module():
    spec = importlib.util.spec_from_file_location('v3_isolated_runtime', HERE / 'isolated_runtime.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def local_module(name):
    spec = importlib.util.spec_from_file_location('v3_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def producer_evidence(report, value_id):
    values = {v['id']: v for v in report.get('value_instances', [])}
    events = {e['id']: e for e in report.get('events', [])}
    value = values.get(value_id, {})
    event = events.get(value.get('producer'), {})
    port = value.get('output_port')
    valid = bool(event and port and event.get('writes', {}).get(port) == value_id)
    initial, seen, errors = set(), set(), []

    def visit(vid, active):
        if vid in active:
            errors.append('cyclic_dependency:' + vid); return
        if vid in seen:
            return
        seen.add(vid)
        v = values.get(vid, {}); e = events.get(v.get('producer'), {})
        if not e or e.get('writes', {}).get(v.get('output_port')) != vid:
            errors.append('invalid_producer_port:' + str(vid)); return
        if e.get('kind') == 'input':
            initial.add(e.get('attributes', {}).get('name', '<unnamed>'))
        for parent in e.get('reads', {}).values():
            visit(parent, active | {vid})

    if valid:
        visit(value_id, set())
    return {'valid': valid and not errors, 'value_id': value_id,
            'producer': event.get('id'), 'output_port': port,
            'initial_inputs': sorted(initial), 'dependency_errors': errors}


def score_numeric(report, execution, expected, supplied_inputs=None):
    supplied_inputs = supplied_inputs or {}
    allowed_inputs = {'epoch_elapsed_years', 'epoch_inclusive_year'}
    events = {e['id']: e for e in report.get('events', [])}
    bindings = {b.get('event_id'): b for b in execution.get('explicit_bindings', [])}
    rows = []
    for field, target in expected.items():
        task = FIELD_MAP.get(field)
        vid = report.get('task_exports', {}).get(task, {}).get(field)
        evidence = producer_evidence(report, vid)
        actual = execution.get('values', {}).get(vid)
        executed = execution.get('event_results', {}).get(evidence['producer'], {})
        same_type = isinstance(actual, bool) == isinstance(target, bool)
        input_provenance = bool(evidence['initial_inputs']) and set(evidence['initial_inputs']) <= (set(supplied_inputs) & allowed_inputs)
        for event in events.values():
            name = event.get('attributes', {}).get('name')
            if event.get('kind') != 'input' or name not in evidence['initial_inputs']:
                continue
            binding = bindings.get(event['id'], {})
            input_vid = event.get('writes', {}).get('result')
            actual_input = execution.get('values', {}).get(input_vid)
            input_provenance = (input_provenance and binding.get('source') == 'inputs'
                                and binding.get('name') == name and name in supplied_inputs
                                and binding.get('value') == supplied_inputs.get(name)
                                and actual_input == supplied_inputs.get(name)
                                and execution.get('event_results', {}).get(event['id'], {}).get('result') == actual_input)
        passed = (evidence['valid'] and evidence['output_port'] in executed
                  and executed[evidence['output_port']] == actual and same_type
                  and actual == target and input_provenance)
        rows.append(dict(field=field, task=task, expected=target, actual=actual,
                         passed=bool(passed), input_provenance_valid=bool(input_provenance), **evidence))
    return {'fields': rows, 'correct': sum(r['passed'] for r in rows),
            'total': len(rows), 'passed': bool(rows) and all(r['passed'] for r in rows),
            'scope': 'numeric projection only; semantic, source and control gates reported separately'}


def _ranges(points):
    ordered = sorted(set(points)); ranges = []
    for point in ordered:
        if ranges and ranges[-1][1] == point:
            ranges[-1][1] += 1
        else:
            ranges.append([point, point + 1])
    return ranges


def coverage_ledger(packet, cards, report, supplemental_anchors=()):
    obligations = [o for card in cards for o in card['obligations']]
    domain = obligations + [{'id': 'supplemental-' + str(i), 'anchor': a} for i, a in enumerate(supplemental_anchors)]
    docs = packet.get('primary_documents', [])
    by_id = {d['doc_id']: d for d in docs}
    marked = {key: set() for key in by_id}
    for obligation in domain:
        anchor = obligation['anchor']; d = by_id.get(anchor['doc_id'])
        if d is None:
            raise ValueError('Reference anchor document not supplied: ' + obligation['id'])
        text = d['text']; a, b = anchor['start'], anchor['end']
        if (anchor['reading_id'] != d['reading_id'] or not 0 <= a < b <= len(text)
                or anchor['text_sha256'] != hashlib.sha256(text.encode()).hexdigest()
                or text[a:b] != anchor['quote']):
            raise ValueError('Invalid reference anchor identity: ' + obligation['id'])
        marked[d['doc_id']].update(range(a, b))
    rows = []
    for d in docs:
        n = len(d['text']); audited = marked[d['doc_id']]
        rows.append({'doc_id': d['doc_id'], 'reading_id': d['reading_id'],
                     'text_sha256': hashlib.sha256(d['text'].encode()).hexdigest(),
                     'source_length': n, 'audited_ranges': _ranges(audited),
                     'unscored_ranges': _ranges(set(range(n)) - audited)})
    raw = list(report.get('unparsed_spans', []))
    coverage = report.get('coverage', {})
    if isinstance(coverage, dict):
        raw += list(coverage.get('unparsed_spans', []))
    diagnostics = report.get('diagnostics', [])
    items = diagnostics if isinstance(diagnostics, list) else [diagnostics] if diagnostics else []
    blockers = {'parser_error', 'parser_gap', 'unresolved_parser', 'unknown_domain', 'unparsed', 'unparsed_span'}
    aggregate = diagnostics if isinstance(diagnostics, dict) else {}
    raw += aggregate.get('unparsed_spans', [])
    causes = {d.get('cause') for d in items if isinstance(d, dict)} & blockers
    causes.update(key for key in blockers if aggregate.get(key))
    if raw:
        causes.add('unparsed')
    return {'documents': rows, 'total_source_length': sum(len(d['text']) for d in docs),
            'audited_obligations': len(obligations),
            'supplemental_relation_anchors': list(supplemental_anchors),
            'audited_character_count': sum(len(v) for v in marked.values()),
            'unparsed_spans': raw, 'unresolved': report.get('unresolved', []),
            'diagnostics': diagnostics, 'diagnostic_count': len(items),
            'diagnostic_spans': [s for d in items if isinstance(d, dict) for s in d.get('source_spans', [])] + aggregate.get('unparsed_spans', []),
            'blocking_causes': sorted(causes),
            'limitation': 'Finite semantic relation annotation; unscored characters are neither correct nor false predictions.'}


def prepare_packet(tradition, boundary_profile='civil_whole_day'):
    packet = copy.deepcopy(load(PACKAGE / 'runtime_inputs' / (tradition + '_CIVIL_CORE.json')))
    packet['selected_profiles'] = (['ST_elapsed', 'ST_intercalation_Cullen_Liu_GT']
                                   if tradition == 'ST' else ['SF_Liu_inclusive', 'SF_completed_four']) + [boundary_profile]
    return packet


def run_numeric_suite(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    runtime = runtime_module()
    cases = load(PACKAGE / 'reference/numerical_cases.json')['cases']
    cards = load(PACKAGE / 'reference/civil_cards.json')
    policy = local_module('civil_policy').build_policy(cards)
    write(out / 'semantic-policy.json', policy)
    grader = local_module('civil_contracts')
    summaries = []
    for case in cases:
        tradition = 'ST' if 'epoch_elapsed_years' in case['inputs'] else 'SF'
        packet = prepare_packet(tradition)
        write(out / (case['id'] + '-input.json'), {'packet': packet, 'inputs': case['inputs']})
        result = runtime.run_isolated(packet, case['inputs'], core_dir=ROOT / 'analysis_parser')
        write(out / (case['id'] + '-runtime.json'), result)
        report = result.get('report', {})
        score = score_numeric(report, result.get('execution', {}), case['expected'], case['inputs'])
        write(out / (case['id'] + '-numeric.json'), score)
        selected_cards = [card for card in cards if card['card_id'].endswith('_' + tradition)]
        semantic = grader.evaluate_cards(packet, report, selected_cards, policy)
        write(out / (case['id'] + '-semantic.json'), semantic)
        primary_ids = {d['doc_id'] for d in packet['primary_documents']}
        extras = [a for a in policy.get('supplemental_anchors', []) if a['doc_id'] in primary_ids]
        write(out / (case['id'] + '-coverage.json'), coverage_ledger(packet, selected_cards, report, extras))
        summaries.append({'case_id': case['id'], 'status': result['status'],
                          'correct': score['correct'], 'total': score['total'], 'passed': score['passed'],
                          'semantic_obligations_passed': semantic['all_obligations_passed']})
    summary = {'numerical_cases': summaries, 'passed': all(r['passed'] for r in summaries),
               'not_claimed': 'This command alone does not establish 47 structural obligations or fresh-window transfer.'}
    write(out / 'numeric-summary.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_numeric_suite(args.out), ensure_ascii=False, indent=2))
