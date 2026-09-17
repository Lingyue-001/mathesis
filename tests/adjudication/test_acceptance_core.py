import hashlib
import unittest

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for, anchor_key
from adjudication.validation import validate_comparison_operands, validate_control_coverage
from analysis_parser.program_ir import ProgramIndex, link_entry


def packet(text, packet_id='p'):
    return {'schema_version': '3.0', 'packet_id': packet_id, 'provided_scope': {'tradition': 'Han_Si_fen_li'},
            'primary_documents': [{'doc_id': 'p', 'reading_id': 'p.r', 'text': text,
                                   'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                                   'edition_transcription': text, 'edition_edits': []}]}


def decision(packet_value, decision_id, action, target, payload):
    return {'decision_id': decision_id, 'actor': {'type': 'scripted_fixture', 'id': 'acceptance'},
            'created_at': '2026-09-17T00:00:00Z', 'branch_id': 'main', 'action': action,
            'targets': [target], 'payload': payload, 'evidence_refs': ['fixture'], 'reason': 'test', 'depends_on': []}


def append_fixture(source, session, row):
    return append_decision(session, row, packet=source)


class TestAcceptanceCore(unittest.TestCase):
    def test_H03_same_quote_has_distinct_stable_source_address(self):
        source = packet('甲甲。')
        self.assertNotEqual(anchor_key(anchor_for(source, 'p', 0, 1)), anchor_key(anchor_for(source, 'p', 1, 2)))

    def test_H05_H13_manual_segmentation_and_known_structure_use_existing_lowerer(self):
        source = packet('推術。', 'manual')
        anchor = anchor_for(source, 'p', 0, 2)
        session = new_session(source, 'manual')
        append_fixture(source, session, decision(source, 'root', 'declare_parameter', anchor,
                                                  {'name': '甲', 'unit': 'integer', 'root_input': True,
                                                   'role': 'root_input', 'evidence_basis': 'source'}))
        append_fixture(source, session, decision(source, 'split-and-build', 'assemble_known_structure', anchor, {
            'replace_automatic': True, 'candidates': [
                {'kind': 'task_marker', 'slots': {'marker': {'ref_kind': 'source_anchor', 'anchor': anchor},
                                                   'target': {'ref_kind': 'source_anchor', 'anchor': anchor}}},
                {'kind': 'load', 'slots': {'value': {'ref_kind': 'root_input', 'label': '甲'}}},
            ]}))
        result = compile_reviewed(source, session)
        self.assertEqual([row['kind'] for row in result['graph']['events']], ['input', 'load'])
        self.assertEqual(result['graph']['events'][1]['production_id'], 'ADJUDICATION_MANUAL_V1')

    def test_H06_manual_node_can_have_two_attested_spans(self):
        source = packet('推術甲。', 'multispan')
        first, second = anchor_for(source, 'p', 0, 2), anchor_for(source, 'p', 2, 3)
        session = new_session(source, 'multispan')
        append_fixture(source, session, decision(source, 'm', 'assemble_known_structure', first, {
            'candidates': [{'kind': 'task_marker', 'source_anchors': [first, second],
                            'slots': {'marker': {'ref_kind': 'source_anchor', 'anchor': first},
                                      'target': {'ref_kind': 'source_anchor', 'anchor': second}}}]}))
        result = compile_reviewed(source, session)
        node = next(row for row in result['graph']['construction_candidates'] if row['production_id'] == 'ADJUDICATION_MANUAL_V1')
        self.assertEqual(len(node['source_spans']), 2)

    def test_H07_scope_changes_program_frame_before_linking(self):
        source = packet('推天正術。推天正術。', 'scope')
        first, second = anchor_for(source, 'p', 0, 4), anchor_for(source, 'p', 5, 9)
        session = new_session(source, 'scope')
        append_fixture(source, session, decision(source, 'scope-1', 'set_scope', second,
                                                  {'definition_anchor': second, 'parent_definition_anchor': first}))
        result = compile_reviewed(source, session)
        definitions = result['graph']['program']['definitions']
        parent = next(row for row in definitions if any(span['start'] == 0 for span in row['source_spans']))
        child = next(row for row in definitions if any(span['start'] == 5 for span in row['source_spans']))
        self.assertEqual(child['parent'], parent['id'])

    def test_H09_scope_parent_cycle_is_rejected(self):
        source = packet('推天正術。推天正術。', 'scope-cycle')
        first, second = anchor_for(source, 'p', 0, 4), anchor_for(source, 'p', 5, 9)
        session = new_session(source, 'scope-cycle')
        append_fixture(source, session, decision(source, 'one', 'set_scope', first,
                                                  {'definition_anchor': first, 'parent_definition_anchor': second}))
        append_fixture(source, session, decision(source, 'two', 'set_scope', second,
                                                  {'definition_anchor': second, 'parent_definition_anchor': first}))
        with self.assertRaisesRegex(ValueError, 'scope_parent_cycle'):
            compile_reviewed(source, session)

    def test_H08_required_control_cannot_be_noncomputational_for_complete_export(self):
        source = packet('十二以上。')
        control = anchor_for(source, 'p', 0, 4)
        graph = {'events': [{'id': 'e', 'kind': 'threshold', 'source_spans': [control]}]}
        issues = validate_control_coverage(graph, {'noncomputational': [{'decision_id': 'n', 'target': control}]})
        self.assertEqual(issues[0]['kind'], 'required_control_marked_noncomputational')

    def test_H10_linker_obeys_verified_producer_port_constraint(self):
        index = ProgramIndex()
        index.definitions = [
            {'id': 'consumer', 'kind': 'ProcedureDef', 'source_role': 'primary', 'parent': None,
             'source_spans': [], 'defined_values': {}, 'return_ports': {}, 'free_variables': {}},
            {'id': 'left', 'kind': 'ProcedureDef', 'source_role': 'primary', 'parent': None,
             'source_spans': [], 'defined_values': {'甲': {'node_id': 'left-name', 'port': 'result'}},
             'return_ports': {'甲': {'node_id': 'left-name', 'port': 'result'}}, 'free_variables': {}},
            {'id': 'right', 'kind': 'ProcedureDef', 'source_role': 'primary', 'parent': None,
             'source_spans': [], 'defined_values': {'甲': {'node_id': 'right-name', 'port': 'result'}},
             'return_ports': {'甲': {'node_id': 'right-name', 'port': 'result'}}, 'free_variables': {}},
        ]
        index.syntaxes = {'p': [
            {'node_id': 'use', 'definition_id': 'consumer', 'kind': 'load', 'slots': {'value': {'kind': 'Term', 'text': '甲'}}, 'source_spans': []},
            {'node_id': 'left-name', 'definition_id': 'left', 'kind': 'name', 'slots': {'label': {'kind': 'Term', 'text': '甲'}}, 'source_spans': []},
            {'node_id': 'right-name', 'definition_id': 'right', 'kind': 'name', 'slots': {'label': {'kind': 'Term', 'text': '甲'}}, 'source_spans': []},
        ]}
        index.binding_constraints = {('consumer', '甲'): {'producer_definition_id': 'right', 'output_port': '甲'}}
        linked = link_entry(index, 'consumer', {})
        self.assertEqual(linked.imports[0]['selected_definition_id'], 'right')
        self.assertEqual(linked.imports[0]['selected_port'], '甲')

    def test_H21_H22_H23_type_evidence_and_time_origin_guards(self):
        self.assertEqual(validate_comparison_operands({'unit': 'day', 'epoch': 'a'}, {'unit': 'day', 'epoch': 'b'})['kind'],
                         'incompatible_time_origin')
        self.assertEqual(validate_comparison_operands({'unit': 'day'}, {'unit': 'month'})['kind'], 'incompatible_units')

    def test_H11_H12_candidate_correction_and_truncation_cannot_silently_close(self):
        source = packet('推術。', 'candidate')
        anchor = anchor_for(source, 'p', 0, 2)
        session = new_session(source, 'candidate')
        append_fixture(source, session, decision(source, 'c1', 'select_candidate', anchor,
                                                  {'selected_candidate_id': 'not-the-only-candidate', 'candidate_set_complete': False,
                                                   'candidate_count': 9}))
        result = compile_reviewed(source, session)
        self.assertIsNotNone(result['graph'])
        self.assertEqual(result['coverage_ledger']['graph_status'], 'partial')
