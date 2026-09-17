"""Focused regressions for the three bounded independent-review findings."""
import copy,unittest
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from analysis_parser.operations import operation
from test_core_scoped import packet
from test_core_mechanisms import synthetic

class ReviewFixOneTests(unittest.TestCase):
    def test_r1_postposed_denominator_cannot_cross_other_task(self):
        p=packet();d=p['primary_documents'][-1]
        d['text']=d['text'].replace('皆以元為法','推五行，皆以元為法')
        r=parse_packet(p)
        self.assertFalse(any(e['rule_id']=='V3_RESCALE' for e in r['events']))
        self.assertTrue(any(e['rule_id']=='V3_NUMERAL' for e in r['events']))
        control=parse_packet(packet())
        self.assertTrue(any(e['rule_id']=='V3_RESCALE' and not e['attributes']['execution_blocked'] for e in control['events']))
    def test_r1_repeat_cannot_borrow_another_task_stop(self):
        p=synthetic('推閏餘所在，置甲，加七得一。推五行，盈乙，數所得。',['甲二百二十一。','乙二百二十八。'],['ST_intercalation_Cullen_Liu_GT'])
        r=parse_packet(p);self.assertFalse(any(e['kind']=='repeat' for e in r['events']))
        self.assertTrue(any(u['cause']=='incomplete_construction' for u in r['unresolved']))
        p['primary_documents'][0]['text']='推閏餘所在，置甲，加七得一。盈乙，數所得。'
        r=parse_packet(p);loop=next(e for e in r['events'] if e['kind']=='repeat')
        self.assertEqual(execute(r,{})['values'][loop['writes']['count']],2)
    def test_r2_empty_absent_body_or_definition_never_legacy_fallback(self):
        for change in ('empty_call','missing_call','empty_definition','missing_library','missing_target'):
            with self.subTest(change=change):
                r=parse_packet(packet());call=next(e for e in r['events'] if e['kind']=='method_call')
                if change=='empty_call':call['attributes']['body']=[]
                if change=='missing_call':del call['attributes']['body']
                if change=='empty_definition':next(m for m in r['method_library'] if m['id']==call['attributes']['target'])['body']=[]
                if change=='missing_library':r['method_library']=[]
                if change=='missing_target':del call['attributes']['target']
                x=execute(r,{'epoch_elapsed_years':143129})
                self.assertNotIn(call['writes']['result'],x['values'])
                self.assertTrue(any(u['event_id']==call['id'] and u['cause'] in ('missing_method','execution_error','invalid_event_contract') for u in x['unresolved']))
    def test_r3_empty_generated_qi_series_unresolved(self):
        p=packet();p['selected_profiles'].append('civil_whole_day');r=parse_packet(p)
        seq=next(e for e in r['events'] if e['kind']=='event_sequence' and e['attributes']['sequence_role']=='qi_events');seq['attributes']['count']=0
        status=execute(r,{'epoch_elapsed_years':143129})['task_outputs']['intercalation']['boundary_result']
        self.assertEqual(status['status'],'requires_external_data');self.assertNotIn('candidate_intervals',status)
    def test_r3_invalid_or_uncovered_direct_sequences_not_evidence_of_absence(self):
        def boundary(moons,qi):
            return operation('boundary_call',{'moon_events':{'events':moons,'epoch':'same','time_frame':'full_local_epoch'},'qi_events':{'events':qi,'epoch':'same','time_frame':'full_local_epoch'}},{'profile':'instant_lunation'})['result']
        for moons,qi in [([0,29,59],[]),([0,59,29],[0,30,60]),([0,29,59],[30,0,60]),([0,29,59],[30]),([0,29,59],[80,100]),([0,29,59],[{'numerator':1,'denominator':0}])]:
            with self.subTest(moons=moons,qi=qi):
                result=boundary(moons,qi);self.assertNotEqual(result['status'],'resolved');self.assertNotIn('candidate_intervals',result)
        result=boundary([0,29,59],[-1,30,60]);self.assertEqual(result['status'],'resolved');self.assertEqual(result['candidate_intervals'],[0])
