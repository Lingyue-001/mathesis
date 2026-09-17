import copy,json,unittest
from fractions import Fraction
from analysis_parser.quantity_semantics import check_transition
from analysis_parser.operations import operation
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from test_core_scoped import ROOT,packet

class ScaleControlTests(unittest.TestCase):
    def test_scale_reference_values_are_not_runtime_inputs(self):
        cases=json.loads((ROOT/'handoff_v3/reference/scale_cases.json').read_text())
        for c in cases:
            with self.subTest(case=c['id']):
                if c['kind'] in ('representation_rescale','numerator_arithmetic_only'):
                    i=c['input'];op=c['operation']
                    source={'schema_version':'3.0','primary_documents':[{'doc_id':'synthetic_scale_operation','text':f"以{op['numerator_multiplier']}乘甲。"}],'context_documents':[{'doc_id':'synthetic_value','text':f"甲{i['numerator']}。"}]}
                    report=parse_packet(source);execution=execute(report,{})
                    mult=next(e for e in report['events'] if e['kind']=='multiply');n=execution['values'][mult['writes']['result']];d=op['new_denominator']
                    metadata={'x':{'unit':i['unit'],'representation':{'denominator':i['denominator']}},'y':{'unit':i['unit'],'representation':{'denominator':d}}}
                    checked=check_transition({'kind':'rescale' if c['kind']=='representation_rescale' else 'multiply','reads':{'value':'x'},'writes':{'result':'y'},'attributes':{'factor':op['numerator_multiplier'],'source_operation':mult['id'],'denominator_declaration':True,'evidence':[{'basis':c['basis']}]}},metadata,{})
                    self.assertEqual(checked['transition'],'value_preserving_rescale' if c['expected']['value_preserved'] else 'arithmetic')
                    self.assertEqual(n,c['expected']['numerator']);self.assertEqual(Fraction(n,d)==Fraction(i['numerator'],i['denominator']),c['expected']['value_preserved'])
                elif c['kind']=='missing_model_rate':
                    values={'x':c['input'],'y':{'unit':c['requested_unit']}}
                    checked=check_transition({'kind':'convert','reads':{'value':'x'},'writes':{'result':'y'}},values,{'rate':c['rate']})
                    self.assertEqual(checked['status'],c['expected_status'])
                elif c['kind']=='incompatible_addition':
                    values=dict(zip(('x','y'),c['inputs']))
                    checked=check_transition({'kind':'add','reads':{'left':'x','right':'y'}},values,{})
                    self.assertEqual(checked['status'],c['expected_status'])
                elif c['kind']=='rate_conversion':
                    i=c['input'];rate=c['rate'];out=operation('convert',{'numerator':i['numerator'],'denominator':i['denominator'],'rate_numerator':rate['numerator'],'rate_denominator':rate['denominator'],'output_denominator':c['expected']['denominator']},{'rate':dict(rate,basis=c['basis'])})
                    self.assertEqual(out['result'],{'numerator':c['expected']['numerator'],'denominator':c['expected']['denominator']})
                elif c['kind']=='mixed_duration':
                    out=operation('fraction',{k:c[k] for k in ('whole','numerator','denominator')},{})
                    self.assertEqual([out['result']['numerator'],out['result']['denominator']],c['expected_fraction'])
    def test_legacy_year_scan_has_distinct_repeat_adapter(self):
        p=json.loads((ROOT/'evaluation/handoff-v2/package/runtime_inputs/W03.json').read_text());r=parse_packet(p)
        e=next(e for e in r['events'] if e['kind']=='year_scan')
        self.assertEqual(e['control']['kind'],'Repeat');self.assertEqual(e['control']['test'],'pre');self.assertEqual(e['control']['update']['kind'],'schedule_selected_subtract')
        self.assertEqual(execute(r,{'定見復數':131126})['values'][e['writes']['years']],9)
    def test_rescale_wrong_unit_rejects_even_equal_denominators(self):
        values={'x':{'unit':'day','representation':{'denominator':1539}},'y':{'unit':'du','representation':{'denominator':1539}}}
        self.assertEqual(check_transition({'kind':'rescale','reads':{'value':'x'},'writes':{'result':'y'},'attributes':{'factor':1,'source_operation':'multiply','denominator_declaration':True,'evidence':['source']}},values,{})['status'],'requires_model_rate')
    def test_unrelated_denominator_declaration_does_not_change_moon(self):
        p=packet();before=execute(parse_packet(p),{'epoch_elapsed_years':143129})['task_outputs']['new_moon']
        p['primary_documents'].append({'doc_id':'unrelated','text':'推未知，皆以元為法。'})
        self.assertEqual(execute(parse_packet(p),{'epoch_elapsed_years':143129})['task_outputs']['new_moon'],before)
    def test_local_epoch_identity_is_not_sexagenary_label(self):
        p=packet();p['selected_profiles'].append('instant_lunation');r=parse_packet(p)
        seq=next(e for e in r['events'] if e['kind']=='event_sequence')
        a=execute(r,{'epoch_elapsed_years':0})['values'][seq['writes']['result']]['epoch']
        b=execute(r,{'epoch_elapsed_years':4617})['values'][seq['writes']['result']]['epoch']
        self.assertIsInstance(a,dict);self.assertNotEqual(a,b)

    def test_bd04_same_day_distinct_instants(self):
        from analysis_parser.control_ir import compare_events
        case=json.loads((ROOT/'handoff_v3/reference/boundary_cases.json').read_text())[3]
        result=compare_events(case['qi'],case['moon'],'declared_local_epoch')
        self.assertTrue(result['same_whole_day']);self.assertEqual(result['ordering'],'before')
        self.assertEqual(compare_events(case['qi'],case['moon'])['status'],'requires_external_data')
    def test_bd05_bd06_real_sf_graph(self):
        r=parse_packet(packet('SF'))
        for y,remainder,slot,celestial,civil in [(9411,16,6,5,3),(3,14,10,9,7)]:
            result=execute(r,{'epoch_inclusive_year':y})['task_outputs']
            self.assertEqual(result['new_moon']['intercalation_remainder'],remainder)
            self.assertEqual(tuple(result['intercalation'][k] for k in ('nominal_leap_slot','nominal_leap_celestial_label','nominal_leap_civil_label')),(slot,celestial,civil))
    def test_day_factor_alone_never_establishes_rate(self):
        p=packet();d=next(d for d in p['primary_documents'] if '推正月朔' in d['text']);d['text']=d['text'].replace('以月法乘積月','以章月乘積月')
        r=parse_packet(p);values={v['id']:v for v in r['value_instances']}
        div=next(e for e in r['events'] if e['kind']=='divmod' and e['scope']['task']=='new_moon' and '日法' in values[e['reads']['divisor']]['labels'])
        self.assertEqual(values[div['writes']['quotient']]['unit'],'unknown')
        self.assertEqual(div['attributes']['quantity_transition']['status'],'unknown')
        self.assertNotIn(div['writes']['quotient'],execute(r,{'epoch_elapsed_years':143129})['values'])
    def test_correct_month_day_rate_attached_to_graph(self):
        for tradition in ('ST','SF'):
            r=parse_packet(packet(tradition));events={e['id']:e for e in r['events']}
            conversions=[e for e in r['events'] if e['kind']=='divmod' and e['attributes'].get('quantity_transition',{}).get('transition')=='rate_conversion']
            self.assertTrue(any(e['attributes']['quantity_transition']['rate']['from_unit']=='month' and e['attributes']['quantity_transition']['rate']['to_unit']=='day' for e in conversions))
            for e in conversions:
                self.assertEqual(e['attributes']['quantity_transition']['status'],'resolved');self.assertTrue(e['evidence'])
    def test_intercalation_lag_representation_is_checked(self):
        r=parse_packet(packet());values={v['id']:v for v in r['value_instances']};loop=next(e for e in r['events'] if e['kind']=='repeat');initial=values[loop['reads']['initial']]
        self.assertEqual(initial['unit'],'month_fraction');self.assertEqual(initial['scale']['value'],228)
        self.assertEqual(initial['representation']['kind'],'fraction_numerator')
        producer=next(e for e in r['events'] if e['id']==initial['producer']);self.assertEqual(producer['kind'],'rescale');self.assertEqual(producer['attributes']['transition']['transition'],'value_preserving_rescale')
        p=packet();d=next(d for d in p['primary_documents'] if '加七得一' in d['text']);d['text']=d['text'].replace('以十二乘閏餘','以十一乘閏餘')
        r=parse_packet(p);self.assertTrue(any(e['kind']=='rescale' and e['attributes'].get('execution_blocked') for e in r['events']))
    def test_repeat_body_is_executable_not_annotation(self):
        r=parse_packet(packet());loop=next(e for e in r['events'] if e['kind']=='repeat');body=loop['control']['body']
        self.assertIsInstance(body[0],dict);self.assertEqual(body[0]['kind'],'add')
        loop['control']['body'][0]['reads']['right']='$counter_increment'
        result=execute(r,{'epoch_elapsed_years':143129})
        self.assertEqual(result['values'][loop['writes']['count']],61)
        loop['control']['stop']['operator']='unknown'
        self.assertTrue(any(u['cause']=='execution_error' and u['event_id']==loop['id'] for u in execute(r,{'epoch_elapsed_years':143129})['unresolved']))
