import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SuiteContractTests(unittest.TestCase):
    def module(self):
        path = ROOT / 'evaluation/handoff-v3/run_suite.py'
        self.assertTrue(path.exists(), 'v3 suite not implemented')
        spec = importlib.util.spec_from_file_location('v3_suite', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def report(self):
        return {'events': [{'id': 'e1', 'kind': 'input', 'reads': {}, 'writes': {'result': 'v1'}, 'attributes': {'name': 'epoch_elapsed_years'}},
                           {'id': 'e2', 'kind': 'divmod', 'reads': {'dividend': 'v1'}, 'writes': {'quotient': 'v2', 'remainder': 'v3'}}],
                'value_instances': [{'id': 'v1', 'producer': 'e1', 'output_port': 'result'},
                                    {'id': 'v2', 'producer': 'e2', 'output_port': 'quotient'},
                                    {'id': 'v3', 'producer': 'e2', 'output_port': 'remainder'}],
                'task_exports': {'new_moon': {'months': 'v2'}}}

    def test_projection_requires_executed_real_export_port(self):
        module = self.module(); report = self.report()
        execution = {'values': {'v1': 2, 'v2': 24}, 'event_results': {'e1': {'result': 2}, 'e2': {'quotient': 24}},
                     'explicit_bindings': [{'event_id': 'e1', 'name': 'epoch_elapsed_years', 'value': 2, 'source': 'inputs'}]}
        result = module.score_numeric(report, execution, {'months': 24}, {'epoch_elapsed_years': 2})
        self.assertTrue(result['passed'])
        self.assertEqual(['epoch_elapsed_years'], result['fields'][0]['initial_inputs'])
        report['value_instances'][1]['output_port'] = 'remainder'
        self.assertFalse(module.score_numeric(report, execution, {'months': 24}, {'epoch_elapsed_years': 2})['passed'])

    def test_boolean_is_not_integer_and_missing_exports_do_not_get_oracle(self):
        module = self.module(); report = self.report()
        execution = {'values': {'v2': True}, 'event_results': {'e2': {'quotient': True}}}
        result = module.score_numeric(report, execution, {'months': 1, 'head_day': 1})
        self.assertFalse(result['passed'])
        self.assertEqual(0, result['correct'])
        self.assertIsNone(result['fields'][1]['actual'])

    def test_forbidden_input_ancestry_is_not_numerical_success(self):
        module = self.module(); report = self.report()
        report['events'][0]['attributes']['name'] = 'gold_answer'
        execution = {'values': {'v2': 24}, 'event_results': {'e2': {'quotient': 24}},
                     'explicit_bindings': [{'event_id': 'e1', 'name': 'gold_answer', 'value': 24, 'source': 'inputs'}]}
        self.assertFalse(module.score_numeric(report, execution, {'months': 24})['passed'])

    def test_coverage_keeps_unscored_ranges_and_rejects_bad_hash(self):
        import hashlib
        module = self.module(); text = '甲乙丙丁戊己'
        doc = {'doc_id': 'd', 'reading_id': 'r', 'text': text}
        anchor = {'doc_id': 'd', 'reading_id': 'r', 'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'start': 1, 'end': 3, 'quote': '乙丙'}
        packet = {'primary_documents': [doc]}
        cards = [{'obligations': [{'id': 'o', 'anchor': anchor}]}]
        result = module.coverage_ledger(packet, cards, {})
        self.assertEqual(6, result['total_source_length'])
        self.assertEqual(2, result['audited_character_count'])
        self.assertEqual([[0, 1], [3, 6]], result['documents'][0]['unscored_ranges'])
        result = module.coverage_ledger(packet, cards, {'diagnostics': [{'cause': 'unknown_domain', 'source_spans': [anchor]}]})
        self.assertEqual(1, result['diagnostic_count'])
        self.assertIn('unknown_domain', result['blocking_causes'])
        result = module.coverage_ledger(packet, cards, {'diagnostics': {'unknown_domain': True, 'unparsed_spans': [anchor]}})
        self.assertEqual([anchor], result['unparsed_spans'])
        self.assertIn('unknown_domain', result['blocking_causes'])
        anchor['text_sha256'] = 'bad'
        with self.assertRaisesRegex(ValueError, 'anchor'):
            module.coverage_ledger(packet, cards, {})


if __name__ == '__main__':
    unittest.main()
