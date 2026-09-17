"""Independent fixed-count relation checks; no parser-generated gold."""
import copy
import importlib.util
from pathlib import Path
import unittest
import tempfile
import shutil
import json
from analysis_parser.execution import execute

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('rescue_scoring', ROOT/'evaluation/rescue-v3_1/fixed_scoring.py')
scoring = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scoring)
PROTOCOL_SPEC=importlib.util.spec_from_file_location('rescue_protocol', ROOT/'evaluation/rescue-v3_1/runtime_protocol.py')
protocol=importlib.util.module_from_spec(PROTOCOL_SPEC)
PROTOCOL_SPEC.loader.exec_module(protocol)


def fixture():
    text = '以甲乘乙'
    anchor = {'doc_id':'test', 'reading_id':'test.declared', 'start':0, 'end':len(text), 'quote':text}
    packet = {'primary_documents':[{'doc_id':'test', 'text':text}]}
    events = []
    values = []
    for i in range(3):
        events.append({'id':f'p{i}', 'kind':'parameter', 'reads':{}, 'writes':{'result':f'v{i}'}, 'source_spans':[anchor], 'attributes':{'name':f'arg{i}', 'value':i+1}})
        values.append({'id':f'v{i}', 'producer':f'p{i}', 'output_port':'result', 'labels':[f'arg{i}']})
    events.append({'id':'main','kind':'multiply','reads':{'left':'v0','right':'v1'},'writes':{},'source_spans':[anchor]})
    report = {'events':events,'value_instances':values}
    reference = {'cards':[{'card_id':'synthetic','obligations':[{'id':'syn.1','anchor':anchor}]}], 'policy':{'supported_actions':['multiply'],'obligations':{'syn.1':{'events':[{'kind':'multiply','reads':{p:{'parameter':f'arg{i}'} for i,p in enumerate(['left','right'])}}]}}}}
    return packet, report, reference


