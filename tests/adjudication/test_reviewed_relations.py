"""The bounded Han Si-fen relation must follow the current source graph."""
import copy
import unittest
from unittest.mock import patch

from adjudication import append_decision, compile_reviewed, new_session
from adjudication.anchors import anchor_for
from analysis_parser.audit import audit
from analysis_parser.execution import execute
from analysis_parser import scoped
from source_adapters.corpus import build_source_packet_from_units


def packet(*, parameters=True):
    contexts = ['sifen:section:15', 'sifen:section:16', 'sifen:section:38']
    if parameters:
        contexts = ['sifen:section:14', *contexts, 'sifen:section:19']
    return build_source_packet_from_units(
        '.', 'sifen', ['sifen:section:39'], contexts,
        {'tradition': 'Han_Si_fen_li'},
    )


def relation_claim(source):
    anchor = lambda doc, start, end: anchor_for(source, doc, start, end)
    return {
        'kind': 'month_to_day',
        'definition_anchor': anchor('sifen:39', 0, 5),
        'invocation_path': [anchor('sifen:39', 0, 5)],
        'month_input_anchor': anchor('sifen:39', 6, 11),
        'month_producer_anchor': anchor('sifen:38', 24, 28),
        'multiply_anchor': anchor('sifen:39', 12, 17),
        'division_anchor': anchor('sifen:39', 18, 23),
        'quotient_anchor': anchor('sifen:39', 24, 28),
        'remainder_anchor': anchor('sifen:39', 29, 34),
        'numerator_parameter_anchor': anchor('sifen:19', 0, 12),
        'denominator_parameter_anchor': anchor('sifen:14', 0, 7),
        'tradition': 'Han_Si_fen_li',
        'task': 'new_moon',
        'query': 'main',
        'evidence_refs': ['Cullen Proc. 3.6, §39'],
    }


