"""Pure display records for the source-first Scholar renderer."""
from unittest import TestCase
from unittest.mock import patch

from adjudication import compile_reviewed, new_session
from analysis_parser.construction_ir import GRAMMAR
from source_adapters.corpus import build_source_packet_from_units
from workbench.annotation_projection import project_scholar_source
from workbench.question_presenter import build_questions
from workbench.scholar_renderer import (
    build_renderer_model,
    corpus_search_hints,
    pack_lanes,
    production_operation_cue,
    step_presentation,
)
from workbench.service import _review_forms


class ScholarRendererTests(TestCase):
    def proc38_model(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        compilation = compile_reviewed(packet, new_session(packet, 'renderer-v02'))
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        projection = project_scholar_source(packet, compilation, questions)
        return build_renderer_model(packet, projection, questions)

    def test_v02_authored_hovers_and_scholar_step_labels(self):
        from analysis_parser.ontology import entry
        model = self.proc38_model()
        divide = next(c for c in model['constructions'] if c['construction_kind'] == 'divide')
        self.assertIn(entry('construction', 'divide')['definition_en'], divide['hover'])
        step = next(s for s in model['steps'] if s['operation'] == 'divmod')
        self.assertIn(entry('operation', 'divmod')['definition_en'], step['hover'])
        multiply = next(s for s in model['steps'] if s['operation'] == 'multiply')
        self.assertEqual([t['label'] for t in multiply['presentation']], ['multiply', 'operand', 'previous result'])
        self.assertEqual([i['role'] for i in multiply['inputs']], ['left', 'right'])
        threshold = [s for s in model['steps'] if s['operation'] == 'threshold']
        self.assertEqual(len(threshold), 1)
        self.assertEqual([(t['label'], t['span']) for t in threshold[0]['presentation']],
                         [('test ≥', [37, 39]), ('lower bound', [35, 37])])

    def test_v02_badge_titles_are_the_existing_question_titles(self):
        model = self.proc38_model()
        for term in model['terms']:
            for badge in term['badges']:
                if badge['question_id']:
                    self.assertEqual(badge['hover'], model['questions'][badge['question_id']]['title'])

    def test_v02_unknown_ontology_is_explicit(self):
        from workbench.scholar_renderer import ontology_hover
        self.assertIn('No authored description registered', ontology_hover('construction', 'unknown'))

    def test_term_hover_is_current_interpretation_with_unranked_machine_choices(self):
        model = build_renderer_model(self.packet, self.projection, self.questions)
        self.assertEqual(model['terms'][0]['hover'], '章月\n2 machine suggestions\n• months\n• days')
        self.assertEqual(model['terms'][1]['hover'], '章月\nReviewed interpretation\nmonths')
        self.projection['terms'][1]['semantic_candidates'].pop()
        single = build_renderer_model(self.packet, self.projection, self.questions)['terms'][0]
        self.assertEqual(single['hover'], '章月\nMachine suggestion\nmonths')

    def test_threshold_alignment_does_not_depend_on_supporting_construction_order(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        compilation = compile_reviewed(packet, new_session(packet, 'threshold-order'))
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        projection = project_scholar_source(packet, compilation, questions)
        threshold = next(s for s in projection['steps'] if s['operation'] == 'threshold')
        threshold['construction_ids'].reverse()
        step = next(s for s in build_renderer_model(packet, projection, questions)['steps'] if s['operation'] == 'threshold')
        self.assertEqual(step['cue'], {'status': 'precise', 'spans': [[37, 39]]})
        self.assertEqual({t['label'] for t in step['presentation']}, {'lower bound', 'test ≥'})

    def setUp(self):
        self.packet = {
            'primary_documents': [{'doc_id': 'p', 'text': '推天正術。以章月乘章月。滿章法得一。'}],
        }
        self.projection = {
            'schema': 'ScholarSourceProjection/1',
            'source': {'doc_id': 'p'},
            'terms': [
                {'id': 'term:p:1-3', 'span': [1, 3], 'surface': '天正', 'display_level': 'component',
                 'semantic_candidates': [], 'reviewed_claims': [], 'decision_refs': []},
                {'id': 'term:p:6-8', 'span': [6, 8], 'surface': '章月', 'display_level': 'maximal',
                 'semantic_candidates': [
                     {'candidate_id': 'a', 'status': 'suggested', 'structured_expression':
                      {'op': 'concept', 'concept_id': 'time.month'}},
                     {'candidate_id': 'b', 'status': 'suggested', 'structured_expression':
                      {'op': 'concept', 'concept_id': 'time.day'}},
                 ], 'reviewed_claims': [], 'decision_refs': []},
                {'id': 'term:p:9-11', 'span': [9, 11], 'surface': '章月', 'display_level': 'maximal',
                 'semantic_candidates': [], 'reviewed_claims': [{
                     'claim': {'expression': {'op': 'concept', 'concept_id': 'time.month'}}
                 }], 'decision_refs': [{'decision_id': 'D7', 'action': 'set_term_interpretation'}]},
                {'id': 'term:p:13-15', 'span': [13, 15], 'surface': '章法', 'display_level': 'maximal',
                 'semantic_candidates': [], 'reviewed_claims': [], 'decision_refs': []},
            ],
            'constructions': [
                {'id': 'construction:p:5-11:multiply', 'span': [5, 11], 'surface': '以章月乘章月',
                 'construction_kind': 'multiply', 'public_kind': 'Multiply',
                 'production_id': 'G_MULTIPLY_6', 'parse_status': 'machine_selected',
                 'slots': [{'name': 'left', 'span': [6, 8], 'linked_term_id': 'term:p:6-8'},
                           {'name': 'right', 'span': [9, 11], 'linked_term_id': 'term:p:9-11'}],
                 'decision_refs': []},
                {'id': 'construction:p:12-17:fixed_expression:C08', 'span': [12, 17], 'surface': '滿章法得一',
                 'construction_kind': 'fixed_expression', 'origin': 'domain_kernel_fixed_expression',
                 'rule_id': 'C08', 'parse_status': 'suggested', 'slots': [], 'decision_refs': []},
            ],
            'steps': [
                {'id': 'step:p:5-11:multiply:0', 'operation': 'multiply', 'source_spans': [[5, 11]],
                 'construction_ids': ['construction:p:5-11:multiply'],
                 'inputs': [{'role': 'left', 'term_id': 'term:p:6-8'}, {'role': 'right', 'term_id': 'term:p:9-11'}],
                 'outputs': [], 'decision_refs': []},
            ],
            'flows': [
                {'id': 'flow:p:章法', 'formal': '章法', 'status': 'unresolved_source', 'decision_refs': []},
                {'id': 'flow:p:章月', 'formal': '章月', 'status': 'linked_source', 'producer_source': {'source_anchors': []},
                 'decision_refs': []},
                {'id': 'flow:p:積月', 'formal': '積月', 'status': 'runtime_value_permitted', 'decision_refs': []},
            ],
            'review_facets': [
                {'facet_key': 'meaning-1', 'object_id': 'term:p:6-8', 'facet': 'term_meaning', 'status': 'pending',
                 'question_id': 'q-meaning', 'related_object_ids': []},
                {'facet_key': 'supply-1', 'object_id': 'term:p:13-15', 'facet': 'source_supply', 'status': 'pending',
                 'question_id': 'q-supply', 'related_object_ids': ['flow:p:章法']},
                {'facet_key': 'context-1', 'object_id': 'construction:p:5-11:multiply',
                 'facet': 'construction_context_requirement', 'status': 'pending',
                 'question_id': 'q-context', 'related_object_ids': []},
            ],
            'links': [],
        }
        self.questions = [
            {'id': 'q-meaning', 'title': 'Meaning', 'options': []},
            {'id': 'q-supply', 'title': 'Supply', 'options': []},
            {'id': 'q-context', 'title': 'Context', 'options': []},
        ]

    def test_maximal_terms_keep_exact_occurrences_and_hide_components(self):
        model = build_renderer_model(self.packet, self.projection, self.questions)
        self.assertEqual([(row['id'], row['span']) for row in model['terms']],
                         [('term:p:6-8', [6, 8]), ('term:p:9-11', [9, 11]), ('term:p:13-15', [13, 15])])
        self.assertEqual(model['terms'][0]['gloss']['kind'], 'suggestions')
        self.assertEqual(model['terms'][1]['gloss'], {'kind': 'reviewed', 'label': 'months'})
        self.assertEqual(model['terms'][1]['decision_refs'], [{'decision_id': 'D7', 'action': 'set_term_interpretation'}])

    def test_facets_are_direct_question_bridges_and_context_stays_distinct(self):
        model = build_renderer_model(self.packet, self.projection, self.questions)
        term = next(row for row in model['terms'] if row['id'] == 'term:p:6-8')
        construction = model['constructions'][0]
        self.assertEqual(term['badges'][0]['question_id'], 'q-meaning')
        self.assertEqual(term['badges'][0]['label'], 'meaning?')
        self.assertEqual(construction['badges'][0]['label'], 'context?')
        self.assertEqual(construction['badges'][0]['facet'], 'construction_context_requirement')

    def test_construction_lanes_are_deterministic(self):
        packed = pack_lanes([
            {'id': 'outer', 'span': [4, 16]}, {'id': 'left', 'span': [4, 9]},
            {'id': 'right', 'span': [10, 16]}, {'id': 'next', 'span': [17, 20]},
        ])
        self.assertEqual({row['id']: row['lane'] for row in packed},
                         {'outer': 1, 'left': 0, 'right': 0, 'next': 0})

    def test_fixed_expression_is_suggested_read_only(self):
        model = build_renderer_model(self.packet, self.projection, self.questions)
        fixed = model['constructions'][1]
        self.assertEqual(fixed['adjudication'], 'suggested_read_only')
        self.assertEqual(fixed['label'], 'suggested · read-only in current adjudication schema')

    def test_flow_states_remain_separate(self):
        model = build_renderer_model(self.packet, self.projection, self.questions)
        self.assertCountEqual([(row['formal'], row['display_status']) for row in model['flows']], [
            ('章月', 'linked historical source'), ('章法', 'unresolved'), ('積月', 'runtime value'),
        ])

    def test_registered_production_yields_only_its_exact_operator_cue(self):
        index = next(i for i, row in enumerate(GRAMMAR)
                     if row[:3] == ('multiply', 'Multiply', '以{left:a}乘{right:a}'))
        construction = {'id': 'c', 'span': [5, 11], 'production_id': f'G_MULTIPLY_{index}',
                        'slots': [{'name': 'left', 'span': [6, 8]}, {'name': 'right', 'span': [9, 11]}]}
        cue = production_operation_cue({'operation': 'multiply', 'construction_ids': ['c']}, construction)
        self.assertEqual(cue, {'status': 'precise', 'spans': [[8, 9]]})
        self.assertEqual(production_operation_cue({'operation': 'multiply', 'construction_ids': ['missing']}, construction),
                         {'status': 'unavailable', 'spans': []})

    def test_exact_corpus_hits_are_read_only_hints(self):
        index = {'units': [
            {'id': 'u1', 'type': 'parameter', 'text_effective': '章法七十九', 'sections': [15]},
            {'id': 'u2', 'type': 'commentary', 'text_effective': '章法可見', 'sections': [16]},
        ], 'parameter_index': {'章法': [{'unit_id': 'u1'}]}}
        with patch('workbench.scholar_renderer._load_effective_index', return_value=({'id': 'sifen'}, index)):
            hints = corpus_search_hints('.', 'sifen', '章法')
        self.assertEqual([(row['unit_id'], row['strength'], row['span']) for row in hints],
                         [('u1', 'registered', [0, 2]), ('u2', 'hint', [0, 2])])
        self.assertTrue(all(row['read_only'] for row in hints))

    def test_proc38_uses_the_canonical_maximal_spans_and_operation_roles(self):
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        session = new_session(packet, 'renderer-proc38')
        compilation = compile_reviewed(packet, session)
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        projection = project_scholar_source(packet, compilation, questions, session['decisions'],
                                            compilation['replay']['decision_status'])
        model = build_renderer_model(packet, projection, questions, root='.')
        self.assertEqual([(row['surface'], row['span']) for row in model['terms'][:5]], [
            ('入蔀年', [6, 9]), ('章月', [13, 15]), ('章法', [19, 21]), ('積月', [26, 28]), ('閏餘', [32, 34]),
        ])
        self.assertEqual([(row['construction_kind'], row['span']) for row in model['constructions'][1:4]], [
            ('load', [5, 11]), ('multiply', [12, 17]), ('divide', [18, 23]),
        ])
        multiply = next(row for row in model['steps'] if row['operation'] == 'multiply')
        self.assertEqual(multiply['inputs'][0]['term_id'], 'term:sifen:38:13-15')
        self.assertEqual(multiply['inputs'][0]['flow_id'], 'flow:sifen:38:章月')
        self.assertEqual(multiply['inputs'][1]['from_step_id'], 'step:sifen:38:5-11:subtract:0')
        self.assertEqual(multiply['cue'], {'status': 'precise', 'spans': [[15, 16]]})

    def test_single_suggestion_shows_its_meaning(self):
        self.projection['terms'][1]['semantic_candidates'].pop()
        model = build_renderer_model(self.packet, self.projection, self.questions)
        self.assertEqual(model['terms'][0]['gloss']['label'], 'months')

    def test_repeated_operands_keep_separate_native_role_spans(self):
        construction = self.projection['constructions'][0]
        step = self.projection['steps'][0]
        index = next(i for i, row in enumerate(GRAMMAR)
                     if row[:3] == ('multiply', 'Multiply', '以{left:a}乘{right:a}'))
        construction['production_id'] = f'G_MULTIPLY_{index}'
        self.assertEqual([(r['label'], r['span']) for r in step_presentation(step, construction)],
                         [('multiply', [8, 9]), ('operand', [6, 8]), ('operand', [9, 11])])

    def test_context_hit_reuses_only_offered_attach_action(self):
        from tools.parser_inspector.review_panel import context_hint_attachment, _option_submission
        from workbench import service
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        compilation = compile_reviewed(packet, new_session(packet, 'hint-test'))
        questions = build_questions(packet, compilation, _review_forms(packet, compilation))
        question = next(q for q in questions if q['semantic_key'].get('formal') == '章法')
        response = {'packet': packet, 'effective_packet': packet, 'compilation': compilation, 'branch_id': 'main'}
        hint = {'unit_id': 'sifen:section:15'}
        attachment = context_hint_attachment('.', response, question, 'sifen', hint)
        self.assertIsNotNone(attachment)
        option, document = attachment
        decisions, _ = _option_submission(response, question, option, {'id': 'test', 'type': 'human'},
                                         'Inspect and attach source', context_document=document)
        self.assertEqual([d['action'] for d in decisions], ['attach_context'])
        self.assertEqual(decisions[0]['payload']['document'], service.review_context_document('.', 'sifen', hint['unit_id']))
        self.assertIsNone(context_hint_attachment('.', response, {**question, 'options': []}, 'sifen', hint))
        self.assertIsNone(context_hint_attachment('.', response, question, 'sifen', {'unit_id': 'sifen:section:38'}))

    def test_unsupported_or_inexact_cues_keep_only_broad_native_spans(self):
        construction = self.projection['constructions'][0]
        step = self.projection['steps'][0]
        construction['production_id'] = 'unregistered'
        self.assertEqual(production_operation_cue(step, construction),
                         {'status': 'unavailable', 'spans': []})
        self.assertEqual(step_presentation(step, construction),
                         [{'label': 'multiply', 'span': [5, 11], 'role': 'operation', 'alignment': 'broad'}])
        index = next(i for i, row in enumerate(GRAMMAR)
                     if row[:3] == ('multiply', 'Multiply', '以{left:a}乘{right:a}'))
        construction['production_id'] = f'G_MULTIPLY_{index}'
        construction['slots'][0]['span'] = [5, 8]
        self.assertEqual(production_operation_cue(step, construction)['status'], 'unavailable')

    def test_reviewed_gloss_keeps_machine_alternatives_without_mutating_projection(self):
        from copy import deepcopy
        term = self.projection['terms'][1]
        term['reviewed_claims'] = [{'claim': {'expression': {'op': 'concept', 'concept_id': 'time.month'}}}]
        original = deepcopy(self.projection)
        model = build_renderer_model(self.packet, self.projection, self.questions)
        self.assertEqual(model['terms'][0]['gloss'], {'kind': 'reviewed', 'label': 'months'})
        self.assertEqual(model['terms'][0]['semantic_candidates'], term['semantic_candidates'])
        self.assertEqual(self.projection, original)

    def test_load_subtract_use_different_cues_and_roles(self):
        from workbench.scholar_renderer import step_presentation
        construction = {'id': 'c', 'span': [5, 11], 'production_id': 'G_LOAD_14', 'slots': [
            {'name': 'value', 'span': [6, 9]}, {'name': 'decrement', 'span': [10, 11]}]}
        load = {'id': 'l', 'operation': 'load', 'construction_ids': ['c'], 'inputs': []}
        subtract = {'id': 's', 'operation': 'subtract', 'construction_ids': ['c'],
                    'inputs': [{'role': 'right', 'literal': 1}]}
        self.assertEqual(production_operation_cue(load, construction)['spans'], [[5, 6]])
        self.assertEqual(production_operation_cue(subtract, construction)['spans'], [[9, 10]])
        self.assertEqual([(r['label'], r['span']) for r in step_presentation(load, construction)],
                         [('load', [5, 6]), ('input', [6, 9])])
        self.assertEqual([(r['label'], r['span']) for r in step_presentation(subtract, construction)],
                         [('subtract 1', [9, 11])])

    def test_selection_scopes_context_and_source_assistance(self):
        from workbench.scholar_renderer import selection_details
        from tests.workbench.test_scholar_source_projection import ScholarSourceProjectionTests
        packet = build_source_packet_from_units('.', 'sifen', ['sifen:section:38'], [], {})
        projection, _, questions = ScholarSourceProjectionTests().project(packet)
        model = build_renderer_model(packet, projection, questions)
        details = selection_details(model, 'term:sifen:38:26-28', root='.')
        self.assertEqual(details['flows'], [])
        self.assertIsNone(details['source_assistance'])
        self.assertEqual([r['surface'] for r in details['composition']], ['積', '月'])
        self.assertEqual(details['named_outputs'][0]['port'], 'quotient')
        self.assertEqual(details['naming'][0]['surface'], '名為積月')
        term = 'term:sifen:38:19-21'
        supply = next(f for f in model['facets'] if f['object_id'] == term and f['facet'] == 'source_supply')
        meaning = next(f for f in model['facets'] if f['object_id'] == term and f['facet'] == 'term_meaning')
        self.assertIsNone(selection_details(model, term, meaning['facet_key'], root='.')['source_assistance'])
        details = selection_details(model, term, supply['facet_key'], root='.')
        self.assertEqual([f['formal'] for f in details['flows']], ['章法'])
        self.assertTrue(details['source_assistance']['registered'])
        self.assertEqual(details['uses'][0]['role'], 'divisor')

    def test_c3_is_a_construction_facet_after_runtime_permission(self):
        from tests.workbench.test_scholar_source_diff import ScholarInteractionTests
        from workbench.scholar_renderer import selection_details
        helper = ScholarInteractionTests(); helper.setUp()
        _, projection, _, _, questions = helper.runtime_transition()
        model = build_renderer_model(helper.packet, projection, questions)
        facet = next(f for f in model['facets'] if f['facet'] == 'construction_context_requirement')
        details = selection_details(model, facet['object_id'], facet['facet_key'])
        self.assertEqual(details['context_requirement']['cause'], 'requires_external_data')
        self.assertEqual(details['context_requirement']['missing_inputs'], ['章法'])
        self.assertIsNone(details['source_assistance'])


if __name__ == '__main__':
    import unittest
    unittest.main()
