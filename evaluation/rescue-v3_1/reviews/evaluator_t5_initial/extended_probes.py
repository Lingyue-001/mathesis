from probes import *
import tempfile

def replace_body_source(raw):
 report=raw['report'];replacement=report['events'][0]['source_spans']
 for method in report['method_library']:
  for node in method['body']:
   if node['kind']=='count':node['source_spans']=copy.deepcopy(replacement)
  for event in report['events']:
   if event.get('attributes',{}).get('target')==method['id']:event['attributes']['body']=copy.deepcopy(method['body'])
  for instance in report.get('method_instances',[]):
   if instance['definition_id']==method['id']:
    for node in instance['events']:
     if node['kind']=='count':node['source_spans']=copy.deepcopy(replacement)

def diagnostic(raw, value):raw['report']['diagnostics']=value

def repeat_probe():
 packet,report,ref=synthetic_fixture();anchor=report['events'][-1]['source_spans'][0]
 # Build a fully executable synthetic loop; the display control says >3,
 # while the executor-visible attributes silently say >=3.
 report={'events':[],'value_instances':[]}
 for name,n in [('initial',0),('increment',1),('threshold',3)]:
  report['events'].append({'id':name,'kind':'literal','reads':{},'writes':{'result':name+'.v'},'attributes':{'value':n},'source_spans':[anchor]})
  report['value_instances'].append({'id':name+'.v','producer':name,'output_port':'result','role':'literal','scope':{},'labels':[]})
 control={'test':'post','stop':{'operator':'gt'},'counter':{'initial':0,'increment':1},'body':[
  {'kind':'add','reads':{'left':'$state','right':'$increment'},'writes':{'result':'state'}},
  {'kind':'add','reads':{'left':'$counter','right':'$counter_increment'},'writes':{'result':'counter'}}]}
 event={'id':'loop','kind':'repeat','reads':{n:n+'.v' for n in ['initial','increment','threshold']},'writes':{'state':'out','count':'counter'},'control':copy.deepcopy(control),'attributes':{'control':copy.deepcopy(control)},'source_spans':[anchor]}
 report['events'].append(event)
 for v,port in [('out','state'),('counter','count')]:report['value_instances'].append({'id':v,'producer':'loop','output_port':port,'role':'temporary','scope':{},'labels':[]})
 ref['policy']['supported_actions']=['repeat']
 ref['policy']['obligations']['syn.1']['events']=[{'kind':'repeat','reads':{n:{'literal':v} for n,v in [('initial',0),('increment',1),('threshold',3)]},'control':copy.deepcopy(control)}]
 before=execute(report,{})
 event['attributes']['control']['stop']['operator']='ge'
 after=execute(report,{})
 result=scoring.evaluate(packet,report,ref,execution=after)
 return {'before':before['event_results']['loop'],'after':after['event_results']['loop'],'unresolved':after['unresolved'],'relations':result['relations'],'passed':result['all_obligations_passed']}

def qualify_probe():
 fixture_root=Path(tempfile.mkdtemp(dir=OUT,prefix='synthetic_protocol_fixture-'))
 # A metadata fixture for lock_batch validation only. Neither freeze() nor
 # run_first() is called, and no experiment is frozen or run.
 fixture_manifest=fixture_root/'manifest_only';fixture_manifest.mkdir(exist_ok=True)
 (fixture_manifest/'manifest.json').write_bytes(runtime._json_bytes(runtime.manifest(ROOT)))
 entries=[]
 for i in range(8):
  packet,report,ref=synthetic_fixture()
  packet['primary_documents'][0]['text']+='，測例'+str(i)
  for p in ref['policy']['obligations']['syn.1']['events']:p['kind']='not_supported_anywhere'
  entries.append({'window_id':'SYNTHETIC_'+str(i),'track':'A' if i<4 else 'B','combination':str(i%2),
   'payload':{'packet':packet,'inputs':{}},'reference':ref,
   'chain_contract':{'required_exports':[{'label':'fake','unit':'fake'}],'root':'missing_input'},'structural_contract':{'fake':True},
   'certificates':{k:{'passed':True,'evidence':'NOT_A_SOURCE_OR_FROZEN_IDENTIFIER'} for k in ['lexical_construction','program_control','background_root_inputs','interpretation_profile','frozen_scoring_support','novel_dependency_composition']}})
 (fixture_root/'requested_entries.json').write_bytes(runtime._json_bytes(entries))
 record=prospective.lock_batch(fixture_root/'accepted_batch',fixture_manifest,entries,[])
 return {'accepted':True,'windows':len(record['windows']),'qualification_log':[],'unsupported_reference_action':'not_supported_anywhere','all_certificate_evidence':'NOT_A_SOURCE_OR_FROZEN_IDENTIFIER','real_freeze_or_first_called':False}

def identity_alias_probe():
 packet,report,ref=synthetic_fixture();report['value_instances'][0]['unit']='day'
 # Both endpoint metadata and transparent producer must agree on the type.
 report['events'].insert(-1,{'id':'alias','kind':'alias','reads':{'value':'v0'},'writes':{'result':'av'},'source_spans':report['events'][0]['source_spans']})
 report['value_instances'].append({'id':'av','producer':'alias','output_port':'result','labels':[],'unit':'month'})
 report['events'][-1]['reads']['left']='av';ref['policy']['obligations']['syn.1']['events'][0]['reads']['left']['unit']='day'
 result=scoring.evaluate(packet,report,ref)
 return {'passed':result['all_obligations_passed'],'relations':result['relations'],'actual_endpoint_unit':'month','producer_unit':'day','required_unit':'day'}

def missing_manifest_required_files():
 with tempfile.TemporaryDirectory(dir=OUT,prefix='manifest-probe-') as directory:
  p=Path(directory);(p/'analysis_parser').mkdir();(p/'analysis_parser/core.py').write_text('x=1\n')
  m=runtime.manifest(p)
  return {'closed_behavior_inventory':m['closed_behavior_inventory'],'files':[x['path'] for x in m['files']],'verification_errors':runtime.verify(p,m),'required_files_absent':['grammar_inventory.json','check_map.json','selection_policy.json']}

def main():
 results={}
 probes=[('method_count_uses_unrelated_source_A02',lambda:score('A02',replace_body_source,True)),('control_execution_identity',repeat_probe),('qualification_accepts_unverifiable_evidence',qualify_probe),('alias_conflicting_unit',identity_alias_probe),('manifest_missing_required_metadata',missing_manifest_required_files)]
 for value in [[{'kind':'incomplete_construction'}],{'kind':'UnsupportedConstruction'}, {'severity':'warning','unresolved':['bad']}, {'status':'ok','errors':['bad']}]:
  probes.append(('chain_diag_'+json.dumps(value),lambda value=value:score('A03',lambda raw:diagnostic(raw,value))))
 for name,func in probes:
  try:results[name]=func()
  except Exception as err:results[name]={'error':type(err).__name__,'message':str(err),'traceback':traceback.format_exc()}
 (OUT/'extended_probe_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(results,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
