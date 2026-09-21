"""Procedure ownership is a reviewed compiler choice, not a corpus merge."""
import unittest

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for


class ProcedureChoiceTests(unittest.TestCase):
    def test_followup_restores_selected_base_after_another_producer_runs(self):
        packet = {'schema_version': '3.0',
                  'primary_documents': [{'doc_id': 'q', 'text': '求丙術，置乙量，加一，名為丙量。'}],
                  'context_documents': [{'doc_id': 'a', 'text': '推甲術，置三，名為甲量。'},
                                        {'doc_id': 'b', 'text': '推乙術，置八，名為乙量。'}]}
        session = new_session(packet, 'base-snapshot')
        target, base = anchor_for(packet, 'q', 0, 3), anchor_for(packet, 'a', 0, 3)
        append_decision(session, {'decision_id': 'follow', 'actor': {'type': 'scripted_fixture', 'id': 'test'},
            'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': 'set_scope',
            'targets': [target], 'payload': {'definition_anchor': target, 'procedure_role': 'followup',
                'parent_definition_anchor': base, 'query_base_anchor': base},
            'reason': 'Restore the selected base, not most recent producer',
            'evidence_refs': [base, target], 'depends_on': []}, packet=packet)
        graph = compile_reviewed(packet, session)['graph']
        base_call, other_call, query_call = graph['program']['calls']
        self.assertEqual(query_call['base_value_ids'], {'甲量': base_call['return_ports']['甲量']['value_id']})
        self.assertEqual(query_call['formal_bindings']['乙量'], other_call['return_ports']['乙量']['value_id'])
        from analysis_parser.execution import execute
        self.assertEqual(execute(graph, {})['named_outputs']['丙術:丙量'], 9)

    def test_followup_schedules_its_base_even_without_a_named_formal(self):
        packet = {'schema_version': '3.0',
                  'primary_documents': [{'doc_id': 'q', 'text': '求乙術，置五，名為乙量。'}],
                  'context_documents': [{'doc_id': 'a', 'text': '推甲術，置三，名為甲量。'}]}
        session = new_session(packet, 'base-required')
        target, base = anchor_for(packet, 'q', 0, 3), anchor_for(packet, 'a', 0, 3)
        append_decision(session, {'decision_id': 'follow', 'actor': {'type': 'scripted_fixture', 'id': 'test'},
            'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': 'set_scope',
            'targets': [target], 'payload': {'definition_anchor': target, 'procedure_role': 'followup',
                'parent_definition_anchor': base, 'query_base_anchor': base},
            'reason': 'Selected shared base', 'evidence_refs': [base, target], 'depends_on': []}, packet=packet)
        graph = compile_reviewed(packet, session)['graph']
        self.assertEqual(len(graph['program']['calls']), 2)
        query_call = graph['program']['calls'][-1]
        self.assertTrue(query_call['base_value_ids'].get('甲量'))

    def test_followup_cannot_claim_a_different_unexecuted_base(self):
        packet = {'schema_version': '3.0',
                  'primary_documents': [{'doc_id': 'q', 'text': '求丙術，置甲量，加一，名為丙量。'}],
                  'context_documents': [{'doc_id': 'a', 'text': '推甲術，置三，名為甲量。'},
                                        {'doc_id': 'b', 'text': '推乙術，置八，名為乙量。'}]}
        session = new_session(packet, 'different-base')
        target, parent, base = (anchor_for(packet, doc, 0, 3) for doc in ('q', 'a', 'b'))
        append_decision(session, {'decision_id': 'follow', 'actor': {'type': 'scripted_fixture', 'id': 'test'},
            'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': 'set_scope',
            'targets': [target], 'payload': {'definition_anchor': target, 'procedure_role': 'followup',
                'parent_definition_anchor': parent, 'query_base_anchor': base},
            'reason': 'Unsupported cross-base fixture', 'evidence_refs': [base, target], 'depends_on': []}, packet=packet)
        result = compile_reviewed(packet, session)
        state = result['replay']['decision_status']['follow']
        self.assertEqual(state['status'], 'needs_revalidation')
        self.assertIn('followup_base_must_match_parent', state['reasons'])
        self.assertFalse(result['replay']['effective']['scopes'])

    def test_explicit_independence_precedes_postposed_heading_heuristic(self):
        text = '推甲術，置三，名為甲量。求中部二十四氣，置五，名為乙量。'
        packet = {'schema_version': '3.0', 'primary_documents': [{'doc_id': 's', 'text': text}]}
        target = anchor_for(packet, 's', text.index('求'), text.index('求')+7)
        session = new_session(packet, 'postposed')
        append_decision(session, {'decision_id': 'independent', 'actor': {'type': 'scripted_fixture', 'id': 'test'},
            'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': 'set_scope',
            'targets': [target], 'payload': {'definition_anchor': target, 'procedure_role': 'independent'},
            'reason': 'Explicit independent heading fixture', 'evidence_refs': [target], 'depends_on': []}, packet=packet)
        graph = compile_reviewed(packet, session)['graph']
        definition = next(d for d in graph['program']['definitions'] if d['goal_surface'] == '中部二十四氣')
        self.assertEqual(definition['kind'], 'ProcedureDef')
        self.assertIsNone(definition['parent'])

    def test_explicit_same_document_followup_resolves_owner_not_initial_query(self):
        text = '推甲術，置三，名為甲量。求乙術，置甲量，加一，名為乙量。'
        packet = {'schema_version': '3.0', 'primary_documents': [{'doc_id': 's', 'text': text}]}
        session = new_session(packet, 'same-doc')
        target = anchor_for(packet, 's', text.index('求'), text.index('求')+3)
        base = anchor_for(packet, 's', 0, 3)
        append_decision(session, {'decision_id': 'follow', 'actor': {'type': 'scripted_fixture', 'id': 'test'},
            'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': 'set_scope',
            'targets': [target], 'payload': {'definition_anchor': target, 'procedure_role': 'followup',
                'parent_definition_anchor': base, 'query_base_anchor': base},
            'reason': 'Explicit same-document query', 'evidence_refs': [base, target], 'depends_on': []}, packet=packet)
        graph = compile_reviewed(packet, session)['graph']
        query = next(d for d in graph['program']['definitions'] if d['goal_surface'] == '乙術')
        parent = next(d for d in graph['program']['definitions'] if d['id'] == query['parent'])
        self.assertEqual(parent['kind'], 'ProcedureDef')
        from analysis_parser.execution import execute
        self.assertEqual(execute(graph, {})['named_outputs']['乙術:乙量'], 4)

    def test_explicit_followup_can_use_a_separate_context_procedure(self):
        packet = {'schema_version': '3.0', 'packet_id': 'followup',
                  'primary_documents': [{'doc_id': 'query', 'text': '求乙術，置甲量，加一，名為乙量。'}],
                  'context_documents': [{'doc_id': 'base', 'text': '推甲術，置三，名為甲量。'}]}
        session = new_session(packet, 'followup')
        target = anchor_for(packet, 'query', 0, 3)
        parent = anchor_for(packet, 'base', 0, 3)
        append_decision(session, {'decision_id': 'followup', 'actor': {'type': 'scripted_fixture', 'id': 'test'},
            'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': 'set_scope',
            'targets': [target], 'payload': {'definition_anchor': target, 'procedure_role': 'followup',
                'parent_definition_anchor': parent, 'query_base_anchor': parent},
            'reason': 'Explicit followup fixture', 'evidence_refs': [target, parent], 'depends_on': []}, packet=packet)
        graph = compile_reviewed(packet, session)['graph']
        selected = next(d for d in graph['program']['definitions'] if d['goal_surface'] == '乙術')
        self.assertEqual(selected['kind'], 'QueryDef')
        self.assertIn(selected['id'], graph['program']['executed_definition_ids'])
        from analysis_parser.execution import execute
        execution = execute(graph, {})
        self.assertFalse(execution['unresolved'])
        self.assertEqual(execution['named_outputs']['乙術:乙量'], 4)

    def test_independent_query_recompiles_and_retraction_restores_native_hierarchy(self):
        text = '推甲術，置三，名為甲量。求乙術，置甲量，加一，名為乙量。'
        packet = {'schema_version': '3.0', 'packet_id': 'ownership',
                  'primary_documents': [{'doc_id': 'source', 'text': text}]}
        session = new_session(packet, 'ownership')
        initial = compile_reviewed(packet, session)['graph']
        target = anchor_for(packet, 'source', text.index('求'), text.index('求') + 3)
        decision = {'decision_id': 'independent', 'actor': {'type': 'scripted_fixture', 'id': 'test'},
                    'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': 'set_scope',
                    'targets': [target], 'payload': {'definition_anchor': target, 'procedure_role': 'independent'},
                    'reason': 'Explicit scope fixture, not a scholarly adjudication',
                    'evidence_refs': [target], 'depends_on': []}
        append_decision(session, decision, packet=packet)
        graph = compile_reviewed(packet, session)['graph']
        selected = next(d for d in graph['program']['definitions'] if d['goal_surface'] == '乙術')
        self.assertEqual(selected['kind'], 'ProcedureDef')
        self.assertIsNone(selected['parent'])
        self.assertNotIn('base_ref', selected)
        self.assertNotEqual(graph['program']['definitions'], initial['program']['definitions'])
        append_decision(session, {**decision, 'decision_id': 'undo', 'action': 'retract',
                                'payload': {'decision_id': 'independent'}}, packet=packet)
        restored = compile_reviewed(packet, session)['graph']
        self.assertEqual(restored['program'], initial['program'])

    def test_unknown_ownership_role_is_rejected(self):
        packet = {'primary_documents': [{'doc_id': 's', 'text': '求乙術，置三。'}]}
        target = anchor_for(packet, 's', 0, 3)
        session = new_session(packet, 'invalid-role')
        with self.assertRaisesRegex(ValueError, 'invalid_procedure_role'):
            append_decision(session, {'decision_id': 'bad', 'actor': {'type': 'scripted_fixture', 'id': 'test'},
                'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': 'set_scope',
                'targets': [target], 'payload': {'definition_anchor': target, 'procedure_role': 'guess'},
                'reason': 'test', 'evidence_refs': [target], 'depends_on': []}, packet=packet)
