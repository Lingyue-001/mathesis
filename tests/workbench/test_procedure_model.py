"""Generic contracts first; §38 is an integration example, never a rule."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from workbench.procedure_model import build_procedure_model, serialize_procedure_model, export_procedure_model


def synthetic():
    def anchor(start, end):
        return {'doc_id': 'doc-x', 'reading_id': 'reading-x', 'start': start, 'end': end,
                'quote': 'ABCDEFGH'[start:end], 'offset_unit': 'unicode_code_point'}
    return {'schema': 'ScholarSourceProjection/1',
            'source': {'doc_id': 'doc-x', 'reading_id': 'reading-x', 'text': 'ABCDEFGH'},
            'terms': [{'id': 'term-a', 'surface': 'Alpha', 'source_anchor': anchor(0, 1)},
                      {'id': 'term-q', 'surface': 'Quanta', 'source_anchor': anchor(3, 4)},
                      {'id': 'term-r', 'surface': 'Residue', 'source_anchor': anchor(4, 5)}],
            'constructions': [], 'links': [], 'projection_diagnostics': [],
            'steps': [
                {'id': 'divide-x', 'operation': 'divmod', 'source_anchors': [anchor(1, 3)],
                 'inputs': [{'role': 'dividend', 'literal': 19},
                            {'role': 'divisor', 'term_id': 'term-a', 'flow_id': 'flow-a'}],
                 'outputs': [{'port': 'quotient', 'labels': ['Quanta'], 'label_term_ids': ['term-q']},
                             {'port': 'remainder', 'labels': ['Residue'], 'label_term_ids': ['term-r']}]},
                {'id': 'test-x', 'operation': 'threshold', 'source_anchors': [anchor(5, 8)],
                 'inputs': [{'role': 'value', 'from_step_id': 'divide-x', 'output_port': 'remainder'},
                            {'role': 'lower', 'literal': 7}],
                 'outputs': [{'port': 'result', 'quantity_kind': 'predicate'}], 'judgment': 'Outcome'}],
            'flows': [{'id': 'flow-a', 'formal': 'Alpha', 'status': 'unresolved_source',
                       'consumer_step_ids': ['divide-x'], 'producer_source': None}]}


class ProcedureModelTests(unittest.TestCase):
    def test_generic_ports_anchors_and_no_mutation(self):
        projection = synthetic()
        original = deepcopy(projection)
        model = build_procedure_model(projection)
        self.assertEqual(projection, original)
        self.assertEqual(model['schema'], 'ProcedureModel/1')
        nodes = {n['id']: n for n in model['nodes']}
        q = next(n for n in nodes.values() if n['label'] == 'Quanta')
        r = next(n for n in nodes.values() if n['label'] == 'Residue')
        self.assertNotEqual(q['id'], r['id'])
        self.assertEqual(r['source_anchors'], [projection['terms'][2]['source_anchor']])
        self.assertIn({'from': 'divide-x', 'to': q['id'], 'role': 'quotient'},
                      [{k: e[k] for k in ('from', 'to', 'role')} for e in model['edges']])
        self.assertTrue(any(e['from'] == r['id'] and e['to'] == 'test-x' for e in model['edges']))
        self.assertFalse(any(e['from'] == q['id'] and e['to'] == 'test-x' for e in model['edges']))
        self.assertEqual(nodes['flow-a']['status'], 'unresolved_source')
        self.assertEqual(nodes['flow-a']['type'], 'unresolved_input')
        self.assertEqual(model['status'], 'incomplete')
        self.assertTrue(all(e['from'] in nodes and e['to'] in nodes for e in model['edges']))
        self.assertIn(r['id'], model['source_index']['term-r']['node_ids'])

    def test_runtime_permission_is_not_historical_source_or_authorship(self):
        p = synthetic()
        p['flows'][0].update(status='runtime_value_permitted', decision_refs=[{'decision_id': 'D7'}])
        model = build_procedure_model(p)
        node = next(n for n in model['nodes'] if n['id'] == 'flow-a')
        self.assertEqual(node['status'], 'runtime_value_permitted')
        self.assertIsNone(node['producer_source'])
        self.assertEqual(node['decision_refs'], [{'decision_id': 'D7'}])
        self.assertFalse(next(n for n in model['nodes'] if n['id'] == 'divide-x')['decision_refs'])
        self.assertEqual(model['status'], 'incomplete')

    def test_linked_flow_and_explicit_producer_dependency(self):
        p = synthetic()
        p['steps'].insert(0, {'id': 'producer-y', 'operation': 'load', 'inputs': [],
                            'outputs': [{'port': 'result'}], 'source_anchors': []})
        p['flows'][0].update(status='linked_source', producer_step_id='producer-y', output_port='result',
                            producer_source={'doc_id': 'external', 'unit_id': 'unit-y', 'source_spans': []})
        model = build_procedure_model(p)
        self.assertTrue(any(e['from'] == 'producer-y' and e['to'] == 'flow-a' for e in model['edges']))
        self.assertEqual(model['status'], 'complete')

    def test_missing_and_ambiguous_ports_are_visible_gaps_not_guessed(self):
        for port in (None, 'absent'):
            p = synthetic()
            p['steps'][1]['inputs'][0]['output_port'] = port
            model = build_procedure_model(p)
            self.assertTrue(any(g['kind'] == 'unresolved_output_port' for g in model['gaps']))
            self.assertTrue(any(n['type'] == 'unresolved_input' and n['id'] != 'flow-a' for n in model['nodes']))

    def test_no_fake_literal_grounding_or_internal_id_leak(self):
        p = synthetic()
        p['steps'][0]['inputs'][0]['value_id'] = 'v99'
        p['steps'][0]['evidence'] = [{'event_id': 'e99'}]
        model = build_procedure_model(p)
        literal = next(n for n in model['nodes'] if n.get('literal') == 19)
        self.assertEqual(literal['anchor_scope'], 'supporting_step')
        self.assertEqual(literal['source_anchors'], p['steps'][0]['source_anchors'])
        p['steps'][0]['inputs'][0]['value_id'] = 'v1'
        p['steps'][0]['evidence'] = [{'event_id': 'e1'}]
        self.assertEqual(model, build_procedure_model(p))
        text = serialize_procedure_model(model)
        self.assertNotIn('value_id', text)
        self.assertNotIn('event_id', text)

    def test_deterministic_export_and_invalid_schema(self):
        model = build_procedure_model(synthetic())
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'model.json'
            export_procedure_model(model, target)
            self.assertEqual(target.read_text(encoding='utf-8'), serialize_procedure_model(model))
            self.assertEqual(json.loads(target.read_text(encoding='utf-8')), model)
        with self.assertRaises(ValueError):
            build_procedure_model({'schema': 'raw-parser'})

    def test_cycle_and_missing_linked_source_remain_visible(self):
        p = synthetic()
        p['flows'][0]['status'] = 'linked_source'
        p['steps'][0]['inputs'][0] = {'role': 'dividend', 'from_step_id': 'test-x', 'output_port': 'result'}
        model = build_procedure_model(p)
        kinds = {g['kind'] for g in model['gaps']}
        self.assertIn('cyclic_dependencies', kinds)
        self.assertIn('linked_source_identity_unavailable', kinds)
        self.assertEqual(model['status'], 'incomplete')
        self.assertTrue(any(e['to'] == 'divide-x' and e.get('output_port') == 'result' for e in model['edges']))

    def test_equal_quantity_labels_do_not_merge_distinct_ports_or_occurrences(self):
        p = synthetic()
        for term in p['terms'][1:]:
            term['surface'] = 'Same label'
        for output in p['steps'][0]['outputs']:
            output['labels'] = ['Same label']
        nodes = [n for n in build_procedure_model(p)['nodes'] if n['type'] == 'named_quantity']
        self.assertEqual(len(nodes), 2)
        self.assertNotEqual(nodes[0]['id'], nodes[1]['id'])
        self.assertNotEqual(nodes[0]['source_anchors'], nodes[1]['source_anchors'])
        self.assertNotEqual(nodes[0]['selection_object_id'], nodes[1]['selection_object_id'])

    def test_empty_projection_and_diagnostics_do_not_claim_completeness(self):
        p = synthetic()
        p['steps'] = []; p['flows'] = []
        self.assertEqual(build_procedure_model(p)['status'], 'incomplete')
        p = synthetic()
        p['flows'][0]['status'] = 'linked_source'
        p['projection_diagnostics'] = [{'kind': 'flow_input_unlinked', 'event_id': 'e77'}]
        self.assertEqual(build_procedure_model(p)['status'], 'incomplete')
        self.assertNotIn('e77', serialize_procedure_model(build_procedure_model(p)))

    def test_ontology_and_no_proc_specific_implementation(self):
        import ast
        import inspect
        import workbench.procedure_model as module
        from analysis_parser.ontology import entry
        op = next(n for n in build_procedure_model(synthetic())['nodes'] if n['id'] == 'divide-x')
        self.assertEqual(op['label'], entry('operation', 'divmod')['label_en'])
        self.assertEqual(op['definition'], entry('operation', 'divmod')['definition_en'])
        constants = [n.value for n in ast.walk(ast.parse(inspect.getsource(module)))
                     if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        self.assertFalse(any(value in text for text in constants for value in ('積月', '閏餘', '章法', 'sifen:38', 'Proc.38')))


class ProcedureModelIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.workbench.test_scholar_source_projection import ScholarSourceProjectionTests
        from source_adapters.corpus import build_source_packet_from_units
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        cls.projection, _, _ = ScholarSourceProjectionTests().project(packet)

    def test_real_model_exact_structure(self):
        m = build_procedure_model(self.projection)
        self.assertEqual([n['operation'] for n in m['nodes'] if n['type'] == 'operation'],
                         ['load', 'subtract', 'multiply', 'divmod', 'threshold'])
        self.assertEqual({n['label'] for n in m['nodes'] if n['type'] == 'unresolved_input'}, {'入蔀年', '章月', '章法'})
        self.assertEqual({n['label'] for n in m['nodes'] if n['type'] == 'named_quantity'}, {'積月', '閏餘'})
        self.assertEqual({n['literal'] for n in m['nodes'] if n['type'] == 'literal'}, {1, 12})
        self.assertEqual([n['label'] for n in m['nodes'] if n['type'] == 'judgment'], ['其歲有閏'])
        self.assertEqual(len(m['nodes']), 13)
        self.assertEqual(len(m['edges']), 12)
        n = {row['label']: row for row in m['nodes']}
        self.assertTrue(any(e['from'] == n['閏餘']['id'] and e['to'] == n['Test threshold']['id'] for e in m['edges']))
        self.assertEqual(m['status'], 'incomplete')
        self.assertTrue(all(node['source_anchors'] and node['scholar_object_ids'] for node in m['nodes']))


if __name__ == '__main__':
    unittest.main()
