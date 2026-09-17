"""M3 counterexamples for local, replayable lexical-function adjudication."""
import unittest

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for


def decision(identifier, target, role):
    return {
        'decision_id': identifier, 'actor': {'type': 'human', 'id': 'scholar-1'},
        'created_at': '2026-09-17T00:00:00Z', 'branch_id': 'main',
        'action': 'set_lexical_role', 'targets': [target],
        'payload': {'contract_version': '1.0', 'grammatical_role': role},
        'evidence_refs': ['source:fixture'], 'reason': 'local grammatical review', 'depends_on': [],
    }


class LocalLexicalRevisionTests(unittest.TestCase):
    def setUp(self):
        self.text = '推甲術。以甲置乙。推乙術。以甲置丙。'
        self.packet = {'schema_version': '3.0', 'packet_id': 'm3-lexical', 'primary_documents': [{
            'doc_id': 'm3', 'reading_id': 'm3.r', 'text': self.text,
            'edition_transcription': self.text, 'edition_edits': [],
        }]}
        self.first = anchor_for(self.packet, 'm3', 4, 5)
        self.second = anchor_for(self.packet, 'm3', 13, 14)

    def test_role_is_scoped_to_one_occurrence_not_the_same_character_elsewhere(self):
        session = new_session(self.packet, 'm3-local')
        append_decision(session, decision('L1', self.first, 'preposition'), packet=self.packet)
        result = compile_reviewed(self.packet, session)
        roles = result['graph']['adjudication']['lexical_roles']
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]['target'], self.first)
        self.assertNotEqual(roles[0]['target'], self.second)

    def test_local_function_word_does_not_mark_its_sentence_noncomputational(self):
        session = new_session(self.packet, 'm3-function')
        append_decision(session, decision('L1', self.first, 'function_word'), packet=self.packet)
        result = compile_reviewed(self.packet, session)
        self.assertEqual(result['replay']['effective']['noncomputational'], [])
        self.assertNotEqual(result['coverage_ledger']['graph_status'], 'closed')

    def test_resegmentation_after_local_role_marks_the_role_for_revalidation(self):
        session = new_session(self.packet, 'm3-stale')
        append_decision(session, decision('L1', self.first, 'term'), packet=self.packet)
        segment = {
            'decision_id': 'S1', 'actor': {'type': 'human', 'id': 'scholar-1'},
            'created_at': '2026-09-17T00:01:00Z', 'branch_id': 'main', 'action': 'resegment',
            'targets': [self.first], 'payload': {'segments': [anchor_for(self.packet, 'm3', 4, 6)]},
            'evidence_refs': ['source:fixture'], 'reason': 'split review', 'depends_on': [],
        }
        append_decision(session, segment, packet=self.packet)
        result = compile_reviewed(self.packet, session)
        self.assertEqual(result['replay']['decision_status']['L1']['status'], 'needs_revalidation')

    def test_unknown_local_role_is_rejected_at_append_time(self):
        session = new_session(self.packet, 'm3-invalid-role')
        with self.assertRaisesRegex(ValueError, 'invalid_lexical_role'):
            append_decision(session, decision('L1', self.first, 'global_dictionary_rewrite'), packet=self.packet)


if __name__ == '__main__':
    unittest.main()
