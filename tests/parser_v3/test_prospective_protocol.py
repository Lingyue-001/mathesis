import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ProspectiveProtocolTests(unittest.TestCase):
    def module(self):
        path = ROOT / 'evaluation/handoff-v3/prospective.py'
        self.assertTrue(path.exists(), 'freeze and prospective protocol not implemented')
        spec = importlib.util.spec_from_file_location('v3_prospective', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def test_freeze_verification_detects_resource_change(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'core.py').write_text('initial')
            manifest = module.make_manifest(root, ['core.py'])
            self.assertEqual([], module.verify_manifest(root, manifest))
            (root / 'core.py').write_text('changed')
            self.assertEqual('core.py', module.verify_manifest(root, manifest)[0]['path'])

    def test_batch_lock_includes_every_source_and_reference_before_running(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            frozen = module.make_manifest(ROOT, ['handoff_v3/coverage/exposure_registry.json'])
            (root / 'freeze.json').write_text(json.dumps(frozen))
            (root / 'packet.json').write_text('{}'); (root / 'reference.json').write_text('{}')
            selection = {'candidate_universe': [{'id': 'B01', 'family': 'test', 'source_locator': 'synthetic test fixture', 'exposed': False}],
                         'selection_log': [{'candidate_id': 'B01', 'decision': 'selected', 'reason': 'test only'}],
                         'exclusion_registry_hashes': frozen['files'],
                         'no_parser_prefilter': True, 'parser_runs_before_lock': 0,
                         'track_limits': {'A': {'shortfall_reason': 'test fixture'}, 'B': {'shortfall_reason': 'test fixture'}}}
            (root / 'selection.json').write_text(json.dumps(selection))
            batch = {'windows': [{'id': 'B01', 'track': 'B', 'family': 'test', 'packet': 'packet.json', 'reference': 'reference.json'}], 'selection_manifest': 'selection.json'}
            lock = module.lock_batch(root, batch)
            self.assertEqual({'packet.json', 'reference.json', 'selection.json'}, {f['path'] for f in lock['files']})
            (root / 'reference.json').write_text('{"later": true}')
            self.assertTrue(module.verify_manifest(root, lock))

    def test_unaccepted_development_gate_cannot_freeze(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            with self.assertRaisesRegex(ValueError, 'development'):
                module.freeze(out, {'passed': False}, root=ROOT)
            self.assertFalse((out / 'freeze.json').exists())

    def test_closed_manifest_rejects_added_parser_code(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'analysis_parser').mkdir()
            (root / 'analysis_parser/core.py').write_text('initial')
            manifest = module.make_manifest(root, module.behavior_files(root)); manifest['closed_behavior_inventory'] = True
            (root / 'analysis_parser/hidden_new_rule.py').write_text('new')
            self.assertTrue(module.verify_manifest(root, manifest))

    def test_selectionless_lock_rejected(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'p.json').write_text('{}'); (root / 'r.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'selection'):
                module.lock_batch(root, {'windows': [{'id': 'x', 'track': 'B', 'packet': 'p.json', 'reference': 'r.json'}]})

    def test_preflight_catches_score_collision_before_any_output(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'first_scores').mkdir(); (root / 'first_scores/x.json').write_text('{}')
            with self.assertRaises(FileExistsError):
                module.preflight_destinations(root, [{'id': 'x'}])
            self.assertFalse((root / 'first_outputs').exists())

    def test_selection_ledger_cannot_contradict_batch_or_skip_earlier_candidate(self):
        module = self.module()
        frozen = module.make_manifest(ROOT, ['handoff_v3/coverage/exposure_registry.json'])
        selection = {'candidate_universe': [{'id': x, 'family': 'test', 'source_locator': 'fixture', 'exposed': False} for x in ['B01', 'B02']],
                     'selection_log': [{'candidate_id': 'B01', 'decision': 'selected', 'reason': 'earliest'}, {'candidate_id': 'B02', 'decision': 'excluded', 'reason': 'later'}],
                     'exclusion_registry_hashes': frozen['files'], 'no_parser_prefilter': True, 'parser_runs_before_lock': 0,
                     'track_limits': {'A': {'shortfall_reason': 'test'}, 'B': {'shortfall_reason': 'test'}}}
        batch = {'windows': [{'id': 'B02', 'track': 'B', 'family': 'test'}]}
        with self.assertRaises(ValueError):
            module.validate_selection(batch, selection, frozen=frozen)

    def test_complete_chain_requires_actual_execution_not_only_structural_success(self):
        module = self.module()
        suite = module.module('run_suite'); policy = module.module('civil_policy')
        cards = suite.load(ROOT / 'handoff_v3/reference/civil_cards.json')
        reference = {'cards': [c for c in cards if c['card_id'].endswith('_ST')],
                     'policy': policy.build_policy(cards), 'coverage': 'complete_procedural_contract'}
        # Deliberately exposed development material: this checks the runner, not transfer.
        for supplied, expected in [({}, False), ({'epoch_elapsed_years': 9410}, True)]:
            with self.subTest(inputs=supplied), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                data = {'packet.json': {'packet': suite.prepare_packet('ST'), 'inputs': supplied},
                        'reference.json': reference,
                        'freeze.json': module.make_manifest(ROOT, module.behavior_files(ROOT))}
                for name, value in data.items():
                    (root / name).write_text(json.dumps(value, ensure_ascii=False))
                prepared = module.make_manifest(root, ['packet.json', 'reference.json'])
                prepared['batch'] = {'windows': [{'id': 'development', 'track': 'B', 'family': 'fixture',
                                                   'packet': 'packet.json', 'reference': 'reference.json'}]}
                (root / 'prepared.json').write_text(json.dumps(prepared))
                summary = module.run_batch(root)['windows'][0]
                score = suite.load(root / 'first_scores/development.json')
                self.assertTrue(score['all_obligations_passed'])
                self.assertEqual(expected, summary['full_source_chain_passed'])
                self.assertEqual(expected, score['execution_status']['completed'])
                self.assertEqual(not expected, bool(summary['execution_unresolved']))
                self.assertEqual(not expected, bool(score['execution_status']['missing_declared_outputs']))


if __name__ == '__main__':
    unittest.main()
