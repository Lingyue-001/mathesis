"""Unit-selected SourcePacket contracts independent of legacy presets."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from analysis_parser.pipeline import parse_packet
from source_adapters import corpus


ROOT = Path(__file__).resolve().parents[1]


class UnitPacketTests(unittest.TestCase):
    def test_selected_primary_unit_builds_a_primary_only_packet(self):
        """A caller-selected effective unit must not add context documents."""
        builder = getattr(corpus, 'build_source_packet_from_units', None)
        self.assertIsNotNone(builder, 'unit-based packet builder is missing')

        packet = builder(ROOT, 'sifen', ['sifen:section:38'])

        self.assertEqual([doc['source']['unit_id'] for doc in packet['primary_documents']],
                         ['sifen:section:38'])
        self.assertEqual(packet['context_documents'], [])
        document = packet['primary_documents'][0]
        source = document['source']
        original = (ROOT / source['path']).read_bytes().decode('utf-8')
        self.assertEqual(document['text'], ''.join(span['quote'] for span in source['source_spans']))
        for span in source['source_spans']:
            self.assertEqual(original[span['start']:span['end']], span['quote'])
        self.assertEqual(document['text_sha256'], hashlib.sha256(document['text'].encode()).hexdigest())
        self.assertTrue(parse_packet(packet)['tokens'])

    def test_legacy_preset_keeps_its_existing_packet_shape(self):
        """Changing the shared builder must not change the legacy Workbench preset."""
        packet = corpus.build_source_packet(ROOT, 'sifen-3-5')['source_packet']

        self.assertEqual(packet['packet_id'], 'repo:sifen-3-5')
        self.assertEqual([doc['source']['unit_id'] for doc in packet['primary_documents']],
                         ['sifen:section:38'])
        self.assertEqual([doc['source']['unit_id'] for doc in packet['context_documents']],
                         ['sifen:section:15', 'sifen:section:16'])
        self.assertEqual(packet['primary_documents'][0]['source']['reconstruction_span_id'], 'sifen:L74')

    def test_legacy_preset_registry_rejects_added_research_objects(self):
        """Adding a registry record must not create a new production source entry."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir()
            manifest = json.loads((ROOT / 'config/workbench-procedures.json').read_text(encoding='utf-8'))
            manifest['procedures'].append({**manifest['procedures'][0], 'id': 'new-research-object'})
            (root / 'config/workbench-procedures.json').write_text(
                json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'legacy_preset_registry_changed'):
                corpus.list_procedures(root)


if __name__ == '__main__':
    unittest.main()
