"""K2-B effect tests for exact local terms and bounded interpretations."""
import hashlib
from copy import deepcopy
import unittest

from adjudication.anchors import anchor_for
from adjudication import append_decision, compile_reviewed, new_session
from adjudication.term_claims import (
    adopt_term_candidate,
    apply_term_interpretations,
    compose_term_interpretation,
    parse_with_term_boundaries,
    revalidate_term_interpretation,
    reject_term_candidates,
    term_tokens,
)
from analysis_parser import inputs, lexical
from analysis_parser.scoped import ScopedParser
from domain_kernel.engine import suggest_term_semantics


def packet(text):
    return {'schema_version': '3.0', 'packet_id': 'term-probe',
            'provided_scope': {'tradition': 'Han_Si_fen_li'},
            'primary_documents': [{'doc_id': 'p', 'reading_id': 'p.r', 'text': text,
                                   'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                                   'edition_transcription': text, 'edition_edits': []}]}


class TestTermClaims(unittest.TestCase):
    def test_reviewed_compiler_boundary_changes_real_construction_then_retracts(self):
        source = packet('以日率乘月率')
        left = anchor_for(source, 'p', 1, 3)
        right = anchor_for(source, 'p', 4, 6)
        session = new_session(source, 'term-compiler')
        def append(ident, action, target, payload):
            append_decision(session, {'decision_id': ident, 'actor': {'type': 'scripted_fixture', 'id': 'term'},
                                      'created_at': '2026-09-20T00:00:00Z', 'branch_id': 'main',
                                      'action': action, 'targets': [target], 'payload': payload,
                                      'evidence_refs': ['fixture'], 'reason': 'test', 'depends_on': []}, packet=source)
        baseline = compile_reviewed(source, session)
        self.assertFalse(any(row['kind'] == 'multiply' for row in baseline['graph']['construction_candidates']))
        append('left', 'set_term_boundary', left, {'contract_version': '1.0', 'branch_id': 'main'})
        append('right', 'set_term_boundary', right, {'contract_version': '1.0', 'branch_id': 'main'})
        reviewed = compile_reviewed(source, session)
        multiplies = [row for row in reviewed['graph']['construction_candidates'] if row['kind'] == 'multiply']
        self.assertEqual(len(multiplies), 1)
        self.assertEqual(multiplies[0]['slots']['left']['text'], '日率')
        self.assertEqual(multiplies[0]['slots']['right']['text'], '月率')
        append('retract-right', 'retract', right, {'decision_id': 'right'})
        # 月率 already has a native local edge; 日率 is the decisive intervention.
        self.assertTrue(any(row['kind'] == 'multiply' for row in
                            compile_reviewed(source, session)['graph']['construction_candidates']))
        append('retract-left', 'retract', left, {'decision_id': 'left'})
        restored = compile_reviewed(source, session)
        self.assertFalse(any(row['kind'] == 'multiply' for row in restored['graph']['construction_candidates']))

    def test_two_boundaries_recover_real_multiply_and_retract_restores_automatic(self):
        source = packet('以日率乘月率')
        doc = inputs.documents(source)[0]
        left = anchor_for(source, 'p', 1, 3)
        right = anchor_for(source, 'p', 4, 6)
        automatic = parse_with_term_boundaries(doc, [])
        reviewed = parse_with_term_boundaries(doc, [left, right])
        self.assertFalse(any(c['kind'] == 'multiply' for c in automatic.candidates()))
        multiply = [c for c in reviewed.candidates() if c['kind'] == 'multiply']
        self.assertEqual(len(multiply), 1)
        self.assertEqual(multiply[0]['slots']['left']['text'], '日率')
        self.assertEqual(multiply[0]['slots']['right']['text'], '月率')
        self.assertEqual(parse_with_term_boundaries(doc, []).to_dict(), automatic.to_dict())
        self.assertEqual(term_tokens(doc, []), lexical.tokenize_candidates(doc, {}))
        self.assertNotIn('日率', lexical.TERMS)
        self.assertNotIn('月率', lexical.TERMS)

    def test_one_occurrence_and_revalidation_does_not_self_prove(self):
        source = packet('日率，日率')
        doc = inputs.documents(source)[0]
        first = anchor_for(source, 'p', 0, 2)
        second = anchor_for(source, 'p', 3, 5)
        bundle = suggest_term_semantics(doc, term_boundaries=[first])
        candidates = [c for c in bundle['candidates'] if c['span']['start'] == 0 and c['span']['end'] == 2]
        self.assertGreaterEqual(len(candidates), 2)
        self.assertFalse(any(c['span']['start'] == 3 and c['span']['end'] == 5 and c['constraint_status'] == 'compatible'
                             for c in bundle['candidates']))
        claim = adopt_term_candidate(first, 'main', candidates[0], bundle)
        self.assertEqual(claim['origin'], 'machine_adoption')
        self.assertEqual(claim['expression'], candidates[0]['expression'])
        self.assertEqual(revalidate_term_interpretation(claim, source, term_boundaries=[first])['status'], 'valid')
        forged = deepcopy(claim)
        forged['expression'] = candidates[1]['expression']
        self.assertEqual(revalidate_term_interpretation(forged, source, term_boundaries=[first])['status'],
                         'needs_revalidation')
        self.assertEqual(revalidate_term_interpretation(claim, source, term_boundaries=[])['status'], 'needs_revalidation')
        self.assertNotEqual(first['start'], second['start'])

    def test_reject_and_human_composition_stays_in_registry_without_numbers(self):
        source = packet('日率')
        anchor = anchor_for(source, 'p', 0, 2)
        doc = inputs.documents(source)[0]
        bundle = suggest_term_semantics(doc, term_boundaries=[anchor])
        ids = [c['id'] for c in bundle['candidates'] if c['span']['start'] == 0 and c['span']['end'] == 2]
        rejected = reject_term_candidates(anchor, 'main', ids[:1], bundle)
        self.assertEqual(rejected['origin'], 'machine_rejection')
        self.assertEqual(rejected['candidate_ids'], ids[:1])
        expression = {'op': 'accumulation', 'arguments': {'quantity': {
            'op': 'rate_for', 'arguments': {'associate': {'op': 'concept', 'concept_id': 'body.sun'}}}}}
        self.assertNotIn(expression, [candidate['expression'] for candidate in bundle['candidates']])
        human = compose_term_interpretation(anchor, 'main', expression)
        self.assertEqual(human['origin'], 'human_composition')
        self.assertEqual(revalidate_term_interpretation(human, source, term_boundaries=[anchor])['status'], 'valid')
        with self.assertRaises(ValueError):
            compose_term_interpretation(anchor, 'main', {'op': 'concept', 'concept_id': 'invented'})
        with self.assertRaises(ValueError):
            compose_term_interpretation(anchor, 'main', {'op': 'number', 'value': 27759})

    def test_interpretation_attaches_to_exact_nominal_slot_without_numeric_fact(self):
        source = packet('以日率乘月率')
        left = anchor_for(source, 'p', 1, 3)
        right = anchor_for(source, 'p', 4, 6)
        doc = inputs.documents(source)[0]
        bundle = suggest_term_semantics(doc, term_boundaries=[left, right])
        candidate = next(c for c in bundle['candidates'] if c['span']['start'] == 1 and c['span']['end'] == 3)
        claim = adopt_term_candidate(left, 'main', candidate, bundle)
        parser = ScopedParser(source)
        from adjudication.term_claims import prepare_term_parser
        prepare_term_parser(parser, [{'target': left}, {'target': right}])
        apply_term_interpretations(parser, [{'decision_id': 'sense', 'claim': claim}])
        multiply = next(c for c in parser.all_candidates['p'] if c['kind'] == 'multiply')
        senses = multiply['attributes']['reviewed_term_interpretations']
        self.assertEqual(len(senses), 1)
        self.assertEqual(senses[0]['slot'], 'left')
        self.assertEqual(senses[0]['expression'], claim['expression'])
        self.assertNotIn('value', senses[0])


if __name__ == '__main__':
    unittest.main()
