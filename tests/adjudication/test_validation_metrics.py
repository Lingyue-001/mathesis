import hashlib
import unittest

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for
from adjudication.bundle import make_bundle
from adjudication.metrics import decision_metrics


PACKET = {'schema_version': '3.0', 'packet_id': 'validation', 'primary_documents': [{
    'doc_id': 'p', 'reading_id': 'p.r', 'text': '推術。',
    'text_sha256': hashlib.sha256('推術。'.encode()).hexdigest(),
    'edition_transcription': '推術。', 'edition_edits': [],
}]}


def decision(decision_id, action, payload):
    return {'decision_id': decision_id, 'actor': {'type': 'scripted_fixture', 'id': 'validation'},
            'created_at': '2026-09-17T00:00:00Z', 'branch_id': 'main', 'action': action,
            'targets': [anchor_for(PACKET, 'p', 0, 2)], 'payload': payload,
            'evidence_refs': ['fixture'], 'reason': 'test', 'depends_on': []}


class TestValidationMetrics(unittest.TestCase):
    def test_H14_unknown_manual_opcode_requires_schema_extension(self):
        session = new_session(PACKET, 'manual')
        append_decision(session, decision('m1', 'assemble_known_structure', {'candidates': [{'kind': 'new_opcode', 'slots': {}}]}))
        result = compile_reviewed(PACKET, session)
        self.assertIsNone(result['graph'])
        self.assertEqual(result['review_queue']['items'][0]['kind'], 'schema_extension_required')

    def test_H15_derived_value_cannot_be_declared_as_parameter(self):
        session = new_session(PACKET, 'derived')
        append_decision(session, decision('p1', 'declare_parameter', {'name': 'derived', 'unit': 'integer', 'derived_role': True}))
        result = compile_reviewed(PACKET, session)
        self.assertIsNone(result['graph'])
        self.assertEqual(result['review_queue']['items'][0]['kind'], 'invalid_human_decision')

    def test_H45_scripted_metrics_do_not_claim_human_time(self):
        session = new_session(PACKET, 'metrics')
        append_decision(session, decision('q1', 'defer', {'schema_extension_required': True}))
        metrics = decision_metrics(session)
        self.assertEqual(metrics['actors'], {'scripted_fixture': 1})
        self.assertIsNone(metrics['human_active_seconds'])

    def test_H39_partial_graph_is_exportable_but_not_complete(self):
        session = new_session(PACKET, 'partial')
        append_decision(session, decision('d1', 'defer', {'unresolved': True}))
        result = make_bundle(compile_reviewed(PACKET, session), session)
        self.assertFalse(result['validation']['valid_for_complete_export'])
