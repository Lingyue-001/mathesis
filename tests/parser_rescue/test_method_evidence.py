"""Independent scorer mutations for executable method bodies and real ports."""
import copy
import importlib.util
from pathlib import Path
import unittest
from analysis_parser.execution import execute

ROOT=Path(__file__).resolve().parents[2]
S=importlib.util.spec_from_file_location('method_score',ROOT/'evaluation/rescue-v3_1/fixed_scoring.py')
score=importlib.util.module_from_spec(S);S.loader.exec_module(score)


def fixture():
    source='積日盈六十，除之，數從首日起'
    span={'doc_id':'independent','reading_id':'independent.declared','start':0,'end':len(source),'quote':source}
    packet={'primary_documents':[{'doc_id':'independent','text':source}]}
    body=[{'id':'reduce','kind':'cycle_reduce','reads':{'dividend':'$offset','divisor':'$cycle'},'writes':{'quotient':'q','remainder':'r'},'source_spans':[span]},
          {'id':'count','kind':'count','reads':{'offset':'r','origin':'$origin','cycle':'$cycle'},'writes':{'result':'day'},'attributes':{'cyclic':True},'source_spans':[span]}]
    method={'id':'definition','body':body,'returns':{'remainder':'r','result':'day'},'formal_inputs':{'offset':{'unit':'day'},'origin':{'unit':'day_index'},'cycle':{'unit':'integer'}},'source_spans':[span]}
    report={'schema_version':'3.0','events':[],'value_instances':[],'method_library':[method]}
    def value(vid,producer,port,unit):return {'id':vid,'producer':producer,'output_port':port,'unit':unit,'role':'temporary','labels':[],'scope':{}}
    for name,number,unit in [('offset',61,'day'),('origin',5,'day_index'),('cycle',60,'integer')]:
        report['events'].append({'id':name,'kind':'literal','reads':{},'writes':{'result':name+'.value'},'attributes':{'value':number},'source_spans':[span]})
        report['value_instances'].append(value(name+'.value',name,'result',unit))
    actuals={name:name+'.value' for name in ['offset','origin','cycle']}
    call={'id':'call','kind':'method_call','call_id':'unique','reads':actuals,'writes':{'remainder':'out.r','result':'out.day'},'attributes':{'target':'definition','body':body,'formal_returns':method['returns']},'method_binding':{'definition_id':'definition','actuals':actuals,'formal_inputs':method['formal_inputs']},'source_spans':[span]}
    report['events'].append(call)
    report['value_instances'] +=[value('out.r','call','remainder','day'),value('out.day','call','result','day_index')]
    instance_events=[{'id':'unique.reduce','kind':'cycle_reduce','reads':{'dividend':'offset.value','divisor':'cycle.value'},'writes':{'quotient':'unique.q','remainder':'unique.r'},'source_spans':[span]},
        {'id':'unique.count','kind':'count','reads':{'offset':'unique.r','origin':'origin.value','cycle':'cycle.value'},'writes':{'result':'unique.day'},'attributes':{'cyclic':True},'source_spans':[span]}]
    bindings={'out.r':'unique.r','out.day':'unique.day'}
    call['method_binding']['return_bindings']=bindings
    report['method_instances']=[{'call_event_id':'call','definition_id':'definition','formal_bindings':actuals,'call_spans':[span],'return_bindings':bindings,'events':instance_events,
        'value_instances':[value('unique.q','unique.reduce','quotient','cycle'),value('unique.r','unique.reduce','remainder','day'),value('unique.day','unique.count','result','day_index')]}]
    return packet,report


class MethodEvidenceTests(unittest.TestCase):
    def test_return_projection_is_real_and_rejects_wrong_producer(self):
        packet,report=fixture();graph=score.Graph(packet,report)
        self.assertFalse(graph.source_errors)
        self.assertEqual(graph.root('out.r'),'unique.r')
        changed=copy.deepcopy(report)
        changed['method_instances'][0]['value_instances'][1]['producer']='unique.count'
        broken=score.Graph(packet,changed)
        self.assertTrue(broken.source_errors)
        self.assertNotEqual(broken.root('out.r'),'unique.r')

    def test_method_semantics_and_execution_trace_are_both_required(self):
        packet,report=fixture();graph=score.Graph(packet,report);method=report['method_library'][0];call=report['events'][-1]
        execution=execute(report,{})
        self.assertFalse(execution['unresolved'])
        self.assertEqual(execution['event_results']['call'],{'remainder':1,'result':6})
        self.assertTrue(score._method.semantic_body(graph,call,method)['cyclical_day'])
        self.assertTrue(score._method.trace_identity(call,method,execution))
        for change in ('divisor','offset','return'):
            altered=copy.deepcopy(report);m=altered['method_library'][0]
            if change=='divisor':altered['events'][2]['attributes']['value']=59
            elif change=='offset':m['body'][1]['reads']['offset']='$offset'
            else:m['returns']['result']='r'
            self.assertFalse(score._method.semantic_body(score.Graph(packet,altered),altered['events'][-1],m)['cyclical_day'])
        falsified=copy.deepcopy(execution)
        [x for x in falsified['execution_trace'] if 'method_body_trace' in x][0]['method_body_trace'][0]['reads']['dividend']=999
        self.assertFalse(score._method.trace_identity(call,method,falsified))

    def test_commutativity_is_one_permutation_and_subtraction_is_not(self):
        packet,report=fixture();graph=score.Graph(packet,report)
        event={'id':'commutative','kind':'multiply','reads':{'left':'origin.value','right':'offset.value'}}
        predicate={'kind':'multiply','reads':{'left':{'literal':61},'right':{'literal':5}}}
        aligned=graph.align(event,predicate)
        self.assertEqual(aligned['reads'],{'left':'offset.value','right':'origin.value'})
        self.assertEqual(event['reads']['left'],'origin.value')
        event['kind']=predicate['kind']='subtract'
        self.assertEqual(graph.align(event,predicate)['reads'],event['reads'])

if __name__=='__main__':unittest.main()
