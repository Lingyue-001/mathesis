import copy
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parents[2]/'evaluation/handoff-v2'
sys.path.insert(0,str(HERE))
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from graph_checks import Graph
from critical import checks
from reference_steps import assess_steps
from layers import assess_layers
from numeric import assess_fixture, explicit_inputs, SUPPLEMENT


class EvaluatorReview2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports={w:parse_packet(json.loads((HERE/'package/runtime_inputs'/f'{w}.json').read_text())) for w in ('W03','W04')}
        cls.refs={w:json.loads((HERE/'package/reference'/f'{w}.json').read_text()) for w in cls.reports}
        cls.specs=json.loads((HERE/'package/evaluation/critical_assertions.json').read_text())['assertions']
        cls.fixtures=json.loads((HERE/'package/evaluation/numerical_fixtures.json').read_text())['fixtures']

    def assert_rejected(self,r,w,layer):
        c=checks(r,w,self.specs);s=assess_steps(r,self.refs[w]);l=assess_layers(r,self.refs[w],s)
        self.assertTrue(any(x['status']=='fail' for x in c))
        self.assertTrue(any(x['status']=='fail' for x in s['rows']))
        self.assertGreater(l['layers'][layer]['FP'],0);self.assertGreater(l['layers'][layer]['FN'],0)
        self.assertFalse(l['full_chain_passed'])

    def assert_numbers_unchanged(self,r,w):
        for f in self.fixtures:
            if f['window_id']==w:
                x=execute(r,explicit_inputs(w,f['inputs']),SUPPLEMENT if w=='W04' else None)
                self.assertEqual(assess_fixture(r,x,f)['status'],'pass')

    def test_invalid_scan_predicates_reject_even_when_numbers_pass(self):
        for predicate in ('never_stop','remaining_months > months_in_current_year','remaining_months <= months_in_current_year','remaining_months < ordinary_year_months'):
            with self.subTest(predicate=predicate):
                r=copy.deepcopy(self.reports['W03']);Graph(r).one('除十三','year_scan')['attributes']['stop_condition']=predicate
                self.assert_numbers_unchanged(r,'W03');self.assert_rejected(r,'W03','condition_scope')

    def test_scan_start_year_and_branches_reject(self):
        for key,value in [('start_year',2),('start_year',True),('branches',['ordinary']),('branches',['ordinary','fabricated'])]:
            with self.subTest(key=key,value=value):
                r=copy.deepcopy(self.reports['W03']);Graph(r).one('除十三','year_scan')['attributes'][key]=value
                self.assert_numbers_unchanged(r,'W03');self.assert_rejected(r,'W03','condition_scope')

    def test_scan_schedule_must_match_source(self):
        r=copy.deepcopy(self.reports['W03']);Graph(r).one('除十三','year_scan')['attributes']['cumulative_schedule'][0]['year']=2
        self.assert_rejected(r,'W03','condition_scope')

    def test_equivalent_normalized_scan_predicates_pass(self):
        for predicate in ('  remaining_months   <   months_in_current_year  ','months_in_current_year > remaining_months'):
            r=copy.deepcopy(self.reports['W03']);Graph(r).one('除十三','year_scan')['attributes']['stop_condition']=predicate
            s=assess_steps(r,self.refs['W03']);self.assertTrue(assess_layers(r,self.refs['W03'],s)['full_chain_passed'])

    def test_external_contract_corruptions_reject_independently(self):
        for key,value in [('method','fabricated'),('missing_data',[]),('missing_data',['adjacent_conjunction_events']),('missing_data',['medial_qi_events']),('allowed_adjustments',[]),('allowed_adjustments',['advance']),('allowed_adjustments',['retreat'])]:
            with self.subTest(key=key,value=value):
                r=copy.deepcopy(self.reports['W04']);Graph(r).one('以朔制之','external_constraint_call')['attributes'][key]=value
                self.assert_numbers_unchanged(r,'W04');self.assert_rejected(r,'W04','method_external_calls')

    def test_external_unresolved_must_agree_with_this_call(self):
        for mode in ('missing','wrong_dependency','extra_dependency','wrong_anchor','duplicate'):
            with self.subTest(mode=mode):
                r=copy.deepcopy(self.reports['W04']);u=next(u for u in r['unresolved'] if 'boundary_data' in u['missing_or_conflicting_inputs'])
                if mode=='missing':r['unresolved'].remove(u)
                elif mode=='wrong_dependency':u['missing_or_conflicting_inputs']=['章閏']
                elif mode=='extra_dependency':u['missing_or_conflicting_inputs'].append('fabricated_dependency')
                else:u['source_spans']=copy.deepcopy(r['unresolved'][0]['source_spans'])
                if mode=='duplicate':
                    u['source_spans']=copy.deepcopy(Graph(r).one('以朔制之','external_constraint_call')['source_spans'])
                    r['unresolved'].append(copy.deepcopy(u))
                self.assert_rejected(r,'W04','method_external_calls')

    def test_external_list_order_is_not_semantic(self):
        r=copy.deepcopy(self.reports['W04']);a=Graph(r).one('以朔制之','external_constraint_call')['attributes']
        a['missing_data'].reverse();a['allowed_adjustments'].reverse()
        self.assertTrue(assess_layers(r,self.refs['W04'],assess_steps(r,self.refs['W04']))['full_chain_passed'])

    def test_directional_operand_swaps_are_fn_and_fp(self):
        for quote,kind,ports in [('以閏減入紀月','subtract',('left','right')),('滿其月法得一','divmod',('dividend','divisor'))]:
            with self.subTest(kind=kind):
                r=copy.deepcopy(self.reports['W04']);e=Graph(r).one(quote,kind);left,right=ports
                e['reads'][left],e['reads'][right]=e['reads'][right],e['reads'][left]
                s=assess_steps(r,self.refs['W04']);l=assess_layers(r,self.refs['W04'],s)
                nid=next(row['reference_node'] for row in s['rows'] if e['id'] in row['event_ids'])
                rows=[b for b in l['binding_assertions'] if b['node']==nid and b['direction']=='input']
                self.assertEqual([b['status'] for b in rows],['fail','fail'])
                wrong=[x for x in l['unsupported_relations'] if x['event']==e['id'] and x.get('read_port') in ports]
                self.assertEqual(len(wrong),2);self.assertFalse(l['full_chain_passed'])

if __name__=='__main__':unittest.main()
