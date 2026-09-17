#!/usr/bin/env python3
"""Reproduce parser, structure, execution, behavior and mutation acceptance.

Run from any directory: python /path/to/evaluation/handoff-v2/run_development.py
This command does NOT perform the handoff package's reference-only self-check.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from critical import checks
from graph_checks import span_audit
from reference_steps import assess_steps
from layers import assess_layers, macro_layers
from numeric import explicit_inputs, SUPPLEMENT, assess_fixture
from behavior import run_behavior


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=HERE/'results')
    args = ap.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    package = HERE/'package'
    packets = {w: json.loads((package/'runtime_inputs'/f'{w}.json').read_text())
               for w in ['W01', 'W02', 'W03', 'W04']}
    specs = json.loads((package/'evaluation/critical_assertions.json').read_text())['assertions']
    fixtures = json.loads((package/'evaluation/numerical_fixtures.json').read_text())['fixtures']
    reports, critical, steps, integrity, layers = {}, [], [], [], []
    for w, packet in packets.items():
        r = parse_packet(packet); reports[w] = r; save(out/f'{w}.json', r)
        c = checks(r, w, specs); critical += c
        reference = json.loads((package/'reference'/f'{w}.json').read_text())
        s = assess_steps(r, reference); steps.append(s)
        layer = assess_layers(r, reference, s); layers.append(layer)
        save(out/f'{w}-layers.json', layer)
        save(out/f'{w}-steps.json', s)
        i = {'window': w, 'span_errors': span_audit(r), 'diagnostics': r['diagnostics'],
             'unparsed_spans': r['coverage']['unparsed_spans'], 'unresolved': r['unresolved'],
             'full_primary_character_denominator': sum(len(d['text']) for d in packet['primary_documents'])}
        i['pass'] = not any(i[k] for k in ['span_errors', 'diagnostics', 'unparsed_spans']) and all(
            x['cause'] == 'requires_external_data' for x in r['unresolved'])
        integrity.append(i)
    numeric = []
    for fixture in fixtures:
        w = fixture['window_id']
        x = execute(reports[w], explicit_inputs(w, fixture['inputs']), SUPPLEMENT if w == 'W04' else None)
        save(out/(fixture['fixture_id']+'-execution.json'), x)
        numeric.append(assess_fixture(reports[w], x, fixture))
    behavior = run_behavior(packets, reports, specs, fixtures, out/'behavior')
    summary = {'mode': 'exposed_development_acceptance_not_generalization',
               'timestamp_utc': datetime.now(timezone.utc).isoformat(),
               'python': platform.python_version(),
               'critical': {'passed': sum(x['status'] == 'pass' for x in critical), 'total': len(critical)},
               'reference_steps': {x['window']: {'passed': sum(r['status'] == 'pass' for r in x['rows']),
                                               'total': len(x['rows'])} for x in steps},
               'numeric': {'passed': sum(x['status'] == 'pass' for x in numeric), 'total': len(numeric)},
               'behavior': {'passed': sum(x['status'] == 'pass' for x in behavior), 'total_run': 25,
                            'D26': 'not_run_in_development'},
               'input_integrity': integrity,
               'layers': {x['window']: x['layers'] for x in layers}, 'layer_macro': macro_layers(layers),
               'full_chain': {x['window']: x['full_chain_passed'] for x in layers},
               'gate_contract': 'All 75 reference steps, 32 critical assertions, N01–N08, D01–D25, and every scored reference-annotated layer must pass. All-token mention recall is not_scored and is not claimed.'}
    summary['development_gate_passed'] = (summary['critical']['passed'] == 32 and
        sum(x['total'] for x in summary['reference_steps'].values()) == 75 and
        all(x['passed'] == x['total'] for x in summary['reference_steps'].values()) and
        all(x['full_chain_passed'] for x in layers) and
        summary['numeric']['passed'] == 8 and summary['behavior']['passed'] == 25 and
        all(x['pass'] for x in integrity))
    paths = sorted((ROOT/'analysis_parser').glob('*.py')) + sorted(HERE.glob('*.py'))
    summary['code_hashes'] = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in paths}
    for name, obj in [('critical', critical), ('numerical', numeric), ('behavior', behavior), ('summary', summary)]:
        save(out/(name+'.json'), obj)
    print(json.dumps({k: v for k, v in summary.items() if k not in ('input_integrity', 'code_hashes')},
                     ensure_ascii=False, indent=2))
    return 0 if summary['development_gate_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
