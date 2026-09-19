"""Read-only, canonical semantic projections of one parser report per unit."""
import json
import re
from pathlib import Path

from analysis_parser.pipeline import parse_packet
from source_adapters.corpus import build_source_packet_from_units


CASE_UNIT_IDS = ('sifen:section:38', 'sifen:section:39', 'sifen:section:41')
_RUNTIME_NAME = re.compile(r'^(?:[ve]\d+|(?:def|call|node|token)-)')


def _span(value):
    return {key: value[key] for key in ('doc_id', 'start', 'end', 'quote') if key in value}


def _spans(values):
    return _canonical([_span(value) for value in values])


def _canonical(value):
    if isinstance(value, dict):
        return {key: _canonical(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        values = [_canonical(item) for item in value]
        return sorted(values, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
    return value


def _slots(slots):
    return _canonical({name: {key: value[key] for key in ('kind', 'text') if key in value}
                       for name, value in slots.items()})


def _variables(values):
    return _canonical({name: {'roles': sorted(set(value.get('roles', [])))}
                       for name, value in values.items()})


def _ports(values):
    return _canonical({name: {'port': value.get('port')} for name, value in values.items()})


def _definition(value):
    return _canonical({
        'kind': value.get('kind'),
        'goal_surface': value.get('goal_surface'),
        'domain_label': value.get('domain_label'),
        'source_spans': _spans(value.get('source_spans', [])),
        'formal_inputs': _variables(value.get('formal_inputs', {})),
        'free_variables': _variables(value.get('free_variables', {})),
        'defined_values': _ports(value.get('defined_values', {})),
        'return_ports': _ports(value.get('return_ports', {})),
    })


def _definition_identity(value):
    if value is None:
        return None
    return _canonical({key: value.get(key) for key in ('kind', 'goal_surface', 'domain_label')}
                      | {'source_spans': _spans(value.get('source_spans', []))})


def _dependency_interface(report):
    candidates = {item.get('node_id'): item for item in report.get('construction_candidates', [])}
    definitions = {item.get('id'): item for item in report.get('program', {}).get('definitions', [])}

    def use_spans(node_ids):
        return _spans(sum((candidates.get(node_id, {}).get('source_spans', []) for node_id in node_ids), []))

    imports = []
    for item in report.get('program', {}).get('imports', []):
        imports.append(_canonical({
            'consumer': _definition_identity(definitions.get(item.get('consumer_definition_id'))),
            'formal': item.get('formal'),
            'use_source_spans': use_spans(item.get('uses', [])),
            'candidates': [_definition_identity(definitions.get(candidate_id))
                           for candidate_id in item.get('candidates', []) if candidate_id in definitions],
            'selected_definition': _definition_identity(definitions.get(item.get('selected_definition_id'))),
            'selected_port': item.get('selected_port'),
            'selection_reason': item.get('selection_reason'),
        }))
    missing = []
    for item in report.get('unresolved', []):
        inputs = [value for value in item.get('missing_or_conflicting_inputs', [])
                  if not _RUNTIME_NAME.match(str(value))]
        missing.append(_canonical({
            'cause': item.get('cause'),
            'source_spans': _spans(item.get('source_spans', [])),
            'missing_inputs': inputs,
            'reason': item.get('reason'),
        }))
    return _canonical({'imports': imports, 'missing_dependencies': missing})


def project_report(report):
    """Project an already-built report without invoking parser stages."""
    lexical = [{
        'source_span': _span(item.get('source_span', {})),
        'surface': item.get('text'),
        'kind': item.get('kind'),
    } for item in report.get('tokens', [])]
    constructions = [{
        'source_spans': _spans(item.get('source_spans', [])),
        'surface': item.get('text'),
        'kind': item.get('kind'),
        'slots': _slots(item.get('slots', {})),
        'status': item.get('status'),
    } for item in report.get('construction_candidates', [])]
    program = [_definition(item) for item in report.get('program', {}).get('definitions', [])]
    return _canonical({'R1': lexical, 'R2': constructions, 'R3': program, 'R4': _dependency_interface(report)})


def _records(layer, value):
    if layer == 'R4':
        return [('import', item) for item in value['imports']] + [
            ('missing_dependency', item) for item in value['missing_dependencies']]
    return [(layer, item) for item in value]


def _identity(layer, record_type, item):
    if layer == 'R1':
        return json.dumps({'source_span': item['source_span'], 'kind': item['kind'], 'surface': item['surface']},
                          ensure_ascii=False, sort_keys=True)
    if layer == 'R2':
        return json.dumps({'source_spans': item['source_spans'], 'kind': item['kind']},
                          ensure_ascii=False, sort_keys=True)
    if layer == 'R3':
        return json.dumps({'source_spans': item['source_spans'], 'kind': item['kind'],
                           'goal_surface': item['goal_surface']}, ensure_ascii=False, sort_keys=True)
    if record_type == 'import':
        return json.dumps({'consumer': item['consumer'], 'formal': item['formal'],
                           'use_source_spans': item['use_source_spans']}, ensure_ascii=False, sort_keys=True)
    return json.dumps({'source_spans': item['source_spans'], 'missing_inputs': item['missing_inputs']},
                      ensure_ascii=False, sort_keys=True)


def _keyed_records(layer, records):
    """Append a deterministic occurrence only where a semantic key repeats."""
    occurrences = {}
    for record_type, item in records:
        base = (record_type, _identity(layer, record_type, item))
        occurrence = occurrences.get(base, 0)
        occurrences[base] = occurrence + 1
        yield (*base, occurrence), item


def diff_projection(before, after):
    """Return a small R1–R4 added/removed/changed/unchanged semantic diff."""
    output = {}
    for layer in ('R1', 'R2', 'R3', 'R4'):
        old = dict(_keyed_records(layer, _records(layer, before[layer])))
        new = dict(_keyed_records(layer, _records(layer, after[layer])))
        keys = sorted(set(old) | set(new), key=lambda key: json.dumps(key, ensure_ascii=False))
        result = {'added': [], 'removed': [], 'changed': [], 'unchanged': []}
        for key in keys:
            if key not in old:
                result['added'].append(new[key])
            elif key not in new:
                result['removed'].append(old[key])
            elif old[key] == new[key]:
                result['unchanged'].append(old[key])
            else:
                result['changed'].append({'before': old[key], 'after': new[key]})
        output[layer] = result
    return output


def build_baseline(root):
    """Build the current machine baseline with exactly one parse per case."""
    cases = {}
    for unit_id in CASE_UNIT_IDS:
        packet = build_source_packet_from_units(
            root, 'sifen', [unit_id], context_unit_ids=[],
            provided_scope={'tradition': 'Han_Si_fen_li'})
        cases[unit_id] = project_report(parse_packet(packet))
    return _canonical({
        'schema': 'SemanticRegressionBaseline/1',
        'baseline_kind': 'current_machine_observation_not_gold',
        'cases': cases,
    })


def baseline_path(root):
    return Path(root) / 'evaluation' / 'semantic_regression_baseline.json'


def write_baseline(root):
    path = baseline_path(root)
    path.write_text(json.dumps(build_baseline(root), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path
