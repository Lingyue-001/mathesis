"""Structural scores must reject numerically invisible binding mistakes."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CivilContractTests(unittest.TestCase):
    def module(self):
        path = ROOT / 'evaluation/handoff-v3/civil_contracts.py'
        self.assertTrue(path.exists(), 'civil graph contracts not implemented')
        spec = importlib.util.spec_from_file_location('civil_contracts', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module

    def fixture(self):
        text = '盈章歲得一，盈章歲得一'
        digest = hashlib.sha256(text.encode()).hexdigest()
        doc = {'doc_id': 'd', 'reading_id': 'r', 'text': text, 'text_sha256': digest}
        anchor = dict(doc_id='d', reading_id='r', start=6, end=11, quote=text[6:11], text_sha256=digest)
        events = [{'id': 'in', 'kind': 'input', 'reads': {}, 'writes': {'result': 'v0'}, 'attributes': {'name': 'epoch_elapsed_years'}},
                  {'id': 'p', 'kind': 'parameter', 'reads': {}, 'writes': {'result': 'v1'}, 'attributes': {'name': '章歲', 'value': 19}},
                  {'id': 'a', 'kind': 'divmod', 'reads': {'dividend': 'v0', 'divisor': 'v1'}, 'writes': {'quotient': 'v2', 'remainder': 'v3'},
                   'source_spans': [dict(anchor, start=0, end=5, quote=text[:5])], 'scope': {'task': 'new_moon'}},
                  {'id': 'b', 'kind': 'divmod', 'reads': {'dividend': 'v2', 'divisor': 'v1'}, 'writes': {'quotient': 'v4', 'remainder': 'v5'},
                   'source_spans': [copy.deepcopy(anchor)], 'scope': {'task': 'new_moon'}}]
        values = [{'id': vid, 'producer': event['id'], 'output_port': port} for event in events for port, vid in event['writes'].items()]
        report = {'events': events, 'value_instances': values, 'task_exports': {'new_moon': {'months': 'v4'}}}
        reference = [{'card_id': 'C', 'obligations': [{'id': 'o', 'anchor': anchor}]}]
        predicate = {'kind': 'divmod', 'scope': {'task': 'new_moon'},
                     'reads': {'dividend': {'origin': {'kind': 'divmod', 'port': 'quotient'}}, 'divisor': {'parameter': '章歲'}},
                     'writes': {'quotient': {'export': ['new_moon', 'months']}}}
        policy = {'supported_actions': ['input', 'parameter', 'divmod', 'alias'], 'obligations': {'o': {'events': [predicate]}}}
        return {'primary_documents': [doc]}, report, reference, policy

    def test_repeated_quote_requires_second_occurrence_and_correct_port(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        self.assertTrue(module.evaluate_cards(packet, report, reference, policy)['all_obligations_passed'])
        report['events'][-1]['reads']['dividend'] = 'v3'
        score = module.evaluate_cards(packet, report, reference, policy)
        self.assertFalse(score['all_obligations_passed'])
        self.assertGreater(score['relations']['FP'], 0)
        self.assertGreater(score['relations']['FN'], 0)
        report['events'].pop()
        self.assertFalse(module.evaluate_cards(packet, report, reference, policy)['all_obligations_passed'])

    def test_wrong_export_pointer_does_not_pass_equal_labels(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        report['task_exports']['new_moon']['months'] = 'v2'
        self.assertFalse(module.evaluate_cards(packet, report, reference, policy)['all_obligations_passed'])

    def test_unknown_actual_action_is_unsupported_not_fp(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        report['events'][-1]['kind'] = 'unknown_new_action'
        score = module.evaluate_cards(packet, report, reference, policy)
        self.assertIsNone(score['all_obligations_passed'])
        self.assertEqual('evaluator_unsupported', score['cards'][0]['obligations'][0]['status'])
        self.assertEqual(0, score['relations']['FP'])

    def test_substituted_quote_with_real_offsets_is_invalid_source(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        report['events'][-1]['source_spans'][0]['quote'] = 'wrong'
        score = module.evaluate_cards(packet, report, reference, policy)
        self.assertFalse(score['all_obligations_passed'])
        self.assertTrue(score['source_errors'])

    def test_three_branch_and_full_table_contracts_are_checked(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        graph = module.Graph(packet, report)
        event = {'id': 'x', 'kind': 'select', 'attributes': {'choices': [{'label': '天統'}]}}
        self.assertFalse(graph.event(event, {'kind': 'select', 'branch_contract': 'three_concordances'})[0])
        packet['context_tables'] = [{'table_id': 't', 'rows': [1, 2], 'columns': ['year', '蔀首日']}]
        graph = module.Graph(packet, report)
        event = {'id': 'x', 'kind': 'lookup', 'attributes': {'table': {'table_id': 't', 'rows': [1], 'columns': ['year', '蔀首日']}, 'day_column': 1, 'row_base': 1, 'column_base': 0}}
        self.assertFalse(graph.event(event, {'kind': 'lookup', 'table_contract': 'full_source_table'})[0])

    def test_method_target_must_have_real_body_and_definition_anchor(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        event = {'id': 'x', 'kind': 'method_call', 'reads': {}, 'attributes': {'target': 'made_up', 'body': []}}
        graph = module.Graph(packet, report)
        self.assertFalse(graph.event(event, {'kind': 'method_call', 'method_contract': {'definition_anchor': reference[0]['obligations'][0]['anchor']}})[0])

    def test_same_numeric_literal_at_other_occurrence_is_not_same_slot(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        event = report['events'][2]
        event.update(kind='literal', attributes={'value': 1010})
        graph = module.Graph(packet, report)
        self.assertFalse(graph.value('v2', {'literal': 1010, 'anchor': reference[0]['obligations'][0]['anchor']}))

    def test_display_control_cannot_hide_different_executed_control(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        graph = module.Graph(packet, report)
        event = {'id': 'x', 'kind': 'repeat', 'control': {'stop': {'operator': 'gt'}},
                 'attributes': {'control': {'stop': {'operator': 'ge'}}}}
        self.assertFalse(graph.event(event, {'kind': 'repeat', 'control': {'stop': {'operator': 'gt'}}})[0])

    def test_crossing_adjacent_span_is_not_occurrence_evidence(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        report['events'][-1]['source_spans'] = [dict(reference[0]['obligations'][0]['anchor'], start=5, end=7, quote=packet['primary_documents'][0]['text'][5:7])]
        self.assertFalse(module.evaluate_cards(packet, report, reference, policy)['all_obligations_passed'])

    def test_value_unit_and_denominator_are_actual_graph_properties(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        value = report['value_instances'][-2]
        value.update(unit='day_fraction', scale={'denominator': 'v1', 'value': 19})
        graph = module.Graph(packet, report)
        self.assertFalse(graph.value('v4', {'export': ['new_moon', 'months'], 'unit': 'month_fraction', 'denominator': {'parameter': '章歲'}}))

    def test_supplemental_export_relation_cannot_be_ignored(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        policy['obligations']['o']['exports'] = [{'path': ['new_moon', 'missing'], 'value': {'literal': 1}}]
        self.assertFalse(module.evaluate_cards(packet, report, reference, policy)['all_obligations_passed'])

    def test_export_alias_cannot_claim_conflicting_quantity(self):
        module = self.module(); packet, report, reference, policy = self.fixture()
        report['value_instances'][-2]['unit'] = 'month_fraction'
        report['events'].append({'id': 'alias', 'kind': 'alias', 'reads': {'value': 'v4'}, 'writes': {'result': 'v6'}})
        report['value_instances'].append({'id': 'v6', 'producer': 'alias', 'output_port': 'result', 'unit': 'day_fraction'})
        report['task_exports']['new_moon']['months'] = 'v6'
        graph = module.Graph(packet, report)
        self.assertFalse(graph.value('v4', {'export': ['new_moon', 'months'], 'unit': 'month_fraction'}))


if __name__ == '__main__':
    unittest.main()
