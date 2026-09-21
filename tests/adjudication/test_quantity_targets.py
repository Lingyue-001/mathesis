"""Reviewed quantities change real source operations without changing producers."""
import unittest

from adjudication.anchors import anchor_for
from analysis_parser.scoped import ScopedParser, lower_linked
from analysis_parser.program_ir import link_entry
from analysis_parser.execution import execute
from tests.adjudication.test_acceptance_core import packet


MONTH = {'coordinate_kind': 'ordinal', 'index_base': 1,
         'reference_origin': 'current_bu_start',
         'counting_boundary': 'start_of_current_month', 'step_unit': 'month'}


class QuantityTargetsTests(unittest.TestCase):
    def compile(self, facets=None, managed=False, text='置甲量減一，名為乙量', path=None):
        from adjudication.quantity_targets import install_quantity_semantics
        source = packet(text)
        parser = ScopedParser(source)
        candidate = next(c for c in parser.program.syntaxes['p'] if c['kind'] == 'load')
        sp = candidate['source_spans'][0]
        anchor = anchor_for(source, 'p', sp['start'], sp['end'])
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'load',
                   'input_slot': 'value', 'formal': candidate['slots']['value']['text'],
                   'branch_id': 'main', 'invocation_path': path or []}
        decisions = [] if facets is None else [{'semantic_input': address, 'facets': facets, 'decision_id': 'Q'}]
        management = [{'semantic_input': address, 'facet': 'coordinate_kind', 'managed': True}] if managed else []
        issues = install_quantity_semantics(parser, source, parser.program, decisions, management)
        self.assertEqual(issues, [])
        entries = [d['id'] for d in parser.program.definitions if d['kind'] == 'ProcedureDef']
        label = candidate['slots']['value']['text']
        graph = lower_linked(link_entry(parser.program, entries, {label: {'unit': 'unknown'}}), parser)
        return graph, execute(graph, {label: 5})

    def test_neutral_three_states_and_unmanage(self):
        baseline, run = self.compile()
        subtraction = next(e for e in baseline['events'] if e['kind'] == 'subtract')
        self.assertEqual(next(v for v in baseline['value_instances'] if v['id'] == subtraction['writes']['result'])['unit'], 'year')
        self.assertEqual(run['named_outputs']['main:乙量'], 4)
        blocked, run = self.compile(managed=True)
        sub = next(e for e in blocked['events'] if e['kind'] == 'subtract')
        self.assertNotEqual(next(v for v in blocked['value_instances'] if v['id'] == sub['writes']['result'])['unit'], 'year')
        self.assertNotIn('main:乙量', run['named_outputs'])
        positive, run = self.compile(MONTH, managed=True)
        sub = next(e for e in positive['events'] if e['kind'] == 'subtract')
        value = next(v for v in positive['value_instances'] if v['id'] == sub['writes']['result'])
        self.assertEqual((value['unit'], value['coordinate_kind'], value['index_base']), ('month', 'elapsed', 0))
        self.assertEqual(value['adjudication_decision_refs'], ['Q'])
        self.assertEqual(run['named_outputs']['main:乙量'], 4)
        root = next(v for v in positive['value_instances'] if v['role'] == 'external_input')
        self.assertEqual(root['unit'], 'unknown')
        self.assertNotIn('coordinate_kind', root)
        restored, run = self.compile(managed=False)
        self.assertEqual(run['named_outputs']['main:乙量'], 4)
        self.assertEqual(restored['events'], baseline['events'])

    def test_real_year_ordinal_uses_one_source_subtraction(self):
        facets = dict(MONTH, step_unit='year', counting_boundary='start_of_current_year')
        graph, result = self.compile(facets, True, '置入蔀年減一，名為積年')
        subs = [e for e in graph['events'] if e['kind'] == 'subtract']
        self.assertEqual(len(subs), 1)
        value = next(v for v in graph['value_instances'] if v['id'] == subs[0]['writes']['result'])
        self.assertEqual((value['unit'], value['coordinate_kind']), ('year', 'elapsed'))
        self.assertEqual(result['named_outputs']['main:積年'], 4)

    def test_combined_incompatible_facets_rejected(self):
        from adjudication.quantity_targets import combined_quantity_compatibility
        with self.assertRaisesRegex(ValueError, 'unit_step_unit'):
            combined_quantity_compatibility({'unit': 'day', 'step_unit': 'month'})

    def test_two_consumers_in_separate_calls_share_unmodified_producer(self):
        from adjudication.quantity_targets import install_quantity_semantics
        text = '章月五。推天正術。置章月減一，名為乙量。推冬至術。置章月減一，名為丙量'
        source = packet(text)
        parser = ScopedParser(source)
        loads = [c for c in parser.program.syntaxes['p'] if c['kind'] == 'load']
        sp = loads[0]['source_spans'][0]
        anchor = anchor_for(source, 'p', sp['start'], sp['end'])
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'load', 'input_slot': 'value',
                   'formal': '章月', 'branch_id': 'main', 'invocation_path': [anchor]}
        self.assertEqual(install_quantity_semantics(parser, source, parser.program,
                         [{'semantic_input': address, 'facets': MONTH, 'decision_id': 'A'}]), [])
        graph = lower_linked(link_entry(parser.program, [d['id'] for d in parser.program.definitions], {}), parser)
        values = {v['id']: v for v in graph['value_instances']}
        subs = [e for e in graph['events'] if e['kind'] == 'subtract']
        self.assertEqual([values[e['writes']['result']]['unit'] for e in subs], ['month', 'year'])
        self.assertNotEqual(subs[0]['call_id'], subs[1]['call_id'])
        producer = next(e for e in graph['events'] if e['kind'] == 'parameter')
        producer_value = producer['writes']['result']
        local_read = next(e for e in graph['events'] if e['rule_id'] == 'REVIEW_QUANTITY_READ')
        other_load = [e for e in graph['events'] if e['kind'] == 'load'][1]
        self.assertEqual(local_read['reads']['value'], producer_value)
        self.assertEqual(other_load['reads']['value'], producer_value)
        self.assertNotIn('coordinate_kind', values[producer_value])
        result = execute(graph, {})
        self.assertEqual((result['named_outputs']['main:乙量'], result['named_outputs']['main:丙量']), (4, 4))

    def test_incomplete_reviewed_ordinal_blocks_required_subtraction(self):
        graph, result = self.compile({'coordinate_kind': 'ordinal'}, managed=True)
        self.assertNotIn('main:乙量', result['named_outputs'])

    def test_explicit_unknown_does_not_resolve_a_managed_facet(self):
        graph, result = self.compile({'coordinate_kind': 'unknown'}, managed=True)
        self.assertNotIn('main:乙量', result['named_outputs'])
        self.assertEqual(graph['managed_scopes'][0]['status'], 'unresolved')

    def test_input_address_without_actual_consumer_is_rejected(self):
        from adjudication.quantity_targets import install_quantity_semantics
        source = packet('置甲量減一，名為乙量')
        parser = ScopedParser(source)
        anchor = anchor_for(source, 'p', 0, 5)
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'imaginary_operation',
                   'input_slot': 'value', 'formal': '甲量', 'branch_id': 'main'}
        issues = install_quantity_semantics(parser, source, parser.program,
                     [{'semantic_input': address, 'facets': MONTH, 'decision_id': 'bad'}])
        self.assertEqual(issues[0]['decision_id'], 'bad')
        self.assertIn('semantic_input_role_not_supported', issues[0]['reason'])

    def test_output_invocation_scope_and_unrelated_closed_region(self):
        from adjudication.quantity_targets import install_quantity_semantics
        source = packet('章月五。推天正術。置章月減一，名為乙量。推冬至術。置章月減一，名為丙量')
        for approved in (True, False):
            parser = ScopedParser(source)
            anchor = anchor_for(source, 'p', 9, 14)
            address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                       'construction_role': 'load', 'semantic_role': 'subtract',
                       'output_port': 'result', 'branch_id': 'main', 'invocation_path': [anchor]}
            payloads = [{'semantic_output': address, 'facets': {'unit': 'month'}, 'decision_id': 'Q'}] if approved else []
            self.assertEqual(install_quantity_semantics(parser, source, parser.program, payloads,
                [{'semantic_output': address, 'facet': 'unit', 'managed': True}]), [])
            graph = lower_linked(link_entry(parser.program, [d['id'] for d in parser.program.definitions], {}), parser)
            result = execute(graph, {})
            if approved:
                self.assertEqual(result['named_outputs']['main:乙量'], 4)
            else:
                self.assertNotIn('main:乙量', result['named_outputs'])
            self.assertEqual(result['named_outputs']['main:丙量'], 4)
            subs = [e for e in graph['events'] if e['kind'] == 'subtract']
            values = {v['id']: v for v in graph['value_instances']}
            self.assertEqual(values[subs[1]['writes']['result']]['unit'], 'year')
            self.assertEqual(values[subs[0]['writes']['result']]['unit'], 'month' if approved else 'unknown')
        parser = ScopedParser(source)
        address['invocation_path'] = [anchor_for(source, 'p', 25, 30)]
        issues = install_quantity_semantics(parser, source, parser.program,
            [{'semantic_output': address, 'facets': {'unit': 'month'}, 'decision_id': 'wrong_call'}])
        self.assertIn('quantity_invocation_path_not_in_current_graph', issues[0]['reason'])

    def test_relation_hook_applies_fraction_metadata_before_remainder_alias(self):
        source = packet('章月五，蔀月二。置章月，以蔀月除之，餘為小餘')
        baseline = ScopedParser(source).run()
        division = next(e for e in baseline['events'] if e['kind'] == 'cycle_reduce')
        for call_id in (division['call_id'], 'another-call'):
            parser = ScopedParser(source)
            parser.review_relation_output_metadata = [{
                'syntax_node_id': division['syntax_node_id'], 'port': 'remainder',
                'semantic_role': division['kind'], 'call_id': call_id,
                'metadata': {'unit': 'day_fraction', 'scale': {'denominator': division['reads']['divisor']},
                             'representation': {'kind': 'fraction_numerator', 'denominator_id': division['reads']['divisor']},
                             'decision_refs': ['relation'], 'reviewed_quantity': True}}]
            graph = parser.run()
            named = next(v for v in graph['value_instances'] if '小餘' in v['labels'])
            if call_id == division['call_id']:
                self.assertEqual(named['unit'], 'day_fraction')
                self.assertEqual(named['representation']['denominator_id'], division['reads']['divisor'])
                self.assertEqual(named['adjudication_decision_refs'], ['relation'])
            else:
                self.assertNotIn('relation', named.get('adjudication_decision_refs', []))

    def test_reviewed_session_management_adoption_retraction_and_unmanage(self):
        from adjudication import append_decision, compile_reviewed, new_session
        from adjudication.decision_contracts import normalize_decision_target
        source = packet('置甲量減一，名為乙量')
        session = new_session(source, 'quantity-lifecycle')
        anchor = anchor_for(source, 'p', 0, 5)
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'load',
                   'input_slot': 'value', 'formal': '甲量', 'branch_id': 'main', 'invocation_path': [anchor]}
        def add(identifier, action, payload):
            append_decision(session, {'decision_id': identifier, 'actor': {'type': 'scripted_fixture', 'id': 'quantity'},
                'created_at': '2026-09-20T00:00:00Z', 'branch_id': 'main', 'action': action,
                'targets': [anchor], 'payload': payload, 'evidence_refs': ['fixture'], 'reason': 'test', 'depends_on': []}, packet=source)
        add('root', 'declare_parameter', {'name': '甲量', 'unit': 'integer', 'root_input': True,
                                        'role': 'root_input', 'evidence_basis': 'source'})
        def run(management=()):
            result = compile_reviewed(source, session, management=management)
            return result, execute(result['graph'], {'甲量': 5})
        baseline, numeric = run()
        self.assertEqual(numeric['named_outputs']['main:乙量'], 4)
        target = normalize_decision_target('set_quantity_semantics', {'semantic_input': address}, [anchor])
        management = [{'event_id': 'manage', 'managed': True, 'facet': 'coordinate_kind',
                       'semantic_target': target, 'target': anchor, 'branch_id': 'main'}]
        blocked, numeric = run(management)
        self.assertNotIn('main:乙量', numeric['named_outputs'])
        self.assertEqual(blocked['graph']['managed_scopes'][0]['status'], 'unresolved')
        add('month', 'set_quantity_semantics', {'semantic_input': address, 'facets': MONTH})
        positive, numeric = run(management)
        self.assertEqual(positive['replay']['decision_status']['month']['status'], 'active')
        self.assertEqual(numeric['named_outputs']['main:乙量'], 4)
        result_value = next(v for v in positive['graph']['value_instances'] if '乙量' in v['labels'])
        self.assertEqual((result_value['unit'], result_value['coordinate_kind']), ('month', 'elapsed'))
        add('retract', 'retract', {'decision_id': 'month'})
        retracted, numeric = run(management)
        self.assertNotIn('main:乙量', numeric['named_outputs'])
        self.assertEqual(retracted['replay']['decision_status']['month']['status'], 'retracted')
        unmanage = [{**management[0], 'managed': False, 'action': 'unmanage'}]
        restored, numeric = run(unmanage)
        self.assertEqual(numeric['named_outputs']['main:乙量'], 4)
        self.assertEqual(restored['graph']['events'], baseline['graph']['events'])

    def test_cross_decision_compatibility_conflicts_atomically_and_recovers_after_retract(self):
        from adjudication import append_decision, compile_reviewed, new_session
        source = packet('置甲量減一，名為乙量')
        session = new_session(source, 'quantity-conflicts')
        anchor = anchor_for(source, 'p', 0, 5)
        address = {'definition_anchor': anchor, 'construction_anchor': anchor,
                   'construction_role': 'load', 'semantic_role': 'load',
                   'input_slot': 'value', 'formal': '甲量', 'branch_id': 'main'}
        def add(identifier, action, payload):
            append_decision(session, {'decision_id': identifier, 'actor': {'type': 'scripted_fixture', 'id': 'quantity'},
                'created_at': '2026-09-20T00:00:00Z', 'branch_id': 'main', 'action': action,
                'targets': [anchor], 'payload': payload, 'evidence_refs': ['fixture'], 'reason': 'test', 'depends_on': []}, packet=source)
        add('day', 'set_quantity_semantics', {'semantic_input': address, 'facets': {'unit': 'day', 'quantity_kind': 'duration'}})
        add('month', 'set_quantity_semantics', {'semantic_input': address, 'facets': {'step_unit': 'month'}})
        result = compile_reviewed(source, session)
        self.assertEqual({result['replay']['decision_status'][i]['status'] for i in ('day', 'month')}, {'conflicted'})
        self.assertEqual(result['replay']['effective']['quantity_semantics'], {})
        add('retract', 'retract', {'decision_id': 'month'})
        result = compile_reviewed(source, session)
        self.assertEqual(result['replay']['decision_status']['day']['status'], 'active')
        effective = next(iter(result['replay']['effective']['quantity_semantics'].values()))
        self.assertEqual(effective['facets'], {'unit': 'day', 'quantity_kind': 'duration'})

    def test_attested_sifen_35_compiles_and_executes_reviewed_year_coordinate(self):
        from adjudication import append_decision, compile_reviewed, new_session
        from source_adapters.corpus import build_source_packet
        source = build_source_packet('.', 'sifen-3-5')['source_packet']
        parser = ScopedParser(source)
        candidate = next(c for stream in parser.program.syntaxes.values() for c in stream
                         if c['kind'] == 'load' and c['slots']['value']['text'] == '入蔀年')
        span = candidate['source_spans'][0]
        anchor = anchor_for(source, span['doc_id'], span['start'], span['end'])
        session = new_session(source, 'attested-coordinate')
        address = {'definition_anchor': anchor, 'construction_anchor': anchor, 'construction_role': 'load',
                   'semantic_role': 'load', 'input_slot': 'value', 'formal': '入蔀年', 'branch_id': 'main', 'invocation_path': [anchor]}
        for identifier, action, payload in [
            ('root', 'declare_parameter', {'name': '入蔀年', 'unit': 'integer', 'root_input': True, 'role': 'root_input', 'evidence_basis': 'source'}),
            ('year', 'set_quantity_semantics', {'semantic_input': address, 'facets': dict(MONTH, step_unit='year', counting_boundary='start_of_current_year')})]:
            append_decision(session, {'decision_id': identifier, 'actor': {'type': 'scripted_fixture', 'id': 'quantity'},
                'created_at': '2026-09-20T00:00:00Z', 'branch_id': 'main', 'action': action,
                'targets': [anchor], 'payload': payload, 'evidence_refs': ['Cullen Proc 3.5'], 'reason': 'ordinal coordinate', 'depends_on': []}, packet=source)
        result = compile_reviewed(source, session)
        graph = result['graph']
        subtract = next(e for e in graph['events'] if e['kind'] == 'subtract' and e['rule_id'] == 'V3_ORDINAL')
        value = next(v for v in graph['value_instances'] if v['id'] == subtract['writes']['result'])
        self.assertEqual((value['unit'], value['coordinate_kind'], value['index_base']), ('year', 'elapsed', 0))
        self.assertEqual(execute(graph, {'入蔀年': 5})['values'][value['id']], 4)


if __name__ == '__main__':
    unittest.main()
