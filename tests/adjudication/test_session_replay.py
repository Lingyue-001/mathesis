import copy
import hashlib
import unittest

from adjudication.anchors import anchor_for
from adjudication.replay import replay_session
from adjudication.session import append_decision as _append_decision, create_branch, new_session


PACKET = {
    'schema_version': '3.0',
    'packet_id': 'test:session',
    'primary_documents': [{
        'doc_id': 'p:1', 'reading_id': 'p:1.r1', 'text': '置甲以乙乘之。',
        'text_sha256': hashlib.sha256('置甲以乙乘之。'.encode()).hexdigest(),
        'edition_transcription': '置甲以乙乘之。', 'edition_edits': [],
    }],
}


def decision(decision_id, action, target, payload, depends_on=None, branch_id='main'):
    return {
        'decision_id': decision_id,
        'actor': {'type': 'scripted_fixture', 'id': 'M2-test'},
        'created_at': '2026-09-17T00:00:00Z',
        'branch_id': branch_id,
        'action': action, 'targets': [target], 'payload': payload,
        'evidence_refs': ['fixture:test'], 'reason': 'test decision',
        'depends_on': depends_on or [],
    }


def append_decision(session, row):
    return _append_decision(session, row, packet=PACKET)


class TestSessionReplay(unittest.TestCase):
    def setUp(self):
        self.anchor = anchor_for(PACKET, 'p:1', 0, 2)
        self.session = new_session(PACKET, session_id='session-test')

    def test_H01_versions_are_separate_from_sourcepacket(self):
        self.assertEqual(self.session['schema'], 'AdjudicationSession')
        self.assertEqual(self.session['schema_version'], '1.0')
        self.assertEqual(PACKET['schema_version'], '3.0')

    def test_H02_bad_source_anchor_is_stale(self):
        changed = copy.deepcopy(PACKET)
        changed['primary_documents'][0]['text'] = '置丙以乙乘之。'
        state = replay_session(self.session, changed)
        self.assertEqual(state['status'], 'stale_source')

    def test_H17_replay_is_deterministic(self):
        append_decision(self.session, decision('d1', 'select_candidate', self.anchor,
                                                {'selected_candidate_id': 'ast-1'}))
        first = replay_session(self.session, PACKET)
        second = replay_session(self.session, PACKET)
        self.assertEqual(first['normalized'], second['normalized'])

    def test_H18_conflicting_active_slot_requires_resolution(self):
        append_decision(self.session, decision('d1', 'bind_value', self.anchor,
                                                {'consumer_definition_anchor': self.anchor,
                                                 'producer_definition_anchor': self.anchor, 'formal': '甲',
                                                 'output_port': 'result'}))
        append_decision(self.session, decision('d2', 'bind_value', self.anchor,
                                                {'consumer_definition_anchor': self.anchor,
                                                 'producer_definition_anchor': self.anchor, 'formal': '甲',
                                                 'output_port': 'other'}))
        state = replay_session(self.session, PACKET)
        self.assertEqual(state['decision_status']['d1']['status'], 'conflicted')
        self.assertEqual(state['decision_status']['d2']['status'], 'conflicted')

    def test_H19_retract_restores_effective_gap_and_stales_dependent(self):
        append_decision(self.session, decision('d1', 'declare_parameter', self.anchor,
                                                {'name': '甲', 'unit': 'integer', 'role': 'root_input',
                                                 'evidence_basis': 'source'}))
        append_decision(self.session, decision('d2', 'set_quantity_semantics', self.anchor,
                                                {'semantic_output': {'definition_anchor': self.anchor,
                                                                     'construction_anchor': self.anchor,
                                                                     'construction_role': 'multiply',
                                                                     'semantic_role': 'multiply',
                                                                     'output_port': 'result', 'branch_id': 'main'},
                                                 'unit': 'integer'}, depends_on=['d1']))
        append_decision(self.session, decision('d3', 'retract', self.anchor,
                                                {'decision_id': 'd1'}))
        state = replay_session(self.session, PACKET)
        self.assertEqual(state['decision_status']['d1']['status'], 'retracted')
        self.assertEqual(state['decision_status']['d2']['status'], 'needs_revalidation')
        self.assertNotIn('甲', state['effective']['parameters'])

    def test_resegmentation_stales_overlapping_downstream_decision(self):
        later = anchor_for(PACKET, 'p:1', 2, 7)
        append_decision(self.session, decision('d1', 'bind_value', later,
                                                {'consumer_definition_anchor': self.anchor,
                                                 'producer_definition_anchor': self.anchor, 'formal': '乙',
                                                 'output_port': 'result'}))
        append_decision(self.session, decision('d2', 'resegment', self.anchor,
                                                {'segments': [anchor_for(PACKET, 'p:1', 0, 4),
                                                              anchor_for(PACKET, 'p:1', 4, 7)]}))
        state = replay_session(self.session, PACKET)
        self.assertEqual(state['decision_status']['d1']['status'], 'needs_revalidation')

    def test_branch_isolated_from_main(self):
        create_branch(self.session, 'reading-b', from_branch='main')
        append_decision(self.session, decision('d1', 'mark_noncomputational', self.anchor,
                                                {'classification': 'commentary'}, branch_id='reading-b'))
        self.assertEqual(replay_session(self.session, PACKET)['effective']['noncomputational'], [])
        self.assertEqual(len(replay_session(self.session, PACKET, branch_id='reading-b')['effective']['noncomputational']), 1)

    def test_H16_context_attachment_stales_prior_binding(self):
        append_decision(self.session, decision('d1', 'bind_value', self.anchor,
                                                {'consumer_definition_anchor': self.anchor,
                                                 'producer_definition_anchor': self.anchor, 'formal': '甲',
                                                 'output_port': 'result'}))
        append_decision(self.session, decision('d2', 'attach_context', self.anchor,
                                                {'document': {'doc_id': 'ctx', 'reading_id': 'ctx.r', 'text': '甲，一。',
                                                              'edition_transcription': '甲，一。', 'edition_edits': []}}))
        state = replay_session(self.session, PACKET)
        self.assertEqual(state['decision_status']['d1']['status'], 'needs_revalidation')
