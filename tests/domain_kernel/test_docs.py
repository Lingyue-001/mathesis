"""Documentation drift and actual consumer/effect-test contracts."""
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.docs = importlib.import_module('domain_kernel.docs')

    def test_repeatable_generation_tracks_registry_and_output_schema(self):
        first = self.docs.render_documents()
        self.assertEqual(first, self.docs.render_documents())
        registry = json.loads((ROOT/'domain_kernel/kernel.registry.json').read_text(encoding='utf-8'))
        registry['composition_rules'].append(dict(copy.deepcopy(registry['composition_rules'][0]), id='C-test'))
        changed = self.docs.render_documents(registry=registry)
        self.assertNotEqual(first['SCHEMA_REFERENCE.md'], changed['SCHEMA_REFERENCE.md'])
        output = json.loads((ROOT/'domain_kernel/output.schema.json').read_text(encoding='utf-8'))
        output['properties']['identity']['description'] = 'Changed source identity contract'
        self.assertNotEqual(first['SCHEMA_REFERENCE.md'], self.docs.render_documents(output_schema=output)['SCHEMA_REFERENCE.md'])

    def test_manifest_checks_real_symbols_and_effect_tests(self):
        manifest = json.loads((ROOT/'domain_kernel/consumer-manifest.json').read_text(encoding='utf-8'))
        self.docs.validate_manifest(manifest)
        for field in ('producer', 'validator', 'consumer', 'effect_test'):
            changed = copy.deepcopy(manifest)
            row = next(r for r in changed['capabilities'] if r['status'] == 'suggestion_only')
            row[field] = ['domain_kernel/engine.py::absent']
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.docs.validate_manifest(changed)
        changed = copy.deepcopy(manifest)
        row = next(r for r in changed['capabilities'] if r['status'] == 'planned')
        row['status'] = 'implemented'
        with self.assertRaises(ValueError):
            self.docs.validate_manifest(changed)

    def test_check_detects_stale_docs_without_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            generated = self.docs.render_documents()
            for name, content in generated.items():
                (root/name).write_text(content, encoding='utf-8')
            self.docs.check_documents(root)
            target = root/'SCHEMA_REFERENCE.md'
            target.write_text(target.read_text(encoding='utf-8')+'stale\n', encoding='utf-8')
            before = target.read_bytes()
            with self.assertRaisesRegex(ValueError, 'generated_doc_stale'):
                self.docs.check_documents(root)
            self.assertEqual(target.read_bytes(), before)

    def test_cli_check_is_read_only_and_current(self):
        files = list((ROOT/'docs/domain-kernel').glob('*.md'))
        before = {p: p.read_bytes() for p in files}
        result = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-m', 'domain_kernel.docs', '--check'],
                                cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in files})


if __name__ == '__main__':
    unittest.main()
