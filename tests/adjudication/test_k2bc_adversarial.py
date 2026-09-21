"""Counterexamples for K2-B+C replay and ownership contracts."""
import tempfile
import unittest
from pathlib import Path

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for
from adjudication.decision_contracts import normalize_decision_target
from adjudication.session import create_branch
from analysis_parser.execution import execute
from tests.adjudication.test_acceptance_core import packet
from tests.adjudication.test_reviewed_relations import packet as sifen_packet, relation_claim
from tests.adjudication.test_term_claims import packet as term_packet
from adjudication.term_claims import adopt_term_candidate, reject_term_candidates
from domain_kernel.engine import suggest_term_semantics
from analysis_parser import inputs
from tests.workbench.test_review_jobs import ACTOR, SELECTION, isolated_source
from workbench import review_jobs, service


def decision(ident, action, anchor, payload, branch='main'):
    return {'decision_id': ident, 'actor': {'type': 'scripted_fixture', 'id': 'adversarial'},
            'created_at': '2026-09-20T00:00:00Z', 'branch_id': branch,
            'action': action, 'targets': [anchor], 'payload': payload,
            'evidence_refs': ['fixture'], 'reason': 'contract counterexample', 'depends_on': []}


class ReplayAdversarialTests(unittest.TestCase):
    def test_same_facet_conflict_preserves_distinct_valid_facet(self):
        source = packet('置甲量減一，名為乙量')
        anchor = anchor_for(source, 'p', 0, 5)
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'load',
                   'input_slot': 'value', 'formal': '甲量', 'branch_id': 'main'}
        session = new_session(source, 'three-facets')
        for ident, facets in [('day', {'unit': 'day'}), ('month', {'unit': 'month'}),
                              ('duration', {'quantity_kind': 'duration'})]:
            append_decision(session, decision(ident, 'set_quantity_semantics', anchor,
                            {'semantic_input': address, 'facets': facets}), packet=source)
        result = compile_reviewed(source, session)
        status = result['replay']['decision_status']
        self.assertEqual(status['day']['status'], 'conflicted')
        self.assertEqual(status['month']['status'], 'conflicted')
        self.assertEqual(status['duration']['status'], 'active')
        effective = next(iter(result['replay']['effective']['quantity_semantics'].values()))
        self.assertEqual(effective['facets'], {'quantity_kind': 'duration'})

    def test_cross_facet_incompatibility_preserves_noncontributing_assertion(self):
        source = packet('置甲量減一，名為乙量')
        anchor = anchor_for(source, 'p', 0, 5)
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'load',
                   'input_slot': 'value', 'formal': '甲量', 'branch_id': 'main'}
        session = new_session(source, 'cross-facet-contributors')
        for ident, facets in [('day', {'unit': 'day'}), ('month-step', {'step_unit': 'month'}),
                              ('duration', {'quantity_kind': 'duration'})]:
            append_decision(session, decision(ident, 'set_quantity_semantics', anchor,
                            {'semantic_input': address, 'facets': facets}), packet=source)
        result = compile_reviewed(source, session)
        status = result['replay']['decision_status']
        self.assertEqual(status['day']['status'], 'conflicted')
        self.assertEqual(status['month-step']['status'], 'conflicted')
        self.assertEqual(status['duration']['status'], 'active')
        effective = next(iter(result['replay']['effective']['quantity_semantics'].values()))
        self.assertEqual(effective['facets'], {'quantity_kind': 'duration'})

    def test_term_claim_branch_must_match_decision_branch(self):
        source = packet('以日率乘月率')
        session = new_session(source, 'term-branch')
        create_branch(session, 'child')
        anchor = anchor_for(source, 'p', 1, 3)
        with self.assertRaisesRegex(ValueError, 'branch'):
            append_decision(session, decision('wrong-branch', 'set_term_boundary', anchor,
                            {'contract_version': '1.0', 'branch_id': 'child'}, branch='main'),
                            packet=source)
        self.assertEqual(session['decisions'], [])

    def test_quantity_address_branch_must_match_decision_branch(self):
        source = packet('置甲量減一，名為乙量')
        session = new_session(source, 'quantity-branch')
        create_branch(session, 'child')
        anchor = anchor_for(source, 'p', 0, 5)
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'load',
                   'input_slot': 'value', 'formal': '甲量', 'branch_id': 'child'}
        with self.assertRaisesRegex(ValueError, 'branch'):
            append_decision(session, decision('wrong-branch', 'set_quantity_semantics', anchor,
                            {'semantic_input': address, 'facets': {'unit': 'month'}}, branch='main'),
                            packet=source)
        self.assertEqual(session['decisions'], [])

    def test_relation_decision_target_must_be_its_attested_division(self):
        source = sifen_packet()
        session = new_session(source, 'relation-decoy')
        claim = relation_claim(source)
        wrong = claim['definition_anchor']
        with self.assertRaisesRegex(ValueError, 'relation.*target|target.*relation'):
            append_decision(session, decision('decoy', 'approve_reviewed_relation', wrong, claim),
                            packet=source)
        self.assertEqual(session['decisions'], [])

    def test_child_inherits_operational_management_and_local_release_restores_only_child(self):
        source = packet('置甲量減一，名為乙量')
        session = new_session(source, 'managed-branches')
        create_branch(session, 'child')
        anchor = anchor_for(source, 'p', 0, 5)
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'load',
                   'input_slot': 'value', 'formal': '甲量', 'branch_id': 'main'}
        target = normalize_decision_target('set_quantity_semantics', {'semantic_input': address}, [anchor])
        event = {'event_id': 'manage-unit', 'action': 'manage', 'target': anchor,
                 'facet': 'unit', 'branch_id': 'main', 'actor': ACTOR,
                 'created_at': '2026-09-20T00:00:00Z', 'reason': 'own input unit',
                 'semantic_target': target}
        job = {'session': session, 'branch_id': 'child', 'management_events': [event]}
        inherited = compile_reviewed(source, session, 'child', management=review_jobs.management_state(job))
        self.assertNotIn('main:乙量', execute(inherited['graph'], {'甲量': 5})['named_outputs'])
        job['management_events'].append({**event, 'event_id': 'release-child',
                                         'action': 'unmanage', 'branch_id': 'child'})
        released = compile_reviewed(source, session, 'child', management=review_jobs.management_state(job))
        self.assertEqual(execute(released['graph'], {'甲量': 5})['named_outputs']['main:乙量'], 4)
        job['branch_id'] = 'main'
        parent = compile_reviewed(source, session, 'main', management=review_jobs.management_state(job))
        self.assertNotIn('main:乙量', execute(parent['graph'], {'甲量': 5})['named_outputs'])

    def test_managed_undecided_source_binding_cannot_use_automatic_unique_producer(self):
        source = sifen_packet()
        session = new_session(source, 'managed-month-source')
        baseline = compile_reviewed(source, session)['graph']
        self.assertTrue(any(row.get('formal') == '入蔀積月' and row.get('selected_definition_id')
                            for row in baseline['program']['linked']['imports']))
        target = anchor_for(source, 'sifen:39', 6, 11)
        management = [{'event_id': 'own-month-source', 'managed': True, 'facet': 'binding',
                       'target': target, 'branch_id': 'main',
                       'semantic_target': {'kind': 'binding', 'consumer':
                           ['sifen:39', target['reading_id'], 6, 11],
                           'formal': '入蔀積月', 'scope': None}}]
        reviewed = compile_reviewed(source, session, management=management)['graph']
        imports = [row for row in reviewed['program']['linked']['imports']
                   if row.get('formal') == '入蔀積月']
        self.assertTrue(imports)
        self.assertFalse(any(row.get('selected_definition_id') for row in imports))
        self.assertTrue(any(e.get('attributes', {}).get('execution_blocked') == 'unresolved_managed_quantity'
                            for e in reviewed['events']))
        self.assertEqual(reviewed['managed_scopes'][-1]['status'], 'unresolved')
        baseline_import = next(row for row in baseline['program']['linked']['imports'] if row.get('formal') == '入蔀積月')
        producer = next(d for d in baseline['program']['definitions'] if d['id'] == baseline_import['selected_definition_id'])
        span = producer['source_spans'][0]
        producer_anchor = {**anchor_for(source, span['doc_id'], span['start'], span['end']), 'definition_kind': producer['kind']}
        consumer_anchor = {**target, 'definition_kind': 'QueryDef'}
        append_decision(session, decision('bind', 'bind_value', target,
            {'consumer_definition_anchor': consumer_anchor, 'formal': '入蔀積月',
             'producer_definition_anchor': producer_anchor, 'output_port': '積月'}), packet=source)
        selected = compile_reviewed(source, session, management=management)['graph']
        self.assertTrue(any(i.get('formal') == '入蔀積月' and i.get('selected_definition_id')
                            for i in selected['program']['linked']['imports']))
        append_decision(session, decision('undo', 'retract', target, {'decision_id': 'bind'}), packet=source)
        undone = compile_reviewed(source, session, management=management)['graph']
        self.assertFalse(any(i.get('formal') == '入蔀積月' and i.get('selected_definition_id')
                             for i in undone['program']['linked']['imports']))
        released = compile_reviewed(source, session, management=[{**management[0], 'managed': False}])['graph']
        self.assertTrue(any(i.get('formal') == '入蔀積月' and i.get('selected_definition_id')
                            for i in released['program']['linked']['imports']))

    def test_reject_one_machine_candidate_then_adopt_another_same_term(self):
        source = term_packet('日率')
        anchor = anchor_for(source, 'p', 0, 2)
        doc = inputs.documents(source)[0]
        bundle = suggest_term_semantics(doc, term_boundaries=[anchor])
        alternatives = [row for row in bundle['candidates']
                        if row['span']['start'] == 0 and row['span']['end'] == 2
                        and row['constraint_status'] == 'compatible']
        self.assertGreaterEqual(len(alternatives), 2)
        session = new_session(source, 'reject-then-adopt')
        append_decision(session, decision('boundary', 'set_term_boundary', anchor,
                        {'branch_id': 'main', 'contract_version': '1.0'}), packet=source)
        reject = reject_term_candidates(anchor, 'main', [alternatives[0]['id']], bundle)
        adopt = adopt_term_candidate(anchor, 'main', alternatives[1], bundle)
        append_decision(session, decision('reject', 'set_term_interpretation', anchor,
                        {'claim': reject}), packet=source)
        append_decision(session, decision('adopt', 'set_term_interpretation', anchor,
                        {'claim': adopt}), packet=source)
        replay = compile_reviewed(source, session)['replay']
        self.assertEqual(replay['decision_status']['reject']['status'], 'active')
        self.assertEqual(replay['decision_status']['adopt']['status'], 'active')
        self.assertEqual(len(replay['effective']['term_interpretations']), 2)

    def test_rejecting_the_adopted_candidate_is_a_real_conflict(self):
        source = term_packet('日率')
        anchor = anchor_for(source, 'p', 0, 2)
        bundle = suggest_term_semantics(inputs.documents(source)[0], term_boundaries=[anchor])
        candidate = next(row for row in bundle['candidates']
                         if row['span']['start'] == 0 and row['span']['end'] == 2
                         and row['constraint_status'] == 'compatible')
        session = new_session(source, 'reject-adopt-same')
        append_decision(session, decision('boundary', 'set_term_boundary', anchor,
                        {'branch_id': 'main', 'contract_version': '1.0'}), packet=source)
        reject = reject_term_candidates(anchor, 'main', [candidate['id']], bundle)
        adopt = adopt_term_candidate(anchor, 'main', candidate, bundle)
        append_decision(session, decision('reject', 'set_term_interpretation', anchor,
                        {'claim': reject}), packet=source)
        append_decision(session, decision('adopt', 'set_term_interpretation', anchor,
                        {'claim': adopt}), packet=source)
        replay = compile_reviewed(source, session)['replay']
        self.assertEqual(replay['decision_status']['reject']['status'], 'conflicted')
        self.assertEqual(replay['decision_status']['adopt']['status'], 'conflicted')


class ManagementAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        isolated_source(self.root)

    def apply(self, response, **changes):
        return service.apply_review_job_changes(
            self.root, 'adversarial-job', expected_revision=response['job']['revision'],
            expected_digest=response['job_digest'], **changes)

    def test_unmanage_cannot_escape_active_v2_input_assertion_and_preserves_bytes(self):
        selection = {**SELECTION, 'primary_unit_ids': ['sifen:section:38']}
        opened = service.create_review_job(self.root, 'adversarial-job', selection)
        source = opened['packet']
        anchor = anchor_for(source, 'sifen:38', 5, 11)
        address = {'definition_anchor': anchor_for(source, 'sifen:38', 0, 4),
                   'construction_anchor': anchor, 'construction_role': 'load',
                   'semantic_role': 'load', 'input_slot': 'value', 'formal': '入蔀年',
                   'branch_id': 'main', 'invocation_path': [anchor_for(source, 'sifen:38', 0, 4)]}
        payload = {'semantic_input': address, 'facets': {'unit': 'month'}}
        row = decision('month-input', 'set_quantity_semantics', anchor, payload)
        event = {'event_id': 'manage-month', 'action': 'manage', 'target': anchor,
                 'facet': 'unit', 'branch_id': 'main', 'actor': ACTOR,
                 'created_at': '2026-09-20T00:00:00Z', 'reason': 'review input unit',
                 'semantic_target': normalize_decision_target(row['action'], payload, row['targets'])}
        managed = self.apply(opened, decisions=[row], management_events=[event])
        path = review_jobs.job_path(self.root, 'adversarial-job')
        saved_bytes = path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'unmanage_has_active'):
            self.apply(managed, management_events=[{**event, 'event_id': 'release-month',
                                                    'action': 'unmanage'}])
        self.assertEqual(path.read_bytes(), saved_bytes)

    def test_conflicting_submitted_facets_are_not_saved(self):
        selection = {**SELECTION, 'primary_unit_ids': ['sifen:section:38']}
        opened = service.create_review_job(self.root, 'adversarial-job', selection)
        source = opened['packet']
        anchor = anchor_for(source, 'sifen:38', 5, 11)
        address = {'definition_anchor': anchor_for(source, 'sifen:38', 0, 4),
                   'construction_anchor': anchor, 'construction_role': 'load',
                   'semantic_role': 'load', 'input_slot': 'value', 'formal': '入蔀年',
                   'branch_id': 'main', 'invocation_path': [anchor_for(source, 'sifen:38', 0, 4)]}
        first = decision('month-input', 'set_quantity_semantics', anchor,
                         {'semantic_input': address, 'facets': {'unit': 'month'}})
        accepted = self.apply(opened, decisions=[first])
        path = review_jobs.job_path(self.root, 'adversarial-job')
        saved_bytes = path.read_bytes()
        conflicting = decision('day-input', 'set_quantity_semantics', anchor,
                               {'semantic_input': address, 'facets': {'unit': 'day'}})
        with self.assertRaisesRegex(ValueError, 'conflict|invalid'):
            self.apply(accepted, decisions=[conflicting])
        self.assertEqual(path.read_bytes(), saved_bytes)


if __name__ == '__main__':
    unittest.main()
