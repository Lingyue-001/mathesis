"""Reviewed syntax must retain the grammar's exact source grounding."""
import unittest

from analysis_parser.construction_ir import parse_syntax
from analysis_parser.inputs import documents
from analysis_parser.lexical import tokenize_candidates
from analysis_parser.syntax_ir import syntax_from_candidates
from adjudication.anchors import anchor_for
from adjudication.compiler import _manual_candidate
from workbench.annotation_projection import _construction_rows


def parsed(text, lexicon=()):
    document = documents({'primary_documents': [{'doc_id': 'p', 'text': text}]})[0]
    syntax = parse_syntax(tokenize_candidates(document, set(lexicon)), document)
    return document, syntax


class ReviewedSyntaxGroundingTests(unittest.TestCase):
    def test_manual_source_and_literal_slots_keep_their_own_grounding(self):
        """Replacing this with a parent span would falsely join distinct operands."""
        packet = {'schema_version': '3.0', 'primary_documents': [
            {'doc_id': 'p', 'reading_id': 'p.r', 'text': '以日率乘月率', 'edition_edits': []}]}
        parent = anchor_for(packet, 'p', 0, 6)
        left, right = anchor_for(packet, 'p', 1, 3), anchor_for(packet, 'p', 4, 6)
        candidate = _manual_candidate(packet, {'decision_id': 'D1', 'target': parent}, {
            'kind': 'multiply', 'source_anchor': parent,
            'slots': {'left': {'ref_kind': 'source_anchor', 'anchor': left},
                      'right': {'ref_kind': 'source_anchor', 'anchor': right}},
        }, 0, set())
        self.assertEqual(candidate['slots']['left']['source_spans'], [left])
        self.assertEqual(candidate['slots']['left']['analysis_range'], [1, 3])
        self.assertEqual(candidate['slots']['right']['source_spans'], [right])
        self.assertEqual(candidate['slots']['right']['analysis_range'], [4, 6])
        restored = syntax_from_candidates([candidate])
        syntax = {node['id']: node for node in restored.nodes}
        projected = _construction_rows(packet, [candidate], {}, syntax)
        self.assertIsNone(projected[0]['public_kind'])
        self.assertTrue(any(d['kind'] == 'ReviewedCandidateMissingPublicKind' for d in restored.diagnostics))

    def test_manual_literal_slot_keeps_its_evidence_anchor(self):
        packet = {'schema_version': '3.0', 'primary_documents': [
            {'doc_id': 'p', 'reading_id': 'p.r', 'text': '以日率乘三', 'edition_edits': []}]}
        parent = anchor_for(packet, 'p', 0, 5)
        left, literal = anchor_for(packet, 'p', 1, 3), anchor_for(packet, 'p', 4, 5)
        candidate = _manual_candidate(packet, {'decision_id': 'D2', 'target': parent}, {
            'kind': 'multiply', 'source_anchor': parent,
            'slots': {'left': {'ref_kind': 'source_anchor', 'anchor': left},
                      'right': {'ref_kind': 'literal', 'text': '三', 'value': 3, 'evidence_anchor': literal}},
        }, 0, set())
        self.assertEqual(candidate['slots']['right']['source_spans'], [literal])
        self.assertEqual(candidate['slots']['right']['analysis_range'], [4, 5])

    def test_candidate_round_trip_keeps_native_public_kind_and_operand_grounding(self):
        """Removing slot grounding must make this fail, rather than widening it to its parent."""
        _, syntax = parsed('以日率乘月率', ('日率', '月率'))
        candidate = next(row for row in syntax.candidates() if row['kind'] == 'multiply')
        self.assertEqual(candidate['public_kind'], 'Multiply')
        self.assertEqual(candidate['slots']['left']['source_spans'][0]['start'], 1)
        self.assertEqual(candidate['slots']['left']['source_spans'][0]['end'], 3)
        self.assertEqual(candidate['slots']['left']['analysis_range'], [1, 3])
        self.assertEqual(candidate['slots']['right']['source_spans'][0]['start'], 4)
        self.assertEqual(candidate['slots']['right']['source_spans'][0]['end'], 6)
        self.assertEqual(candidate['slots']['right']['analysis_range'], [4, 6])

        restored = syntax_from_candidates([candidate])
        nodes = {node['id']: node for node in restored.nodes}
        parent = nodes[candidate['node_id']]
        left, right = nodes[parent['slots']['left']], nodes[parent['slots']['right']]
        self.assertEqual(parent['kind'], 'Multiply')
        self.assertEqual((left['source_spans'][0]['start'], left['source_spans'][0]['end']), (1, 3))
        self.assertEqual((right['source_spans'][0]['start'], right['source_spans'][0]['end']), (4, 6))
        self.assertEqual((left['analysis_range'], right['analysis_range']), ([1, 3], [4, 6]))

    def test_round_trip_preserves_every_grounded_slot_in_a_multiclause_source(self):
        """A reviewed syntax adapter may not alter unrelated construction grounding."""
        _, syntax = parsed('推天正術。以日率乘月率。滿章法得一。不滿為閏餘。',
                           ('天正術', '日率', '月率', '章法', '閏餘'))
        candidates = syntax.candidates()
        restored = syntax_from_candidates(candidates)
        nodes = {node['id']: node for node in restored.nodes}
        for candidate in candidates:
            parent = nodes[candidate['node_id']]
            self.assertEqual(parent['kind'], candidate['public_kind'])
            for name, slot in candidate['slots'].items():
                if not slot.get('source_spans'):
                    continue
                child = nodes[parent['slots'][name]]
                self.assertEqual(child['source_spans'], slot['source_spans'])
                self.assertEqual(child['analysis_range'], slot['analysis_range'])


if __name__ == '__main__':
    unittest.main()
