"""ReviewJob transactions use temporary stores and real active corpus adapters."""
import copy
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from adjudication.anchors import anchor_for
from source_adapters import corpus_review
from tests.adjudication.test_dependency_closure import decision
from workbench import service

ROOT = Path(__file__).resolve().parents[2]
ACTOR = {'type': 'scripted_fixture', 'id': 'k2a-test'}
SELECTION = {'source_id': 'sifen', 'primary_unit_ids': ['sifen:section:39'],
             'context_unit_ids': [], 'provided_scope': {'tradition': 'Han_Si_fen_li'}, 'selected_profiles': []}


def isolated_source(root):
    (root / 'config').mkdir()
    shutil.copyfile(ROOT / 'config/calendrical-ir-pipeline.json', root / 'config/calendrical-ir-pipeline.json')
    shutil.copyfile(ROOT / 'calendars-四分历.md', root / 'calendars-四分历.md')
    corpus_review.regenerate(root)


class ReviewJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); isolated_source(self.root)

    def create(self):
        self.assertTrue(hasattr(service, 'create_review_job'), 'ReviewJob service is missing')
        result = service.create_review_job(self.root, 'test-job', SELECTION)
        self.jobs = importlib.import_module('workbench.review_jobs')
        return result

    def row(self, response, ident='defer'):
        p = response['packet']; doc = p['primary_documents'][0]
        return decision(p, ident, target=anchor_for(p, doc['doc_id'], 0, 2))

    def apply(self, response, **changes):
        return service.apply_review_job_changes(self.root, 'test-job', expected_revision=response['job']['revision'],
                                               expected_digest=response['job_digest'], **changes)

    def test_restart_export_import_and_base_identity(self):
        r = self.create(); r = self.apply(r, decisions=[self.row(r)])
        code = "from workbench.service import compile_review_job; import sys,json; r=compile_review_job(sys.argv[1],'test-job'); print(json.dumps([r['job']['session']['session_id'],r['job']['revision'],r['job_digest']]))"
        out = subprocess.check_output([sys.executable, '-X', 'utf8', '-B', '-c', code, str(self.root)], cwd=ROOT, text=True)
        self.assertEqual(json.loads(out), [r['job']['session']['session_id'], r['job']['revision'], r['job_digest']])
        exported = self.jobs.export_job(r['job'])
        dest = self.root / 'other'; dest.mkdir(); isolated_source(dest)
        loaded = service.import_review_job(dest, exported)
        self.assertEqual(loaded['job'], r['job'])

    def test_stale_revision_and_digest_cannot_overwrite(self):
        r = self.create(); after = self.apply(r, decisions=[self.row(r)])
        with self.assertRaisesRegex(ValueError, 'stale_job'):
            self.apply(r, decisions=[self.row(r, 'other')])
        with self.assertRaisesRegex(ValueError, 'stale_job'):
            service.apply_review_job_changes(self.root, 'test-job', decisions=[], expected_revision=after['job']['revision'], expected_digest='wrong')
        self.assertEqual(self.jobs.load_job(self.root, 'test-job'), after['job'])

    def test_compile_failure_and_write_failure_preserve_exact_bytes(self):
        r = self.create(); path = self.jobs.job_path(self.root, 'test-job'); before = path.read_bytes()
        for target, error in [('workbench.service.compile_reviewed', RuntimeError('compile failed')),
                              ('workbench.review_jobs._atomic', OSError('disk failed'))]:
            with patch(target, side_effect=error):
                with self.assertRaises(type(error)):
                    self.apply(r, decisions=[self.row(r)])
            self.assertEqual(path.read_bytes(), before)

    def test_invalid_payload_and_cycle_never_saved(self):
        r = self.create(); bad = self.row(r); bad['action'] = 'bind_value'; bad['payload'] = {}
        with self.assertRaises(ValueError): self.apply(r, decisions=[bad])
        a = self.row(r, 'a'); b = self.row(r, 'b'); a['depends_on'] = ['b']; b['depends_on'] = ['a']
        with self.assertRaisesRegex(ValueError, 'cycle'): self.apply(r, decisions=[a, b])
        self.assertEqual(self.jobs.load_job(self.root, 'test-job'), r['job'])

    def test_duplicate_submission_does_not_create_another_effective_decision(self):
        r = self.create(); row = self.row(r); after = self.apply(r, decisions=[row])
        duplicate = {**row, 'decision_id': 'new-ui-id'}
        again = self.apply(after, decisions=[duplicate])
        self.assertEqual(after['job'], again['job'])

    def test_management_survives_retraction_and_unmanage_checks_dependencies(self):
        self.jobs = importlib.import_module('workbench.review_jobs')
        r = service.create_review_job(self.root, 'test-job', {**SELECTION, 'primary_unit_ids': ['sifen:section:38']})
        anchor = anchor_for(r['packet'], 'sifen:38', 5, 11)
        row = self.row(r); row.update(action='set_quantity_semantics', targets=[anchor], payload={
            'semantic_output': {'definition_anchor': anchor_for(r['packet'], 'sifen:38', 0, 4),
                'construction_anchor': anchor, 'construction_role': 'load', 'semantic_role': 'load',
                'output_port': 'result', 'branch_id': 'main'}, 'unit': 'year', 'role': 'reviewed_input'})
        event = {'event_id': 'manage', 'action': 'manage', 'target': anchor, 'facet': 'unit', 'branch_id': 'main',
                 'actor': ACTOR, 'created_at': '2026-09-19T00:00:00Z', 'reason': '单独接管'}
        event['semantic_target'] = service.normalize_decision_target(row['action'], row['payload'], row['targets'])
        # K2-C consumes this existing quantity action in the same managed trial.
        managed = self.apply(r, management_events=[event], decisions=[row])
        self.assertTrue(managed['managed_scope'][0]['managed'])
        self.assertEqual(managed['managed_scope'][0]['consumer_status'], 'applied_before_operation')
        self.assertEqual(managed['managed_scope'][0]['status'], 'interpretation_recorded')
        with self.assertRaisesRegex(ValueError, 'unmanage_has_active'):
            self.apply(managed, management_events=[{**event, 'event_id': 'blocked', 'action': 'unmanage'}])
        retract = self.row(managed, 'retract'); retract.update(action='retract', payload={'decision_id': row['decision_id']})
        after = self.apply(managed, decisions=[retract])
        self.assertEqual(after['job']['management_events'], managed['job']['management_events'])
        self.assertEqual(after['managed_scope'][0]['status'], 'pending')
        unmanage = {**event, 'event_id': 'unmanage', 'action': 'unmanage'}
        released = self.apply(after, management_events=[unmanage])
        self.assertFalse(released['managed_scope'][0]['managed'])

    def test_context_attachment_has_real_effect_and_no_effect_is_honest(self):
        r = self.create(); doc = service.build_source_packet_from_units(self.root, 'sifen', ['sifen:section:38'])['primary_documents'][0]
        row = self.row(r, 'attach'); row.update(action='attach_context', payload={'document': doc})
        after = self.apply(r, decisions=[row])
        self.assertIn(doc['doc_id'], [d['doc_id'] for d in after['effective_packet']['context_documents']])
        self.assertTrue(after['effects']['documents']['added'])
        self.assertEqual(r['job']['base_packet_identity'], after['job']['base_packet_identity'])
        self.assertTrue(after['effects']['baseline'] == 'reviewed_before_to_reviewed_after')
        after2 = self.apply(after, decisions=[self.row(after)])
        self.assertEqual(after2['effects']['message'], '已记录，编译结构未变')

    def test_stale_source_is_readable_but_cannot_submit(self):
        r = self.create(); path = self.root / 'calendars-四分历.md'; path.write_bytes(path.read_bytes() + b'\nchanged')
        stale = service.compile_review_job(self.root, 'test-job')
        self.assertEqual(stale['freshness']['status'], 'stale')
        self.assertEqual(stale['job'], r['job'])
        with self.assertRaises(ValueError): self.apply(r, decisions=[self.row(r)])

    def test_source_selection_resolves_the_newest_fresh_job_and_never_reuses_stale(self):
        first = service.resolve_current_review_job(self.root, SELECTION)
        self.assertTrue(first['job']['job_id'].startswith('session-'))
        self.assertEqual(service.resolve_current_review_job(self.root, SELECTION)['job']['job_id'],
                         first['job']['job_id'])

        old = first['job']
        old['session']['identity_locks']['engine']['sha256'] = 'obsolete-engine'
        importlib.import_module('workbench.review_jobs').write_job_atomic(self.root, old)
        replacement = service.resolve_current_review_job(self.root, SELECTION)
        self.assertNotEqual(replacement['job']['job_id'], old['job_id'])
        self.assertEqual(replacement['freshness']['status'], 'current')
        self.assertEqual(replacement['job']['source_selection'], SELECTION)

    def test_bad_import_never_overwrites_job_and_rejects_paths(self):
        r = self.create()
        for text in ['{}', self.jobs.export_job(r['job']), '{"schema":"DynamicAnalysis"}', 'x' * (self.jobs.MAX_JOB_BYTES + 1)]:
            with self.assertRaises(ValueError): service.import_review_job(self.root, text)
        with self.assertRaises(ValueError): self.jobs.load_job(self.root, '../escape')
        self.assertEqual(self.jobs.load_job(self.root, 'test-job'), r['job'])

    def test_second_lock_is_rejected(self):
        self.create()
        with self.jobs.job_lock(self.root, 'test-job'):
            with self.assertRaisesRegex(ValueError, 'job_locked'):
                with self.jobs.job_lock(self.root, 'test-job'): pass

    def test_context_binding_reaches_linker_and_retraction_removes_it(self):
        r = self.create()
        doc = service.review_context_document(self.root, 'sifen', 'sifen:section:38')
        attach = self.row(r, 'attach'); attach.update(action='attach_context', payload={'document': doc})
        r = self.apply(r, decisions=[attach])
        form = next(f for f in r['review_forms'] if f['formal'] == '入蔀積月')
        producer = next(p for p in form['producers'] if p['anchor']['doc_id'] == 'sifen:38' and p['output_port'] == '積月')
        payload = {'consumer_definition_anchor': form['consumer_anchor'], 'formal': form['formal'],
                   'producer_definition_anchor': producer['anchor'], 'output_port': producer['output_port']}
        row = service.review_decision(r, 'bind_value', form['anchors'][0], payload, ACTOR, '明确采用前段结果')
        self.assertIn('attach', row['depends_on'])
        after = self.apply(r, decisions=[row])
        self.assertEqual(after['compilation']['replay']['decision_status'][row['decision_id']]['status'], 'active')
        self.assertTrue(after['effects']['bindings']['added'])
        imports = after['graph']['program']['linked']['imports']
        self.assertTrue(any(i.get('formal') == '入蔀積月' and i.get('selection_reason') == 'reviewed producer/port constraint' for i in imports))
        retract = self.row(after, 'withdraw'); retract.update(action='retract', payload={'decision_id': 'attach'})
        restored = self.apply(after, decisions=[retract])
        self.assertEqual(restored['compilation']['replay']['decision_status'][row['decision_id']]['status'], 'needs_revalidation')
        self.assertFalse(restored['compilation']['replay']['effective']['bindings'])

    def test_effect_comparison_preserves_operands_children_scope_and_ports(self):
        from tests.adjudication.test_m31_consistency import product_session
        from adjudication import compile_reviewed
        packet, session = product_session(); compiled = compile_reviewed(packet, session)
        before = {'graph': compiled['graph'], 'compilation': compiled, 'effective_packet': packet,
                  'session': session, 'review_forms': []}
        def change_literal(r): r['graph']['events'][0]['attributes']['value'] = 7
        def swap_operands(r):
            reads = r['graph']['events'][2]['reads']; reads['left'], reads['right'] = reads['right'], reads['left']
        def swap_children(r): r['graph']['syntax']['nodes'][-1]['children'].reverse()
        def change_scope(r): r['graph']['events'][-1]['scope']['query'] = 'another invocation'
        def change_port(r): r['graph']['value_instances'][-1]['output_port'] = 'remainder'
        for mutation in (change_literal, swap_operands, swap_children, change_scope, change_port):
            with self.subTest(mutation=mutation.__name__):
                after = copy.deepcopy(before); mutation(after)
                self.assertTrue(service._review_effects(before, after)['structure_changed'])
        after = copy.deepcopy(before)
        after['graph']['events'][-1]['adjudication_decision_refs'] = ['new-evidence']
        self.assertFalse(service._review_effects(before, after)['structure_changed'])

    def test_inactive_context_management_can_be_explicitly_released_and_imported(self):
        r = self.create()
        doc = service.review_context_document(self.root, 'sifen', 'sifen:section:38')
        attach = self.row(r, 'attach'); attach.update(action='attach_context', payload={'document': doc})
        r = self.apply(r, decisions=[attach])
        target = anchor_for(r['effective_packet'], doc['doc_id'], 0, 4)
        event = {'event_id': 'manage-context', 'action': 'manage', 'target': target, 'facet': 'unit', 'branch_id': 'main',
                 'actor': ACTOR, 'created_at': '2026-09-19T00:00:00Z', 'reason': '接管背景位置', 'depends_on': ['attach']}
        r = self.apply(r, management_events=[event])
        retract = self.row(r, 'retract'); retract.update(action='retract', payload={'decision_id': 'attach'})
        r = self.apply(r, decisions=[retract])
        self.assertEqual(r['managed_scope'][0]['status'], 'needs_revalidation')
        r = self.apply(r, management_events=[{**event, 'event_id': 'release', 'action': 'unmanage'}])
        self.assertFalse(r['managed_scope'][0]['managed'])
        self.assertEqual(r['managed_scope'][0]['status'], 'unmanaged')
        dest = self.root / 'imported'; dest.mkdir(); isolated_source(dest)
        imported = service.import_review_job(dest, self.jobs.export_job(r['job']))
        self.assertEqual(imported['managed_scope'], r['managed_scope'])

    def test_evidence_anchor_cannot_claim_semantic_management(self):
        self.jobs = importlib.import_module('workbench.review_jobs')
        r = service.create_review_job(self.root, 'test-job', {**SELECTION, 'primary_unit_ids': ['sifen:section:38']})
        evidence = anchor_for(r['packet'], 'sifen:38', 0, 1)
        output = anchor_for(r['packet'], 'sifen:38', 5, 11)
        row = service.review_decision(r, 'set_quantity_semantics', evidence, {
            'semantic_output': {'definition_anchor': anchor_for(r['packet'], 'sifen:38', 0, 4),
                'construction_anchor': output, 'construction_role': 'load', 'semantic_role': 'load',
                'output_port': 'result', 'branch_id': 'main'}, 'unit': 'year', 'role': 'reviewed_input'}, ACTOR, '范围外证据')
        event = {'event_id': 'manage-evidence', 'action': 'manage', 'target': evidence, 'facet': 'unit', 'branch_id': 'main',
                 'actor': ACTOR, 'created_at': '2026-09-19T00:00:00Z', 'reason': '只管理证据位置'}
        r = self.apply(r, decisions=[row], management_events=[event])
        self.assertEqual(r['managed_scope'][0]['status'], 'pending')
        self.assertEqual(r['managed_scope'][0]['decision_refs'], [])
        r = self.apply(r, management_events=[{**event, 'event_id': 'release', 'action': 'unmanage'}])
        self.assertFalse(r['managed_scope'][0]['managed'])

    def test_review_item_requires_suggested_constructible_consumer_action(self):
        """A visible form is actionable only when it can resolve this queue item."""
        cases = [
            ({'kind': 'missing_input', 'suggested_actions': ['bind_value', 'defer']},
             {'actions': ['bind_value', 'defer']}, 'scholar_actionable', ['bind_value']),
            ({'kind': 'missing_input', 'suggested_actions': ['bind_value', 'defer']},
             {'actions': ['attach_context', 'defer']}, 'future_semantic_question', []),
            ({'kind': 'quantity_semantics', 'suggested_actions': ['set_quantity_semantics', 'defer']},
             {'actions': ['set_quantity_semantics', 'defer']}, 'future_semantic_question', []),
            ({'kind': 'invalid_graph_structure', 'suggested_actions': ['retract']},
             {'actions': ['retract']}, 'system_diagnostic', []),
            ({'kind': 'stale_decision', 'suggested_actions': ['retract'],
              'details': {'decision_id': 'old'}}, {'actions': ['retract']}, 'decision_issue', []),
        ]
        for question, form, category, resolving in cases:
            with self.subTest(kind=question['kind'], expected=category):
                classified = service.classify_review_item(question, form)
                self.assertEqual(classified['category'], category)
                self.assertEqual(classified['resolving_actions'], resolving)

    def test_review_forms_keep_context_binding_actionable_but_hide_system_diagnostics(self):
        response = self.create()
        diagnostics = [f for f in response['review_forms'] if f['category'] == 'system_diagnostic']
        # C6 now preserves the true remainder producer even with unknown units.
        self.assertFalse(diagnostics)
        self.assertEqual(service.classify_review_item({'kind': 'invalid_graph_structure'},
            {'actions': ['defer']})['category'], 'system_diagnostic')
        doc = service.review_context_document(self.root, 'sifen', 'sifen:section:38')
        attach = self.row(response, 'attach'); attach.update(action='attach_context', payload={'document': doc})
        response = self.apply(response, decisions=[attach])
        binding = next(f for f in response['review_forms']
                       if f['formal'] == '入蔀積月' and 'bind_value' in f['resolving_actions'])
        self.assertEqual(binding['category'], 'scholar_actionable')

    def test_review_forms_do_not_offer_a_root_parameter_for_a_produced_value(self):
        response = self.create()
        compilation = copy.deepcopy(response['compilation'])
        compilation['graph']['program']['definitions'][0].setdefault('defined_values', {})['入蔀積月'] = {}
        forms = service._review_forms(response['packet'], compilation)
        form = next(f for f in forms if f['question']['kind'] == 'missing_input'
                    and f['formal'] == '入蔀積月')
        self.assertNotIn('declare_parameter', form['actions'])
        self.assertEqual(form['category'], 'future_semantic_question')
