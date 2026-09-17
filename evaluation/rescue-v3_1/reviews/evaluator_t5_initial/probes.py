"""Independent T5 round-0 probes. A3 and synthetic material only; no first/freeze."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys,traceback
ROOT=Path(__file__).resolve().parents[4]
HERE=ROOT/'evaluation/rescue-v3_1'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
import fixed_scoring as scoring
import runtime_protocol as runtime
import prospective_protocol as prospective
from chain_gate import assess
from analysis_parser.execution import execute
OUT=Path(__file__).resolve().parent

def load(name):
 raw=json.loads((HERE/'checkpoints/A3'/f'{name}.json').read_text())
 payload=json.loads((HERE/'checkpoints/A3/inputs'/f'{name}.json').read_text())
 ref=json.loads((HERE/'registered_references'/f'{name}.json').read_text())
 contract=json.loads((HERE/'contracts/chain_contracts.json').read_text())[name]
 return payload,raw,ref,contract

def score(name, mutate=None, execute_again=False):
 payload,raw,ref,contract=load(name)
 if mutate:mutate(raw)
 if execute_again:
  raw['execution']=execute(raw['report'],payload['inputs'])
  raw['reverse_query_execution']=runtime.audit_query_order(raw['report'],payload['inputs'],execute)
 scored=scoring.evaluate(payload['packet'],raw['report'],ref,execution=raw['execution'],auxiliary=raw)
 chain=assess(payload['packet'],raw['report'],raw['execution'],scored,contract,scoring.Graph)
 return dict(relations=scored['relations'],passed=scored['all_obligations_passed'],chain=chain['full_chain_passed'],chain_checks=chain['checks'],source_errors=scored['source_errors'],blockers=scored['blocking_diagnostics'],unresolved=raw['execution'].get('unresolved'),method_results={e['id']:raw['execution'].get('event_results',{}).get(e['id']) for e in raw['report']['events'] if e['kind']=='method_call'},witnesses=scored['contract_witness_events'])

def method_returns_swap(raw):
 report=raw['report']
 for method in report.get('method_library',[]):
  if set(method['returns']) != {'result','remainder'}:continue
  method['returns']={k:method['returns']['result' if k=='remainder' else 'remainder'] for k in ['result','remainder']}
  for event in report['events']:
   if event.get('attributes',{}).get('target')!=method['id']:continue
   event['attributes']['formal_returns']=copy.deepcopy(method['returns'])
   old=event['method_binding']['return_bindings'];a=event['writes']['result'];b=event['writes']['remainder']
   updated=dict(old);updated[a],updated[b]=old[b],old[a]
   event['method_binding']['return_bindings']=updated
   for instance in report['method_instances']:
    if instance['call_event_id']==event['id']:instance['return_bindings']=copy.deepcopy(updated)

def corrupt_witness(raw):
 report=raw['report']
 for method in report['method_library']:
  for node in method['body']:
   if node['kind']=='count':node['attributes']['cyclic']=False
  for event in report['events']:
   if event.get('attributes',{}).get('target')==method['id']:event['attributes']['body']=copy.deepcopy(method['body'])
  for instance in report['method_instances']:
   if instance['definition_id']==method['id']:
    for node in instance['events']:
     if node['kind']=='count':node['attributes']['cyclic']=False

def no_execution_trace(raw):
 raw['execution']['execution_trace']=[];raw['execution']['event_results']={}

def duplicate_id_wrong_first(raw):
 event=copy.deepcopy(next(e for e in raw['report']['events'] if e['kind']=='multiply'))
 event['reads']['right']=event['reads']['left']
 raw['report']['events'].insert(0,event)

def synthetic_fixture():
 source='以甲乘乙'
 anchor={'doc_id':'test','reading_id':'test.declared','start':0,'end':len(source),'quote':source}
 packet={'primary_documents':[{'doc_id':'test','text':source}]}
 events=[];values=[]
 for i in range(2):
  events.append({'id':f'p{i}','kind':'parameter','reads':{},'writes':{'result':f'v{i}'},'source_spans':[anchor],'attributes':{'name':f'arg{i}','value':i+1}})
  values.append({'id':f'v{i}','producer':f'p{i}','output_port':'result','labels':[f'arg{i}']})
 events.append({'id':'main','kind':'multiply','reads':{'left':'v0','right':'v1'},'writes':{},'source_spans':[anchor]})
 ref={'cards':[{'card_id':'synthetic','obligations':[{'id':'syn.1','anchor':anchor}]}],'policy':{'supported_actions':['multiply'],'obligations':{'syn.1':{'events':[{'kind':'multiply','reads':{'left':{'parameter':'arg0'},'right':{'parameter':'arg1'}}}]}}}}
 return packet,{'events':events,'value_instances':values},ref

def synthetic_probes():
 packet,report,ref=synthetic_fixture();results={}
 normalized=scoring.normalized(ref)
 for typ in ['omit_atom','duplicate_predicate']:
  r=copy.deepcopy(normalized)
  if typ=='omit_atom':
   r['policy']['fixed_atoms']=[a for a in r['policy']['fixed_atoms'] if '/reads/' not in a['predicate_path']]
   bad=copy.deepcopy(report);bad['events'][-1]['reads']['right']='v0'
  else:
   atom=copy.deepcopy(r['policy']['fixed_atoms'][0]);atom['atom_id']='duplicate';r['policy']['fixed_atoms'].append(atom);bad=report
  r['policy']['fixed_atom_count']=len(r['policy']['fixed_atoms'])
  registration=scoring.register(r);s=scoring.evaluate(packet,bad,r)
  results[typ]={'registered_count':registration['gold_atom_count'],'relations':s['relations'],'passed':s['all_obligations_passed']}
 for kind in ['repeat','lookup','not_supported_anywhere']:
  r=copy.deepcopy(ref);r['policy']['obligations']['syn.1']['events'][0]['kind']=kind
  registration=scoring.register(r);results['register_'+kind]={'accepted':True,'registered_count':registration['gold_atom_count']}
 for value in [{'severity':'warning','unresolved':['bad']},{'severity':'error','cause':'bad'}, {'status':'ok','errors':['bad']}, {'wrapper':{'incomplete':'bad'}}]:
  results['diag_'+json.dumps(value)]=scoring.blocking_diagnostics({'diagnostics':value})
 return results

def main():
 results={}
 probes=[('baseline_'+n,lambda n=n:score(n)) for n in ['A01','A02','A03','A04']]
 probes += [('swap_method_returns_'+n,lambda n=n:score(n,method_returns_swap,True)) for n in ['A01','A02','A04']]
 probes += [('corrupt_witness_A04',lambda:score('A04',corrupt_witness,True)),('no_execution_evidence_A03',lambda:score('A03',no_execution_trace)),('duplicate_id_A03',lambda:score('A03',duplicate_id_wrong_first)),('synthetic',synthetic_probes)]
 for name,func in probes:
  try:results[name]=func()
  except Exception as err:results[name]={'error':type(err).__name__,'message':str(err),'traceback':traceback.format_exc()}
 (OUT/'probe_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
