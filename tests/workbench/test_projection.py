"""Research projection preserves IR identity and uncertainty, without execution."""
import copy
import importlib
from pathlib import Path
import unittest
from unittest.mock import patch

from analysis_parser.pipeline import parse_packet
from source_adapters.corpus import build_source_packet

ROOT = Path(__file__).resolve().parents[2]


class ProjectionTests(unittest.TestCase):
    def project(self, graph):
        self.assertTrue((ROOT / 'workbench/projection.py').exists(), 'IR projection is missing')
        return importlib.import_module('workbench.projection').project_graph(graph)

    def graph(self):
        return parse_packet(build_source_packet(ROOT, 'sifen-3-5')['source_packet'])

    def test_projection_is_lossless_for_identity_and_does_not_mutate_ir(self):
        graph = self.graph()
        original = copy.deepcopy(graph)
        view = self.project(graph)
        self.assertEqual(graph, original)
        self.assertEqual({n['id'] for n in view['nodes']}, {e['id'] for e in graph['events']})
        self.assertEqual({s['id'] for s in view['steps']}, set(graph['syntax']['roots']))
        by_id = {s['id']: s for s in view['steps']}
        frame = view['frames'][0]
        self.assertEqual([item['id'] for item in frame['body']], graph['program']['definitions'][0]['body'])
        multiply = next(s for s in by_id.values() if s['kind'] == 'Multiply')
        self.assertEqual(multiply['event_ids'], ['e7'])
        self.assertEqual(multiply['source_spans'], next(n for n in graph['syntax']['nodes'] if n['id'] == multiply['id'])['source_spans'])

    def test_edges_preserve_producer_port_consumer_slot_and_fraction_scale(self):
        view = self.project(self.graph())
        edge = next(e for e in view['edges'] if e['value_id'] == 'v9')
        self.assertEqual((edge['producer'], edge['output_port'], edge['consumer'], edge['input_port']), ('e8', 'remainder', 'e10', 'value'))
        value = next(v for v in view['quantities'] if v['id'] == 'v11')
        self.assertEqual(value['role'], 'remainder')
        self.assertEqual(value['unit'], 'month_fraction')
        self.assertEqual(value['scale'], {'denominator': 'v1', 'value': 19})
        self.assertEqual((value['origin_producer'], value['origin_port']), ('e8', 'remainder'))

    def test_unknown_type_and_linker_diagnostics_are_not_hidden_by_execution(self):
        view = self.project(self.graph())
        self.assertTrue(any(i['kind'] == 'missing_import' for i in view['issues']))
        self.assertTrue(any(i.get('value_id') == 'v7' and i['kind'] == 'quantity_unresolved' for i in view['issues']))
        step = next(s for s in view['steps'] if s['kind'] == 'Multiply')
        self.assertTrue(step['issue_ids'])

    def test_different_procedure_and_unlowered_syntax_remain_visible(self):
        packet = {'schema_version': '3.0', 'primary_documents': [{'doc_id': 'other', 'text': '推別課，置三，以五乘之，神秘操作，名曰乙量。'}]}
        graph = parse_packet(packet)
        view = self.project(graph)
        self.assertEqual(len(view['nodes']), len(graph['events']))
        self.assertTrue(any(s['surface'] == '神秘操作' for s in view['steps']))
        self.assertTrue(view['issues'])
        self.assertTrue(all(s['id'].startswith('other:') for s in view['steps']))

    def test_nested_query_hierarchy_and_control_are_retained(self):
        packet = {'schema_version': '3.0', 'primary_documents': [{'doc_id': 'query', 'text': '推甲術，置十，名曰甲量。求乙，置甲量，以二乘之，名曰乙量。'}]}
        graph = parse_packet(packet)
        view = self.project(graph)
        children = [f for f in view['frames'] if f['parent']]
        self.assertTrue(children)
        for child in children:
            parent = next(f for f in view['frames'] if f['id'] == child['parent'])
            self.assertIn(child['id'], [item['id'] for item in parent['body']])
            self.assertEqual(child['kind'], 'QueryDef')
            self.assertTrue(child['base_ref'])

    def test_analysis_does_not_invoke_executor(self):
        service = importlib.import_module('workbench.service')
        self.assertTrue(hasattr(service, 'analyze_procedure'), 'Compile-only service is missing')
        with patch('workbench.service.execute', side_effect=AssertionError('analysis must not execute')):
            result = service.analyze_procedure(ROOT, 'sifen-3-5')
        self.assertIn('projection', result)
        self.assertNotIn('execution', result)
        self.assertEqual(result['summary']['execution_status'], 'not_run')

    def test_composed_roots_do_not_hide_operations_referenced_by_program_body(self):
        graph = self.graph()
        root_ids = graph['syntax']['roots'][:]
        graph['syntax']['nodes'].append({'id': 'sequence-root', 'kind': 'Sequence',
                                        'children': root_ids, 'slots': {}, 'source_spans': [], 'surface': ''})
        graph['syntax']['roots'] = ['sequence-root']
        view = self.project(graph)
        self.assertTrue(set(root_ids).issubset({step['id'] for step in view['steps']}))


if __name__ == '__main__':
    unittest.main()
