"""Permanent CR-01/CR-02 regressions copied from the independent review repros.

Run from the worktree root. Tests assert required behavior, so a failing test is
the retained counterexample. No production module or frozen packet is modified.
"""
import copy
import json
from pathlib import Path
import unittest

from analysis_parser.context_compiler import compile_context
from analysis_parser.execution import execute
from analysis_parser.inputs import documents
from analysis_parser.operations import method_body
from analysis_parser.pipeline import parse_packet

HERE = Path(__file__).resolve().parent
OBSERVED = {}


def run_text(text):
    packet = {'schema_version': '3.0', 'primary_documents': [{'doc_id': 'synthetic', 'text': text}]}
    report = parse_packet(packet)
    result = execute(report, {})
    return report, result


def summarize(report, result):
    return {
        'named_outputs': result['named_outputs'],
        'parser_unresolved': report['unresolved'],
        'parser_diagnostics': report['diagnostics'],
        'linked_diagnostics': report['program']['linked']['diagnostics'],
        'execution_unresolved': result['unresolved'],
        'calls': report['program']['calls'],
        'events': report['events'],
    }


class CoreReviewCounterexamples(unittest.TestCase):
    def test_denominator_cannot_cross_procedure_boundary(self):
        text = '推甲課，置十，以二為法，如法得一，名曰甲量．推乙課，置二十，如法得一，名曰乙量．'
        report, result = run_text(text)
        control, control_result = run_text(text.replace('置二十，如法', '置二十，以四為法，如法'))
        OBSERVED['denominator_leak'] = {'input': text, 'actual': summarize(report, result),
            'explicit_second_denominator_control': summarize(control, control_result)}
        self.assertEqual(result['named_outputs']['main:甲量'],5)
        self.assertEqual(control_result['named_outputs']['main:乙量'],5)
        self.assertNotIn('main:乙量', result['named_outputs'],
            'Procedure 2 has no denominator declaration; a missing denominator must block its result.')

    def test_domain_label_cannot_share_accumulator_between_definitions(self):
        text = '推冬至，置三，名曰甲量．推冬至，加二，名曰乙量．'
        report, result = run_text(text)
        neutral, neutral_result = run_text(text.replace('冬至', '甲課'))
        OBSERVED['domain_state_leak'] = {'input': text, 'actual': summarize(report, result),
            'neutral_heading_control': summarize(neutral, neutral_result)}
        self.assertEqual(result['named_outputs']['main:甲量'],3)
        self.assertEqual(neutral_result['named_outputs']['main:甲量'],3)
        self.assertNotIn('main:乙量',neutral_result['named_outputs'])
        self.assertNotIn('main:乙量', result['named_outputs'],
            'Procedure 2 has no accumulator or import: domain label must not supply Procedure 1 state.')

    def test_source_method_preserves_multiply_and_updated_return(self):
        text = '積日盈六十，除之，不盈者名曰大餘，以二乘大餘，名曰大餘，以統首日命之．'
        context = compile_context(documents({'context_documents': [{'doc_id': 'method', 'text': text}]}), [], {})
        self.assertEqual(len(context['method_library']), 1)
        method = context['method_library'][0]
        result = method_body(method['body'], method['returns'], {'offset': 5, 'origin': 1, 'cycle': 60})
        OBSERVED['source_method_multiply'] = {'input': text, 'method': method, 'actual': result,
            'required_count_result': 11, 'derivation': '(5 mod 60) * 2 = 10; cyclic count from 1 is 11'}
        self.assertEqual(result['result'], 11,
            'The count consumes the updated 大餘, whose multiply/name producers cannot be omitted.')

    def test_used_source_method_cannot_hide_hole_rebinding_its_return(self):
        baseline = json.loads(Path('evaluation/rescue-v3_1/development_packets/A01.json').read_text())
        packet = copy.deepcopy(baseline['packet'])
        for doc in packet['context_documents']:
            if doc['doc_id'] == 'ST.2.3':
                doc['text'] = doc['text'].replace('數從統首日起', '未定其法，名曰大餘，數從統首日起')
                for key in ('text_sha256', 'source_sha256', 'edition_transcription', 'edition_sha256'):
                    doc.pop(key, None)
        report = parse_packet(packet)
        result = execute(report, baseline['inputs'])
        baseline_report = parse_packet(baseline['packet'])
        baseline_result = execute(baseline_report, baseline['inputs'])
        def calls(r, x):
            return [{'id': e['id'], 'body': e['attributes']['body'], 'result': x['event_results'].get(e['id'])}
                for e in r['events'] if e['kind'] == 'method_call']
        OBSERVED['source_method_hole'] = {'synthetic_mutation_of_exposed_source_only':
            'Insert 未定其法，名曰大餘， immediately before 數從統首日起 in ST.2.3; old packet unchanged.',
            'syntax_diagnostics': report['program']['diagnostics'],
            'parser_unresolved': report['unresolved'], 'execution_unresolved': result['unresolved'],
            'mutated_calls': calls(report, result), 'baseline_calls': calls(baseline_report, baseline_result)}
        self.assertTrue(report['unresolved'] or result['unresolved'],
            'The used method return 大餘 is rebound from an unsupported operation; calls must not certify closure.')



