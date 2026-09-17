"""The runtime must not see scholarly answers or injected derived year/head values."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / 'evaluation/handoff-v3/isolated_runtime.py'


class RuntimeIsolationTests(unittest.TestCase):
    def runner(self):
        self.assertTrue(MODULE.exists(), 'isolated runtime is not implemented')
        spec = importlib.util.spec_from_file_location('isolated_runtime', MODULE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_inherited_packet_runs_without_reference_files(self):
        runner = self.runner()
        packet = json.loads((ROOT / 'handoff_v3/runtime_inputs/ST_CIVIL_CORE.json').read_text())
        # Deliberately use the inherited adapter to isolate the isolation test from v3 development.
        packet.pop('schema_version')
        result = runner.run_isolated(packet, {}, core_dir=ROOT / 'analysis_parser')
        self.assertIn('events', result['report'])
        self.assertTrue(result['runtime_audit']['reference_access_blocked'])
        self.assertTrue(result['runtime_audit']['network_blocked'])
        self.assertTrue(result['runtime_audit']['opened_files'])
        self.assertFalse(any('/reference/' in x['path'] for x in result['runtime_audit']['opened_files']))

    def test_derived_entry_input_rejected(self):
        runner = self.runner()
        with self.assertRaisesRegex(ValueError, 'epoch'):
            runner.run_isolated({}, {'入蔀年': 63}, core_dir=ROOT / 'analysis_parser')

    def test_reference_fields_cannot_enter_source_packet(self):
        runner = self.runner()
        with self.assertRaisesRegex(ValueError, 'packet field'):
            runner.run_isolated({'reference': {'answer': 63}}, {}, core_dir=ROOT / 'analysis_parser')

    def test_reference_read_attempt_blocked_and_logged(self):
        runner = self.runner()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            core = root / 'analysis_parser'; core.mkdir()
            (core / '__init__.py').write_text('')
            secret = root / 'answer.json'; secret.write_text('{"answer": 63}')
            (core / 'pipeline.py').write_text(
                'def parse_packet(packet):\n    return open(' + repr(str(secret)) + ').read()\n')
            (core / 'execution.py').write_text('def execute(report, inputs):\n    return {}\n')
            result = runner.run_isolated({}, {}, core_dir=core)
            self.assertEqual('runtime_error', result['status'])
            self.assertIn('outside runtime', result['error']['message'])
            self.assertEqual(str(secret), result['runtime_audit']['blocked_accesses'][0]['path'])

    def test_first_result_is_exclusive_create(self):
        runner = self.runner()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'first.json'
            runner.write_exclusive(path, {'attempt': 1})
            with self.assertRaises(FileExistsError):
                runner.write_exclusive(path, {'attempt': 2})
            self.assertEqual({'attempt': 1}, json.loads(path.read_text()))


if __name__ == '__main__':
    unittest.main()
