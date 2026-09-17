import copy,json,unittest
from fractions import Fraction
from pathlib import Path
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from analysis_parser.control_ir import boundary_membership
from test_core_scoped import packet,ROOT

def synthetic(text,context=(),profiles=()):
    return {'schema_version':'3.0','selected_profiles':list(profiles),'provided_scope':{'tradition':'synthetic'},'primary_documents':[{'doc_id':'synthetic','text':text}],'context_documents':[{'doc_id':'context'+str(i),'text':x} for i,x in enumerate(context)]}

class MechanismTests(unittest.TestCase):
    def test_repeat_variable_increment_and_equality(self):
        for profile,inc,count,last in [('ST_intercalation_Cullen_Liu_GT',7,2,235),('ST_intercalation_GE_contrast',7,1,228),('ST_intercalation_Cullen_Liu_GT',5,2,231)]:
            p=synthetic(f'置甲，加{inc}得一．盈乙，數所得。',['甲二百二十一。','乙二百二十八。'],[profile])
            r=parse_packet(p);x=execute(r,{})
            loops=[e for e in r['events'] if e['kind']=='repeat'];self.assertEqual(len(loops),1)
            self.assertEqual(x['values'][loops[0]['writes']['count']],count);self.assertEqual(x['values'][loops[0]['writes']['state']],last)
    def test_repeat_pre_zero_post_one(self):
        p=synthetic('置甲，加七得一．盈乙，數所得。',['甲二百三十。','乙二百二十八。'],['ST_intercalation_Cullen_Liu_GT'])
        r=parse_packet(p);e=next(e for e in r['events'] if e['kind']=='repeat')
        self.assertEqual(execute(r,{})['values'][e['writes']['count']],1)
        e['attributes']['control']['test']='pre'
        self.assertEqual(execute(r,{})['values'][e['writes']['count']],0)
    def test_context_method_actual_winter_args(self):
        p=packet();moon=[d for d in p['primary_documents'] if '推正月朔' in d['text']]
        p['primary_documents']=[d for d in p['primary_documents'] if '推日月元統' in d['text'] or '推冬至' in d['text']];p['context_documents']+=moon
        r=parse_packet(p);x=execute(r,{'epoch_elapsed_years':143129})
        self.assertEqual(x['task_outputs']['winter']['winter_day'],11)
        call=next(e for e in r['events'] if e['kind']=='method_call')
        values={v['id']:v for v in r['value_instances']}
        self.assertEqual(values[call['reads']['offset']]['scope']['task'],'winter')
        self.assertTrue(call['method_binding']);self.assertEqual([n['kind'] for n in r['method_library'][0]['body']],['cycle_reduce','count'])
        r['method_library']=[];self.assertTrue(any(u['cause']=='execution_error' for u in execute(r,{'epoch_elapsed_years':143129})['unresolved']))
    def test_method_ambiguity_and_wrong_unit(self):
        p=packet();moon=next(d for d in p['primary_documents'] if '推正月朔' in d['text'])
        extra=copy.deepcopy(moon);extra['doc_id']='conflict';extra['text']=extra['text'].replace('盈六十','盈五十');p['context_documents'].append(extra)
        r=parse_packet(p);self.assertTrue(any(u['cause']=='interpretive_ambiguity' and 'method' in str(u) for u in r['unresolved']))
        p=packet();p['context_documents'].append({'doc_id':'angular','text':'積度盈六十，除之，數從角首起。'})
        r=parse_packet(p);self.assertTrue(any(m['formal_inputs']['offset']['unit']=='du' for m in r['method_library']))
        self.assertEqual(execute(r,{'epoch_elapsed_years':143129})['task_outputs']['winter']['winter_day'],11)
    def test_query_base_not_nodes_and_explicit_recurrence(self):
        p=packet();base=execute(parse_packet(p),{'epoch_elapsed_years':143129})['task_outputs']['qi']
        d=p['primary_documents'][-1];d['text']=d['text'].replace('求八節，加大餘四十五，小餘千一十．','')
        # Keep the qi multiply/postposed declaration block; no nodes result exists.
        r=parse_packet(p);x=execute(r,{'epoch_elapsed_years':143129})
        self.assertEqual(x['task_outputs']['qi'],base)
        p=packet('SF');d=next(d for d in p['primary_documents'] if '求次氣' in d['text']);d['text']+='又加大餘十五，小餘七，除命之如前。'
        r=parse_packet(p);x=execute(r,{'epoch_inclusive_year':2})
        self.assertEqual(x['task_outputs']['qi']['first_qi_remainder32'],22)
    def test_rescale_removed_or_inconsistent_declaration(self):
        p=packet();d=p['primary_documents'][-1];d['text']=d['text'].replace('皆以元為法','未定其法')
        r=parse_packet(p);self.assertFalse(any(e['kind']=='rescale' and e['scope'].get('task') in ('nodes','qi') for e in r['events']))
        p=packet();d=next(d for d in p['context_documents'] if d['text'].startswith('元法'));d['text']=d['text'].replace('四千六百一十七','三千七十八')
        r=parse_packet(p);self.assertTrue(any(e['kind']=='rescale' and e['attributes']['execution_blocked']=='inconsistent_representation' for e in r['events']))
    def test_declarations_three_quantities_and_alternatives(self):
        p=json.loads((ROOT/'handoff_v3/runtime_inputs/DIAGNOSTIC_DECLARATIONS.json').read_text());r=parse_packet(p);x=execute(r,{})
        vals=list(x['task_outputs']['declarations'].values())
        self.assertEqual(vals,[{'numerator':112424,'denominator':1539},{'numerator':28106,'denominator':1539},{'numerator':42159,'denominator':1539}])
        last=[e for e in r['events'] if e['kind']=='fraction'][-1]
        self.assertEqual(last['attributes']['historical_role_alternatives'],['中央','water_before_central']);self.assertEqual(last['attributes']['temporal_anchor']['label'],'冬至後')
    def test_boundary_profiles_common_epoch(self):
        moons=[[0,1],[29,2],[30,1]];qi=[72,5]
        self.assertEqual(boundary_membership(moons,qi,'instant_lunation','epoch')['interval'],0)
        self.assertEqual(boundary_membership(moons,qi,'civil_whole_day','epoch')['interval'],1)
        self.assertEqual(boundary_membership(moons,qi,'instant_lunation')['status'],'requires_external_data')
    def test_generated_sequences_and_false_intercalation(self):
        p=packet();p['selected_profiles'].append('civil_whole_day');r=parse_packet(p);x=execute(r,{'epoch_elapsed_years':143129})
        self.assertEqual(x['task_outputs']['intercalation']['boundary_result']['status'],'resolved')
        self.assertEqual(len([e for e in r['events'] if e['kind']=='event_sequence']),2)
        p=packet('SF');r=parse_packet(p);x=execute(r,{'epoch_inclusive_year':2})
        self.assertEqual(x['task_outputs']['intercalation']['boundary_result']['status'],'no_intercalation')
    def test_document_renaming_and_reformatting(self):
        p=packet();r=parse_packet(p);expected=execute(r,{'epoch_elapsed_years':143129})['task_outputs']
        for i,d in enumerate(p['primary_documents']+p['context_documents']):d['doc_id']='renamed'+str(i);d['text']='\n '.join(d['text'])
        x=execute(parse_packet(p),{'epoch_elapsed_years':143129})
        self.assertEqual(x['task_outputs'],expected)
    def test_unknown_does_not_silently_flow(self):
        p=synthetic('置甲，未知而求之，以三乘之。',['甲七。'])
        r=parse_packet(p);x=execute(r,{})
        mult=next(e for e in r['events'] if e['kind']=='multiply')
        self.assertNotIn(mult['writes']['result'],x['values'])

