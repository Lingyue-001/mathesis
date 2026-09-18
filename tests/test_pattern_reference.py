import copy
import json
from pathlib import Path
import unittest

from analysis_parser.pipeline import parse_packet
from source_adapters.corpus import build_source_packet
from evaluation.pattern_reference import compare_reference
from evaluation.pattern_importer import import_annotations


ROOT = Path(__file__).resolve().parents[1]


class PatternReferenceTests(unittest.TestCase):
    def setUp(self):
        self.packet = build_source_packet(ROOT, 'sifen-3-5')['source_packet']
        self.graph = parse_packet(self.packet)
        assets = ROOT / 'evaluation/pattern-reference'
        self.crosswalk = json.loads((assets / 'operation-crosswalk.json').read_text(encoding='utf-8'))
        annotations = json.loads((assets / 'ch3-chunk-breakdown.json').read_text(encoding='utf-8'))
        sources = json.loads((assets / 'source-chunks.json').read_text(encoding='utf-8'))
        imported = import_annotations(annotations, sources, self.packet, self.crosswalk)
        self.reference = next(r['procedure_reference'] for r in imported['chunks'] if r['original']['chunk_id'] == 'cullen:ch3:chunk:0055')

    def compare(self):
        return compare_reference(self.packet, self.graph, self.reference, self.crosswalk)

    def test_real_steps_share_a_construction_without_being_collapsed(self):
        result = self.compare()
        self.assertEqual(len(result['rows']), 7)
        self.assertEqual([r['status'] for r in result['rows']], ['match'] * 7)
        a, b = result['rows'][:2]
        self.assertEqual(a['construction_ids'], b['construction_ids'])
        self.assertNotEqual(a['event_ids'], b['event_ids'])
        self.assertEqual(result['construction_groups'][a['construction_ids'][0]], ['step-1', 'step-2'])
        self.assertTrue(any(d['kind'] == 'missing_import' for d in result['machine_link_diagnostics']))
        self.assertEqual(result['graph_closure'], 'not_assessed_by_reference_comparison')

    def test_wrong_remainder_port_is_a_mismatch(self):
        division = next(e for e in self.graph['events'] if e['kind'] == 'divmod')
        alias = next(e for e in self.graph['events'] if e['attributes'].get('label') == '閏餘')
        alias['reads']['value'] = division['writes']['quotient']
        self.assertEqual(self.compare()['rows'][5]['status'], 'mismatch')

    def test_composite_load_without_subtraction_does_not_pass_by_overlap(self):
        self.graph['events'] = [e for e in self.graph['events'] if e['kind'] != 'subtract']
        self.assertEqual(self.compare()['rows'][1]['status'], 'missing_machine_semantics')

    def test_changed_reading_and_bad_quote_are_rejected(self):
        for field, value in [('reading_id', 'another-reading'), ('quote', '錯文'), ('start', 0)]:
            with self.subTest(field=field):
                ref = copy.deepcopy(self.reference)
                ref['steps'][0]['source_anchors'][0][field] = value
                with self.assertRaises(ValueError):
                    compare_reference(self.packet, self.graph, ref, self.crosswalk)

    def test_graph_from_another_reading_is_rejected(self):
        self.graph['documents'][0]['reading_id'] = 'old-reading'
        with self.assertRaisesRegex(ValueError, 'machine_source_mismatch'):
            self.compare()

    def test_reference_character_mapping_cannot_shift_an_occurrence(self):
        self.reference['steps'][0]['source_anchors'][0]['start'] += 1
        with self.assertRaisesRegex(ValueError, 'invalid_exact_anchor'):
            self.compare()

    def test_changed_threshold_and_wrong_operand_fail_semantic_checks(self):
        threshold = next(e for e in self.graph['events'] if e['kind'] == 'threshold')
        threshold['attributes']['lower_inclusive'] = False
        self.assertEqual(self.compare()['rows'][6]['status'], 'mismatch')
        multiplication = next(e for e in self.graph['events'] if e['kind'] == 'multiply')
        multiplication['reads']['right'] = multiplication['reads']['left']
        self.assertEqual(self.compare()['rows'][2]['status'], 'mismatch')

    def test_repeated_text_uses_coordinates_not_first_string_match(self):
        original = self.graph['events'][3]
        duplicate = copy.deepcopy(original)
        duplicate['id'] = 'wrong-occurrence'
        duplicate['syntax_node_id'] = 'other-node'
        duplicate['source_spans'] = [dict(original['source_spans'][0], start=50, end=56)]
        self.graph['events'].insert(0, duplicate)
        self.assertEqual(self.compare()['rows'][0]['event_ids'], [original['id']])

    def test_ambiguous_events_are_not_silently_selected(self):
        event = copy.deepcopy(next(e for e in self.graph['events'] if e['kind'] == 'load'))
        event['id'] = 'duplicate-load'
        value = copy.deepcopy(next(v for v in self.graph['value_instances'] if v['id'] == event['writes']['result']))
        value.update(id='duplicate-value', producer=event['id'])
        event['writes']['result'] = value['id']
        self.graph['value_instances'].append(value)
        self.graph['events'].append(event)
        self.assertEqual(self.compare()['rows'][0]['status'], 'ambiguous')

    def test_multispan_judgment_requires_both_evidence_spans(self):
        result = self.compare()
        self.assertEqual(len(self.reference['steps'][6]['source_anchors']), 2)
        event = next(e for e in self.graph['events'] if e['kind'] == 'threshold')
        event['source_spans'] = event['source_spans'][:1]
        self.assertEqual(self.compare()['rows'][6]['status'], 'missing_machine_semantics')

    def test_comparison_is_read_only_and_unknown_taxonomy_is_explicit(self):
        before = copy.deepcopy((self.packet, self.graph, self.reference, self.crosswalk))
        self.compare()
        self.assertEqual(before, (self.packet, self.graph, self.reference, self.crosswalk))
        self.reference['steps'][0]['legacy']['op'] = 'unknown_operation'
        self.assertEqual(self.compare()['rows'][0]['status'], 'crosswalk_missing')


if __name__ == '__main__':
    unittest.main()
