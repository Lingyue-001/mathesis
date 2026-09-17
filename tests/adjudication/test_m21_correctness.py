"""M2.1 red-first contract tests for reviewed compilation."""
import copy
import hashlib
import unittest

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for, semantic_output_address
from adjudication.coverage import build_coverage_ledger
from adjudication.registry import validate_manual_structure, validate_quantity_semantics
from adjudication.replay import replay_session
from adjudication.review_queue import build_review_queue
from adjudication.trace import build_reconstruction_trace
from adjudication.validation import validate_root_parameters
from analysis_parser.state import Environment
from source_adapters.corpus import build_source_packet


def decision(identifier, action, anchor, payload, depends_on=None):
    return {'decision_id': identifier, 'actor': {'type': 'scripted_fixture', 'id': 'm2.1'},
            'created_at': '2026-09-17T00:00:00Z', 'branch_id': 'main', 'action': action,
            'targets': [anchor], 'payload': payload, 'evidence_refs': ['fixture:m2.1'],
            'reason': 'red-first contract fixture', 'depends_on': depends_on or []}


class M21CorrectnessTests(unittest.TestCase):
    def setUp(self):
        self.packet = build_source_packet('.', 'sifen-3-5')['source_packet']
        self.anchor = anchor_for(self.packet, 'sifen:38', 12, 17)

    def test_empty_source_spans_and_unsafe_public_append_are_rejected(self):
        with self.assertRaises(ValueError):
            anchor_for(self.packet, 'sifen:38', 12, 12)
        session = new_session(self.packet, 'm21-public')
        with self.assertRaises(TypeError):
            append_decision(session, decision('d', 'select_candidate', self.anchor,
                                              {'selected_candidate_id': 'sifen:38:ast9'}))

    def test_session_locks_engine_grammar_registry_and_profile_identity(self):
        locks = new_session(self.packet, 'm21-identities')['identity_locks']
        self.assertEqual(set(locks), {'engine', 'grammar', 'registry', 'profiles'})
        self.assertTrue(all(row['sha256'] for row in locks.values()))

    def test_same_candidate_slot_with_distinct_answers_conflicts(self):
        session = new_session(self.packet, 'm21-selection')
        append_decision(session, decision('A', 'select_candidate', self.anchor,
                                          {'selected_candidate_id': 'candidate-A'}), packet=self.packet)
        append_decision(session, decision('B', 'select_candidate', self.anchor,
                                          {'selected_candidate_id': 'candidate-B'}), packet=self.packet)
        replay = replay_session(session, self.packet)
        self.assertEqual(replay['decision_status']['A']['status'], 'conflicted')
        self.assertEqual(replay['decision_status']['B']['status'], 'conflicted')
        append_decision(session, decision('R', 'retract', self.anchor, {'decision_id': 'A'}), packet=self.packet)
        self.assertEqual(replay_session(session, self.packet)['decision_status']['B']['status'], 'active')

    def test_new_binding_on_segmentation_revision_is_active_then_stales_after_retraction(self):
        session = new_session(self.packet, 'm21-revision')
        split = decision('S', 'resegment', self.anchor, {'segments': [anchor_for(self.packet, 'sifen:38', 12, 14),
                                                                       anchor_for(self.packet, 'sifen:38', 14, 17)]})
        append_decision(session, split, packet=self.packet)
        binding = decision('B', 'bind_value', self.anchor, {'consumer_definition_anchor': anchor_for(self.packet, 'sifen:38', 0, 4),
                                                             'producer_definition_anchor': anchor_for(self.packet, 'sifen:38', 0, 4),
                                                             'formal': '章月', 'output_port': '積月'}, depends_on=['S'])
        append_decision(session, binding, packet=self.packet)
        self.assertEqual(replay_session(session, self.packet)['decision_status']['B']['status'], 'active')
        append_decision(session, decision('R', 'retract', self.anchor, {'decision_id': 'S'}), packet=self.packet)
        self.assertEqual(replay_session(session, self.packet)['decision_status']['B']['status'], 'needs_revalidation')

    def test_resegment_recompiles_candidate_region_and_retract_restores_automatic_syntax(self):
        session = new_session(self.packet, 'm21-segments')
        automatic = compile_reviewed(self.packet, session)
        automatic_ids = [row['node_id'] for row in automatic['graph']['construction_candidates']
                         if row['source_spans'][0]['doc_id'] == 'sifen:38' and row['kind'] == 'multiply']
        append_decision(session, decision('S', 'resegment', self.anchor, {'segments': [anchor_for(self.packet, 'sifen:38', 12, 14),
                                                                           anchor_for(self.packet, 'sifen:38', 14, 17)]}), packet=self.packet)
        segmented = compile_reviewed(self.packet, session)
        segmented_ids = [row['node_id'] for row in segmented['graph']['construction_candidates']
                         if row['source_spans'][0]['doc_id'] == 'sifen:38' and row['kind'] == 'multiply']
        self.assertNotEqual(automatic_ids, segmented_ids)
        self.assertNotEqual(automatic['graph']['program']['definitions'], segmented['graph']['program']['definitions'])
        append_decision(session, decision('R', 'retract', self.anchor, {'decision_id': 'S'}), packet=self.packet)
        restored = compile_reviewed(self.packet, session)
        restored_ids = [row['node_id'] for row in restored['graph']['construction_candidates']
                        if row['source_spans'][0]['doc_id'] == 'sifen:38' and row['kind'] == 'multiply']
        self.assertEqual(automatic_ids, restored_ids)

    def test_manual_registry_rejects_missing_or_bogus_slots(self):
        with self.assertRaises(ValueError):
            validate_manual_structure({'candidates': [{'kind': 'multiply', 'slots': {}}]})
        with self.assertRaises(ValueError):
            validate_manual_structure({'candidates': [{'kind': 'multiply', 'slots': {'bogus': {'kind': 'Term', 'text': '甲'}}}]})

    def test_unknown_structure_preserves_known_graph_and_creates_local_hole(self):
        session = new_session(self.packet, 'm21-hole')
        append_decision(session, decision('D', 'assemble_known_structure', self.anchor,
                                          {'candidates': [{'kind': 'not-in-registry', 'slots': {}}]}), packet=self.packet)
        result = compile_reviewed(self.packet, session)
        self.assertIsNotNone(result['graph'])
        self.assertEqual(result['coverage_ledger']['graph_status'], 'partial')
        self.assertTrue(any(item['kind'] == 'ontology_extension_required' for item in result['review_queue']['items']))

    def test_semantic_output_address_and_derived_status_are_not_runtime_id_or_payload_controlled(self):
        with self.assertRaises(ValueError):
            validate_quantity_semantics({'syntax_node_id': 'ast9', 'output_port': 'result',
                                         'unit': 'product', 'resolution_status': 'resolved'})

    def test_uncovered_ledger_span_becomes_located_review_item(self):
        graph = {'diagnostics': [], 'unresolved': [], 'events': [], 'value_instances': [], 'program': {}}
        queue = build_review_queue(graph, {'decision_status': {}}, uncovered=[self.anchor])
        item = next(row for row in queue['items'] if row['kind'] == 'uncovered_source')
        self.assertEqual(item['source_anchors'], [self.anchor])

    def test_trace_keeps_computed_source_and_independent_scholar_comparisons_separate(self):
        span = self.anchor
        graph = {'events': [{'id': 'e1', 'kind': 'literal', 'reads': {}, 'writes': {'result': 'v1'},
                             'source_spans': [span], 'attributes': {'value': 4}}],
                 'value_instances': [{'id': 'v1', 'producer': 'e1', 'output_port': 'result',
                                      'unit': 'integer', 'scale': 1, 'source_spans': [span]}]}
        trace = build_reconstruction_trace(graph, source_attested_values={'e1': 4},
                                           scholarly_reconstructed_values={'e1': 5}, computed_values={'v1': 4})
        comparison = trace['steps'][0]['comparisons']
        self.assertEqual(comparison['computed_vs_source']['status'], 'exact')
        self.assertEqual(comparison['computed_vs_scholar']['status'], 'mismatch')

    def test_semantic_address_includes_emission_role_and_noncomputational_cannot_cover_unknown_text(self):
        address = semantic_output_address(self.packet, anchor_for(self.packet, 'sifen:38', 0, 4),
                                          self.anchor, 'multiply', 'result', semantic_role='multiply')
        self.assertEqual(address['semantic_role'], 'multiply')
        graph = {'events': [], 'value_instances': [], 'diagnostics': [], 'unresolved': [], 'program': {}}
        ledger = build_coverage_ledger(self.packet, graph, {
            'noncomputational': [{'decision_id': 'N', 'target': self.anchor,
                                  'reason': 'unproven commentary'}]})
        self.assertEqual(ledger['graph_status'], 'partial')
        self.assertTrue(any(row['doc_id'] == self.anchor['doc_id'] and row['start'] == self.anchor['start']
                            for row in ledger['unresolved_required_spans']))

    def test_linker_diagnostics_are_reviewed_and_invalid_binding_blocks_closure(self):
        graph = {'events': [], 'value_instances': [], 'diagnostics': [], 'unresolved': [],
                 'program': {'linked': {'diagnostics': [{'kind': 'invalid_review_binding',
                                                         'source_spans': [self.anchor]}]}}}
        queue = build_review_queue(graph, {'decision_status': {}})
        self.assertEqual(queue['items'][0]['kind'], 'invalid_review_binding')
        ledger = build_coverage_ledger(self.packet, graph, {})
        self.assertEqual(ledger['graph_status'], 'invalid')

    def test_downstream_event_inherits_human_provenance_as_mechanically_derived(self):
        report = {'events': [], 'value_instances': [], 'schema_version': '3.0'}
        env = Environment(report, {})
        source = env.value('input', {}, [self.anchor], 'fixture', meta={
            'unit': 'integer', 'adjudication_decision_refs': ['H1'],
            'evidence_basis': 'scholarship', 'decision_origin': 'human_construction'})
        downstream = env.value('load', {'value': source}, [self.anchor], 'fixture', meta={'unit': 'integer'})
        event = report['events'][-1]
        value = env.values[downstream]
        self.assertEqual(event['evidence_status'], 'mechanically_derived')
        self.assertEqual(value['adjudication_decision_refs'], ['H1'])
        self.assertEqual(value['decision_origin'], 'automatic_derivation')

    def test_source_derived_value_cannot_be_declared_as_root_by_omitting_derived_role(self):
        program = type('Program', (), {'definitions': [{
            'id': 'procedure', 'defined_values': {'derived': {'node_id': 'n', 'port': 'result'}},
            'formal_inputs': {'derived': {'uses': ['n']}}}]})()
        issues = validate_root_parameters(program, {'parameters': {
            'derived': {'decision_id': 'P', 'name': 'derived', 'role': 'root_input',
                        'root_input': True, 'evidence_basis': 'source'}}})
        self.assertEqual(issues[0]['kind'], 'invalid_parameter_declaration')

    def test_synthetic_abcd_replays_known_subgraph_and_retains_extension_hole(self):
        text = '推甲術。置元名甲。推乙術。置元名甲。推丙術。置甲。未知。'
        source = {'schema_version': '3.0', 'packet_id': 'm21-abcd', 'primary_documents': [{
            'doc_id': 'abcd', 'reading_id': 'abcd.r', 'text': text,
            'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'edition_transcription': text, 'edition_edits': []}]}
        p1, p2, p3 = (anchor_for(source, 'abcd', 0, 3), anchor_for(source, 'abcd', 9, 12),
                      anchor_for(source, 'abcd', 18, 21))
        a1, a2, c, d = (anchor_for(source, 'abcd', 4, 8), anchor_for(source, 'abcd', 13, 17),
                        anchor_for(source, 'abcd', 22, 24), anchor_for(source, 'abcd', 25, 27))
        session = new_session(source, 'm21-abcd')
        append_decision(session, decision('root', 'declare_parameter', a1,
                                          {'name': '元', 'unit': 'integer', 'root_input': True,
                                           'role': 'root_input', 'evidence_basis': 'source'}), packet=source)
        for decision_id, target, label in (('P1', a1, anchor_for(source, 'abcd', 7, 8)),
                                           ('P2', a2, anchor_for(source, 'abcd', 16, 17))):
            append_decision(session, decision(decision_id, 'assemble_known_structure', target, {
                'replace_automatic': True, 'candidates': [
                    {'kind': 'load', 'slots': {'value': {'ref_kind': 'root_input', 'label': '元'}}},
                    {'kind': 'name', 'slots': {'label': {'ref_kind': 'source_anchor', 'anchor': label}}}]}), packet=source)
        append_decision(session, decision('C', 'assemble_known_structure', c, {
            'replace_automatic': True, 'candidates': [
                {'kind': 'load', 'slots': {'value': {'ref_kind': 'quantity_ref', 'label': '甲'}}}]}), packet=source)
        append_decision(session, decision('D', 'assemble_known_structure', d,
                                          {'candidates': [{'kind': 'unsupported_for_m21', 'slots': {}}]}), packet=source)
        before_binding = compile_reviewed(source, session)
        self.assertTrue(any(row['kind'] == 'producer_or_port_ambiguity' for row in before_binding['review_queue']['items']))
        self.assertEqual(before_binding['coverage_ledger']['graph_status'], 'partial')
        append_decision(session, decision('B', 'bind_value', c, {
            'consumer_definition_anchor': p3, 'producer_definition_anchor': p2,
            'formal': '甲', 'output_port': '甲'}), packet=source)
        reviewed = compile_reviewed(source, session)
        self.assertIsNotNone(reviewed['graph'])
        self.assertTrue(reviewed['graph']['adjudication']['holes'])
        self.assertEqual(reviewed['coverage_ledger']['graph_status'], 'partial')
        append_decision(session, decision('RB', 'retract', c, {'decision_id': 'B'}), packet=source)
        self.assertTrue(any(row['kind'] == 'producer_or_port_ambiguity'
                            for row in compile_reviewed(source, session)['review_queue']['items']))
        append_decision(session, decision('RC', 'retract', c, {'decision_id': 'C'}), packet=source)
        restored = compile_reviewed(source, session)
        self.assertFalse(any(row.get('attributes', {}).get('decision_id') == 'C'
                             for row in restored['graph']['construction_candidates']))

    def test_semantic_output_metadata_targets_only_one_emission_from_a_load_with_decrement(self):
        session = new_session(self.packet, 'm21-emission')
        load_anchor = anchor_for(self.packet, 'sifen:38', 5, 11)
        append_decision(session, decision('S', 'set_quantity_semantics', load_anchor, {
            'semantic_output': {'definition_anchor': anchor_for(self.packet, 'sifen:38', 0, 4),
                                'construction_anchor': load_anchor, 'construction_role': 'load',
                                'semantic_role': 'load', 'output_port': 'result', 'branch_id': 'main'},
            'unit': 'year', 'role': 'reviewed_input'}), packet=self.packet)
        graph = compile_reviewed(self.packet, session)['graph']
        load = next(row for row in graph['events'] if row['kind'] == 'load')
        decrement = next(row for row in graph['events'] if row['kind'] == 'subtract')
        self.assertEqual(load['adjudication_decision_refs'], ['S'])
        self.assertNotIn('adjudication_decision_refs', decrement)

    def test_manual_quantity_reference_must_resolve_to_an_existing_value_or_declaration(self):
        session = new_session(self.packet, 'm21-no-free-reference')
        append_decision(session, decision('F', 'assemble_known_structure', self.anchor, {
            'candidates': [{'kind': 'load', 'slots': {
                'value': {'ref_kind': 'quantity_ref', 'label': 'invented-value'}}}]}), packet=self.packet)
        result = compile_reviewed(self.packet, session)
        self.assertTrue(any(row['kind'] == 'invalid_human_decision' for row in result['review_queue']['items']))

    def test_public_binding_rejects_runtime_definition_ids_without_semantic_anchors(self):
        session = new_session(self.packet, 'm21-binding-address')
        with self.assertRaises(ValueError):
            append_decision(session, decision('B', 'bind_value', self.anchor, {
                'consumer_definition_id': 'def-runtime', 'producer_definition_id': 'def-other',
                'formal': '甲', 'output_port': 'result'}), packet=self.packet)

    def test_literal_slot_requires_a_source_evidence_anchor(self):
        session = new_session(self.packet, 'm21-literal-evidence')
        append_decision(session, decision('L', 'assemble_known_structure', self.anchor, {
            'candidates': [{'kind': 'multiply', 'slots': {
                'left': {'ref_kind': 'literal', 'text': '1'},
                'right': {'ref_kind': 'literal', 'text': '2'}}}]}), packet=self.packet)
        result = compile_reviewed(self.packet, session)
        self.assertTrue(any(row['kind'] == 'invalid_human_decision' for row in result['review_queue']['items']))

    def test_literal_text_must_equal_its_source_evidence_quote(self):
        session = new_session(self.packet, 'm21-literal-match')
        one = anchor_for(self.packet, 'sifen:38', 10, 11)
        append_decision(session, decision('L', 'assemble_known_structure', self.anchor, {
            'candidates': [{'kind': 'multiply', 'slots': {
                'left': {'ref_kind': 'literal', 'text': '999', 'evidence_anchor': one},
                'right': {'ref_kind': 'literal', 'text': '一', 'evidence_anchor': one}}}]}), packet=self.packet)
        result = compile_reviewed(self.packet, session)
        self.assertTrue(any(row['kind'] == 'invalid_human_decision' for row in result['review_queue']['items']))