class AdditionalBoundaries(unittest.TestCase):
    def test_method_cannot_span_heading(self):
        text='推甲課，積日盈六十，除之，不盈者名曰大餘．推乙課，以統首日命之．'
        context=compile_context(documents({'context_documents':[{'doc_id':'boundary','text':text}]}),[],{})
        self.assertFalse(context['method_library'])

    def test_unknown_intervening_method_statement_blocks_execution(self):
        text='積日盈六十，除之，不盈者名曰大餘，未定其法，名曰大餘，以統首日命之．'
        context=compile_context(documents({'context_documents':[{'doc_id':'hole','text':text}]}),[],{})
        self.assertEqual(len(context['method_library']),1)
        with self.assertRaises(ValueError):method_body(context['method_library'][0]['body'],context['method_library'][0]['returns'],{'offset':5,'origin':1,'cycle':60})

    def test_schedule_method_keeps_hole_dependency(self):
        baseline=json.loads(Path('evaluation/rescue-v3_1/development_packets/A02.json').read_text());packet=copy.deepcopy(baseline['packet'])
        for doc in packet['context_documents']:
            if '不盈者數起於天正' in doc['text']:
                doc['text']=doc['text'].replace('以章月除月元餘','未定其法，名曰月元餘，以章月除月元餘')
                for key in ('text_sha256','source_sha256','edition_transcription','edition_sha256'):doc.pop(key,None)
        report=parse_packet(packet);result=execute(report,baseline['inputs'])
        self.assertTrue(result['unresolved'])


class FinalReceiverRegressions(unittest.TestCase):
    def compare_method_and_direct(self,middle,offset):
        from analysis_parser.program_ir import link_entry
        from analysis_parser.scoped import ScopedParser,lower_linked
        text='積日盈六十，除之，不盈者名曰大餘，'+middle+'，以統首日命之．'
        packet={'schema_version':'3.0','primary_documents':[{'doc_id':'boundary','text':text}]}
        method=compile_context(documents(packet),[],{})['method_library'][0]
        result=method_body(method['body'],method['returns'],{'offset':offset,'origin':1,'cycle':60})
        parser=ScopedParser(packet);linked=link_entry(parser.program,parser.program.definitions[0]['id'],{'積日':{'unit':'day'},'統首日':{'unit':'day_index'}})
        report=lower_linked(linked,parser);direct=execute(report,{'積日':offset,'統首日':1})
        self.assertFalse(direct['unresolved'])
        counts=[direct['event_results'][e['id']]['result'] for e in report['events'] if e['kind']=='count']
        self.assertEqual(counts,[result['result']])
        return method,result

    def test_later_cycle_deletion_updates_the_count_receiver(self):
        method,result=self.compare_method_and_direct('大餘滿十除去之',15)
        self.assertEqual(result,{'remainder':5,'result':6})
        reductions=[n for n in method['body'] if n['kind']=='cycle_reduce']
        self.assertEqual(len(reductions),2)
        self.assertEqual(method['returns']['remainder'],reductions[1]['writes']['remainder'])
        count=next(n for n in method['body'] if n['kind']=='count')
        self.assertEqual(count['reads']['offset'],reductions[1]['writes']['remainder'])
        self.assertTrue(any(b['binding_kind']=='receiver_update' and b['value_id']==reductions[1]['writes']['remainder'] for b in method['source_bindings']))

    def test_receiver_writes_and_focus_only_arithmetic_have_distinct_roles(self):
        for source,expected in [('加二於大餘',18),('二其大餘',31),('以二乘大餘，名曰大餘',31),('加二',16)]:
            with self.subTest(source=source):
                method,result=self.compare_method_and_direct(source,15)
                self.assertEqual(result['result'],expected)

    def test_divmod_named_receiver_keeps_remainder_and_quotient_distinct(self):
        from analysis_parser.context_compiler import MethodBuilder
        from analysis_parser.lexical import tokenize_candidates
        from analysis_parser.construction_ir import propose_constructions
        doc=documents({'primary_documents':[{'doc_id':'division','text':'甲量盈四得一．'}]})[0]
        candidate=propose_constructions(tokenize_candidates(doc,{}),doc)[0]
        builder=MethodBuilder({'x':{'unit':'integer'}},'$x');builder.names['甲量']='$x';builder.lower(candidate)
        division=next(n for n in builder.body if n['kind']=='divmod')
        self.assertEqual(builder.names['甲量'],division['writes']['remainder'])
        self.assertEqual(builder.focus,division['writes']['quotient'])
        result=method_body(builder.body,{'whole':builder.focus,'remainder':builder.names['甲量']},{'x':15})
        self.assertEqual(result,{'whole':3,'remainder':3})
