"""M1.5: real corpus input and HTTP/compiler behavior, not stored result replay."""
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


class AdapterTests(unittest.TestCase):
    def adapter(self):
        self.assertTrue((ROOT / 'source_adapters/corpus.py').is_file(), 'Canonical corpus adapter is missing')
        return importlib.import_module('source_adapters.corpus')

    def test_real_source_and_context_are_exact_corpus_slices(self):
        result = self.adapter().build_source_packet(ROOT, 'sifen-3-5')
        packet = result['source_packet']
        self.assertEqual(packet['schema_version'], '3.0')
        self.assertEqual(len(packet['primary_documents']), 1)
        self.assertEqual(len(packet['context_documents']), 2)
        for doc in packet['primary_documents'] + packet['context_documents']:
            source = doc['source']
            original = (ROOT / source['path']).read_bytes().decode('utf-8')
            self.assertEqual(original[source['start']:source['end']], doc['text'])
            self.assertEqual(hashlib.sha256(doc['text'].encode()).hexdigest(), doc['text_sha256'])
        self.assertIn('置入蔀年減一', packet['primary_documents'][0]['text'])

    def test_adapter_uses_a_validated_effective_corpus_index(self):
        adapter = self.adapter()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir(parents=True)
            for name in ('calendrical-ir-pipeline.json', 'workbench-procedures.json'):
                shutil.copyfile(ROOT / 'config' / name, root / 'config' / name)
            shutil.copyfile(ROOT / 'calendars-四分历.md', root / 'calendars-四分历.md')
            with self.assertRaisesRegex(FileNotFoundError, 'effective_corpus_index_missing'):
                adapter.build_source_packet(root, 'sifen-3-5')
            subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/corpus/extract_sifen_units.py'), '--root', str(root)], check=True)
            self.assertEqual(adapter.build_source_packet(root, 'sifen-3-5')['source_packet'],
                             adapter.build_source_packet(ROOT, 'sifen-3-5')['source_packet'])
            path = root / 'calendars-四分历.md'
            raw = path.read_bytes()
            path.write_bytes(raw.replace('章法，十九'.encode(), '章法，十八'.encode()))
            with self.assertRaisesRegex(ValueError, 'corpus_index_source_hash_mismatch'):
                adapter.build_source_packet(root, 'sifen-3-5')
            path.write_bytes(raw + b'\n38\tduplicate\n')
            with self.assertRaisesRegex(ValueError, 'corpus_index_source_hash_mismatch'):
                adapter.build_source_packet(root, 'sifen-3-5')
            path.write_bytes(b''.join(line for line in raw.splitlines(keepends=True) if not line.startswith(b'38\t')))
            with self.assertRaisesRegex(ValueError, 'corpus_index_source_hash_mismatch'):
                adapter.build_source_packet(root, 'sifen-3-5')

    def test_unknown_procedure_is_not_a_path(self):
        with self.assertRaisesRegex(ValueError, 'unknown_procedure'):
            self.adapter().build_source_packet(ROOT, '../evaluation/anything')


class ServiceTests(unittest.TestCase):
    def service(self):
        self.assertTrue((ROOT / 'workbench/service.py').is_file(), 'Workbench service is missing')
        return importlib.import_module('workbench.service')

    def test_actual_compiler_executes_local_procedure(self):
        result = self.service().compile_procedure(ROOT, 'sifen-3-5', {'入蔀年': 25})
        self.assertEqual(result['graph']['ir_revision'], '3.1-rescue')
        self.assertEqual(result['execution']['named_outputs']['main:積月'], 296)
        self.assertEqual(result['execution']['named_outputs']['main:閏餘'], 16)
        self.assertEqual(result['summary']['execution_status'], 'executed')
        self.assertFalse(result['unresolved']['compiler'])
        self.assertTrue(result['graph']['events'])

    def test_omitted_input_is_visible_not_filled_from_fixture(self):
        result = self.service().compile_procedure(ROOT, 'sifen-3-5', {})
        self.assertEqual(result['summary']['execution_status'], 'missing_inputs')
        self.assertTrue(any(row.get('name') == '入蔀年' for row in result['unresolved']['execution']))
        self.assertEqual(result['execution']['named_outputs'], {})

    def test_only_declared_typed_inputs_are_accepted(self):
        service = self.service()
        for inputs in ({'入蔀年': True}, {'入蔀年': 1.5}, {'入蔀年': 0}, {'入蔀年': 77}, {'積月': 296}, []):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                service.compile_procedure(ROOT, 'sifen-3-5', inputs)


class HTTPTests(unittest.TestCase):
    def test_local_server_rejects_incompatible_site_prefix_before_starting(self):
        api = importlib.import_module('workbench.api')
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / 'index.html').write_text('<html data-baseurl="/mathesis/">', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'local_site_requires_root_prefix'):
                api.make_server(ROOT, 0, site_root=site)

    def test_same_origin_shell_api_and_rejection_paths(self):
        self.assertTrue((ROOT / 'workbench/api.py').is_file(), 'Local HTTP workbench is missing')
        api = importlib.import_module('workbench.api')
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        site = Path(directory.name)
        (site / 'index.html').write_text('MATHesis home', encoding='utf-8')
        server = api.make_server(ROOT, 0, site_root=site)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f'http://127.0.0.1:{server.server_port}'
        def fetch(path, value=None, headers=None):
            body = json.dumps(value).encode() if value is not None else None
            request = Request(origin + path, data=body, headers=headers or {'Content-Type': 'application/json'})
            return urlopen(request, timeout=15)
        try:
            with self.assertRaises(HTTPError) as error:
                fetch('/adjudication/')
            self.assertEqual(error.exception.code, 404)
            with fetch('/') as response:
                self.assertEqual(response.read().decode(), 'MATHesis home')
            with fetch('/api/analysis/sifen-3-5') as response:
                result = json.load(response)
                self.assertIn('projection', result)
                self.assertNotIn('execution', result)
            with fetch('/api/procedures') as response:
                self.assertEqual(json.load(response)['procedures'][0]['id'], 'sifen-3-5')
            with fetch('/api/procedures/sifen-3-5') as response:
                self.assertIn('source_packet', json.load(response))
            with fetch('/api/compile', {'procedure_id': 'sifen-3-5', 'inputs': {'入蔀年': 25}}) as response:
                self.assertEqual(json.load(response)['summary']['execution_status'], 'executed')
            for path in ('/AGENTS.md', '/evaluation/rescue-v3_1/registered_references/A01.json', '/adjudication/../api.py', '/%2e%2e/AGENTS.md', '/%5c..%5cAGENTS.md'):
                with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                    fetch(path)
                self.assertEqual(error.exception.code, 404)
            with self.assertRaises(HTTPError) as error:
                fetch('/api/compile', {'procedure_id': 'sifen-3-5', 'inputs': {}},
                      {'Content-Type': 'application/json', 'Origin': 'https://example.invalid'})
            self.assertEqual(error.exception.code, 403)
            with self.assertRaises(HTTPError) as error:
                fetch('/api/procedures', headers={'Host': 'evil.invalid'})
            self.assertEqual(error.exception.code, 403)
            with self.assertRaises(HTTPError) as error:
                fetch('/api/compile', {'procedure_id': 'sifen-3-5', 'inputs': {}, 'source_packet': {}})
            self.assertEqual(error.exception.code, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