class ReviewedRelationTests(unittest.TestCase):
    def setUp(self):
        self.packet = packet()
        self.graph = compile_reviewed(self.packet, new_session(self.packet, 'relation-probe'))['graph']
        self.claim = relation_claim(self.packet)

    def resolve(self, graph=None, claim=None, source=None):
        from adjudication.reviewed_relations import resolve_reviewed_relation
        return resolve_reviewed_relation(source or self.packet, graph or self.graph, claim or self.claim)

    def test_proposer_uses_current_graph_evidence_and_preserves_durable_anchors(self):
        from adjudication.reviewed_relations import propose_reviewed_relations
        candidates = propose_reviewed_relations(self.packet, self.graph)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0], self.claim)
        self.resolve(claim=candidates[0])
        missing = packet(parameters=False)
        missing_graph = compile_reviewed(missing, new_session(missing, 'missing-parameters'))['graph']
        self.assertEqual(propose_reviewed_relations(missing, missing_graph), [])

    def test_proposer_withdraws_question_when_current_call_changes(self):
        from adjudication.reviewed_relations import propose_reviewed_relations
        graph = copy.deepcopy(self.graph)
        next(e for e in graph['events'] if e['kind'] == 'multiply'
             and e['source_spans'][0]['doc_id'] == 'sifen:39')['scope']['call_id'] = 'other-call'
        self.assertEqual(propose_reviewed_relations(self.packet, graph), [])

    def test_real_source_operations_resolve_without_new_arithmetic(self):
        result = self.resolve()
        self.assertEqual(result['parameters'], {'numerator': 27759, 'denominator': 940})
        self.assertEqual(result['quotient']['unit'], 'day')
        self.assertEqual(result['remainder']['unit'], 'day_fraction')
        self.assertEqual(result['remainder']['representation']['kind'], 'fraction_numerator')
        self.assertEqual(result['remainder']['representation']['denominator_id'], result['denominator_value_id'])
        self.assertEqual(result['multiply_event_id'], result['source_division']['multiply_event_id'])
        self.assertEqual(len(self.graph['events']), result['preflight_event_count'])
        execution = execute(self.graph, {'入蔀年': 2})
        self.assertEqual(execution['event_results'][result['multiply_event_id']]['result'], 333108)
        self.assertEqual(execution['event_results'][result['division_event_id']],
                         {'quotient': 354, 'remainder': 348})
        self.assertEqual(execution['named_outputs']['main:積日'], 354)
        self.assertEqual(execution['named_outputs']['main:小餘'], 348)

    def test_approval_recompiles_same_arithmetic_with_reviewed_port_provenance(self):
        session = new_session(self.packet, 'relation-approved')
        automatic = compile_reviewed(self.packet, session)['graph']
        append_decision(session, {
            'decision_id': 'relation-39', 'actor': {'type': 'scripted_fixture', 'id': 'relation'},
            'created_at': '2026-09-20T00:00:00Z', 'branch_id': 'main',
            'action': 'approve_reviewed_relation', 'targets': [self.claim['division_anchor']],
            'payload': self.claim, 'evidence_refs': self.claim['evidence_refs'],
            'reason': 'Cullen Proc. 3.6 scoped calibration', 'depends_on': [],
        }, packet=self.packet)
        reviewed = compile_reviewed(self.packet, session)['graph']
        self.assertEqual([e['kind'] for e in reviewed['events']],
                         [e['kind'] for e in automatic['events']])
        division = next(e for e in reviewed['events'] if e['kind'] == 'divmod'
                        and e['source_spans'][0]['start'] == 18
                        and e['source_spans'][0]['doc_id'] == 'sifen:39')
        values = {v['id']: v for v in reviewed['value_instances']}
        self.assertIn('relation-39', values[division['writes']['quotient']].get('adjudication_decision_refs', []))
        remainder = values[division['writes']['remainder']]
        self.assertIn('relation-39', remainder.get('adjudication_decision_refs', []))
        self.assertEqual(remainder['representation']['kind'], 'fraction_numerator')
        self.assertEqual(remainder['representation']['denominator_id'], division['reads']['divisor'])
        numbers = execute(reviewed, {'入蔀年': 2})
        self.assertEqual(numbers['event_results'][division['id']], {'quotient': 354, 'remainder': 348})
        self.assertEqual(numbers['named_outputs']['main:小餘'], 348)

    def test_approved_relation_resolves_division_when_legacy_rate_is_disabled(self):
        """The reviewed claim must control the real division transition, not decorate a legacy result."""
        session = new_session(self.packet, 'relation-without-legacy-rate')
        without_month_day_rate = tuple(rule for rule in scoped.CONTEXTUAL_RATES
                                       if not (rule['numerator_term'] == '蔀日'
                                               and rule['denominator_terms'] == ['蔀月']))
        with patch('analysis_parser.scoped.CONTEXTUAL_RATES', without_month_day_rate):
            automatic = compile_reviewed(self.packet, session)['graph']
            before = next(e for e in automatic['events'] if e['kind'] == 'divmod'
                          and e['source_spans'][0]['doc_id'] == 'sifen:39'
                          and e['source_spans'][0]['start'] == 18)
            self.assertEqual(before['attributes']['quantity_transition']['status'], 'unknown')
            self.assertEqual(before['attributes']['execution_blocked'], 'unknown_quantity_use')
            append_decision(session, {
                'decision_id': 'isolated-relation-39', 'actor': {'type': 'scripted_fixture', 'id': 'relation'},
                'created_at': '2026-09-20T00:00:00Z', 'branch_id': 'main',
                'action': 'approve_reviewed_relation', 'targets': [self.claim['division_anchor']],
                'payload': self.claim, 'evidence_refs': self.claim['evidence_refs'],
                'reason': 'Cullen Proc. 3.6 isolated legacy-rate test', 'depends_on': [],
            }, packet=self.packet)
            reviewed = compile_reviewed(self.packet, session)['graph']
            division = next(e for e in reviewed['events'] if e['kind'] == 'divmod'
                            and e['source_spans'][0]['doc_id'] == 'sifen:39'
                            and e['source_spans'][0]['start'] == 18)
            self.assertEqual(division['attributes']['quantity_transition']['status'], 'resolved')
            self.assertEqual(division['attributes']['quantity_transition']['transition'], 'reviewed_month_to_day_relation')
            self.assertNotIn('execution_blocked', division['attributes'])
            numbers = execute(reviewed, {'入蔀年': 2})
        self.assertFalse(any(row['event_id'] == division['id'] for row in numbers['unresolved']))
        self.assertEqual(numbers['event_results'][division['id']], {'quotient': 354, 'remainder': 348})

    def test_changed_parameter_or_call_requires_revalidation(self):
        graph = copy.deepcopy(self.graph)
        numerator = next(v for v in graph['value_instances'] if '蔀日' in v['labels'])
        next(e for e in graph['events'] if e['id'] == numerator['producer'])['attributes']['value'] = 27760
        with self.assertRaisesRegex(ValueError, 'parameter'):
            self.resolve(graph)
        graph = copy.deepcopy(self.graph)
        next(e for e in graph['events'] if e['kind'] == 'multiply' and e['scope'].get('call_id') == 'call-2')['scope']['call_id'] = 'other-call'
        with self.assertRaisesRegex(ValueError, 'call|scope'):
            self.resolve(graph)

    def test_month_count_must_keep_its_reviewed_source_producer(self):
        graph = copy.deepcopy(self.graph)
        source = next(e for e in graph['events'] if e['kind'] == 'alias'
                      and e['attributes'].get('label') == '積月')
        source['source_spans'] = [self.claim['quotient_anchor']]
        with self.assertRaisesRegex(ValueError, 'month_source'):
            self.resolve(graph)

    def test_changed_source_reading_or_operation_ports_requires_revalidation(self):
        source = copy.deepcopy(self.packet)
        source['context_documents'][0]['text'] = '蔀月，九百四十一。'
        with self.assertRaisesRegex(ValueError, 'stale_source_anchor'):
            self.resolve(source=source)
        graph = copy.deepcopy(self.graph)
        division = next(e for e in graph['events'] if e['kind'] == 'divmod' and e['scope'].get('call_id') == 'call-2')
        division['writes']['quotient'], division['writes']['remainder'] = division['writes']['remainder'], division['writes']['quotient']
        with self.assertRaisesRegex(ValueError, 'port|invariant'):
            self.resolve(graph)

    def test_graph_invariant_cannot_be_waived_by_relation(self):
        graph = copy.deepcopy(self.graph)
        alias = next(e for e in graph['events'] if e['kind'] == 'alias' and e['attributes'].get('label') == '小餘')
        division = next(e for e in graph['events'] if e['kind'] == 'divmod' and e['scope'].get('call_id') == 'call-2')
        alias['reads']['value'] = division['writes']['quotient']
        self.assertIn('remainder_producer_corruption', {d['kind'] for d in audit(graph)})
        with self.assertRaisesRegex(ValueError, 'invariant|remainder'):
            self.resolve(graph)


class RemainderProducerRegression(unittest.TestCase):
    def test_unknown_unit_keeps_real_remainder_port_and_execution_block(self):
        source = packet(parameters=False)
        graph = compile_reviewed(source, new_session(source, 'producer-probe'))['graph']
        events = graph['events']
        division = next(e for e in events if e['kind'] == 'divmod' and e['source_spans'][0]['doc_id'] == 'sifen:39')
        alias = next(e for e in events if e['kind'] == 'alias' and e['attributes'].get('label') == '小餘')
        self.assertEqual(alias['reads']['value'], division['writes']['remainder'])
        self.assertEqual(division['attributes']['execution_blocked'], 'unknown_quantity_use')
        self.assertNotIn('remainder_producer_corruption', {d['kind'] for d in graph['diagnostics']})


if __name__ == '__main__':
    unittest.main()
