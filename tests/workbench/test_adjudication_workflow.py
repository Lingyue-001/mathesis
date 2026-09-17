"""M3-A contracts for the same-origin reviewed Procedure Workbench."""
import importlib
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]


class ReviewedWorkbenchTests(unittest.TestCase):
    def service(self):
        return importlib.import_module('workbench.service')

    def test_open_adjudication_returns_real_reviewed_products_and_stages(self):
        result = self.service().open_adjudication(ROOT, 'sifen-3-5')
        self.assertEqual(result['session']['schema'], 'AdjudicationSession')
        self.assertEqual(result['bundle']['schema'], 'ReviewedProcedureBundle')
        self.assertEqual(result['projection']['projection_version'], 2)
        self.assertEqual(
            [stage['id'] for stage in result['stages']],
            ['source_scope', 'lexical_syntax', 'procedure_control', 'quantity_binding', 'graph_coverage', 'review'],
        )
        self.assertTrue(all(stage['status'] in {'completed', 'needs_review', 'blocked', 'stale'} for stage in result['stages']))
        self.assertIn('layers', result['projection'])
        self.assertIn('coverage', result['projection'])
        self.assertIn('review_queue', result['projection'])
        self.assertEqual(result['summary']['execution_status'], 'not_run')

    def test_same_adapter_exposes_a_second_real_procedure_with_a_review_hole(self):
        procedures = importlib.import_module('source_adapters.corpus').list_procedures(ROOT)
        self.assertGreaterEqual(len(procedures), 2)
        second = next(row for row in procedures if row['id'] != 'sifen-3-5')
        result = self.service().open_adjudication(ROOT, second['id'])
        self.assertEqual(result['source_packet']['schema_version'], '3.0')
        self.assertTrue(result['projection']['review_queue']['items'])

    def test_stale_session_preserves_decisions_and_exposes_separate_unresolved_reference(self):
        service = self.service()
        opened = service.open_adjudication(ROOT, 'sifen-3-7-alternative')
        from adjudication.anchors import anchor_for
        from adjudication import append_decision
        packet = opened['source_packet']
        session_with_decision = copy.deepcopy(opened['session'])
        append_decision(session_with_decision, {
            'decision_id': 'retained-role', 'actor': {'type': 'scripted_fixture', 'id': 'stale-session-test'},
            'created_at': '2026-09-17T00:00:00Z', 'branch_id': 'main', 'action': 'set_lexical_role',
            'targets': [anchor_for(packet, 'sifen:40', 9, 14)],
            'payload': {'contract_version': '1.0', 'grammatical_role': 'term'},
            'evidence_refs': ['source:test'], 'reason': 'retention probe', 'depends_on': [],
        }, packet=packet)
        for stale_field in ('identity_locks', 'source_packet'):
            with self.subTest(stale_field=stale_field):
                session = copy.deepcopy(session_with_decision)
                session[stale_field] = {'sha256': 'previous-version'}
                original = copy.deepcopy(session)
                result = service.compile_adjudication(ROOT, opened['procedure']['id'], session)
                self.assertIsNone(result['graph'], 'stale decisions must never be silently relocked')
                self.assertEqual(result['summary']['review_status'], 'needs_revalidation')
                self.assertTrue(result['bundle']['review_queue']['items'])
                self.assertEqual(result['session'], original)
                reference = result['reference_analysis']
                self.assertEqual(reference['kind'], 'current_automatic_reference')
                self.assertEqual(reference['graph'], opened['graph'])
                self.assertEqual(reference['projection'], opened['projection'])
                self.assertTrue(any(span['quote'] == '周天乘減之'
                                    for issue in reference['graph']['unresolved']
                                    for span in issue['source_spans']))
                with self.assertRaisesRegex(ValueError, 'reviewed_graph_unavailable'):
                    service.execute_adjudication(ROOT, opened['procedure']['id'], session, 'main', {})

    def test_numerical_check_executes_the_reviewed_graph_not_a_fresh_automatic_graph(self):
        service = self.service()
        opened = service.open_adjudication(ROOT, 'sifen-3-5')
        result = service.execute_adjudication(ROOT, 'sifen-3-5', opened['session'], 'main', {'入蔀年': 25})
        self.assertEqual(result['execution']['named_outputs']['main:積月'], 296)
        self.assertEqual(result['summary']['execution_graph'], 'reviewed')

    def test_http_decision_endpoint_appends_then_recompiles_instead_of_accepting_a_graph(self):
        api = importlib.import_module('workbench.api')
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / 'adjudication').mkdir()
            (site / 'adjudication/index.html').write_text('<html data-baseurl="/">Workbench</html>', encoding='utf-8')
            server = api.make_server(ROOT, 0, site_root=site)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            origin = f'http://127.0.0.1:{server.server_port}'
            try:
                with urlopen(origin + '/api/adjudication/sifen-3-5', timeout=15) as response:
                    opened = json.load(response)
                target = opened['source_packet']['primary_documents'][0]
                anchor = {'doc_id': target['doc_id'], 'reading_id': target['reading_id'],
                          'source_sha256': target['text_sha256'], 'start': 0, 'end': 4,
                          'quote': target['text'][:4], 'offset_unit': 'unicode_code_point'}
                decision = {'decision_id': 'web-role', 'actor': {'type': 'human', 'id': 'browser-test'},
                            'created_at': '2026-09-17T00:00:00Z', 'branch_id': 'main',
                            'action': 'set_lexical_role', 'targets': [anchor],
                            'payload': {'contract_version': '1.0', 'grammatical_role': 'term'},
                            'evidence_refs': ['source:browser'], 'reason': 'test', 'depends_on': []}
                body = json.dumps({'procedure_id': 'sifen-3-5', 'session': opened['session'],
                                   'decision': decision, 'branch_id': 'main'}).encode()
                request = Request(origin + '/api/adjudication/decision', data=body,
                                  headers={'Content-Type': 'application/json'})
                with urlopen(request, timeout=15) as response:
                    updated = json.load(response)
                self.assertEqual(updated['graph']['adjudication']['lexical_roles'][0]['grammatical_role'], 'term')
                self.assertNotIn('graph', updated['session'])
            finally:
                server.shutdown(); server.server_close(); thread.join()


if __name__ == '__main__':
    unittest.main()
