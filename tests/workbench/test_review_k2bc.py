"""Transaction and current-job execution regressions for the final K2 milestone."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from adjudication.anchors import anchor_for
from adjudication.session import create_branch
from tests.workbench.test_review_jobs import isolated_source, SELECTION, ACTOR
from workbench import service, review_jobs


class K2TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        isolated_source(self.root)
        self.r = service.create_review_job(self.root, 'k2bc', SELECTION)

    def event(self, action='manage', branch='main'):
        return dict(event_id=action + ':' + branch, action=action,
                    target=anchor_for(self.r['packet'], 'sifen:39', 0, 2),
                    facet='unit', branch_id=branch, actor=ACTOR,
                    created_at=service._now(), reason='Explicit ownership test')

    def apply(self, **changes):
        return service.apply_review_job_changes(self.root, 'k2bc',
            expected_revision=self.r['job']['revision'], expected_digest=self.r['job_digest'], **changes)

    def test_manage_and_unmanage_participate_in_trial_compilation(self):
        actual = service.compile_reviewed
        seen = []
        def compile_capture(*args, **kwargs):
            seen.append(copy.deepcopy(kwargs.get('management', [])))
            return actual(*args, **kwargs)
        with patch.object(service, 'compile_reviewed', side_effect=compile_capture):
            self.r = self.apply(management_events=[self.event()])
        self.assertTrue(any(any(e['managed'] for e in state) for state in seen))
        seen.clear()
        with patch.object(service, 'compile_reviewed', side_effect=compile_capture):
            self.r = self.apply(management_events=[self.event('unmanage')])
        self.assertTrue(any(state and all(not e['managed'] for e in state) for state in seen))

    def test_child_inherits_management_and_can_release_without_changing_parent(self):
        job = copy.deepcopy(self.r['job'])
        job['management_events'] = [self.event()]
        create_branch(job['session'], 'child')
        job['branch_id'] = 'child'
        self.assertEqual(len(review_jobs.management_state(job)), 1)
        self.assertEqual(review_jobs.management_state(job)[0]['branch_id'], 'child')
        job['management_events'].append(self.event('unmanage', 'child'))
        self.assertFalse(review_jobs.management_state(job)[0]['managed'])
        job['branch_id'] = 'main'
        self.assertTrue(review_jobs.management_state(job)[0]['managed'])

    def test_execution_is_current_job_and_refuses_obsolete_revision(self):
        self.assertTrue(hasattr(service, 'execute_review_job'))
        run = service.execute_review_job(self.root, 'k2bc', {},
            expected_revision=self.r['job']['revision'], expected_digest=self.r['job_digest'])
        self.assertEqual(run['schema'], 'ReviewExecution/1')
        self.assertEqual(run['revision'], 1)
        self.assertEqual(run['branch_id'], 'main')
        self.assertEqual(run['job_digest'], self.r['job_digest'])
        self.assertTrue(run['analysis_identity'])
        self.assertIn('graph_status', run)
        self.assertTrue(run['unresolved'])
        old = self.r
        self.r = self.apply(management_events=[self.event()])
        self.assertTrue(service.review_execution_stale(run, self.r))
        with self.assertRaisesRegex(ValueError, 'stale_job'):
            service.execute_review_job(self.root, 'k2bc', {},
                expected_revision=old['job']['revision'], expected_digest=old['job_digest'])

    def test_failed_management_trial_preserves_original_bytes(self):
        before = review_jobs.job_path(self.root, 'k2bc').read_bytes()
        actual = service.compile_reviewed
        def fail_trial(*args, **kwargs):
            if kwargs.get('management'):
                raise RuntimeError('trial management failure')
            return actual(*args, **kwargs)
        with patch.object(service, 'compile_reviewed', side_effect=fail_trial):
            with self.assertRaisesRegex(RuntimeError, 'trial management failure'):
                self.apply(management_events=[self.event()])
        self.assertEqual(review_jobs.job_path(self.root, 'k2bc').read_bytes(), before)
