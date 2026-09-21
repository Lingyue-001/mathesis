"""K2-A: final effective decisions agree with context and compiler validity."""
import copy
import unittest

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for, packet_identity
from adjudication.replay import replay_session


def packet(text='置甲量，名為乙量。'):
    return {'schema_version': '3.0', 'packet_id': 'closure',
            'primary_documents': [{'doc_id': 'p', 'text': text}]}


def decision(p, ident, action='defer', payload=None, deps=(), target=None):
    return {'decision_id': ident, 'actor': {'type': 'scripted_fixture', 'id': 'k2a'},
            'created_at': '2026-09-19T00:00:00Z', 'branch_id': 'main', 'action': action,
            'targets': [target or anchor_for(p, 'p', 0, 2)], 'payload': payload or {'unresolved': ident},
            'evidence_refs': ['synthetic:closure'], 'reason': '验证人工审阅', 'depends_on': list(deps)}


class DependencyClosureTests(unittest.TestCase):
    def chain(self, p, first):
        s = new_session(p, 'chain')
        append_decision(s, first, packet=p)
        for ident, dep, start in [('child', first['decision_id'], 2), ('grandchild', 'child', 3)]:
            append_decision(s, decision(p, ident, deps=[dep], target=anchor_for(p, 'p', start, start+1)), packet=p)
        return s

    def assert_descendants_inactive(self, state):
        for ident in ('child', 'grandchild'):
            self.assertEqual(state['decision_status'][ident]['status'], 'needs_revalidation')
        self.assertFalse(any(d['decision_id'] in ('child', 'grandchild') for d in state['effective']['deferred']))

    def test_conflict_invalidates_grandchild(self):
        p = packet(); s = self.chain(p, decision(p, 'first'))
        append_decision(s, decision(p, 'other'), packet=p)
        self.assert_descendants_inactive(replay_session(s, p))

    def test_stale_anchor_invalidates_grandchild(self):
        p = packet(); s = self.chain(p, decision(p, 'first'))
        s['decisions'][0]['targets'][0]['quote'] = '错误'
        self.assert_descendants_inactive(replay_session(s, p))

    def test_compiler_invalid_candidate_recompiles_without_descendants(self):
        p = packet(); s = self.chain(p, decision(p, 'first', 'select_candidate', {'selected_candidate_id': 'missing'}))
        result = compile_reviewed(p, s)
        self.assert_descendants_inactive(result['replay'])
        self.assertNotEqual(result['replay']['decision_status']['first']['status'], 'active')
        self.assertEqual(result['graph']['adjudication']['effective_decisions'], result['replay']['effective'])

    def test_compiler_invalid_root_invalidates_descendants(self):
        p = packet(); s = self.chain(p, decision(p, 'first', 'declare_parameter',
            {'name': '乙量', 'unit': 'integer', 'role': 'root_input', 'evidence_basis': 'source'}))
        self.assert_descendants_inactive(compile_reviewed(p, s)['replay'])

    def test_cycle_rejected_on_append_and_imported_cycle_inactive(self):
        p = packet(); s = new_session(p, 'cycle')
        a = decision(p, 'a', deps=['b']); b = decision(p, 'b', deps=['a'], target=anchor_for(p, 'p', 2, 3))
        append_decision(s, a, packet=p)
        before = copy.deepcopy(s)
        with self.assertRaisesRegex(ValueError, 'cycle'):
            append_decision(s, b, packet=p)
        self.assertEqual(before, s)
        s['decisions'].append(b)
        self.assertTrue(all(v['status'] != 'active' for v in replay_session(s, p)['decision_status'].values()))

    def test_context_targets_require_attachment_dependency_and_keep_base_identity(self):
        p = packet(); s = new_session(p, 'context'); identity = packet_identity(p)
        ctx = {'doc_id': 'c', 'reading_id': 'c.r1', 'text': '甲量，三。'}
        append_decision(s, decision(p, 'attach', 'attach_context', {'document': ctx}), packet=p)
        effective = copy.deepcopy(p); effective['context_documents'] = [ctx]
        target = anchor_for(effective, 'c', 0, 2)
        with self.assertRaisesRegex(ValueError, 'attachment_dependency'):
            append_decision(s, decision(p, 'bad', target=target), packet=p)
        append_decision(s, decision(p, 'dependent', target=target, deps=['attach']), packet=p)
        self.assertEqual(compile_reviewed(p, s)['replay']['decision_status']['dependent']['status'], 'active')
        self.assertEqual(s['source_packet'], identity)
        self.assertNotIn('context_documents', p)
        append_decision(s, decision(p, 'withdraw', 'retract', {'decision_id': 'attach'}), packet=p)
        result = compile_reviewed(p, s)
        self.assertEqual(result['replay']['decision_status']['dependent']['status'], 'needs_revalidation')
        self.assertFalse(result['replay']['effective']['contexts'])

    def test_conflicting_context_text_rejected(self):
        p = packet(); s = new_session(p, 'conflict')
        append_decision(s, decision(p, 'one', 'attach_context', {'document': {'doc_id': 'c', 'text': '甲量，三。'}}), packet=p)
        with self.assertRaisesRegex(ValueError, 'context_document_identity_conflict'):
            append_decision(s, decision(p, 'two', 'attach_context', {'document': {'doc_id': 'c', 'text': '甲量，四。'}}), packet=p)

    def test_payload_context_anchor_also_requires_dependency(self):
        p = packet(); s = new_session(p, 'payload')
        ctx = {'doc_id': 'c', 'text': '置丙量，名為甲量。'}
        append_decision(s, decision(p, 'attach', 'attach_context', {'document': ctx}), packet=p)
        effective = {**p, 'context_documents': [ctx]}
        binding = {'consumer_definition_anchor': anchor_for(p, 'p', 0, 2),
                   'producer_definition_anchor': anchor_for(effective, 'c', 0, 2), 'formal': '甲量', 'output_port': '甲量'}
        with self.assertRaisesRegex(ValueError, 'attachment_dependency'):
            append_decision(s, decision(p, 'binding', 'bind_value', binding), packet=p)

    def test_inactive_retraction_does_not_retract_an_unrelated_target(self):
        p = packet(); s = new_session(p, 'retract-premise')
        append_decision(s, decision(p, 'premise'), packet=p)
        append_decision(s, decision(p, 'target', target=anchor_for(p, 'p', 3, 4)), packet=p)
        append_decision(s, decision(p, 'retract', 'retract', {'decision_id': 'target'}, deps=['premise']), packet=p)
        append_decision(s, decision(p, 'conflict'), packet=p)
        state = replay_session(s, p)
        self.assertEqual(state['decision_status']['retract']['status'], 'needs_revalidation')
        self.assertEqual(state['decision_status']['target']['status'], 'active')

    def test_compiler_invalid_scope_invalidates_descendants(self):
        p = packet(); s = self.chain(p, decision(p, 'first', 'set_scope',
            {'definition_anchor': anchor_for(p, 'p', 1, 3), 'procedure_role': 'independent'}))
        result = compile_reviewed(p, s)
        self.assert_descendants_inactive(result['replay'])
        self.assertEqual(result['replay']['decision_status']['first']['status'], 'needs_revalidation')
        self.assertFalse(result['replay']['effective']['scopes'])

    def test_linker_invalid_binding_invalidates_descendants(self):
        p = packet(); anchor = anchor_for(p, 'p', 0, 2)
        s = self.chain(p, decision(p, 'first', 'bind_value', {
            'consumer_definition_anchor': anchor, 'producer_definition_anchor': anchor,
            'formal': '甲量', 'output_port': 'missing-port'}))
        result = compile_reviewed(p, s)
        self.assert_descendants_inactive(result['replay'])
        self.assertFalse(result['replay']['effective']['bindings'])
        self.assertEqual(result['graph']['adjudication']['effective_decisions'], result['replay']['effective'])
