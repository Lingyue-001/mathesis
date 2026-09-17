import copy
import json
import unittest

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for
from adjudication.bundle import make_bundle
from source_adapters.corpus import build_source_packet


def fixture_decision(decision_id, action, target, payload, depends_on=None):
    return {'decision_id': decision_id, 'actor': {'type': 'scripted_fixture', 'id': 'M2-real-flow'},
            'created_at': '2026-09-17T00:00:00Z', 'branch_id': 'main', 'action': action,
            'targets': [target], 'payload': payload, 'evidence_refs': ['Cullen Proc. 3.5; canonical sifen source'],
            'reason': 'software acceptance fixture; not a human adjudication', 'depends_on': depends_on or []}


class TestRealProcedure(unittest.TestCase):
    def setUp(self):
        self.packet = build_source_packet('.', 'sifen-3-5')['source_packet']
        self.session = new_session(self.packet, 'm2-real-procedure')
        self.input_anchor = anchor_for(self.packet, 'sifen:38', 6, 9)
        self.multiply_anchor = anchor_for(self.packet, 'sifen:38', 12, 17)

    def _review(self):
        append_decision(self.session, fixture_decision(
            'D-root-input', 'declare_parameter', self.input_anchor,
            {'name': '入蔀年', 'unit': 'year', 'root_input': True}))
        append_decision(self.session, fixture_decision(
            'D-product-semantics', 'set_quantity_semantics', self.multiply_anchor,
            {'syntax_node_id': 'sifen:38:ast9', 'output_port': 'result', 'unit': 'product',
             'quantity_kind': 'composite_product', 'representation': {'kind': 'whole'},
             'resolution_status': 'resolved'}, depends_on=['D-root-input']))

    def test_H01_empty_review_reuses_automatic_compiler(self):
        result = compile_reviewed(self.packet, self.session)
        self.assertEqual(result['graph']['adapter'], 'typed_scoped_v3')
        self.assertEqual(result['graph']['adjudication']['effective_decisions']['parameters'], {})

    def test_H20_H40_real_replay_is_closed_but_execution_is_separate(self):
        self._review()
        first = make_bundle(compile_reviewed(self.packet, self.session), self.session)
        second = make_bundle(compile_reviewed(self.packet, self.session), self.session)
        self.assertEqual(first['coverage_ledger']['graph_status'], 'closed')
        self.assertTrue(first['validation']['valid_for_complete_export'])
        self.assertEqual(json.dumps(first['graph'], ensure_ascii=False, sort_keys=True),
                         json.dumps(second['graph'], ensure_ascii=False, sort_keys=True))
        self.assertIsNone(first['metrics']['human_active_seconds'])

    def test_H19_retract_restores_automatic_missing_input_gap(self):
        self._review()
        append_decision(self.session, fixture_decision(
            'D-retract-root', 'retract', self.input_anchor, {'decision_id': 'D-root-input'}))
        result = compile_reviewed(self.packet, self.session)
        self.assertEqual(result['replay']['decision_status']['D-root-input']['status'], 'retracted')
        self.assertEqual(result['coverage_ledger']['graph_status'], 'partial')
        self.assertTrue(result['graph']['program']['linked']['diagnostics'])

    def test_H43_metadata_is_emitted_with_decision_provenance(self):
        self._review()
        graph = compile_reviewed(self.packet, self.session)['graph']
        product = next(event for event in graph['events'] if event.get('syntax_node_id') == 'sifen:38:ast9')
        value = graph['value_instances'][int(product['writes']['result'][1:]) - 1]
        self.assertEqual(product['adjudication_decision_refs'], ['D-product-semantics'])
        self.assertEqual(value['adjudication_decision_refs'], ['D-product-semantics'])
        self.assertEqual(product['evidence_status'], 'scholarly_calibrated')
