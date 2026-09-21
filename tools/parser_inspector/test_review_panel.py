"""Source-first K2 panel behavior over isolated real ReviewJobs."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from adjudication.anchors import anchor_for
from tests.workbench.test_review_jobs import isolated_source, SELECTION
from tools.parser_inspector.review_panel import evidence_html
from tools.parser_inspector.source_annotation import marks_for_document, selection_anchor
from workbench import review_jobs, service


def app_entry(root):
    import streamlit as st
    from tools.parser_inspector.readable import render
    st.set_page_config(layout='wide')
    render(root, 'en')


def app_entry_zh(root):
    import streamlit as st
    from tools.parser_inspector.readable import render
    st.set_page_config(layout='wide')
    st.session_state['inspector_language'] = 'zh'
    render(root, 'zh')


class ReviewPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        isolated_source(self.root)

    def app_for(self, job_id):
        app = AppTest.from_function(app_entry, args=(str(self.root),), default_timeout=30).run()
        app.session_state['k2_requested_job'] = job_id
        app.run()
        self.assertFalse(app.exception)
        return app

    def test_normal_entry_selects_source_and_section_then_restores_background_session(self):
        app = AppTest.from_function(app_entry, args=(str(self.root),), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertIsNotNone(app.selectbox(key='k2_source'))
        self.assertIsNotNone(app.selectbox(key='k2_section'))
        self.assertFalse(any(box.key == 'k2_job_picker' for box in app.selectbox))
        self.assertFalse(any('Create review job' in button.label for button in app.button))
        job_id = app.session_state['k2_displayed']['job_id']
        self.assertTrue(job_id.startswith('session-'))
        self.assertIsNone(app.session_state['k2_question'])
        self.assertNotIn('k2_scholar_facet', app.session_state)
        app.run()
        self.assertEqual(app.session_state['k2_displayed']['job_id'], job_id)
        self.assertIsNone(app.session_state['k2_question'])
        app.selectbox(key='k2_section').select('sifen:section:39').run()
        switched = app.session_state['k2_displayed']['job_id']
        self.assertNotEqual(switched, job_id)
        self.assertIsNone(app.session_state['k2_question'])
        self.assertNotIn('k2_scholar_facet', app.session_state)
        self.assertEqual(service.compile_review_job(self.root, switched)['job']['source_selection']['primary_unit_ids'],
                         ['sifen:section:39'])

    def test_parser_review_chrome_uses_the_selected_language_without_changing_data_values(self):
        app = AppTest.from_function(app_entry_zh, args=(str(self.root),), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.subheader[0].value, '解析检查器')
        self.assertEqual(app.selectbox(key='k2_source').label, '来源')
        self.assertEqual(app.selectbox(key='k2_section').label, '章节')
        self.assertIn('当前问题', [item.value for item in app.subheader])
        self.assertEqual(app.session_state['k2_displayed']['job_id'].startswith('session-'), True)

    def test_source_selection_and_marks_keep_exact_occurrences(self):
        text = '日率，日率 <unsafe>'
        packet = {'primary_documents': [{'doc_id': 'p', 'reading_id': 'p.r', 'text': text}]}
        first = anchor_for(packet, 'p', 0, 2)
        second = selection_anchor(packet, 'p', [3, 5])
        self.assertNotEqual(first['start'], second['start'])
        marks = marks_for_document(packet, 'p', [{'id': 'one', 'anchor': first, 'title': 'First'}],
                                   [{'decision_id': 'two', 'targets': [second]}])
        self.assertEqual([(m['start'], m['end'], m['status']) for m in marks],
                         [(0, 2, 'pending'), (3, 5, 'reviewed')])
        html = evidence_html(packet, second)
        self.assertIn('<mark>日率</mark>', html)
        self.assertIn('&lt;unsafe&gt;', html)
        with self.assertRaises(ValueError):
            selection_anchor(packet, 'p', [5, 3])

    def test_question_selection_is_visibly_unsaved_until_confirmed(self):
        response = service.create_review_job(self.root, 'draft-ui', SELECTION)
        question = response['questions'][0]
        app = self.app_for('draft-ui')
        app.session_state['k2_question'] = question['id']; app.run()
        self.assertIn('not saved', ' '.join(item.value.lower() for item in app.caption))

    def test_next_and_previous_leave_job_bytes_and_revision_unchanged(self):
        response = service.create_review_job(self.root, 'navigation-ui',
            {**SELECTION, 'primary_unit_ids': ['sifen:section:38']})
        question = response['questions'][0]
        path = review_jobs.job_path(self.root, 'navigation-ui')
        before = path.read_bytes()
        app = self.app_for('navigation-ui')
        app.session_state['k2_question'] = question['id']; app.run()
        options = app.radio(key='k2_option:' + question['id']).options
        if len(options) > 1:
            app.radio(key='k2_option:' + question['id']).set_value(options[-1]).run()
        app.button(key='k2_next').click().run()
        app.button(key='k2_previous').click().run()
        self.assertEqual(review_jobs.load_job(self.root, 'navigation-ui')['revision'], 1)
        self.assertEqual(path.read_bytes(), before)

    def test_term_choice_changes_real_review_and_retract_restores_question(self):
        response = service.create_review_job(self.root, 'term-ui', SELECTION)
        question = next(q for q in response['questions'] if q['kind'] == 'term_interpretation')
        option = next(o for o in question['options'] if o['action'] == 'set_term_interpretation')
        app = self.app_for('term-ui')
        app.session_state['k2_question'] = question['id']
        app.run()
        self.assertFalse(app.exception)
        self.assertNotIn('k2_action', [box.key for box in app.selectbox])
        self.assertIn('Why these options?', [item.label for item in app.expander])
        app.radio(key='k2_option:' + question['id']).set_value(option['id']).run()
        app.button(key='k2_save').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error, [item.value for item in app.error])
        saved = service.compile_review_job(self.root, 'term-ui')
        self.assertEqual(saved['job']['revision'], 2)
        self.assertFalse(any(q['id'] == question['id'] for q in saved['questions']))
        self.assertIn('Decision history and retract', [item.label for item in app.expander])
        self.assertIn('Management', [item.label for item in app.expander])
        app.text_input(key='k2_retract_reason').set_value('Reopen interpretation').run()
        app.button(key='k2_retract').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        restored = service.compile_review_job(self.root, 'term-ui')
        self.assertEqual(restored['job']['revision'], 3)
        self.assertTrue(any(q['id'] == question['id'] for q in restored['questions']))

    def test_scholar_projection_confirmation_emits_a_canonical_diff(self):
        response = service.create_review_job(self.root, 'renderer-diff-ui', SELECTION)
        question = next(q for q in response['questions'] if q['kind'] == 'term_interpretation')
        option = next(o for o in question['options'] if o['action'] == 'set_term_interpretation')
        app = self.app_for('renderer-diff-ui')
        self.assertEqual(app.session_state['k2_scholar_projection']['schema'], 'ScholarSourceProjection/1')
        self.assertEqual(app.session_state['k2_scholar_model']['schema'], 'ScholarRendererModel/1')
        app.session_state['k2_question'] = question['id']; app.run()
        app.radio(key='k2_option:' + question['id']).set_value(option['id']).run()
        app.button(key='k2_save').click().run()
        delta = app.session_state['k2_last_scholar_diff']['diff']
        self.assertEqual(delta['schema'], 'ScholarSourceDiff/1')
        self.assertEqual(delta['trigger']['mode'], 'saved')
        self.assertEqual(len(delta['trigger']['decision_ids']), 1)
        self.assertGreater(delta['summary']['semantic_change_count'], 0)

    def test_local_composition_supports_a_bounded_nested_registered_expression(self):
        response = service.create_review_job(self.root, 'nested-ui', SELECTION)
        question = next(q for q in response['questions'] if q['kind'] == 'term_interpretation')
        app = self.app_for('nested-ui')
        app.session_state['k2_question'] = question['id']; app.run()
        app.radio(key='k2_option:' + question['id']).set_value('local-compose').run()
        root = app.selectbox(key='k2_compose:' + question['id'] + ':meaning')
        nested = ('constructor', 'accumulation')
        root.set_value(nested).run()
        child = app.selectbox(key='k2_compose:' + question['id'] + ':meaning.quantity')
        child.set_value(nested).run()
        self.assertIn('Preview: accumulation(quantity=accumulation(', ' '.join(item.value for item in app.caption))
        app.button(key='k2_save').click().run()
        saved = service.compile_review_job(self.root, 'nested-ui')
        claim = next(row['payload']['claim'] for row in saved['session']['decisions']
                     if row['action'] == 'set_term_interpretation')
        self.assertEqual(claim['expression']['op'], 'accumulation')
        self.assertEqual(claim['expression']['arguments']['quantity']['op'], 'accumulation')

    def test_no_question_keeps_history_management_diagnostics_and_execution(self):
        service.create_review_job(self.root, 'empty-ui', SELECTION)
        with patch('workbench.question_presenter.build_questions', return_value=[]):
            app = self.app_for('empty-ui')
            self.assertIn('No current scholar question', ' '.join(item.value for item in app.info))
            labels = [item.label for item in app.expander]
            self.assertIn('Decision history and retract', labels)
            self.assertIn('Management', labels)
            self.assertIn('Run current reviewed model', labels)
            self.assertFalse(any(button.key == 'k2_save' for button in app.button))

    def test_question_with_only_leave_unresolved_stays_in_future_semantic_work(self):
        response = service.create_review_job(self.root, 'future-ui', SELECTION)
        anchor = response['packet']['primary_documents'][0]
        question = {'id': 'unanswerable', 'kind': 'counting_convention', 'title': 'No grounded answer',
                    'anchor': anchor_for(response['packet'], anchor['doc_id'], 0, 1),
                    'options': [{'id': 'defer', 'label': 'Leave unresolved', 'action': 'defer', 'payload': {}}],
                    'evidence': {'reason': 'no grounded option'}}
        with patch('workbench.question_presenter.build_questions', return_value=[question]):
            app = self.app_for('future-ui')
            self.assertIn('No current scholar question', ' '.join(item.value for item in app.info))
            self.assertIn('Future semantic work · 1', [item.label for item in app.expander])
            self.assertFalse(any(button.key == 'k2_save' for button in app.button))

    def test_execution_panel_distinguishes_partial_graph_from_current_numeric_check(self):
        response = service.create_review_job(self.root, 'execution-ui', SELECTION)
        run = service.execute_review_job(self.root, 'execution-ui', {},
            expected_revision=response['job']['revision'], expected_digest=response['job_digest'])
        run.update(status='executed', unresolved=[], graph_status='partial')
        app = self.app_for('execution-ui')
        app.session_state['k2_execution'] = run
        app.run()
        displayed = ' '.join(item.value for item in app.markdown)
        self.assertIn('Graph: partial', displayed)
        self.assertIn('Numerical check: executed for current closed region', displayed)

    def test_source_review_uses_data_flow_status_and_boundary_entry_label(self):
        app = self.app_for('source-labels')
        displayed = ' '.join(item.value for item in [*app.caption, *app.markdown])
        self.assertIn('Data-flow status: incomplete ⓘ', displayed)
        self.assertEqual(app.toggle(key='k2_adjust').label, 'Adjust term boundary')

    def test_stale_displayed_revision_cannot_save(self):
        response = service.create_review_job(self.root, 'stale-ui', SELECTION)
        question = response['questions'][0]
        app = self.app_for('stale-ui')
        app.session_state['k2_question'] = question['id']; app.run()
        row = service.review_decision(response, 'defer', question['anchor'],
                                      {'unresolved': 'Other page'},
                                      {'type': 'scripted_fixture', 'id': 'other'}, 'Other page')
        service.apply_review_job_changes(self.root, 'stale-ui', decisions=[row],
            expected_revision=response['job']['revision'], expected_digest=response['job_digest'])
        app.button(key='k2_save').click().run()
        self.assertFalse(app.exception)
        self.assertIn('stale_job', ' '.join(item.value for item in app.error))
        self.assertEqual(review_jobs.load_job(self.root, 'stale-ui')['revision'], 2)

    def test_failed_submission_keeps_saved_bytes_and_does_not_claim_success(self):
        response = service.create_review_job(self.root, 'failure', SELECTION)
        app = self.app_for('failure')
        app.session_state['k2_question'] = response['questions'][0]['id']; app.run()
        path = review_jobs.job_path(self.root, 'failure')
        before = path.read_bytes()
        with patch('workbench.review_jobs._atomic', side_effect=OSError('write failed')):
            app.button(key='k2_save').click().run()
        self.assertFalse(app.exception)
        self.assertIn('write failed', ' '.join(e.value for e in app.error))
        self.assertFalse(app.success)
        self.assertEqual(path.read_bytes(), before)

    def test_attach_context_then_retract_and_unmanage_obsolete_scope(self):
        response = service.create_review_job(self.root, 'context-ui', SELECTION)
        question = next(q for q in response['questions'] if any(o['action'] == 'attach_context' for o in q['options']))
        option = next(o for o in question['options'] if o['action'] == 'attach_context')
        app = self.app_for('context-ui')
        app.session_state['k2_question'] = question['id']; app.run()
        app.radio(key='k2_option:' + question['id']).set_value(option['id']).run()
        app.selectbox(key='k2_context_unit').select('sifen:section:38').run()
        app.button(key='k2_save').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        attached = service.compile_review_job(self.root, 'context-ui')
        self.assertEqual(attached['job']['revision'], 2)
        context = next(d for d in attached['effective_packet']['context_documents'] if d['doc_id'] == 'sifen:38')
        anchor = anchor_for(attached['effective_packet'], context['doc_id'], 0, 1)
        event = {'event_id': 'context-scope', 'action': 'manage', 'target': anchor, 'facet': 'unit',
            'branch_id': 'main', 'actor': {'type': 'human', 'id': 'fixture'}, 'created_at': service._now(),
            'reason': 'Review this context', 'depends_on': [attached['session']['decisions'][0]['decision_id']]}
        service.apply_review_job_changes(self.root, 'context-ui', management_events=[event],
            expected_revision=2, expected_digest=attached['job_digest'])
        app.run()
        app.text_input(key='k2_retract_reason').set_value('Withdraw context').run()
        app.button(key='k2_retract').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertNotIn('sifen:38', app.selectbox(key='k2_document').options)
        app.selectbox(key='k2_management_action').select('unmanage').run()
        app.button(key='k2_manage').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        current = service.compile_review_job(self.root, 'context-ui')
        self.assertEqual(current['job']['revision'], 5)
        self.assertEqual(current['managed_scope'][0]['status'], 'unmanaged')

    def test_old_job_is_read_only_and_can_create_current_job_without_migration(self):
        response = service.create_review_job(self.root, 'old-ui', SELECTION)
        old = response['job']
        old['session']['identity_locks']['engine']['sha256'] = 'pre-BC-runtime'
        review_jobs.write_job_atomic(self.root, old)
        path = review_jobs.job_path(self.root, 'old-ui'); before = path.read_bytes()
        app = self.app_for('old-ui')
        self.assertIn('read-only', ' '.join(e.value for e in app.error))
        self.assertFalse(any(b.key in ('k2_save', 'k2_run') for b in app.button))
        app.button(key='k2_create_fresh').click().run()
        self.assertFalse(app.exception)
        fresh = service.compile_review_job(self.root, app.session_state['k2_active_saved_job'])
        self.assertEqual(fresh['freshness']['status'], 'current')
        self.assertEqual(fresh['job']['source_selection'], old['source_selection'])
        self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