class AdditionalContractTests(unittest.TestCase):
    def test_three_concordance_branches_source_derived(self):
        r=parse_packet(packet());e=next(e for e in r['events'] if e['kind']=='select')
        self.assertEqual(len(e['attributes']['choices']),3)
        for n,index,head in [(0,0,1),(1538,0,1),(1539,1,41),(3077,1,41),(3078,2,21),(4616,2,21),(4617,0,1)]:
            out=execute(r,{'epoch_elapsed_years':n})['task_outputs']['era_entry']
            self.assertEqual((out['concordance_index'],out['head_day']),(index,head))
        p=packet();p['primary_documents'][0]['text']=p['primary_documents'][0]['text'].replace('地統甲辰','地統乙巳')
        self.assertEqual(execute(parse_packet(p),{'epoch_elapsed_years':1539})['task_outputs']['era_entry']['head_day'],42)
    def test_lift_omission_and_wrong_factor_rejected(self):
        from analysis_parser.audit import audit
        p=packet();p['selected_profiles'].append('civil_whole_day');r=parse_packet(p)
        seq=next(e for e in r['events'] if e['kind']=='event_sequence' and e['attributes']['sequence_role']=='qi_events')
        seq['reads']['whole']=r['task_exports']['winter']['winter_whole_residual']
        self.assertTrue(any(d['kind']=='invalid_time_frame' for d in audit(r)))
        self.assertTrue(any(u['cause']=='invalid_time_frame' for u in execute(r,{'epoch_elapsed_years':143129})['unresolved']))
        r=parse_packet(p);lift=next(e for e in r['events'] if e['kind']=='cycle_lift');factor=next(v for v in r['value_instances'] if v['id']==lift['reads']['factor']);next(e for e in r['events'] if e['id']==factor['producer'])['attributes']['value']=300
        self.assertTrue(any(d['kind']=='invalid_time_frame' for d in audit(r)))
    def test_missing_event_data_keeps_boundary_call(self):
        p=packet();p['selected_profiles'].append('civil_whole_day');p['primary_documents']=[d for d in p['primary_documents'] if '推冬至' not in d['text'] and '求八節' not in d['text']]
        r=parse_packet(p);x=execute(r,{'epoch_elapsed_years':143129})
        self.assertTrue(any(e['kind']=='boundary_call' for e in r['events']))
        self.assertEqual(x['task_outputs']['intercalation']['boundary_result']['status'],'requires_external_data')
    def test_long_month_exact_boundaries(self):
        for tradition,threshold in [('ST',38),('SF',441)]:
            r=parse_packet(packet(tradition));e=next(e for e in r['events'] if e['kind']=='threshold' and e['attributes'].get('judgment')=='其月大')
            for n in (threshold-1,threshold,threshold+1):
                simple={'events':[{'id':'x','kind':'literal','reads':{},'writes':{'result':e['reads']['value']},'attributes':{'value':n}}, {'id':'y','kind':'literal','reads':{},'writes':{'result':e['reads']['lower']},'attributes':{'value':threshold}},e],'value_instances':[]}
                self.assertEqual(execute(simple,{})['values'][e['writes']['result']],n>=threshold)
    def test_unknown_quantity_and_bad_unit_addition_block(self):
        p=synthetic('置甲，加乙。',['甲七。','乙八。'])
        r=parse_packet(p)
        e=next(e for e in r['events'] if e['kind']=='add')
        self.assertEqual(e['attributes']['quantity_transition']['status'],'unknown')
