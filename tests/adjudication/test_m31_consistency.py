"""M3.1 consistency regressions imported from the independent audit package.

These tests exercise the actual repository packages.  They intentionally
cover contracts across decisions, reviewed syntax, graph derivation and
closure rather than HTTP/UI success alone.
"""
import copy
import hashlib
import json
import unittest

from adjudication import append_decision, compile_reviewed, new_session, create_branch
from adjudication.anchors import anchor_for, semantic_output_address
from adjudication.replay import replay_session
from adjudication.coverage import build_coverage_ledger
from analysis_parser.audit import audit
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from workbench.projection import project_graph


def document(ident, text):
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return {'doc_id': ident, 'reading_id': ident + '.' + digest[:12], 'text': text,
            'text_sha256': digest, 'edition_transcription': text, 'edition_edits': []}


def packet(text, contexts=()):
    return {'schema_version': '3.0', 'packet_id': 'audit',
            'provided_scope': {'tradition': 'Han_Si_fen_li'},
            'primary_documents': [document('p', text)],
            'context_documents': [document('c' + str(i), value) for i, value in enumerate(contexts)]}


def add(packet_value, session, ident, action, target, payload, **extra):
    row = {'decision_id': ident, 'actor': {'type': 'scripted_fixture', 'id': 'combined-audit'},
           'created_at': '2026-09-17T20:00:00Z', 'branch_id': 'main', 'action': action,
           'targets': [target], 'payload': payload, 'evidence_refs': ['audit:synthetic'],
           'reason': 'controlled architecture probe', 'depends_on': []}
    row.update(extra)
    append_decision(session, row, packet=packet_value)


def product_session():
    packet_value = packet('以二乘三。')
    session = new_session(packet_value, 'product')
    anchor = anchor_for(packet_value, 'p', 0, 4)
    add(packet_value, session, 'Q', 'set_quantity_semantics', anchor, {
        'unit': 'integer', 'quantity_kind': 'count',
        'semantic_output': semantic_output_address(packet_value, anchor, anchor, 'multiply', 'result', semantic_role='multiply')})
    return packet_value, session


def order_example(ident):
    packet_value = packet('甲二乙。')
    session = new_session(packet_value, 'order')
    anchor, name_anchor, number_anchor, label_anchor = (
        anchor_for(packet_value, 'p', start, end) for start, end in [(0, 3), (0, 1), (1, 2), (2, 3)])
    add(packet_value, session, 'R', 'declare_parameter', name_anchor,
        {'name': '甲', 'unit': 'integer', 'root_input': True, 'role': 'root_input', 'evidence_basis': 'source'})
    candidates = [
        {'kind': 'load', 'slots': {'value': {'ref_kind': 'root_input', 'label': '甲'}}},
        {'kind': 'multiply', 'slots': {'left': {'ref_kind': 'root_input', 'label': '甲'},
          'right': {'ref_kind': 'literal', 'text': '二', 'evidence_anchor': number_anchor}}},
        {'kind': 'name', 'slots': {'label': {'ref_kind': 'source_anchor', 'anchor': label_anchor}}}]
    add(packet_value, session, ident, 'assemble_known_structure', anchor,
        {'replace_automatic': True, 'candidates': candidates})
    result = compile_reviewed(packet_value, session)
    return {'order': [candidate['kind'] for candidate in result['graph']['construction_candidates']],
            'execution': execute(result['graph'], {'甲': 7})}


class PositiveControls(unittest.TestCase):
    def test_source_anchor_mismatch_rejected(self):
        packet_value = packet('置甲。')
        session = new_session(packet_value, 'anchor')
        anchor = anchor_for(packet_value, 'p', 0, 2)
        anchor['quote'] = 'wrong'
        with self.assertRaises(ValueError):
            add(packet_value, session, 'L', 'set_lexical_role', anchor,
                {'contract_version': '1.0', 'grammatical_role': 'term'})

    def test_numeric_primitive_multiply_still_computes(self):
        packet_value = packet('以二乘三。')
        bundle = compile_reviewed(packet_value, new_session(packet_value, 'number'))
        execution = execute(bundle['graph'], {})
        self.assertFalse(execution['unresolved'])
        self.assertEqual(list(execution['values'].values())[-1], 6)

    def test_retract_restores_graph_without_mutating_source(self):
        packet_value = packet('置甲，以乙乘之。', ['甲，二。', '乙，三。'])
        original = copy.deepcopy(packet_value)
        session = new_session(packet_value, 'retract')
        baseline = compile_reviewed(packet_value, session)['graph']
        anchor = anchor_for(packet_value, 'p', 3, 7)
        add(packet_value, session, 'S', 'resegment', anchor,
            {'segments': [anchor_for(packet_value, 'p', 3, 5), anchor_for(packet_value, 'p', 5, 7)]})
        compile_reviewed(packet_value, session)
        add(packet_value, session, 'R', 'retract', anchor, {'decision_id': 'S'})
        restored = compile_reviewed(packet_value, session)['graph']
        for key in ('events', 'value_instances', 'construction_candidates', 'syntax', 'program'):
            self.assertEqual(baseline[key], restored[key], key)
        self.assertEqual(original, packet_value)

    def test_child_decision_does_not_change_main(self):
        packet_value = packet('置甲。', ['甲，二。'])
        session = new_session(packet_value, 'branch')
        original = compile_reviewed(packet_value, session)['graph']
        create_branch(session, 'child')
        anchor = anchor_for(packet_value, 'p', 0, 1)
        add(packet_value, session, 'L', 'set_lexical_role', anchor,
            {'contract_version': '1.0', 'grammatical_role': 'term'}, branch_id='child')
        self.assertEqual(original, compile_reviewed(packet_value, session, 'main')['graph'])
        exported = json.loads(json.dumps(session, ensure_ascii=False))
        self.assertEqual(compile_reviewed(packet_value, session, 'child'), compile_reviewed(packet_value, exported, 'child'))

    def test_unknown_registry_family_keeps_known_graph(self):
        packet_value = packet('以二乘三。')
        session = new_session(packet_value, 'extension')
        before = compile_reviewed(packet_value, session)['graph']['events']
        anchor = anchor_for(packet_value, 'p', 0, 4)
        add(packet_value, session, 'M', 'assemble_known_structure', anchor, {'replace_automatic': True,
            'candidates': [{'kind': 'new_unimplemented_family', 'slots': {}}]})
        bundle = compile_reviewed(packet_value, session)
        self.assertEqual(before, bundle['graph']['events'])
        self.assertTrue(bundle['graph']['adjudication']['holes'])


