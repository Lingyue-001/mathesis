"""A non-ASCII packet must survive isolation; manifest keys must survive OS moves."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimePortability(unittest.TestCase):
    def test_exposed_host_reads_utf8_metadata_without_utf8_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'checkpoint'
            process = subprocess.run([
                sys.executable, '-X', 'utf8=0', '-B',
                'evaluation/rescue-v3_1/run_exposed.py', '--out', str(out),
                '--source-asset-map', 'docs/reconciliation/source-asset-map.json',
            ], cwd=ROOT, env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
                capture_output=True, encoding='utf-8', timeout=90)
            self.assertTrue((out / 'summary.json').is_file(), process.stderr)
            summary = json.loads((out / 'summary.json').read_text(encoding='utf-8'))
            self.assertTrue(all(row['full_chain_passed'] for row in summary['windows']))
            manifest = json.loads((out / 'behavior_manifest.json').read_text(encoding='utf-8'))
            # Missing external assets remain genuine failures, never encoding errors.
            self.assertTrue(all(error['cause'] == 'source_asset_identity_mismatch'
                                for error in manifest['inventory_errors']))
            self.assertEqual(process.returncode, 0 if summary['all_passed'] else 1)

    def test_both_isolated_workers_preserve_source_and_execute(self):
        text = '推甲課，置十，以二為法，如法得一，名曰甲量．'
        packet = {'schema_version': '3.0', 'primary_documents': [
            {'doc_id': 'synthetic.𠀀', 'text': text}]}
        for path, name in [
            ('evaluation/handoff-v3/isolated_runtime.py', 'portable_v3'),
            ('evaluation/rescue-v3_1/runtime_protocol.py', 'portable_rescue'),
        ]:
            with self.subTest(protocol=name):
                result = load(path, name).run_isolated(packet, {}, core_dir=ROOT / 'analysis_parser')
                self.assertEqual(result['status'], 'completed', result.get('stderr', result))
                self.assertEqual(result['report']['documents'][0]['text'], text)
                self.assertEqual(result['report']['documents'][0]['doc_id'], 'synthetic.𠀀')
                self.assertEqual(result['execution']['named_outputs'], {'main:甲量': 5})
                self.assertFalse(result['runtime_audit']['blocked_accesses'])

    def test_manifest_keys_and_mutation_diagnostics_use_portable_paths(self):
        runtime = load('evaluation/rescue-v3_1/runtime_protocol.py', 'portable_manifest')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            core = root / 'analysis_parser'
            core.mkdir()
            source = core / 'core.py'
            source.write_text('value = 1\n', encoding='utf-8')
            manifest = runtime.manifest(root)
            self.assertEqual([f['path'] for f in manifest['files']], ['analysis_parser/core.py'])
            source.write_text('value = 2\n', encoding='utf-8')
            self.assertTrue(any(e.get('path') == 'analysis_parser/core.py'
                                and e.get('actual') != e.get('expected')
                                for e in runtime.verify(root, manifest)))

    def test_asset_relocation_preserves_identity_and_never_hides_missing_assets(self):
        runtime = load('evaluation/rescue-v3_1/runtime_protocol.py', 'relocated_assets')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / 'evaluation/rescue-v3_1/contracts/source_assets.json'
            contract.parent.mkdir(parents=True)
            local = root / 'source.txt'
            content = '來源𠀀'.encode('utf-8')
            local.write_bytes(content)
            original = '/original/source.txt'
            contract.write_text(json.dumps({'files': [{'path': original, 'present': True,
                'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}]}), encoding='utf-8')
            mapping = {original: 'source.txt'}
            asset_errors = lambda errors: [e for e in errors if e['cause'].startswith('source_asset')]
            self.assertTrue(asset_errors(runtime.inventory_errors(root)))
            self.assertFalse(asset_errors(runtime.inventory_errors(root, source_asset_paths=mapping)))
            record = runtime.manifest(root, source_asset_paths=mapping)
            self.assertEqual(record['source_asset_paths'], mapping)
            self.assertFalse(asset_errors(runtime.verify(root, record)))
            local.write_bytes(b'wrong bytes')
            self.assertTrue(asset_errors(runtime.verify(root, record)))
            local.unlink()
            self.assertTrue(asset_errors(runtime.verify(root, record)))
            # The original frozen identity file is never rewritten by relocation.
            self.assertEqual(json.loads(contract.read_text(encoding='utf-8'))['files'][0]['path'], original)


if __name__ == '__main__':
    unittest.main()
