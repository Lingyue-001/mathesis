"""Source segmentation regressions; never write the live research workspace."""
from pathlib import Path
import unittest
from unittest.mock import patch

from source_adapters import corpus_index as index

ROOT = Path(__file__).resolve().parents[1]


class SegmentationRuleTests(unittest.TestCase):
    def test_cues_are_nonoverlapping_and_do_not_count_query_markers(self):
        self.assertEqual(index._classify('不滿不滿不滿。')[0], 'discourse')
        self.assertEqual(index._classify('其求求求求')[0], 'heading')
        self.assertEqual(index.cue_count('不滿滿不滿餘'), 4)

    def test_parameter_exclusions_are_independent_of_cue_count(self):
        self.assertEqual(index._parameter_fields('日餘，百六十八。'), [{'name': '日餘', 'value_text': '百六十八', 'note': None}])
        self.assertEqual(index._classify('日餘，百六十八。')[0], 'parameter')
        self.assertEqual(index._parameter_fields('求日，百六十八。'), [])
        self.assertNotEqual(index._classify('求日，百六十八。')[0], 'parameter')

    def test_nighttime_is_not_a_sufficient_join_condition(self):
        spans, events = index._physical_spans(index.numbered_sections('1 日在夜半\n2 月在東井。'))
        self.assertEqual(len(spans), 2)
        self.assertEqual(events, [])

    def test_real_incomplete_joins_have_left_right_condition_evidence(self):
        with patch.object(index, '_physical_spans', wraps=index._physical_spans) as physical:
            auto = index.build_auto_index(ROOT)
        self.assertEqual(physical.call_count, 1)
        for pair in ((35, 36), (57, 58)):
            event = next(e for e in auto['boundary_events'] if (e['left_section'], e['right_section']) == pair)
            self.assertTrue(event['left']['text'])
            self.assertTrue(event['right']['text'])
            self.assertTrue(event['conditions'])
            self.assertTrue(any(u['sections'] == list(pair) for u in auto['units']))

    def test_query_units_remain_separate_with_a_reviewable_proposal(self):
        auto = index.build_auto_index(ROOT)
        for section in (49, 50, 59):
            self.assertTrue(any(u['sections'] == [section] for u in auto['units']))
        proposal = next(q for q in auto['review_queue'] if q['kind'] == 'confirm_followup_grouping' and q['sections'] == [50])
        self.assertEqual(proposal['candidate_target'], 'sifen:section:49')
        self.assertTrue(proposal['left']['text'])
        self.assertTrue(proposal['right']['text'].startswith('求'))

    def test_planet_scopes_and_local_procedure_markers_remain_candidates(self):
        self.assertEqual(index._classify('步術曰：置甲，以乙乘之。')[0], 'procedure_root')
        for planet in '木火土金水':
            text = planet + '，周率，十二。日率，三百。月餘，二十。'
            self.assertEqual(index._classify(text)[0], 'parameter_block')
            self.assertTrue(all(p['scope'] == planet for p in index._parameter_fields(text)))

    def test_boundary_review_displays_real_evidence(self):
        from tools.parser_inspector import segmentation_review as ui
        self.assertTrue(callable(getattr(ui, 'proposal_text', None)))
        event = next(e for e in index.build_auto_index(ROOT)['boundary_events'] if e['left_section'] == 57)
        rendered = ui.proposal_text(event)
        self.assertIn(event['left']['text'], rendered)
        self.assertIn(event['right']['text'], rendered)
        self.assertIn(event['conditions'][0]['match'], rendered)


if __name__ == '__main__':
    unittest.main()
