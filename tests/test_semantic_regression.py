"""Semantic regression projection contracts using synthetic parser reports."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import unittest


def sample_report():
    span = {'doc_id': 'sifen:38', 'reading_id': 'sifen:38.volatile', 'start': 4, 'end': 8, 'quote': '置入蔀年'}
    return {
        'tokens': [
            {'id': 'token-a', 'kind': 'Term', 'text': '入蔀年', 'source_span': span},
            {'id': 'token-b', 'kind': 'Syntax', 'text': '置', 'source_span': {'doc_id': 'sifen:38', 'start': 0, 'end': 1, 'quote': '置'}},
        ],
        'construction_candidates': [{
            'node_id': 'node-a', 'kind': 'assignment', 'text': '置入蔀年', 'status': 'selected',
            'slots': {'value': {'kind': 'Term', 'text': '入蔀年'}}, 'source_spans': [span],
        }],
        'program': {
            'definitions': [{
                'id': 'definition-a', 'kind': 'ProcedureDef', 'goal_surface': '天正術',
                'source_spans': [span], 'formal_inputs': {'入蔀年': {'uses': ['node-a'], 'roles': ['value']}},
                'free_variables': {'入蔀年': {'uses': ['node-a'], 'roles': ['value']}},
                'defined_values': {'積月': {'node_id': 'node-a', 'port': 'result'}},
                'return_ports': {'積月': {'node_id': 'node-a', 'port': 'result', 'value_id': 'value-a'}},
            }],
            'imports': [{
                'consumer_definition_id': 'definition-a', 'formal': '入蔀年', 'uses': ['node-a'],
                'candidates': [], 'selected_definition_id': None, 'selected_port': '入蔀年',
                'selection_reason': 'no declared root or source producer',
            }],
        },
        'unresolved': [{
            'cause': 'requires_external_data', 'source_spans': [span],
            'missing_or_conflicting_inputs': ['入蔀年'], 'reason': 'No source-defined current instance',
        }],
    }


class SemanticRegressionTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('evaluation.semantic_regression'),
                             'semantic regression projection module is missing')
        return importlib.import_module('evaluation.semantic_regression')

    def test_canonical_projection_is_deterministic_when_source_lists_reorder(self):
        module = self.module()
        first = sample_report()
        second = copy.deepcopy(first)
        second['tokens'].reverse()
        self.assertEqual(module.project_report(first), module.project_report(second))

    def test_runtime_ids_do_not_create_a_semantic_diff(self):
        module = self.module()
        before = sample_report()
        after = copy.deepcopy(before)
        after['tokens'][0]['id'] = 'token-new'
        after['construction_candidates'][0]['node_id'] = 'node-new'
        after['program']['definitions'][0]['id'] = 'definition-new'
        after['program']['definitions'][0]['formal_inputs']['入蔀年']['uses'] = ['node-new']
        after['program']['definitions'][0]['free_variables']['入蔀年']['uses'] = ['node-new']
        after['program']['definitions'][0]['defined_values']['積月']['node_id'] = 'node-new'
        after['program']['definitions'][0]['return_ports']['積月']['node_id'] = 'node-new'
        after['program']['definitions'][0]['return_ports']['積月']['value_id'] = 'value-new'
        after['program']['imports'][0]['consumer_definition_id'] = 'definition-new'
        after['program']['imports'][0]['uses'] = ['node-new']

        diff = module.diff_projection(module.project_report(before), module.project_report(after))

        self.assertTrue(all(not layer['added'] and not layer['removed'] and not layer['changed']
                            and layer['unchanged'] for layer in diff.values()))

    def test_semantic_field_change_is_reported_as_changed_at_the_same_span(self):
        module = self.module()
        before = sample_report()
        after = copy.deepcopy(before)
        after['construction_candidates'][0]['slots']['value']['text'] = '章月'

        diff = module.diff_projection(module.project_report(before), module.project_report(after))

        self.assertEqual(len(diff['R2']['changed']), 1)
        self.assertEqual(diff['R2']['added'], [])
        self.assertEqual(diff['R2']['removed'], [])

    def test_lexical_records_with_different_kinds_at_one_span_are_not_dropped(self):
        module = self.module()
        report = sample_report()
        report['tokens'].append({
            'id': 'token-number', 'kind': 'Number', 'text': '入蔀年',
            'source_span': copy.deepcopy(report['tokens'][0]['source_span']),
        })
        report['tokens'] = [report['tokens'][0], report['tokens'][-1]]

        projection = module.project_report(report)
        diff = module.diff_projection(projection, projection)

        self.assertEqual(len(diff['R1']['unchanged']), 2)

    def test_definition_kinds_sharing_source_spans_are_not_dropped(self):
        module = self.module()
        report = sample_report()
        duplicate = copy.deepcopy(report['program']['definitions'][0])
        duplicate.update({'id': 'definition-query', 'kind': 'QueryDef', 'goal_surface': '天正術問'})
        report['program']['definitions'].append(duplicate)

        projection = module.project_report(report)
        diff = module.diff_projection(projection, projection)

        self.assertEqual(len(diff['R3']['unchanged']), 2)

    def test_real_baseline_records_have_unique_generated_identities(self):
        module = self.module()
        baseline = json.loads((Path(__file__).resolve().parents[1] / 'evaluation' /
                               'semantic_regression_baseline.json').read_text(encoding='utf-8'))
        for unit_id, projection in baseline['cases'].items():
            for layer in ('R1', 'R2', 'R3', 'R4'):
                records = module._records(layer, projection[layer])
                identities = [key for key, _ in module._keyed_records(layer, records)]
                with self.subTest(unit_id=unit_id, layer=layer):
                    self.assertEqual(len(identities), len(set(identities)))


if __name__ == '__main__':
    unittest.main()