class EvaluationIntegrityTests(unittest.TestCase):
    def test_E01(self):
        packet, report, ref = fixture()
        complete = scoring.evaluate(packet, report, ref)
        self.assertTrue(complete['all_obligations_passed'])
        n = complete['gold_atom_count']
        self.assertEqual(n, 4)  # action, occurrence, two legal multiply endpoints
        for mode in ['whole','port']:
            broken = copy.deepcopy(report)
            if mode == 'whole': broken['events'].pop()
            else: del broken['events'][-1]['reads']['right']
            result = scoring.evaluate(packet, broken, ref)
            self.assertEqual(result['relations']['TP']+result['relations']['FN'], n)
            self.assertFalse(result['all_obligations_passed'])
        self.assertEqual(scoring.evaluate(packet, {'events':[], 'value_instances':[]}, ref)['relations']['FN'],4)

    def test_E02(self):
        packet, report, ref = fixture()
        report['events'][-1]['reads']['extra'] = 'v2'
        result = scoring.evaluate(packet, report, ref)
        self.assertEqual(result['relations']['TP'],4)
        self.assertEqual(result['relations']['FP'],1)
        self.assertFalse(result['all_obligations_passed'])
        second = copy.deepcopy(report['events'][-1]); second['id']='wrong'; second['reads']['left']='v1'
        report['events'].append(second)
        self.assertGreater(scoring.evaluate(packet,report,ref)['relations']['FP'],1)

    def test_E03(self):
        packet, report, ref = fixture()
        report['events'][-1]['kind']='unknown_main'
        result = scoring.evaluate(packet,report,ref,track='A')
        self.assertEqual(result['relations']['FN'],4)
        self.assertFalse(result['all_obligations_passed'])
        self.assertIn('unknown_main',result['unsupported_actual_actions'])
        b=scoring.evaluate(packet,report,ref,track='B')
        self.assertEqual(b['gold_atom_count'],4)
        self.assertFalse(b['all_obligations_passed'])
        self.assertIn('unknown_main', b['unsupported_actual_actions'])

    def test_E04(self):
        for diagnostic in [{'severity':'error','cause':'bad'},{'cause':'unresolved'},{'status':'incomplete'}]:
            for value in [[diagnostic],diagnostic,{'items':[diagnostic]}]:
                self.assertTrue(scoring.blocking_diagnostics({'diagnostics':value}))
        self.assertFalse(scoring.blocking_diagnostics({'diagnostics':[{'severity':'info','cause':'annotation'}]}))
        self.assertTrue(scoring.blocking_diagnostics({'unresolved':[{'cause':'missing_definition'}]}))

    def test_registered_atoms_are_kept_when_all_events_are_missing(self):
        for name,count in [('A01',114),('A02',83),('A03',91),('A04',81)]:
            reference=json.loads((ROOT/f'evaluation/rescue-v3_1/registered_references/{name}.json').read_text())
            packet=json.loads((ROOT/f'evaluation/handoff-v3/prospective/packets/{name}.json').read_text())['packet']
            result=scoring.evaluate(packet,{'events':[],'value_instances':[]},reference)
            self.assertEqual(result['gold_atom_count'],count)
            self.assertEqual(result['relations']['FN'],count)
            self.assertEqual(result['relations']['TP'],0)
            self.assertFalse(result['all_obligations_passed'])

    def test_E05(self):
        packet={'schema_version':'3.0','primary_documents':[{'doc_id':'legit','text':'推甲課，置甲量．'}], 'context_documents':[{'doc_id':'source','text':'甲量十七．'}]}
        baseline=ROOT/'evaluation/rescue-v3_1/baseline/snapshot/analysis_parser'
        valid=protocol.run_isolated(packet,{},core_dir=baseline)
        self.assertEqual(valid['status'],'completed')
        self.assertFalse(valid['runtime_audit']['blocked_accesses'])
        self.assertTrue(any(e['kind']=='parameter' and e['attributes'].get('value')==17 for e in valid['report']['events']))
        for location in ['top','nested']:
            bad=copy.deepcopy(packet)
            if location=='top':bad['expected_graph']={}
            else:bad['primary_documents'][0]['metadata']={'expected_graph':{}}
            denied=protocol.run_isolated(bad,{},core_dir=baseline)
            self.assertEqual(denied['status'],'input_rejected')
            self.assertTrue(denied['runtime_audit']['blocked_accesses'])
        for operation,want in [('open("/tmp/rescue-reference.json").read()','open'),('__import__("socket").socket()','socket.__new__')]:
            with tempfile.TemporaryDirectory() as directory:
                core=Path(directory)/'analysis_parser';shutil.copytree(baseline,core)
                with (core/'pipeline.py').open('a') as handle:handle.write('\n'+operation+'\n')
                denied=protocol.run_isolated(packet,{},core_dir=core)
                self.assertEqual(denied['status'],'runtime_error')
                self.assertTrue(any(x['event']==want for x in denied['runtime_audit']['blocked_accesses']))

    def test_E06(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'analysis_parser').mkdir()
            behavior=root/'analysis_parser/core.py';behavior.write_text('value = 1\n')
            frozen=protocol.manifest(root)
            self.assertFalse(frozen['closed_behavior_inventory'])
            self.assertTrue(any(e.get('cause')=='missing_required_behavior_file' for e in protocol.verify(root,frozen)))
            destination=root/'first_outputs/A1.json'
            protocol.exclusive(destination,{'result':'first'})
            with self.assertRaises(FileExistsError):protocol.exclusive(destination,{'result':'replay'})
            self.assertEqual(json.loads(destination.read_text())['result'],'first')
            behavior.write_text('value = 2\n')
            self.assertTrue(any(e.get('path')=='analysis_parser/core.py' and e.get('actual')!=e.get('expected') for e in protocol.verify(root,frozen)))
            behavior.write_text('value = 1\n')
            (root/'analysis_parser/resources.json').write_text('{}')
            self.assertTrue(any(e.get('path')=='analysis_parser/resources.json' and e.get('actual')!=e.get('expected') for e in protocol.verify(root,frozen)))
            (root/'analysis_parser/resources.json').unlink()
            protocol.claim_first_attempt(root,'source-digest','A1')
            with self.assertRaises(FileExistsError):protocol.claim_first_attempt(root,'source-digest','renamed-A1')

    def test_query_order_audit_executes_independent_calls_in_reverse(self):
        # An actual graph and public executor, without parser or score mocks.
        report={'schema_version':'3.0','events':[], 'value_instances':[],
                'program':{'definitions':[{'id':'q1','kind':'QueryDef'},{'id':'q2','kind':'QueryDef'}],
                           'calls':[]}}
        def append(eid,kind,reads,value=None,cid=None):
            vid=eid+'.value'
            event={'id':eid,'kind':kind,'reads':reads,'writes':{'result':vid},'attributes':{},'source_spans':[]}
            if value is not None:event['attributes']['value']=value
            if cid:event['call_id']=cid
            report['events'].append(event)
            report['value_instances'].append({'id':vid,'producer':eid,'output_port':'result','role':'temporary','scope':{},'labels':[]})
            return vid
        base=append('base','literal',{},10)
        two=append('two','literal',{},2)
        three=append('three','literal',{},3)
        first=append('first','add',{'left':base,'right':two},cid='c1')
        second=append('second','add',{'left':base,'right':three},cid='c2')
        for did,cid,vid in [('q1','c1',first),('q2','c2',second)]:
            report['program']['calls'].append({'id':cid,'definition_id':did,'base_ref':'shared',
                'base_value_ids':{'whole':base},'return_ports':{'result':vid}})
        before=copy.deepcopy(report);forward=execute(report,{})
        audit=protocol.audit_query_order(report,{},execute)
        self.assertEqual(report,before)
        self.assertEqual(audit['status'],'executed')
        reverse=audit['execution']
        self.assertFalse(reverse['unresolved'])
        self.assertEqual((forward['values'][first],forward['values'][second]),(12,13))
        self.assertEqual(reverse['values'],forward['values'])
        self.assertLess(audit['reordered_event_ids'].index('second'),audit['reordered_event_ids'].index('first'))
        # A false claim of independent bases must never remove a real dependency.
        report['events'][-1]['reads']['left']=first
        blocked=protocol.audit_query_order(report,{},execute)
        self.assertLess(blocked['reordered_event_ids'].index('first'),blocked['reordered_event_ids'].index('second'))
        self.assertEqual(blocked['execution']['values'][second],15)

if __name__ == '__main__': unittest.main()
