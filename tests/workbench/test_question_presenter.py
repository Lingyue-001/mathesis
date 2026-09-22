import unittest
from adjudication import compile_reviewed, new_session, append_decision
from adjudication.anchors import anchor_for
from adjudication.effective_packet import derive_packet
from source_adapters.corpus import build_source_packet_from_units
from tests.adjudication.test_acceptance_core import packet, decision
from workbench.service import _review_forms


class QuestionPresenterTests(unittest.TestCase):
    def test_eligibility_has_no_surface_or_proc_whitelist(self):
        import ast
        import inspect
        from workbench.question_presenter import build_questions
        literals = [node.value for node in ast.walk(ast.parse(inspect.getsource(build_questions)))
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)]
        for forbidden in ('積月', '閏餘', 'sifen:section:38', 'sifen:38'):
            self.assertFalse(any(forbidden in value for value in literals), forbidden)

    def test_generic_named_output_eligibility_uses_existing_contract(self):
        p = packet('名為積日，不滿為日餘，名為積日')
        questions = self.questions(p, new_session(p, 'generic-named-output'))
        meanings = [q for q in questions if q['kind'] == 'term_interpretation']
        self.assertEqual([(q['anchor']['quote'], q['anchor']['start'], q['anchor']['end']) for q in meanings],
                         [('積日', 2, 4), ('日餘', 8, 10), ('積日', 13, 15)])
        for q in meanings:
            self.assertEqual({o['action'] for o in q['options']}, {'set_term_interpretation', 'defer'})
            option = next(o for o in q['options'] if o['action'] == 'set_term_interpretation')
            s = new_session(p, 'contract')
            append_decision(s, decision(p, 'adopt', option['action'], q['anchor'], option['payload']), packet=p)
            self.assertEqual(compile_reviewed(p, s)['replay']['decision_status']['adopt']['status'], 'active')

    def test_named_output_without_compatible_candidate_has_no_question(self):
        from copy import deepcopy
        from unittest.mock import patch
        from domain_kernel.engine import suggest_packet_semantics
        from workbench.question_presenter import build_questions
        p = packet('名為積日')
        c = compile_reviewed(p, new_session(p, 'incompatible'))
        bundles = deepcopy(suggest_packet_semantics(p))
        for bundle in bundles.values():
            for candidate in bundle['candidates']:
                candidate['constraint_status'] = 'incompatible'
        with patch('workbench.question_presenter.suggest_packet_semantics', return_value=bundles):
            self.assertFalse(any(q['kind'] == 'term_interpretation' for q in build_questions(p, c, [])))
        p = packet('名為陌生量')
        self.assertFalse(any(q['kind'] == 'term_interpretation' for q in self.questions(p, new_session(p, 'no-candidate'))))

    def test_named_output_requires_its_own_exact_slot_grounding(self):
        from workbench.question_presenter import build_questions
        p = packet('名為積日，名為積日')
        c = compile_reviewed(p, new_session(p, 'missing-grounding'))
        c['graph']['construction_candidates'][0]['slots']['label']['source_spans'] = []
        meanings = [q for q in build_questions(p, c, []) if q['kind'] == 'term_interpretation']
        self.assertEqual([q['anchor']['start'] for q in meanings], [7])

    def test_named_output_adopt_and_reject_are_occurrence_local(self):
        from workbench.annotation_projection import project_scholar_source
        for origin in ('machine_adoption', 'machine_rejection'):
            with self.subTest(origin=origin):
                p = packet('名為積日，名為積日')
                s = new_session(p, 'local-' + origin)
                questions = [q for q in self.questions(p, s) if q['kind'] == 'term_interpretation']
                self.assertEqual(len(questions), 2)
                first, second = questions
                option = next(o for o in first['options'] if o.get('payload', {}).get('claim', {}).get('origin') == origin)
                append_decision(s, decision(p, 'local', option['action'], first['anchor'], option['payload']), packet=p)
                after = self.questions(p, s)
                if origin == 'machine_adoption':
                    self.assertNotIn(first['id'], [q['id'] for q in after])
                    # These two names are a real alias chain. The second may now
                    # inherit the expression, but never a human decision record.
                    self.assertNotIn(second['id'], [q['id'] for q in after])
                    from adjudication.semantic_closure import term_resolution
                    inherited = term_resolution(compile_reviewed(p, s)['semantic_closure'], second['anchor'])
                    self.assertTrue(inherited['resolved'])
                    self.assertTrue(all(a['authority'] == 'derived' for a in inherited['assertions']))
                else:
                    self.assertEqual(next(q for q in after if q['id'] == second['id']), second)
                    local = next(q for q in after if q['id'] == first['id'])
                    self.assertFalse(any(o.get('payload', {}).get('claim', {}).get('origin') == 'machine_adoption'
                                         for o in local['options']))
                compiled = compile_reviewed(p, s)
                projection = project_scholar_source(p, compiled, after, s['decisions'], compiled['replay']['decision_status'])
                a = next(t for t in projection['terms'] if t['span'] == [2, 4])
                b = next(t for t in projection['terms'] if t['span'] == [7, 9])
                self.assertTrue(a['reviewed_claims'])
                self.assertEqual(b['reviewed_claims'], [])
                self.assertEqual(b['decision_refs'], [])

    def test_fixed_expression_has_no_fake_review_action_or_facet(self):
        from workbench.annotation_projection import project_scholar_source
        p = packet('實如法而一。')
        s = new_session(p, 'fixed-read-only')
        c = compile_reviewed(p, s)
        qs = self.questions(p, s)
        projection = project_scholar_source(p, c, qs)
        fixed = {r['id'] for r in projection['constructions'] if r.get('origin') == 'domain_kernel_fixed_expression'}
        self.assertTrue(fixed)
        self.assertFalse(any(f['object_id'] in fixed for f in projection['review_facets']))
        self.assertFalse(any(o['action'].startswith('set_construction') for q in qs for o in q['options']))

    def questions(self, p, s):
        from workbench.question_presenter import build_questions
        c = compile_reviewed(p, s)
        catalog = derive_packet(p, [])
        return build_questions(catalog, c, _review_forms(catalog, c))

    def real_sifen_year_packet(self):
        return build_source_packet_from_units(
            '.', 'sifen', ['sifen:section:38'], ['sifen:section:15', 'sifen:section:16'],
            {'tradition': 'Han_Si_fen_li'},
        )

    def real_sifen_proc_38_without_context(self):
        return build_source_packet_from_units(
            '.', 'sifen', ['sifen:section:38'], [], {},
        )

    def test_source_supply_questions_use_consumer_formal_identity_and_exact_use_display(self):
        """A binding gap is one consumer/formal issue, not one question per diagnostic anchor."""
        p = self.real_sifen_proc_38_without_context()
        questions = self.questions(p, new_session(p, 'proc-38-source-supply'))
        sources = [q for q in questions if q['kind'] == 'quantity_source']
        self.assertEqual([q['semantic_key']['formal'] for q in sources], ['入蔀年', '章月', '章法'])
        self.assertEqual(len({q['id'] for q in sources}), 3)
        zhang_fa = next(q for q in sources if q['semantic_key']['formal'] == '章法')
        self.assertEqual(zhang_fa['semantic_key']['issue_family'], 'source_supply')
        self.assertEqual(zhang_fa['display_anchor']['quote'], '章法')
        self.assertEqual(zhang_fa['anchor'], zhang_fa['display_anchor'])
        self.assertEqual(zhang_fa['decision_target']['quote'], '推天正術')
        self.assertGreater(len(zhang_fa['evidence_anchors']), 1)
        self.assertEqual(len(zhang_fa['evidence']['native_questions']), 2)

    def test_every_proc_38_question_carries_brief_machine_context(self):
        p = self.real_sifen_proc_38_without_context()
        questions = self.questions(p, new_session(p, 'proc-38-machine-context'))
        self.assertTrue(questions)
        self.assertTrue(all(q['machine_context'].get('reading') and q['machine_context'].get('why_blocked')
                            for q in questions))

    def test_one_real_input_question_disappears_and_retract_restores_it(self):
        p = packet('置甲量')
        s = new_session(p, 'last')
        questions = self.questions(p, s)
        self.assertEqual(len(questions), 1)
        option = next(o for o in questions[0]['options'] if o['action'] == 'declare_parameter')
        append_decision(s, decision(p, 'root', option['action'], questions[0]['anchor'], option['payload']), packet=p)
        self.assertEqual(self.questions(p, s), [])
        append_decision(s, decision(p, 'undo', 'retract', anchor_for(p, 'p', 0, 1), {'decision_id': 'root'}), packet=p)
        self.assertEqual([q['id'] for q in self.questions(p, s)], [q['id'] for q in questions])

    def test_neutral_decrement_question_does_not_invent_a_bu_coordinate(self):
        p = packet('置甲量減一，名為乙量')
        questions = self.questions(p, new_session(p, 'count'))
        counting = next(q for q in questions if q['kind'] == 'counting_convention')
        self.assertEqual([o for o in counting['options'] if o['action'] == 'set_quantity_semantics'], [])
        self.assertEqual(counting['evidence']['basis'], 'Source subtract-one operation; no scoped ordinal evidence.')

    def test_bu_year_candidate_allows_only_evidenced_year_coordinate(self):
        p = self.real_sifen_year_packet()
        counting = next(q for q in self.questions(p, new_session(p, 'year-count'))
                        if q['kind'] == 'counting_convention'
                        and q['evidence']['construction']['slots']['value']['text'] == '入蔀年')
        options = [o for o in counting['options'] if o['action'] == 'set_quantity_semantics']
        self.assertEqual([o['payload']['facets']['step_unit'] for o in options], ['year'])
        self.assertEqual(options[0]['payload']['facets']['reference_origin'], 'current_bu_start')
        self.assertIn('S-C46', counting['evidence']['kernel_candidate']['provenance_ids'])

    def test_diagnostics_are_never_scholar_questions(self):
        from workbench.question_presenter import build_questions
        p = packet('置甲量')
        c = compile_reviewed(p, new_session(p, 'diag'))
        forms = [{'category': 'system_diagnostic', 'question': {'kind': 'invalid_graph_structure'}, 'anchors': []}]
        self.assertEqual(build_questions(p, c, forms), [])

    def test_partial_counting_assertion_keeps_compatible_completion_question(self):
        p = self.real_sifen_year_packet()
        s = new_session(p, 'partial')
        q = next(q for q in self.questions(p, s) if q['kind'] == 'counting_convention')
        option = next(o for o in q['options'] if o.get('payload', {}).get('facets', {}).get('step_unit') == 'year')
        payload = {**option['payload'], 'facets': {'unit': 'year'}}
        append_decision(s, decision(p, 'unit', 'set_quantity_semantics', q['anchor'], payload), packet=p)
        q = next(q for q in self.questions(p, s) if q['kind'] == 'counting_convention')
        choices = [o for o in q['options'] if o['action'] == 'set_quantity_semantics']
        self.assertEqual([o['payload']['facets']['step_unit'] for o in choices], ['year'])
        append_decision(s, decision(p, 'complete', 'set_quantity_semantics', q['anchor'], choices[0]['payload']), packet=p)
        self.assertFalse(any(q['kind'] == 'counting_convention' for q in self.questions(p, s)))

    def test_incoherent_counting_boundary_cannot_become_a_partial_assertion(self):
        from adjudication.quantity_targets import validate_quantity_facets
        with self.assertRaisesRegex(ValueError, 'counting_boundary_step_unit'):
            validate_quantity_facets({'coordinate_kind': 'ordinal', 'step_unit': 'month',
                'index_base': 1, 'reference_origin': 'current_bu_start', 'counting_boundary': 'start_of_current_year'})
