import unittest
from analysis_parser.context_compiler import compile_documents
from analysis_parser.inputs import documents
from analysis_parser.execution import execute
from analysis_parser.scoped import ScopedParser


def fixture(seed=5):
    return {'schema_version':'3.0','provided_scope':{},'primary_documents':[{'doc_id':'out','text':'推終課，置中間乙，盈四得一，名曰商量，不盈者名曰餘量．'}], 'context_documents':[{'doc_id':'a','text':'推初課，置種子，以三乘之，名曰中間甲．'},{'doc_id':'b','text':'推次課，置中間甲，加七，名曰中間乙．'}]}

class Programs(unittest.TestCase):
    def test_P01(self):
        from analysis_parser.program_ir import link_entry
        p=fixture();a=compile_documents(documents(p),{});entry=next(d['id'] for d in a.definitions if d['source_role']=='primary');l=link_entry(a,entry,{'種子':{'unit':'integer'}})
        self.assertEqual(len(l.order),3)
        swapped=fixture();swapped['primary_documents'],swapped['context_documents']=swapped['context_documents'],swapped['primary_documents']
        b=compile_documents(documents(swapped),{})
        def structural(index):return {d['id']:{k:v for k,v in d.items() if k!='source_role'} for d in index.definitions}
        self.assertEqual(structural(a),structural(b))
    def run_chain(self,seed):
        from analysis_parser.program_ir import link_entry
        from analysis_parser.scoped import lower_linked
        parser=ScopedParser(fixture());entry=next(d['id'] for d in parser.program.definitions if d['source_role']=='primary');linked=link_entry(parser.program,entry,{'種子':{'unit':'integer'}})
        r=lower_linked(linked,parser);return r,execute(r,{'種子':seed})
    def test_P02(self):
        r,x=self.run_chain(5);self.assertFalse(x['unresolved']);self.assertEqual([x['named_outputs']['main:'+n] for n in ('中間甲','中間乙','商量','餘量')],[15,22,5,2]);self.assertEqual(len(r['program']['calls']),3)
    def test_P03(self):
        r,x=self.run_chain(9);self.assertEqual([x['named_outputs']['main:'+n] for n in ('中間甲','中間乙','商量','餘量')],[27,34,8,2])
    def test_P04(self):
        from analysis_parser.program_ir import link_entry
        p=fixture();p['context_documents']=p['context_documents'][1:];a=compile_documents(documents(p),{});l=link_entry(a,a.definitions[0]['id'],{'種子':{'unit':'integer'}});self.assertTrue(any(d['kind']=='missing_import' for d in l.diagnostics))
    def test_P05(self):
        self.interval_parameter_check()
        from analysis_parser.program_ir import link_entry
        p=fixture();p['context_documents'].append({'doc_id':'duplicate','text':'推異課，置八，名曰中間甲．'});a=compile_documents(documents(p),{});l=link_entry(a,a.definitions[0]['id'],{'種子':{'unit':'integer'}});self.assertTrue(any(d['kind']=='ambiguous_import' for d in l.diagnostics))
    def test_P06(self):
        # Reuse one compiled method definition in one graph with independent
        # source literal actuals and return instances, including reverse order.
        parser=ScopedParser({'schema_version':'3.0','primary_documents':[{'doc_id':'m','text':'置五，置九，以三乘之，盈四得一．'}]})
        sp=parser.docs[0];from analysis_parser.inputs import span
        spans=[span(sp,0,len(sp['text']))]
        method={'id':'synthetic-method','name':'synthetic','formal_inputs':{'x':{'unit':'integer'},'factor':{'unit':'integer'},'divisor':{'unit':'integer'}},'returns':{'quotient':'q','remainder':'r'},'source_spans':spans,'body':[{'id':'mul','kind':'multiply','reads':{'left':'$x','right':'$factor'},'writes':{'result':'a'},'source_spans':spans},{'id':'div','kind':'divmod','reads':{'dividend':'a','divisor':'$divisor'},'writes':{'quotient':'q','remainder':'r'},'source_spans':spans}]}
        parser.report['method_library'].append(method);calls=[]
        for seed in (5,9,9,5):
            reads={k:parser.literal(str(v),spans) for k,v in {'x':seed,'factor':3,'divisor':4}.items()};calls.append(parser.emit_method_call(method,reads,spans))
        x=execute(parser.report,{})
        self.assertFalse(x['unresolved']);self.assertEqual([x['values'][c['writes']['quotient']] for c in calls],[3,6,6,3])
        self.assertEqual(len({c['call_id'] for c in calls}),4);self.assertEqual(len({c['writes']['quotient'] for c in calls}),4);self.assertEqual({c['method_binding']['definition_id'] for c in calls},{'synthetic-method'})
        a,x=self.run_chain(5);b,y=self.run_chain(9);c,z=self.run_chain(5);self.assertEqual(x['named_outputs'],z['named_outputs']);self.assertNotEqual(x['named_outputs'],y['named_outputs'])
    def test_P08(self):
        from analysis_parser.context_compiler import compile_context
        p={'context_documents':[{'doc_id':'c','text':'甲法三．置乙量五．加大餘二十九．積日盈六十，除之．'}]}
        context=compile_context(documents(p),[],{})
        self.assertEqual([d['label'] for d in context['declarations']],['甲法'])
    def test_P09(self):
        from analysis_parser.operations import method_body
        body=[{'kind':'multiply','reads':{'left':'$x','right':'$factor'},'writes':{'result':'a'}},{'kind':'add','reads':{'left':'a','right':'$delta'},'writes':{'result':'b'}},{'kind':'divmod','reads':{'dividend':'b','divisor':'$divisor'},'writes':{'quotient':'q','remainder':'r'}}]
        body.append({'kind':'count','reads':{'offset':'q'},'writes':{'result':'ordinal'},'attributes':{'ordinal_origin':1,'cyclic':False}})
        self.assertEqual(method_body(body,{'quotient':'q','remainder':'r','count':'ordinal'},{'x':5,'factor':3,'delta':7,'divisor':4}),{'quotient':5,'remainder':2,'count':6})
    def test_P10(self):
        from analysis_parser.scoped import lower_linked
        from analysis_parser.program_ir import link_entry
        independent=fixture();independent['context_documents'].append({'doc_id':'unused','text':'推異課，置未給量，加七，名曰異量．'})
        parser=ScopedParser(independent);linked=link_entry(parser.program,parser.program.definitions[0]['id'],{'種子':{'unit':'integer'}});report=lower_linked(linked,parser)
        self.assertFalse(execute(report,{'種子':5})['unresolved'])
        self.assertNotIn(next(d['id'] for d in parser.program.definitions if d.get('goal_surface')=='異課'),linked.order)
        from analysis_parser.program_ir import link_entry
        p=fixture();p['context_documents'][0]['text']='推初課，置中間乙，以三乘之，名曰中間甲．';a=compile_documents(documents(p),{});l=link_entry(a,a.definitions[0]['id'],{});self.assertTrue(any(d['kind']=='dependency_cycle' for d in l.diagnostics))

    def test_P07(self):
        import json
        from pathlib import Path
        from analysis_parser.pipeline import parse_packet
        packet=json.loads(Path('evaluation/rescue-v3_1/development_packets/A01.json').read_text())
        report=parse_packet(packet['packet']);result=execute(report,packet['inputs'])
        self.assertFalse(result['unresolved']);self.assertFalse(report['unresolved'])
        self.assertTrue(report['method_instances'])
        executed=report['program']['executed_definition_ids']
        unrelated=[d['id'] for d in report['program']['definitions'] if d['goal_surface'] in ('弦','望','其次月')]
        self.assertFalse(set(executed)&set(unrelated))
        # The used count body comes from the source containing these unused queries.
        self.assertTrue(any(s['doc_id']=='ST.2.3' for m in report['method_instances'] for s in m['definition_spans']))

    def interval_parameter_check(self):
        import json
        from pathlib import Path
        from analysis_parser.pipeline import parse_packet
        packet=json.loads(Path('evaluation/rescue-v3_1/development_packets/A02.json').read_text());report=parse_packet(packet['packet']);result=execute(report,packet['inputs'])
        event=next(e for e in report['events'] if e['kind']=='add' and e['attributes'].get('receiver_label')=='月元餘' and e['rule_id']=='RESCUE_UPDATE')
        values={v['id']:v for v in report['value_instances']};events={e['id']:e for e in report['events']}
        self.assertEqual(result['values'][event['reads']['right']],13)
        self.assertEqual(events[values[event['reads']['right']]['producer']]['kind'],'parameter')
        self.assertEqual(values[event['reads']['right']]['parameter_role'],'per_appearance_increment')
        altered=json.loads(json.dumps(packet['packet']));altered['context_documents']=[d for d in altered['context_documents'] if '積月十三，月餘' not in d['text']]
        bad=parse_packet(altered);self.assertTrue(execute(bad,packet['inputs'])['unresolved'])
