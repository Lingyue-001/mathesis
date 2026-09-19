"""Corpus unit extraction and manifest-to-SourcePacket contracts."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import unittest

from source_adapters.corpus import build_source_packet
from source_adapters.corpus_index import build_effective_index


ROOT = Path(__file__).resolve().parents[1]


class CorpusIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name)
        (cls.root / 'config').mkdir()
        for name in ('calendrical-ir-pipeline.json', 'workbench-procedures.json'):
            shutil.copyfile(ROOT / 'config' / name, cls.root / 'config' / name)
        for path in ROOT.glob('calendars-*.md'):
            shutil.copyfile(path, cls.root / path.name)
        subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/corpus/extract_sifen_units.py'), '--root', str(cls.root)],
                       check=True, capture_output=True, text=True)

    def test_effective_index_preserves_raw_byte_coordinates(self):
        index = build_effective_index(self.root, 'sifen')
        raw = (self.root / 'calendars-四分历.md').read_bytes()
        text = raw.decode('utf-8')
        self.assertGreater(raw.count(b'\r\n'), 0)
        self.assertEqual(index['source']['sha256'], hashlib.sha256(raw).hexdigest())
        for unit in index['units']:
            for span in unit['source_spans']:
                self.assertEqual(text[span['start']:span['end']], span['text'])
        self.assertEqual(index['source']['offset_unit'], 'unicode_code_point_in_utf8_decoded_bytes')

    def test_manifest_unit_selection_constructs_existing_real_packets(self):
        expected = {
            'sifen-3-5': (['sifen:section:38'], ['sifen:section:15', 'sifen:section:16']),
            'sifen-3-7-alternative': (['sifen:section:40'], ['sifen:section:17', 'sifen:section:19', 'sifen:section:25']),
        }
        for procedure_id, (primary_ids, context_ids) in expected.items():
            with self.subTest(procedure_id=procedure_id):
                packet = build_source_packet(self.root, procedure_id)['source_packet']
                documents = packet['primary_documents'] + packet['context_documents']
                self.assertEqual([doc['source']['unit_id'] for doc in packet['primary_documents']], primary_ids)
                self.assertEqual([doc['source']['unit_id'] for doc in packet['context_documents']], context_ids)
                for document in documents:
                    source = document['source']
                    self.assertEqual(document['text'], ''.join(span['quote'] for span in source['source_spans']))
                    self.assertEqual(document['text_sha256'], hashlib.sha256(document['text'].encode()).hexdigest())

    def test_adapter_requires_emitted_effective_index_and_uses_its_units(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir(parents=True)
            for name in ('calendrical-ir-pipeline.json', 'workbench-procedures.json'):
                shutil.copyfile(ROOT / 'config' / name, root / 'config' / name)
            shutil.copyfile(ROOT / 'calendars-四分历.md', root / 'calendars-四分历.md')
            with self.assertRaisesRegex(FileNotFoundError, 'effective_corpus_index_missing'):
                build_source_packet(root, 'sifen-3-5')
            subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/corpus/extract_sifen_units.py'), '--root', str(root)],
                           check=True, capture_output=True, text=True)
            index_path = root / 'corpus-review/sifen/effective.json'
            index = json.loads(index_path.read_text(encoding='utf-8'))
            index['units'] = [unit for unit in index['units'] if unit['id'] != 'sifen:section:38']
            index_path.write_text(json.dumps(index, ensure_ascii=False), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'corpus_index_not_current'):
                build_source_packet(root, 'sifen-3-5')

    def test_corpus_index_is_not_a_parser_input(self):
        packet = build_source_packet(self.root, 'sifen-3-5')['source_packet']
        self.assertNotIn('corpus_index', packet)
        self.assertNotIn('unit_relations', packet)
        self.assertNotIn('review_queue', packet)

    def test_index_keeps_parameter_candidates_separate_from_parser_input(self):
        index = build_effective_index(self.root, 'sifen')
        chapter_rule = next(unit for unit in index['units'] if unit['id'] == 'sifen:section:15')
        self.assertEqual(chapter_rule['parameters'], [{'name': '章法', 'value_text': '十九', 'note': None}])
        self.assertEqual(index['parameter_index']['章法'][0]['unit_id'], 'sifen:section:15')
        packet = build_source_packet(self.root, 'sifen-3-5')['source_packet']
        self.assertNotIn('parameters', packet['context_documents'][0])

    def test_extraction_command_writes_repeatable_auto_and_effective_artifacts(self):
        script = ROOT / 'scripts/corpus/extract_sifen_units.py'
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            command = [sys.executable, '-B', str(script), '--root', str(self.root), '--output-dir', str(output)]
            subprocess.run(command, check=True, capture_output=True, text=True)
            first = {name: (output / name).read_bytes() for name in ('sifen-units.auto.json', 'sifen-units.effective.json')}
            subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertEqual(first, {name: (output / name).read_bytes() for name in first})
            auto = json.loads(first['sifen-units.auto.json'])
            effective = json.loads(first['sifen-units.effective.json'])
            self.assertEqual(auto['method']['mode'], 'automatic')
            self.assertEqual(effective['method']['mode'], 'automatic_plus_human_overrides')
            self.assertEqual(auto['source']['sha256'], effective['source']['sha256'])

    def test_override_refuses_stale_source_and_unmapped_text_correction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir(parents=True)
            (root / 'corpus-review/sifen').mkdir(parents=True)
            shutil.copyfile(ROOT / 'config/calendrical-ir-pipeline.json', root / 'config/calendrical-ir-pipeline.json')
            shutil.copyfile(ROOT / 'calendars-四分历.md', root / 'calendars-四分历.md')
            override = root / 'corpus-review/sifen/overrides.json'
            override.write_text(json.dumps({'source_lock': {'source_id': 'sifen', 'sha256': 'obsolete'}, 'operations': []}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'override_source_lock_mismatch'):
                build_effective_index(root, 'sifen')
            override.write_text(json.dumps({'operations': [
                {'op': 'replace_text', 'target_id': 'sifen:section:15', 'text': '章法，十八。'}
            ]}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'override_source_lock_required'):
                build_effective_index(root, 'sifen')
            override.write_text(json.dumps({'source_lock': {'source_id': 'sifen', 'sha256': build_effective_index(self.root, 'sifen')['source']['sha256']}, 'operations': [
                {'op': 'replace_text', 'target_id': 'sifen:section:15', 'text': '章法，十八。'}
            ]}), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'replace_text_requires_versioned_reading_mapping'):
                build_effective_index(root, 'sifen')

    def test_override_rejects_relation_to_nonexistent_unit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir(parents=True)
            (root / 'corpus-review/sifen').mkdir(parents=True)
            shutil.copyfile(ROOT / 'config/calendrical-ir-pipeline.json', root / 'config/calendrical-ir-pipeline.json')
            shutil.copyfile(ROOT / 'calendars-四分历.md', root / 'calendars-四分历.md')
            source_hash = build_effective_index(self.root, 'sifen')['source']['sha256']
            (root / 'corpus-review/sifen/overrides.json').write_text(json.dumps({
                'source_lock': {'source_id': 'sifen', 'sha256': source_hash},
                'operations': [{'op': 'set_relations', 'target_id': 'sifen:section:15',
                                'relations': [{'kind': 'alternative_of', 'target_id': 'sifen:section:404'}]}],
            }), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'dangling_unit_relation'):
                build_effective_index(root, 'sifen')


if __name__ == '__main__':
    unittest.main()
