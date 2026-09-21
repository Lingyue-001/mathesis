"""Interaction acceptance over real reviewed compilations and scholar snapshots."""
from copy import deepcopy
import unittest

from adjudication import append_decision, new_session
from adjudication.anchors import anchor_for
from source_adapters.corpus import build_source_packet_from_units
from tests.adjudication.test_acceptance_core import packet as synthetic_packet, decision
from tests.workbench import test_scholar_source_projection as projection_tests
from workbench.annotation_projection import project_scholar_source


class ScholarInteractionTests(unittest.TestCase):
    def setUp(self):
        self.helper = projection_tests.ScholarSourceProjectionTests()
        self.packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})

    def project(self, packet=None, session=None):
        return self.helper.project(packet or self.packet, session)

    def diff(self, before, after, **kwargs):
        from workbench.annotation_projection import diff_scholar_source
        return diff_scholar_source(before, after, **kwargs)

    def runtime_transition(self):
        before, _, questions = self.project()
        source = next(q for q in questions if q['kind'] == 'quantity_source'
                      and q['semantic_key'].get('formal') == '章法')
        option = next(o for o in source['options'] if o['action'] == 'declare_parameter')
        session = new_session(self.packet, 'interaction-runtime')
        append_decision(session, decision(self.packet, 'allow-zhangfa', option['action'],
                                         source['decision_target'], option['payload']), packet=self.packet)
        after, compilation, questions = self.project(session=session)
        return before, after, session, compilation, questions

    def test_C4_term_flow_bridge_references_existing_questions(self):
        actual, _, questions = self.project()
        for formal, term_id in [('入蔀年', 'term:sifen:38:6-9'), ('章月', 'term:sifen:38:13-15'),
                                ('章法', 'term:sifen:38:19-21')]:
            question = next(q for q in questions if q['semantic_key'].get('formal') == formal)
            facet = next(f for f in actual['review_facets'] if f['question_id'] == question['id'])
            self.assertEqual(facet['object_id'], term_id)
            self.assertEqual(facet['related_object_ids'], ['flow:sifen:38:' + formal])
            self.assertTrue(facet['facet_key'])
            self.assertNotIn('title', facet)
            self.assertNotIn('options', facet)
            flow = next(f for f in actual['flows'] if f['formal'] == formal)
            self.assertIn('source_supply', flow['review_facets'])

    def test_C1_section15_diff_has_no_term_construction_or_step_churn(self):
        before, _, _ = self.project()
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], ['sifen:section:15'], {})
        after, _, _ = self.project(packet)
        delta = self.diff(before, after, trigger={'mode': 'context'})
        self.assertEqual(delta['schema'], 'ScholarSourceDiff/1')
        for layer in ('terms', 'constructions', 'steps', 'links'):
            self.assertEqual(delta['layers'][layer], {'added': [], 'removed': [], 'changed': []})
        flow_change, = delta['layers']['flows']['changed']
        self.assertEqual(flow_change['id'], 'flow:sifen:38:章法')
        self.assertIn({'path': 'status', 'before': 'unresolved_source', 'after': 'linked_source'}, flow_change['changed_fields'])
        removed, = delta['layers']['review_facets']['removed']
        self.assertEqual((removed['object_id'], removed['facet']), ('term:sifen:38:19-21', 'source_supply'))
        self.assertEqual(delta['layers']['review_facets']['changed'], [])
        self.assertEqual(delta['summary']['semantic_change_count'], 2)

    def test_C2_boundary_transition_does_not_invent_step_provenance(self):
        packet = synthetic_packet('以日率乘月率')
        session = new_session(packet, 'interaction-boundary')
        append_decision(session, decision(packet, 'right', 'set_term_boundary', anchor_for(packet, 'p', 4, 6),
                        {'contract_version': '1.0', 'branch_id': 'main'}), packet=packet)
        before, _, _ = self.project(packet, session)
        append_decision(session, decision(packet, 'left', 'set_term_boundary', anchor_for(packet, 'p', 1, 3),
                        {'contract_version': '1.0', 'branch_id': 'main'}), packet=packet)
        after, compilation, _ = self.project(packet, session)
        trigger = {'decision_id': 'left', 'action': 'set_term_boundary', 'mode': 'trial'}
        delta = self.diff(before, after, trigger=trigger)
        self.assertEqual(delta['trigger'], trigger)
        self.assertFalse(any(s['operation'] == 'multiply' for s in before['steps']))
        multiply = next(s for s in after['steps'] if s['operation'] == 'multiply')
        self.assertIn(multiply['id'], {s['id'] for s in delta['layers']['steps']['added']})
        self.assertTrue(any(c['construction_kind'] == 'multiply' for c in delta['layers']['constructions']['added']))
        construction = next(c for c in after['constructions'] if c['construction_kind'] == 'multiply')
        self.assertEqual([(slot['name'], slot['span'], slot['linked_term_id']) for slot in construction['slots']],
                         [('left', [1, 3], 'term:p:1-3'), ('right', [4, 6], 'term:p:4-6')])
        self.assertEqual([(row['role'], row['term_id']) for row in multiply['inputs']],
                         [('left', 'term:p:1-3'), ('right', 'term:p:4-6')])
        term = next(t for t in after['terms'] if t['surface'] == '日率')
        self.assertIn({'decision_id': 'left', 'action': 'set_term_boundary', 'basis': 'explicit'}, term['decision_refs'])
        native = next(e for e in compilation['graph']['events'] if e['id'] == multiply['evidence'][0]['event_id'])
        self.assertNotIn('adjudication_decision_refs', native)
        self.assertEqual(multiply.get('decision_refs', []), [])
        self.assertIn(term['id'], {t['id'] for t in delta['layers']['terms']['changed']})
        self.assertEqual({t['id'] for t in delta['layers']['terms']['added']},
                         {t['id'] for t in after['terms']} - {t['id'] for t in before['terms']})
        self.assertEqual(construction.get('decision_refs', []), [])

    def test_C3_runtime_permission_keeps_facet_identity_after_question_disappears(self):
        before, after, _, _, _ = self.runtime_transition()
        primary = 'term:sifen:38:19-21'
        old = next(f for f in before['review_facets'] if f['object_id'] == primary and f['facet'] == 'source_supply')
        new = next(f for f in after['review_facets'] if f['object_id'] == primary and f['facet'] == 'source_supply')
        self.assertEqual(old['facet_key'], new['facet_key'])
        self.assertEqual(new['related_object_ids'], ['flow:sifen:38:章法'])
        self.assertEqual((new['status'], new['decision_id'], new['question_id']), ('reviewed', 'allow-zhangfa', None))
        delta = self.diff(before, after)
        flow = next(c for c in delta['layers']['flows']['changed'] if c['id'] == 'flow:sifen:38:章法')
        self.assertIn({'path': 'status', 'before': 'unresolved_source', 'after': 'runtime_value_permitted'}, flow['changed_fields'])
        self.assertTrue(any(c['key'] == old['facet_key'] for c in delta['layers']['review_facets']['changed']))
        self.assertIsNone(next(f for f in after['flows'] if f['formal'] == '章法')['producer_source'])
        self.assertEqual(next(f for f in after['flows'] if f['formal'] == '章法')['decision_refs'],
                         [{'decision_id': 'allow-zhangfa', 'action': 'declare_parameter', 'basis': 'explicit'}])

    def test_C3_context_requirement_is_a_distinct_typed_gap_not_generic_context_material(self):
        """The reviewed root permission resolves supply, not the threshold's external-data requirement."""
        _, _, _, _, questions = self.runtime_transition()
        self.assertFalse(any(q['semantic_key'].get('issue_family') == 'context_material' for q in questions))
        question = next(q for q in questions
                        if q['semantic_key'].get('issue_family') == 'construction_context_requirement')
        self.assertEqual(question['anchor']['quote'], '滿章法得一')
        self.assertEqual(question['semantic_key']['cause'], 'requires_external_data')
        self.assertEqual(question['semantic_key']['missing_inputs'], ['章法'])
        self.assertEqual([o['action'] for o in question['options'][:-1]], ['attach_context'])
        self.assertNotEqual(question['decision_target']['quote'], '推天正術')

    def test_term_interpretation_round_trip_does_not_change_other_construction_grounding(self):
        """A semantic claim must not rewrite public syntax kinds or slot spans elsewhere."""
        before, _, questions = self.project()
        question = next(q for q in questions if q['kind'] == 'term_interpretation' and q['anchor']['quote'] == '章法')
        option = next(o for o in question['options'] if o['action'] == 'set_term_interpretation')
        session = new_session(self.packet, 'meaning-grounding')
        append_decision(session, decision(self.packet, 'meaning', option['action'], question['decision_target'], option['payload']),
                        packet=self.packet)
        after, _, _ = self.project(session=session)
        signature = lambda row: (row['public_kind'], row['span'], row['source_spans'],
                                 [(slot['name'], slot.get('span')) for slot in row['slots']])
        self.assertEqual({row['id']: signature(row) for row in before['constructions']},
                         {row['id']: signature(row) for row in after['constructions']})

    def test_facet_keys_ignore_wording_and_opaque_definition_ids(self):
        before, compilation, questions = self.project()
        for q in questions:
            q['title'] = 'Changed displayed wording'
        old_id = compilation['graph']['program']['definitions'][0]['id']
        def rename(value):
            if isinstance(value, dict): return {k: rename(v) for k, v in value.items()}
            if isinstance(value, list): return [rename(v) for v in value]
            return 'renumbered-definition' if value == old_id else value
        after = project_scholar_source(self.packet, rename(compilation), rename(questions))
        self.assertEqual([f['facet_key'] for f in before['review_facets']], [f['facet_key'] for f in after['review_facets']])
        self.assertEqual(self.diff(before, after)['summary']['semantic_change_count'], 0)

    def test_diff_ignores_native_ids_evidence_order_and_question_id_renumbering(self):
        before, _, _ = self.project()
        after = deepcopy(before)
        for layer in ('terms', 'constructions', 'steps', 'flows', 'review_facets', 'links'):
            after[layer].reverse()
            for row in after[layer]:
                row['evidence'] = [{'event_id': 'e999', 'value_id': 'v999', 'call_id': 'c999'}]
        for step in after['steps']:
            step['inputs'].reverse()
            step['outputs'].reverse()
            for row in step['inputs'] + step['outputs']:
                row['value_id'] = 'v999'
        for construction in after['constructions']:
            construction['slots'].reverse()
        for flow in after['flows']:
            flow['consumer_definition_id'] = 'opaque-new'
        for facet in after['review_facets']:
            if facet['question_id']: facet['question_id'] = 'renumbered-' + facet['question_id']
        before_copy, after_copy = deepcopy(before), deepcopy(after)
        delta = self.diff(before, after)
        self.assertEqual(delta['summary']['semantic_change_count'], 0)
        self.assertEqual((before, after), (before_copy, after_copy))

    def test_diff_rejects_source_or_reading_changes_and_invalid_trigger(self):
        before, _, _ = self.project()
        for field in ('source_id', 'unit_id', 'doc_id', 'text', 'reading_id'):
            after = deepcopy(before)
            after['source'][field] += '-changed'
            with self.assertRaisesRegex(ValueError, 'scholar_diff_source_changed'):
                self.diff(before, after)
        with self.assertRaises(ValueError):
            self.diff(before, before, trigger={'mode': 'invented'})

    def test_explicit_native_provenance_is_read_without_surface_or_prose_inference(self):
        _, compilation, questions = self.project()
        candidate = next(c for c in compilation['graph']['construction_candidates'] if c['kind'] == 'multiply')
        candidate['attributes']['resegmentation_decision_id'] = 'resegment-explicit'
        event = next(e for e in compilation['graph']['events'] if e['kind'] == 'multiply')
        event['adjudication_decision_refs'] = ['quantity-explicit']
        value = next(v for v in compilation['graph']['value_instances'] if v['id'] in event['writes'].values())
        value['adjudication_decision_refs'] = ['value-explicit']
        imported = next(r for r in compilation['graph']['program']['linked']['imports'] if r['formal'] == '章法')
        imported['decision_id'] = 'binding-explicit'
        imported['selection_reason'] = 'generated after forged-D17'
        actual = project_scholar_source(self.packet, compilation, questions)
        construction = next(c for c in actual['constructions'] if c['construction_kind'] == 'multiply')
        self.assertEqual({r['decision_id'] for r in construction['decision_refs']}, {'resegment-explicit'})
        step = next(s for s in actual['steps'] if s['operation'] == 'multiply')
        self.assertEqual({r['decision_id'] for r in step['decision_refs']}, {'quantity-explicit', 'value-explicit'})
        flow = next(f for f in actual['flows'] if f['formal'] == '章法')
        self.assertEqual({r['decision_id'] for r in flow['decision_refs']}, {'binding-explicit'})
        self.assertFalse(any(r.get('decision_refs') for r in actual['terms']))

    def test_diff_preserves_reviewed_claims_provenance_and_link_basis_changes(self):
        before, _, questions = self.project()
        q = next(q for q in questions if q['kind'] == 'term_interpretation' and q['anchor']['quote'] == '章法')
        option = next(o for o in q['options'] if o['action'] == 'set_term_interpretation')
        session = new_session(self.packet, 'interaction-meaning')
        append_decision(session, decision(self.packet, 'meaning', option['action'], q['decision_target'], option['payload']), packet=self.packet)
        after, _, _ = self.project(session=session)
        delta = self.diff(before, after)
        changed = next(c for c in delta['layers']['terms']['changed'] if c['id'] == 'term:sifen:38:19-21')
        self.assertTrue(any(c['path'].startswith('reviewed_claims') for c in changed['changed_fields']))
        self.assertTrue(any(c['path'] == 'decision_refs' for c in changed['changed_fields']))
        same = deepcopy(after)
        same['links'][0]['basis'] = 'explicit' if same['links'][0]['basis'] != 'explicit' else 'structurally_derived'
        self.assertEqual(len(self.diff(after, same)['layers']['links']['changed']), 1)

    def test_rejection_and_adoption_keep_current_meaning_reviewed_and_both_refs(self):
        _, _, questions = self.project()
        q = next(q for q in questions if q['kind'] == 'term_interpretation' and q['anchor']['quote'] == '入蔀年')
        reject = next(o for o in q['options'] if o['action'] == 'set_term_interpretation'
                      and o['payload']['claim']['origin'] == 'machine_rejection')
        adopt = next(o for o in q['options'] if o['action'] == 'set_term_interpretation'
                     and o['payload']['claim']['origin'] == 'machine_adoption'
                     and o['payload']['claim']['candidate_snapshot']['candidate_id'] not in reject['payload']['claim']['candidate_ids'])
        session = new_session(self.packet, 'adopt-other-meaning')
        for ident, option in [('reject', reject), ('adopt', adopt)]:
            append_decision(session, decision(self.packet, ident, option['action'], q['decision_target'], option['payload']), packet=self.packet)
        after, _, _ = self.project(session=session)
        facet = next(f for f in after['review_facets'] if f['object_id'] == 'term:sifen:38:6-9' and f['facet'] == 'term_meaning')
        self.assertEqual((facet['status'], facet['decision_id']), ('reviewed', 'adopt'))
        term = next(t for t in after['terms'] if t['id'] == facet['object_id'])
        self.assertEqual({r['decision_id'] for r in term['decision_refs']}, {'reject', 'adopt'})

    def test_flow_can_be_primary_when_exact_term_is_absent(self):
        from unittest.mock import patch
        _, compilation, questions = self.project()
        # A canonical Anaphor operand can consume a supply without a Term slot.
        candidate = next(c for c in compilation['graph']['construction_candidates'] if c['kind'] == 'divide')
        candidate['slots']['divisor']['kind'] = 'Anaphor'
        with patch('workbench.annotation_projection.suggest_packet_semantics', return_value={}):
            after = project_scholar_source(self.packet, compilation, questions)
        facet = next(f for f in after['review_facets'] if f['facet'] == 'source_supply' and f['object_id'] == 'flow:sifen:38:章法')
        self.assertEqual(facet['related_object_ids'], [])
        self.assertTrue(facet['question_id'])

    def test_real_quantity_provenance_is_carried_by_native_values(self):
        _, _, questions = self.project()
        q = next(q for q in questions if q['kind'] == 'counting_convention')
        option = next(o for o in q['options'] if o['action'] == 'set_quantity_semantics')
        session = new_session(self.packet, 'real-quantity-provenance')
        append_decision(session, decision(self.packet, 'quantity', option['action'], q['decision_target'], option['payload']), packet=self.packet)
        after, compilation, _ = self.project(session=session)
        native_events = {e['id']: e for e in compilation['graph']['events']}
        native_values = {v['id']: v for v in compilation['graph']['value_instances']}
        self.assertTrue(any(s['decision_refs'] for s in after['steps']))
        for step in after['steps']:
            event = native_events[step['evidence'][0]['event_id']]
            refs = set(event.get('adjudication_decision_refs', []))
            for direction in ('reads', 'writes'):
                for ident in event.get(direction, {}).values():
                    refs.update(native_values[ident].get('adjudication_decision_refs', []))
            self.assertEqual({r['decision_id'] for r in step['decision_refs']}, refs)

    def test_source_facet_identity_survives_an_unprojectable_consumer(self):
        _, compilation, questions = self.project()
        for event in compilation['graph']['events']:
            if event['kind'] == 'divmod':
                event['syntax_node_id'] = None
        before = project_scholar_source(self.packet, compilation, questions)
        old = next(f for f in before['review_facets'] if f['object_id'] == 'term:sifen:38:19-21' and f['facet'] == 'source_supply')
        for q in questions:
            if 'consumer_definition_id' in q['semantic_key']:
                q['semantic_key']['consumer_definition_id'] = 'renumbered-definition'
        after = project_scholar_source(self.packet, compilation, questions)
        new = next(f for f in after['review_facets'] if f['object_id'] == old['object_id'] and f['facet'] == old['facet'])
        self.assertEqual(old['facet_key'], new['facet_key'])

    def test_repeated_supply_occurrences_each_bridge_to_the_same_existing_question(self):
        packet = synthetic_packet('推天正術。置章月。以章月乘之。')
        before, _, questions = self.project(packet)
        question = next(q for q in questions if q['semantic_key'].get('formal') == '章月')
        flow = next(f for f in before['flows'] if f['formal'] == '章月')
        terms = [t for t in before['terms'] if t['surface'] == '章月']
        self.assertEqual(len(terms), 2)
        for term in terms:
            related = [f for f in before['review_facets'] if f['object_id'] == term['id']
                       and f['facet'] == 'source_supply']
            self.assertEqual(len(related), 1)
            self.assertEqual(related[0]['question_id'], question['id'])
            self.assertEqual(related[0]['related_object_ids'], [flow['id']])

    def test_repeated_operands_use_distinct_canonical_slot_anchors(self):
        packet = synthetic_packet('推天正術。以章月乘章月。')
        actual, _, questions = self.project(packet)
        multiply = next(c for c in actual['constructions'] if c['construction_kind'] == 'multiply')
        self.assertEqual([(slot['name'], slot['span']) for slot in multiply['slots']],
                         [('left', [6, 8]), ('right', [9, 11])])
        question = next(q for q in questions if q['semantic_key'].get('formal') == '章月')
        self.assertEqual(question['display_anchor']['start'], 6)
        self.assertEqual([(a['start'], a['end']) for a in question['evidence_anchors'][:2]], [(6, 8), (9, 11)])


if __name__ == '__main__':
    unittest.main()