class DesiredContractRegressions(unittest.TestCase):
    def test_resegmented_candidates_and_projection_have_current_syntax(self):
        packet_value = packet('置甲，以乙乘之。', ['甲，二。', '乙，三。'])
        session = new_session(packet_value, 'segment')
        before = compile_reviewed(packet_value, session)
        anchor = anchor_for(packet_value, 'p', 3, 7)
        add(packet_value, session, 'S', 'resegment', anchor,
            {'segments': [anchor_for(packet_value, 'p', 3, 5), anchor_for(packet_value, 'p', 5, 7)]})
        bundle = compile_reviewed(packet_value, session)
        graph = bundle['graph']
        ast_ids = {node['id'] for node in graph['syntax']['nodes']}
        missing = [candidate['node_id'] for candidate in graph['construction_candidates'] if candidate['node_id'] not in ast_ids]
        self.assertEqual(missing, [], 'reviewed candidates have no AST nodes')
        self.assertNotEqual(before['graph']['syntax'], graph['syntax'])
        self.assertTrue(project_graph(graph, bundle)['steps'])

    def test_rejected_context_declaration_cannot_supply_old_value(self):
        packet_value = packet('置甲。', ['甲，三。'])
        session = new_session(packet_value, 'context')
        before = compile_reviewed(packet_value, session)
        candidate = next(row for row in before['graph']['construction_candidates'] if row['kind'] == 'declaration')
        anchor = anchor_for(packet_value, 'c0', 0, 3)
        add(packet_value, session, 'R', 'reject_candidate', anchor, {'candidate_id': candidate['node_id']})
        bundle = compile_reviewed(packet_value, session)
        parameters = [event for event in bundle['graph']['events'] if event['kind'] == 'parameter']
        self.assertEqual(parameters, [], 'rejected declaration still produces parameter')
        self.assertTrue(execute(bundle['graph'], {})['unresolved'])

    def test_empty_review_preserves_method_definitions(self):
        packet_value = packet('積日盈六十，除之，數從統首日起。')
        automatic = parse_packet(packet_value)
        reviewed = compile_reviewed(packet_value, new_session(packet_value, 'method'))['graph']
        automatic_ids = [definition['id'] for definition in automatic['program']['definitions'] if definition['kind'] == 'MethodSlice']
        reviewed_ids = [definition['id'] for definition in reviewed['program']['definitions'] if definition['kind'] == 'MethodSlice']
        self.assertEqual(automatic_ids, reviewed_ids)

    def test_manual_sequence_is_independent_of_decision_identifier(self):
        left, right = order_example('D0'), order_example('D2')
        self.assertEqual(left['order'], ['load', 'multiply', 'name'])
        self.assertEqual(left['execution']['named_outputs']['main:乙'], 14)
        self.assertEqual(left['execution']['named_outputs'], right['execution']['named_outputs'])

    def test_context_quantity_decision_is_consumed(self):
        packet_value = packet('置甲。', ['甲，三。'])
        session = new_session(packet_value, 'context-quantity')
        anchor = anchor_for(packet_value, 'c0', 0, 3)
        add(packet_value, session, 'Q', 'set_quantity_semantics', anchor, {'unit': 'integer', 'quantity_kind': 'count',
            'semantic_output': semantic_output_address(packet_value, anchor, anchor, 'declaration', 'result', semantic_role='parameter')})
        bundle = compile_reviewed(packet_value, session)
        value = bundle['graph']['value_instances'][0]
        self.assertEqual(value['unit'], 'integer')
        self.assertIn('Q', value.get('adjudication_decision_refs', []))

    def test_integer_multiply_metadata_is_consistent(self):
        packet_value = packet('以二乘三。')
        bundle = compile_reviewed(packet_value, new_session(packet_value, 'metadata'))
        result = bundle['graph']['value_instances'][-1]
        self.assertEqual(result['unit'], 'integer')
        self.assertEqual(result['quantity_kind'], 'count')
        self.assertEqual(result['resolution_status'], 'resolved')

    def test_same_semantic_binding_conflicts_across_ui_selection_spans(self):
        packet_value = packet('推甲術。置甲。推乙術。置乙。')
        session = new_session(packet_value, 'binding')
        consumer = anchor_for(packet_value, 'p', 0, 3)
        producer = anchor_for(packet_value, 'p', 7, 10)
        payload = {'consumer_definition_anchor': consumer, 'producer_definition_anchor': producer,
                   'formal': '甲', 'output_port': 'left'}
        add(packet_value, session, 'A', 'bind_value', consumer, payload)
        add(packet_value, session, 'B', 'bind_value', anchor_for(packet_value, 'p', 4, 6),
            {**payload, 'output_port': 'right'})
        replay = replay_session(session, packet_value)
        self.assertEqual(replay['decision_status']['A']['status'], 'conflicted')
        self.assertEqual(replay['decision_status']['B']['status'], 'conflicted')

    def test_invalid_manual_replacement_preserves_old_candidate(self):
        packet_value = packet('置甲。', ['甲，三。'])
        session = new_session(packet_value, 'manual-invalid')
        anchor = anchor_for(packet_value, 'p', 0, 2)
        before = compile_reviewed(packet_value, session)['graph']['events']
        add(packet_value, session, 'M', 'assemble_known_structure', anchor, {'replace_automatic': True,
            'candidates': [{'kind': 'load', 'slots': {'value': {'ref_kind': 'root_input', 'label': 'nonexistent'}}}]})
        self.assertEqual(before, compile_reviewed(packet_value, session)['graph']['events'])

    def test_invalid_candidate_selection_is_not_silently_applied(self):
        packet_value = packet('置甲。', ['甲，三。'])
        session = new_session(packet_value, 'bad-candidate')
        anchor = anchor_for(packet_value, 'p', 0, 2)
        before = compile_reviewed(packet_value, session)['graph']['events']
        add(packet_value, session, 'S', 'select_candidate', anchor,
            {'selected_candidate_id': 'not-in-current-candidates', 'candidate_set_complete': True})
        self.assertEqual(before, compile_reviewed(packet_value, session)['graph']['events'])

    def test_empty_selection_payload_rejected_at_append(self):
        packet_value = packet('置甲。')
        session = new_session(packet_value, 'shape')
        anchor = anchor_for(packet_value, 'p', 0, 2)
        with self.assertRaises(ValueError):
            add(packet_value, session, 'E', 'select_candidate', anchor, {})

    def test_scope_frontend_payload_requires_valid_definition_address(self):
        packet_value = packet('推天正術。')
        session = new_session(packet_value, 'scope')
        anchor = anchor_for(packet_value, 'p', 0, 4)
        with self.assertRaises(ValueError):
            add(packet_value, session, 'S', 'set_scope', anchor, {'query_base': 'anything'})

    def test_graph_audit_failure_prevents_closed_status(self):
        packet_value, session = product_session()
        bundle = compile_reviewed(packet_value, session)
        self.assertEqual(bundle['coverage_ledger']['graph_status'], 'closed')
        graph = copy.deepcopy(bundle['graph'])
        target = next(event for event in graph['events'] if event['kind'] == 'multiply')
        del target['reads']['right']
        graph['diagnostics'] = audit(graph)
        ledger = build_coverage_ledger(packet_value, graph, bundle['replay']['effective'], bundle['replay'])
        self.assertNotEqual(ledger['graph_status'], 'closed')

    def test_duplicate_context_attachment_is_idempotent(self):
        packet_value = packet('置甲。', ['甲，三。'])
        session = new_session(packet_value, 'duplicate')
        anchor = anchor_for(packet_value, 'p', 0, 2)
        add(packet_value, session, 'C', 'attach_context', anchor, {'document': packet_value['context_documents'][0]})
        graph = compile_reviewed(packet_value, session)['graph']
        ids = [document['doc_id'] for document in graph['documents']]
        self.assertEqual(len(ids), len(set(ids)))

    def test_extension_request_becomes_explicit_extension_issue(self):
        packet_value = packet('未知句。')
        session = new_session(packet_value, 'extension-request')
        anchor = anchor_for(packet_value, 'p', 0, 3)
        add(packet_value, session, 'E', 'defer', anchor, {'schema_extension_required': True})
        bundle = compile_reviewed(packet_value, session)
        self.assertTrue(any(item['kind'] == 'ontology_extension_required' for item in bundle['review_queue']['items']))
