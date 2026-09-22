"""Source review uses corpus facts and the executed conditions, never lexical inference."""
import inspect
import ast
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from adjudication import compile_reviewed, new_session
from tests.adjudication.test_acceptance_core import packet
from tests.workbench.test_review_jobs import isolated_source, SELECTION
from workbench import service
from workbench.question_presenter import build_questions


class SourceReviewTests(unittest.TestCase):
    def test_source_trace_does_not_replace_meaning_question_evidence(self):
        p = packet('名為積日')
        c = compile_reviewed(p, new_session(p, 'meaning-evidence'))
        q = next(q for q in build_questions(p, c, service._review_forms(p, c)) if q['kind'] == 'term_interpretation')
        self.assertFalse(q.get('rule_trace'))
        self.assertTrue(q['evidence'])

    def test_declaration_and_later_occurrence_in_same_unit_are_both_visible(self):
        from source_adapters.corpus_index import source_review_evidence
        index = {'units': [{'id': 'u', 'type': 'parameter', 'sections': [7],
                           'text_effective': '甲數，三。以甲數乘之'}],
                 'parameter_index': {'甲數': [{'unit_id': 'u', 'value_text': '三', 'sections': [7]}]}}
        evidence = source_review_evidence(index, '甲數')
        self.assertEqual([(r['quote'], r['span']) for r in evidence['declarations']], [('甲數，三', [0, 4])])
        self.assertEqual([r['span'] for r in evidence['occurrences']], [[6, 8]])

    def test_context_does_not_require_any_compiler_action_suggestion(self):
        p = packet('置甲量')
        c = compile_reviewed(p, new_session(p, 'unsuggested'))
        for item in c['review_queue']['items']:
            item['suggested_actions'] = []
        questions = build_questions(p, c, service._review_forms(p, c))
        self.assertTrue(any(o['action'] == 'attach_context' for q in questions for o in q['options']))

    def test_invalid_decision_anchor_cannot_enable_context_attachment(self):
        p = packet('置甲量')
        c = compile_reviewed(p, new_session(p, 'invalid-anchor'))
        forms = service._review_forms(p, c)
        for form in forms:
            if form.get('consumer_anchor'):
                form['consumer_anchor']['source_sha256'] = 'stale'
        questions = build_questions(p, c, forms)
        source = next(q for q in questions if q['semantic_key']['issue_family'] == 'source_supply')
        self.assertNotIn('attach_context', [o['action'] for o in source['options']])

    def test_no_fixture_terms_in_new_source_review_rules(self):
        from analysis_parser import rule_trace
        from source_adapters.corpus_index import source_review_evidence, search_effective_units
        from workbench.question_presenter import _source_supply_target
        functions = [source_review_evidence, search_effective_units, _source_supply_target, service._review_forms]
        sources = [inspect.getsource(f) for f in functions] + [inspect.getsource(rule_trace)]
        for source in sources:
            literals = [n.value for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            for forbidden in ('入蔀年', '章月', '章法', '積月', '閏餘', 'sifen', 'section:38'):
                self.assertFalse(any(forbidden in value for value in literals), forbidden)

    def test_runtime_false_branch_cannot_offer_a_fallback(self):
        p = packet('置乙數')
        c = compile_reviewed(p, new_session(p, 'not-required'))
        for definition in c['graph']['program']['definitions']:
            definition['formal_inputs'] = {}
        for form in service._review_forms(p, c):
            trace = next(t for t in form['rule_trace'] if t['rule_id'] == 'RUNTIME-INPUT-01')
            self.assertFalse(trace['matched'])
            self.assertNotIn('declare_parameter', form['actions'])

    def test_rejected_linker_candidates_cannot_be_offered_as_producers(self):
        from source_adapters.corpus import build_source_packet_from_units
        p = build_source_packet_from_units('.', 'sifen', ['sifen:section:39'], ['sifen:section:38'], {})
        c = compile_reviewed(p, new_session(p, 'incompatible-producer'))
        binding = next(i for i in c['graph']['program']['linked']['imports'] if i.get('selected_definition_id'))
        consumer = next(d for d in c['graph']['program']['definitions'] if d['id'] == binding['consumer_definition_id'])
        binding['selected_definition_id'] = None
        for candidate in binding['candidate_evidence']:
            candidate['compatible'] = False
        c['review_queue']['items'] = [{'kind': 'missing_input', 'source_spans': consumer['source_spans'],
            'suggested_actions': ['bind_value'], 'details': {'definition_id': consumer['id'],
                'formal': binding['formal'], 'candidates': binding['candidates']}}]
        form = service._review_forms(p, c)[0]
        self.assertNotIn('bind_value', form['actions'])

    def test_generic_input_always_offers_context_and_separate_runtime_action(self):
        p = packet('置甲量')
        c = compile_reviewed(p, new_session(p, 'source-test'))
        q = build_questions(p, c, service._review_forms(p, c))[0]
        self.assertIn('attach_context', [o['action'] for o in q['options']])
        runtime = next(o for o in q['options'] if o['action'] == 'declare_parameter')
        self.assertEqual(runtime['group'], 'runtime_fallback')
        self.assertEqual(runtime['label'], 'Supply a runtime test value for “甲量”')
        self.assertEqual(q['semantic_key']['issue_family'], 'source_supply')

    def test_real_source_question_exposes_actual_rule_path_and_corpus_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); isolated_source(root)
            response = service.create_review_job(root, 'source-test',
                {**SELECTION, 'primary_unit_ids': ['sifen:section:38'], 'provided_scope': {}})
            sources = {q['semantic_key']['formal']: q for q in response['questions']
                       if q['semantic_key']['issue_family'] == 'source_supply'}
            for formal, section in [('章法', 15), ('章月', 16)]:
                self.assertIn(section, sources[formal]['source_review']['declarations'][0]['sections'])
            q = sources['入蔀年']
            self.assertEqual(q['source_review']['declarations'], [])
            self.assertTrue(q['source_review']['occurrences'])
            traces = {r['rule_id']: r for r in q['rule_trace']}
            for ident in ('LINK-IMPORT-01', 'REVIEW-MISSING-INPUT-01', 'SOURCE-SUPPLY-01',
                          'PARAMETER-DECLARATION-EXACT-01', 'EXACT-OCCURRENCE-01',
                          'SOURCE-CONTEXT-01', 'RUNTIME-INPUT-01'):
                self.assertIn(ident, traces)
            self.assertEqual(traces['PARAMETER-DECLARATION-EXACT-01']['result']['result_class'], 'no_match')
            for trace in traces.values():
                self.assertEqual(trace['matched'], all(c['matched'] for c in trace['conditions']))
                implementation = trace['implementation']
                self.assertTrue(implementation['revision'])
                self.assertTrue(Path(implementation['file']).is_file())
                self.assertIn('def ', implementation['source'])
                file = Path(implementation['file'])
                self.assertEqual(implementation['content_sha256'], hashlib.sha256(file.read_bytes()).hexdigest())
                lines = file.read_text(encoding='utf-8').splitlines(keepends=True)
                self.assertEqual(implementation['source'], ''.join(lines[implementation['line'] - 1:implementation['end_line']]))
                committed = subprocess.check_output(['git', 'show', implementation['revision'] + ':' + file.as_posix()])
                self.assertEqual(implementation['code_state'], 'committed' if committed == file.read_bytes() else 'working_tree')
            self.assertNotIn('rule_trace', response['graph'])

    def test_exact_parameter_declaration_can_be_attached_without_claiming_a_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); isolated_source(root)
            response = service.create_review_job(root, 'exact-declaration',
                {**SELECTION, 'primary_unit_ids': ['sifen:section:38'], 'provided_scope': {}})
            question = next(q for q in response['questions']
                            if q.get('semantic_key', {}).get('formal') == '章月')
            option = next(o for o in question['options'] if o.get('exact_declaration'))
            self.assertEqual(option['action'], 'attach_context')
            self.assertEqual(option['payload']['document']['doc_id'], 'sifen:16')
            self.assertFalse(option.get('requires_context_picker'))
            self.assertNotIn('binding', ' '.join(option['assertions']).lower())
            decision = service.review_decision(response, option['action'], question['decision_target'],
                                               option['payload'], {'type': 'human', 'id': 'test'}, 'Use exact declaration')
            updated = service.apply_review_job_changes(root, 'exact-declaration', decisions=[decision],
                expected_revision=response['job']['revision'], expected_digest=response['job_digest'])
            self.assertEqual(updated['job']['revision'], 2)
            self.assertEqual(updated['session']['decisions'][-1]['action'], 'attach_context')

    def test_context_attachment_keeps_a_record_of_the_source_question(self):
        """An attached declaration is context, not a silent resolution of its prompt."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); isolated_source(root)
            response = service.create_review_job(root, 'recorded-declaration',
                {**SELECTION, 'primary_unit_ids': ['sifen:section:38'], 'provided_scope': {}})
            question = next(q for q in response['questions']
                            if any(o.get('exact_declaration', {}).get('unit_id') == 'sifen:section:16'
                                   for o in q['options']))
            option = next(o for o in question['options']
                          if o.get('exact_declaration', {}).get('unit_id') == 'sifen:section:16')
            decision = service.review_decision(response, option['action'], question['decision_target'],
                                               option['payload'], {'type': 'human', 'id': 'test'},
                                               'Use exact declaration')
            updated = service.apply_review_job_changes(root, 'recorded-declaration', decisions=[decision],
                expected_revision=response['job']['revision'], expected_digest=response['job_digest'])
            retained = next(q for q in updated['questions'] if q['id'] == question['id'])
            self.assertEqual(retained['recorded_decision']['decision_id'], decision['decision_id'])
            self.assertEqual(retained['recorded_decision']['option_id'], option['id'])
            self.assertEqual(retained['recorded_decision']['status'], 'recorded')
            from workbench.annotation_projection import project_scholar_source
            projection = project_scholar_source(updated['effective_packet'], updated['compilation'], updated['questions'],
                updated['session']['decisions'], updated['compilation']['replay']['decision_status'])
            term = next(row for row in projection['terms']
                        if row['source_anchor']['start'] == retained['display_anchor']['start']
                        and row['source_anchor']['end'] == retained['display_anchor']['end'])
            context_facets = [row for row in projection['review_facets'] if row['facet'] == 'source_context']
            self.assertEqual([(row['object_id'], row['question_id'], row['status']) for row in context_facets],
                             [(term['id'], retained['id'], 'reviewed')])
            self.assertTrue(any(row['object_id'] == term['id'] and row['facet'] == 'source_supply'
                                and row['status'] == 'pending' for row in projection['review_facets']))

    def test_trace_does_not_change_graph_or_form_action_semantics(self):
        p = packet('置乙數')
        c = compile_reviewed(p, new_session(p, 'audit'))
        self.assertIn('rule_trace', c)
        form = next(f for f in service._review_forms(p, c) if f['formal'] == '乙數')
        runtime = next(t for t in form['rule_trace'] if t['rule_id'] == 'RUNTIME-INPUT-01')
        self.assertEqual(runtime['matched'], 'declare_parameter' in form['actions'])
        from source_adapters.corpus_index import search_effective_units
        units = [{'id': 'a', 'text_effective': '甲𠀀乙'}, {'id': 'b', 'text_effective': '甲乙'}]
        self.assertEqual(search_effective_units({'units': units}, ''), units)
        self.assertEqual(search_effective_units({'units': units}, '𠀀'), [units[0]])
        self.assertEqual(search_effective_units({'units': units}, '.*'), [])


if __name__ == '__main__':
    unittest.main()
