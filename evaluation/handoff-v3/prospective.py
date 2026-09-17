"""Freeze behavior files; lock an entire curated batch; preserve first outputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def exclusive(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')


def module(name):
    spec = importlib.util.spec_from_file_location('prospective_' + name, HERE / (name + '.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def make_manifest(root, paths):
    root = Path(root)
    return {'created_utc': datetime.now(timezone.utc).isoformat(), 'files': [
        {'path': str(Path(p)), 'sha256': hashlib.sha256((root / p).read_bytes()).hexdigest(),
         'bytes': (root / p).stat().st_size} for p in sorted(set(paths))]}


def verify_manifest(root, manifest):
    errors = []
    for row in manifest['files']:
        path = Path(root) / row['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != row['sha256']:
            errors.append({'path': row['path'], 'expected': row['sha256'], 'actual': actual})
    if manifest.get('closed_behavior_inventory'):
        recorded = {row['path'] for row in manifest['files']}
        for path in sorted(set(behavior_files(root)) - recorded):
            errors.append({'path': path, 'expected': None, 'actual': 'new_behavior_file'})
    return errors


def behavior_files(root):
    root = Path(root)
    patterns = ['analysis_parser/**/*',
                'evaluation/handoff-v3/*.py', 'evaluation/handoff-v3/*.json', 'evaluation/handoff-v3/SELECTION_POLICY.md',
                'handoff_v3/runtime_inputs/*.json', 'handoff_v3/reference/*.json',
                'handoff_v3/coverage/*', 'evaluation/handoff-v2/exposure-audit.json',
                'handoff_v3/sources/*.json', 'evaluation/handoff-v2/package/evidence/page_index.json',
                'tests/parser_v3/*.py', 'tests/parser/*.py']
    return sorted({str(p.relative_to(root)) for pattern in patterns for p in root.glob(pattern)
                   if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'})


def freeze(out, gate, root=ROOT):
    if gate.get('passed') is not True or gate.get('independent_reviews') != {'core': 'PASS', 'evaluator': 'PASS'}:
        raise ValueError('Accepted development gate and both independent reviews are required before freeze')
    manifest = make_manifest(root, behavior_files(root))
    manifest.update(environment={'python': sys.version, 'platform': platform.platform(),
                                 'implementation': platform.python_implementation(),
                                 'external_runtime_dependencies': [],
                                 'dependency_policy': 'Frozen core and grader use Python standard library only; worker import/file audit saved per run'},
                    closed_behavior_inventory=True,
                    gate=gate, protocol='v3-prospective-v1',
                    independence='prospective source-held-out evaluation; not independent human review')
    exclusive(Path(out) / 'freeze.json', manifest)
    return manifest


def lock_batch(root, batch):
    paths = []
    selection_path = batch.get('selection_manifest')
    if not selection_path:
        raise ValueError('A complete selection manifest is required')
    selection = load(Path(root) / selection_path)
    if not (Path(root) / 'freeze.json').exists():
        raise ValueError('selection must follow a saved behavior freeze')
    validate_selection(batch, selection, frozen=load(Path(root) / 'freeze.json'))
    paths.append(selection_path)
    ids = [w['id'] for w in batch['windows']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate prospective window IDs')
    for window in batch['windows']:
        paths.extend([window['packet'], window['reference']])
    paths.extend(batch.get('supporting_files', []))
    manifest = make_manifest(root, paths)
    manifest['batch'] = batch
    exclusive(Path(root) / 'prepared.json', manifest)
    return manifest


def validate_selection(batch, selection, *, frozen):
    universe = selection.get('candidate_universe', [])
    log = selection.get('selection_log', [])
    identities = [c.get('id') for c in universe]
    if not universe or None in identities or len(identities) != len(set(identities)):
        raise ValueError('selection candidate universe must have unique complete IDs')
    records = {c['id']: c for c in universe}
    if any(not c.get('family') or not c.get('source_locator') or 'exposed' not in c for c in universe):
        raise ValueError('selection universe requires family/source/exposure metadata')
    if (len(log) != len(identities) or {row.get('candidate_id') for row in log} != set(identities)
            or any(not row.get('decision') or not row.get('reason') for row in log)):
        raise ValueError('selection ledger must account for every candidate with decision and reason')
    if (not selection.get('exclusion_registry_hashes') or selection.get('no_parser_prefilter') is not True
            or selection.get('parser_runs_before_lock') != 0):
        raise ValueError('selection requires frozen exclusions and explicit no-prefilter declaration')
    frozen_files = {f['path']: f['sha256'] for f in frozen['files']}
    for registry in selection['exclusion_registry_hashes']:
        path = registry.get('path'); expected = registry.get('sha256')
        actual_path = ROOT / (path or '')
        if (not path or frozen_files.get(path) != expected or not actual_path.is_file()
                or hashlib.sha256(actual_path.read_bytes()).hexdigest() != expected):
            raise ValueError('selection exclusion hashes must match actual frozen resources')
    selected_ids = []
    for window in batch['windows']:
        cid = window.get('candidate_id', window['id']); selected_ids.append(cid)
        candidate = records.get(cid, {})
        if (not candidate or candidate['exposed'] or window.get('family') != candidate['family']
                or window['track'] not in ('A', 'B')):
            raise ValueError('selection window violates universe/exposure/family/track metadata')
        if window['track'] == 'A' and candidate.get('eligible_A') is not True:
            raise ValueError('selection A requires source-reviewed known-mechanism eligibility')
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError('selection candidate repeated across windows or tracks')
    selected_rows = {r['candidate_id'] for r in log if r['decision'] in ('selected', 'selected_A', 'selected_B')}
    if selected_rows != set(selected_ids):
        raise ValueError('selection ledger selected decisions contradict locked batch')
    rows_by_id = {r['candidate_id']: r for r in log}
    for window in batch['windows']:
        decision = rows_by_id[window.get('candidate_id', window['id'])]['decision']
        if decision != 'selected' and decision != 'selected_' + window['track']:
            raise ValueError('selection ledger track contradicts locked batch')
    available = [c for c in universe if not c['exposed'] and not c.get('source_unavailable', False)]
    expected_a = [c['id'] for c in available if c.get('eligible_A') is True][:4]
    actual_a = [w.get('candidate_id', w['id']) for w in batch['windows'] if w['track'] == 'A']
    if actual_a != expected_a:
        raise ValueError('selection A must use the earliest eligible candidates')
    remaining = [c for c in available if c['id'] not in expected_a]
    expected_b = remaining[:4]
    if len(expected_b) == 4 and len({c['family'] for c in expected_b}) == 1:
        alternate = next((c for c in remaining[4:] if c['family'] != expected_b[0]['family']), None)
        if alternate:
            expected_b[-1] = alternate
    actual_b = [w.get('candidate_id', w['id']) for w in batch['windows'] if w['track'] == 'B']
    if actual_b != [c['id'] for c in expected_b]:
        raise ValueError('selection B must use earliest remaining candidates with only registered last-family replacement')
    for track in ('A', 'B'):
        windows = [w for w in batch['windows'] if w['track'] == track]
        positions = [identities.index(w.get('candidate_id', w['id'])) for w in windows]
        if positions != sorted(positions):
            raise ValueError('selection must preserve candidate-universe order within each track')
        categories = {w.get('combination') if track == 'A' else w['family'] for w in windows}
        complete = len(windows) >= 4 and len(categories - {None}) >= 2
        if not complete and not selection.get('track_limits', {}).get(track, {}).get('shortfall_reason'):
            raise ValueError('selection count/family/combination shortfall requires an explicit limitation')


def preflight_destinations(root, windows):
    root = Path(root)
    destinations = [root / 'summary.json', root / 'run_journal.jsonl']
    destinations += [root / folder / (w['id'] + '.json') for w in windows for folder in ('first_outputs', 'first_scores')]
    for path in destinations:
        if path.exists():
            raise FileExistsError('Immutable first-run destination already exists: ' + str(path))
        for parent in path.parents:
            if parent.exists() and not parent.is_dir():
                raise FileExistsError('Output parent is not a directory: ' + str(parent))


def run_batch(root):
    root = Path(root)
    frozen, locked = load(root / 'freeze.json'), load(root / 'prepared.json')
    errors = verify_manifest(ROOT, frozen) + verify_manifest(root, locked)
    if errors:
        raise ValueError('Frozen files changed: ' + json.dumps(errors, ensure_ascii=False))
    windows = locked['batch']['windows']
    preflight_destinations(root, windows)
    runner = module('isolated_runtime'); grader = module('civil_contracts'); suite = module('run_suite')
    summary = []
    with (root / 'run_journal.jsonl').open('x', encoding='utf-8') as journal:
        def record(stage, **fields):
            journal.write(json.dumps(dict(stage=stage, utc=datetime.now(timezone.utc).isoformat(), **fields), ensure_ascii=False) + '\n'); journal.flush()
        record('started', expected_windows=[w['id'] for w in windows], state='incomplete_until_summary')
        try:
            for window in windows:
                record('window_started', window=window['id'])
                raw_packet = load(root / window['packet'])
                packet = raw_packet.get('packet', raw_packet); inputs = raw_packet.get('inputs', {})
                try:
                    result = runner.run_isolated(packet, inputs, core_dir=ROOT / 'analysis_parser')
                except Exception as error:
                    result = {'status': 'runtime_error', 'error': {'type': type(error).__name__, 'message': str(error)}, 'first_attempt_output_unavailable': True}
                exclusive(root / 'first_outputs' / (window['id'] + '.json'), result)
                record('raw_output_preserved', window=window['id'], status=result['status'])
                reference = load(root / window['reference'])
                report = result.get('report', {})
                score = grader.evaluate_cards(packet, report, reference['cards'], reference['policy'])
                coverage = suite.coverage_ledger(packet, reference['cards'], report, reference.get('supplemental_anchors', []))
                parser_clear = not (coverage['unparsed_spans'] or coverage['unresolved'] or coverage['diagnostics'])
                execution = result.get('execution')
                execution_present = isinstance(execution, dict)
                execution = execution if execution_present else {}
                execution_unresolved = execution.get('unresolved', [])
                external = [item for item in execution_unresolved if item.get('cause') == 'requires_external_data']
                outputs = execution.get('task_outputs', {})
                missing_outputs = [{'task': task, 'port': port, 'value_id': vid}
                                   for task, ports in report.get('task_exports', {}).items()
                                   for port, vid in ports.items() if port not in outputs.get(task, {})]
                execution_complete = (execution_present and 'unresolved' in execution
                                      and not execution_unresolved and not missing_outputs
                                      and any(report.get('task_exports', {}).values()))
                score['execution_status'] = {'completed': bool(execution_complete),
                                             'execution_present': execution_present,
                                             'unresolved': execution_unresolved,
                                             'requires_external_data': external,
                                             'missing_declared_outputs': missing_outputs}
                score['full_source_chain_passed'] = (result['status'] == 'completed' and score['all_obligations_passed'] is True and parser_clear and bool(execution_complete)
                                                     and reference.get('coverage') == 'complete_procedural_contract')
                score['coverage'] = coverage
                exclusive(root / 'first_scores' / (window['id'] + '.json'), score)
                summary.append({'id': window['id'], 'track': window['track'], 'family': window.get('family'),
                                'full_source_chain_passed': score['full_source_chain_passed'],
                                'relations': score['relations'], 'unparsed_spans': len(coverage['unparsed_spans']),
                                'unresolved': len(coverage['unresolved']),
                                'execution_unresolved': len(execution_unresolved),
                                'requires_external_data': len(external),
                                'missing_declared_outputs': len(missing_outputs),
                                'evaluator_unsupported': sum(o['status'] == 'evaluator_unsupported' for c in score['cards'] for o in c['obligations'])})
                record('window_scored', window=window['id'])
        except BaseException as error:
            record('preserved_partial_failure', completed_windows=[w['id'] for w in summary], error_type=type(error).__name__, message=str(error))
            raise
        record('all_windows_scored', state='awaiting_summary')
    result = {'windows': summary, 'first_outputs_preserved': True,
              'post_run_manifest_errors': verify_manifest(ROOT, frozen) + verify_manifest(root, locked),
              'selection_limits': locked['batch'].get('limitations', [])}
    exclusive(root / 'summary.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['freeze', 'lock', 'run'])
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--gate', type=Path)
    parser.add_argument('--batch', type=Path)
    args = parser.parse_args()
    result = (freeze(args.directory, load(args.gate)) if args.action == 'freeze' else
              lock_batch(args.directory, load(args.batch)) if args.action == 'lock' else run_batch(args.directory))
    print(json.dumps(result, ensure_ascii=False, indent=2))
