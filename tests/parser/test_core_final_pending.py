import unittest

from analysis_parser.execution import execute
from analysis_parser.pipeline import parse_packet
from test_core_composition import packet


class PendingCycleLifecycleTests(unittest.TestCase):
    def test_incomplete_cycle_at_eof_is_reported_with_original_span(self):
        report = parse_packet(packet('置甲，甲盈乙。'))

        issue = next(u for u in report['unresolved'] if u['cause'] == 'incomplete_construction')
        self.assertEqual(issue['missing_or_conflicting_inputs'], ['除之'])
        self.assertEqual(issue['source_spans'][0]['quote'], '甲盈乙')
        self.assertTrue(any(d['kind'] == 'incomplete_construction' for d in report['diagnostics']))

    def test_new_pending_cycle_rejects_replacement_and_uses_new_operands(self):
        report = parse_packet(packet('置甲，甲盈乙，丙盈丁，除之。'))

        issue = next(u for u in report['unresolved'] if u['cause'] == 'incomplete_construction')
        self.assertEqual(issue['source_spans'][0]['quote'], '甲盈乙')
        cycle = next(e for e in report['events'] if e['kind'] == 'cycle_reduce')
        labels = {v['id']: v['labels'] for v in report['value_instances']}
        self.assertIn('丙', labels[cycle['reads']['dividend']])
        self.assertIn('丁', labels[cycle['reads']['divisor']])

    def test_load_abandons_pending_cycle_so_later_continuation_cannot_attach(self):
        report = parse_packet(packet('置甲，甲盈乙。置丙，除之，名曰丁。'))

        self.assertFalse(any(e['kind'] == 'cycle_reduce' for e in report['events']))
        self.assertTrue(any(u['cause'] == 'incomplete_construction' for u in report['unresolved']))
        self.assertTrue(any(s['quote'] == '除之' for s in report['coverage']['unparsed_spans']))
        self.assertEqual(execute(report, {'甲': 8, '乙': 3, '丙': 20})['named_outputs']['main:丁'], 20)

    def test_adjacent_continuation_still_emits_cycle_reduce(self):
        report = parse_packet(packet('置甲，甲盈乙，除之，名曰丙。'))

        self.assertEqual(len([e for e in report['events'] if e['kind'] == 'cycle_reduce']), 1)
        self.assertFalse(any(u['cause'] == 'incomplete_construction' for u in report['unresolved']))
        self.assertEqual(execute(report, {'甲': 8, '乙': 3})['named_outputs']['main:丙'], 2)


if __name__ == '__main__':
    unittest.main()
