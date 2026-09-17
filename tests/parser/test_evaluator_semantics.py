import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'evaluation/handoff-v2'
sys.path.insert(0, str(HERE))
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from graph_checks import Graph
from critical import checks
from reference_steps import assess_steps
from numeric import assess_fixture, explicit_inputs


class EvaluatorSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = {w: parse_packet(json.loads((HERE/'package/runtime_inputs'/f'{w}.json').read_text())) for w in ('W01','W02','W03','W04')}
        cls.refs = {w: json.loads((HERE/'package/reference'/f'{w}.json').read_text()) for w in cls.reports}
        cls.specs = json.loads((HERE/'package/evaluation/critical_assertions.json').read_text())['assertions']
        cls.fixtures = json.loads((HERE/'package/evaluation/numerical_fixtures.json').read_text())['fixtures']

    def rejected(self, report, w):
        self.assertTrue(any(x['status']=='fail' for x in checks(report,w,self.specs)))
        self.assertTrue(any(x['status']=='fail' for x in assess_steps(report,self.refs[w])['rows']))

    def test_clean_reference_steps(self):
        for w,r in self.reports.items():
            self.assertTrue(all(x['status']=='pass' for x in assess_steps(r,self.refs[w])['rows']), w)

    def test_parameter_method_target_rejected(self):
        r=copy.deepcopy(self.reports['W01']);g=Graph(r)
        g.one('數除如法','method_call')['attributes']['target']=next(e['id'] for e in r['events'] if e['kind']=='parameter')
        self.rejected(r,'W01')

    def test_incompatible_method_rejected(self):
        r=copy.deepcopy(self.reports['W01']);g=Graph(r)
        call=g.one('數除如法','method_call');target=g.events[call['attributes']['target']]
        target['reads']['cycle']=g.named('日法',parameter=True)
        self.rejected(r,'W01')

    def test_different_declared_count_target_rejected(self):
        r=copy.deepcopy(self.reports['W01']);g=Graph(r);call=g.one('數除如法','method_call')
        target=copy.deepcopy(g.events[call['attributes']['target']]);target['id']='different_method'
        target['reads']['origin']=g.named('入統歲數')
        declaration=copy.deepcopy(r['methods'][0]);declaration['event_id']=target['id'];declaration['origin']=target['reads']['origin']
        r['events'].append(target);r['methods'].append(declaration);call['attributes']['target']=target['id']
        self.rejected(r,'W01')

    def test_incorrect_condition_assertion_counts_fp_and_fn(self):
        from layers import assess_layers
        r=copy.deepcopy(self.reports['W01']);Graph(r).one('閏餘十二以上','threshold')['attributes']['scope_end']='end_of_document'
        layer=assess_layers(r,self.refs['W01'],assess_steps(r,self.refs['W01']))['layers']['condition_scope']
        self.assertGreater(layer['FP'],0);self.assertGreater(layer['FN'],0)

    def test_wrong_annotated_quantity_role_counts_fp_and_fn(self):
        from layers import assess_layers
        r=copy.deepcopy(self.reports['W01']);g=Graph(r);g.values[g.named('閏餘')]['role']='fabricated'
        layer=assess_layers(r,self.refs['W01'],assess_steps(r,self.refs['W01']))['layers']['quantity_mention_roles']
        self.assertGreater(layer['FP'],0);self.assertGreater(layer['FN'],0)

    def test_station_origin_and_convention_rejected(self):
        for key,value in [('ordinal_origin',2),('origin_label','冬至'),('convention','wrong'),('output_role','medial_ordinal'),('zero_offset_at_origin',False)]:
            r=copy.deepcopy(self.reports['W03']);Graph(r).one('次數從星紀起','count')['attributes'][key]=value
            self.rejected(r,'W03')

    def test_station_fixture_checked(self):
        r=copy.deepcopy(self.reports['W03']);Graph(r).one('次數從星紀起','count')['attributes']['ordinal_origin']=2
        for f in self.fixtures:
            if f['window_id']=='W03':
                self.assertEqual(assess_fixture(r,execute(r,explicit_inputs('W03',f['inputs'])),f)['status'],'fail')

    def test_threshold_scope_rejected(self):
        r=copy.deepcopy(self.reports['W01']);Graph(r).one('閏餘十二以上','threshold')['attributes']['scope_end']='end_of_document'
        self.rejected(r,'W01')

    def test_extra_source_anchored_binding_is_fp(self):
        from layers import assess_layers
        r=copy.deepcopy(self.reports['W03']);g=Graph(r)
        g.one('從之','add')['reads']['fabricated']=g.named('中元餘')
        l=assess_layers(r,self.refs['W03'],assess_steps(r,self.refs['W03']))
        self.assertGreater(l['layers']['producer_port_relations']['FP'],0)
        self.assertFalse(l['full_chain_passed'])

    def test_fabricated_add_and_call_in_compound_are_fp(self):
        from layers import assess_layers
        for kind in ('add','method_call'):
            r=copy.deepcopy(self.reports['W01']);g=Graph(r)
            original=next(e for e in r['events'] if e['kind']==kind and e['scope']['query']=='弦')
            fabricated=copy.deepcopy(original);fabricated['id']='fabricated_event'
            for port,vid in list(fabricated['writes'].items()):
                value=copy.deepcopy(g.values[vid]);value['id']='fabricated_'+vid;value['producer']='fabricated_event'
                fabricated['writes'][port]=value['id'];r['value_instances'].append(value)
            r['events'].append(fabricated)
            l=assess_layers(r,self.refs['W01'],assess_steps(r,self.refs['W01']))
            self.assertGreater(l['layers']['producer_port_relations']['FP'],0)
            self.assertFalse(l['full_chain_passed'])

    def test_duplicate_simple_semantic_event_is_fp(self):
        from layers import assess_layers
        r=copy.deepcopy(self.reports['W03']);e=copy.deepcopy(Graph(r).one('從之','add'));e['id']='fabricated_event';r['events'].append(e)
        l=assess_layers(r,self.refs['W03'],assess_steps(r,self.refs['W03']))
        self.assertGreater(l['layers']['producer_port_relations']['FP'],0)

    def test_missing_binding_is_fn(self):
        from layers import assess_layers
        r=copy.deepcopy(self.reports['W03']);g=Graph(r)
        del g.one('從之','add')['reads']['right']
        l=assess_layers(r,self.refs['W03'],assess_steps(r,self.refs['W03']))
        self.assertGreater(l['layers']['producer_port_relations']['FN'],0)
        self.assertFalse(l['full_chain_passed'])

    def test_extra_output_is_fp(self):
        from layers import assess_layers
        r=copy.deepcopy(self.reports['W03']);g=Graph(r)
        g.one('從之','add')['writes']['fabricated']=g.named('中元餘')
        l=assess_layers(r,self.refs['W03'],assess_steps(r,self.refs['W03']))
        self.assertGreater(l['layers']['producer_port_relations']['FP'],0)

    def test_clean_layers_and_empty_denominators(self):
        from layers import assess_layers
        for w,r in self.reports.items():
            l=assess_layers(r,self.refs[w],assess_steps(r,self.refs[w]))
            self.assertTrue(l['full_chain_passed'],l['unsupported_relations'])
            self.assertEqual(l['layers']['all_token_mentions']['status'],'not_scored')
        self.assertIsNone(l['layers']['cross_document_relations']['precision'])

    def test_carry_boundaries_and_wrong_carry_rejected(self):
        from behavior import assess_carry_boundary
        for w in ('W01','W02'):
            self.assertEqual(len(assess_carry_boundary(self.reports[w],w)['rows']),3)
            def broken(report,inputs):
                x=execute(report,inputs);g=Graph(report)
                for e in report['events']:
                    if inputs['小餘'] in (38,441) and e['kind']=='divmod' and e['scope']['query']!='main':
                        x['values'][g.output(e,'quotient')]=99
                return x
            with self.assertRaises(AssertionError):assess_carry_boundary(self.reports[w],w,broken)

    def test_executable_cross_call_rejection(self):
        from behavior import assess_cross_call
        evidence=assess_cross_call(self.reports['W04'],self.specs)
        self.assertEqual(evidence['contaminated_second']['second_product'],59230)
        self.assertTrue(evidence['second_result_rejected'])

    def test_unknown_reference_action_is_failure(self):
        ref=copy.deepcopy(self.refs['W01']);ref['nodes'][0]['action']='unimplemented_historical_action'
        scored=assess_steps(self.reports['W01'],ref)
        self.assertEqual(scored['rows'][0]['status'],'fail')

if __name__=='__main__': unittest.main()
