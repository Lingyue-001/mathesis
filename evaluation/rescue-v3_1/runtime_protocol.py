"""Reference-free worker and immutable behavior manifest for rescue evaluation.

This Python audit hook detects accidental leakage; it is not an OS boundary for
hostile parser code. The complete worker stdout/stderr/exit status is preserved.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import copy

VERSION='rescue-runtime-1'
ROOT_INPUTS={'epoch_elapsed_years','epoch_inclusive_year','query_initial_rule_ordinal'}
PACKET_FIELDS={'schema_version','input_mode','provided_scope','primary_documents','context_documents','runtime_policy','context_tables','context_supplied_values','selected_profiles','event_horizon','boundary_events','generate_event_series'}
FORBIDDEN_KEYS={'expected_graph','expected_answer','expected_outputs','gold','reference','references','AST','ast','producer_id','goal_type','method_body','formal_returns','calls','events','task_exports','derived_inputs'}
BEHAVIOR_PATTERNS=(
    'analysis_parser/**/*','evaluation/rescue-v3_1/*.py','evaluation/rescue-v3_1/contracts/*',
    'evaluation/rescue-v3_1/development/inventory_*/*.json','evaluation/rescue-v3_1/development_packets/*','evaluation/rescue-v3_1/source_supplements/*','evaluation/rescue-v3_1/grammar_inventory.json',
    'evaluation/rescue-v3_1/registered_references/*','evaluation/rescue-v3_1/check_map.json',
    'tests/parser_rescue/*.py','tests/parser_v3/*.py','tests/parser/*.py',
    'evaluation/handoff-v3/*.py','evaluation/handoff-v3/*.json',
    'evaluation/handoff-v2/exposure-audit.json','evaluation/handoff-v2/package/evidence/page_index.json',
    'evaluation/handoff-v3/prospective/selection.json','reports/v3/exposure_registry_for_next_round.json',
    'handoff_v3/runtime_inputs/*.json','handoff_v3/reference/*.json','handoff_v3/sources/*.json',
    'rescue/package/contracts/*','rescue/package/tools/*.py','rescue/package/04_TRANSFER_AND_DECISION.md',
)


def _json_bytes(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def exclusive(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as handle: handle.write(_json_bytes(value))


def claim_first_attempt(experiment_root,source_digest,window_id):
    """Reserve source identity before executing; renaming cannot make a new first."""
    key=hashlib.sha256(source_digest.encode()).hexdigest()
    exclusive(Path(experiment_root)/'attempt_claims'/(key+'.json'),
              {'source_digest':source_digest,'window_id':window_id,
               'claimed_utc':datetime.now(timezone.utc).isoformat()})


def audit_query_order(report,inputs,execute_fn):
    """A fixed metamorphic audit on the already parsed immutable graph.

    One parser invocation; independent query calls are requested in reverse
    order. A dependency preventing reversal is reported, never removed.
    """
    program=report.get('program',report.get('program_index',{}))
    definitions={d['id']:d for d in program.get('definitions',[])}
    calls=[c for c in program.get('calls',[]) if definitions.get(c.get('definition_id'),{}).get('kind')=='QueryDef']
    groups={}
    for call in calls:
        base=call.get('base_value_ids',{})
        if base and call.get('base_ref'):
            key=(call['base_ref'],json.dumps(base,sort_keys=True))
            groups.setdefault(key,[]).append(call.get('id',call.get('call_id')))
    eligible=[group for group in groups.values() if len(group)>=2 and None not in group]
    if not eligible:return {'status':'not_applicable','reason':'no independent-base query-call group'}
    priority={cid:-i for group in eligible for i,cid in enumerate(group)}
    events=report.get('events',[]);by_id={e['id']:e for e in events}
    producers={v:e['id'] for e in events for v in e.get('writes',{}).values()}
    deps={e['id']:{producers[v] for v in e.get('reads',{}).values() if v in producers} for e in events}
    # A reversed call's prerequisites inherit its scheduling priority. Otherwise
    # the first forward call can run while a later literal is still waiting.
    ranks={e['id']:priority.get(e.get('call_id') or e.get('scope',{}).get('call_id'),1) for e in events}
    changed=True
    while changed:
        changed=False
        for eid,parents in deps.items():
            for parent in parents:
                if ranks[parent]>ranks[eid]:ranks[parent]=ranks[eid];changed=True
    ordered=[];done=set();position={e['id']:i for i,e in enumerate(events)}
    while len(done)<len(events):
        ready=[eid for eid in by_id if eid not in done and deps[eid]<=done]
        if not ready:return {'status':'dependency_cycle','event_ids':sorted(set(by_id)-done)}
        def rank(eid):
            return ranks[eid],position[eid]
        eid=min(ready,key=rank);done.add(eid);ordered.append(by_id[eid])
    altered=copy.deepcopy(report);altered['events']=ordered
    result=execute_fn(altered,inputs)
    return {'status':'executed','groups':eligible,'reordered_event_ids':[e['id'] for e in ordered],
            'source_report_sha256':hashlib.sha256(_json_bytes(report)).hexdigest(),
            'execution':result}


def validate(packet,inputs):
    if not isinstance(packet,dict) or not isinstance(inputs,dict): raise ValueError('Packet/inputs must be objects')
    if set(packet)-PACKET_FIELDS: raise ValueError('Undeclared source packet field: '+','.join(sorted(set(packet)-PACKET_FIELDS)))
    if set(inputs)-ROOT_INPUTS: raise ValueError('Undeclared initial input: '+','.join(sorted(set(inputs)-ROOT_INPUTS)))
    if packet.get('context_supplied_values'):raise ValueError('Derived/context-supplied values are forbidden in the source-only rescue runtime')
    for name,value in inputs.items():
        if type(value) is not int or value<0: raise ValueError('Initial input must be a nonnegative integer: '+name)
    if 'query_initial_rule_ordinal' in inputs and 'C2017_ST_concordance_midnight_frame_v1' not in packet.get('selected_profiles',[]):
        raise ValueError('Initial Rule selector requires the registered source-frame profile')
    def walk(item,path):
        if isinstance(item,dict):
            for key,value in item.items():
                if key in FORBIDDEN_KEYS: raise ValueError('Forbidden structured runtime field: '+'.'.join(path+[key]))
                walk(value,path+[key])
        elif isinstance(item,list):
            for i,value in enumerate(item):walk(value,path+[str(i)])
    walk(packet,[])


def run_isolated(packet,inputs,*,core_dir,timeout=60):
    try: validate(packet,inputs)
    except ValueError as error:
        return {'status':'input_rejected','error':{'type':'ValueError','message':str(error)},'stdout':'','stderr':'','exit_code':None,
                'runtime_audit':{'policy':VERSION,'blocked_accesses':[{'event':'input_validation','reason':str(error)}],'worker_started':False}}
    with tempfile.TemporaryDirectory(prefix='mathesis-rescue-runtime-') as temporary:
        root=Path(temporary)
        shutil.copytree(core_dir,root/'analysis_parser',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        shutil.copyfile(__file__,root/'runtime_protocol.py')
        (root/'input.json').write_bytes(_json_bytes({'packet':packet,'inputs':inputs}))
        args=[sys.executable,'-I','-X','utf8','-B',str(root/'runtime_protocol.py'),'--worker']
        try:
            process=subprocess.run(args,cwd=root,env={'PATH':os.environ.get('PATH',''),'LANG':'C.UTF-8'},capture_output=True,encoding='utf-8',timeout=timeout,check=False)
            stdout,stderr,exit_code=process.stdout,process.stderr,process.returncode
        except subprocess.TimeoutExpired as error:
            decode=lambda x:x.decode('utf8',errors='replace') if isinstance(x,bytes) else x or ''
            return {'status':'timeout','stdout':decode(error.stdout),'stderr':decode(error.stderr),'exit_code':None,'timeout_seconds':timeout,'runtime_audit_unavailable':True}
        try: result=json.loads(stdout)
        except (ValueError,TypeError): result={'status':'invalid_worker_output','runtime_audit_unavailable':True}
        if not isinstance(result,dict):result={'status':'invalid_worker_output','runtime_audit_unavailable':True}
        result.update(stdout=stdout,stderr=stderr,exit_code=exit_code)
        if exit_code: result['status']='process_error'
        return result


def _worker():
    # Preload guard dependencies; only core/input and standard-library reads follow.
    import dataclasses
    import fractions
    import re
    root=Path(__file__).resolve().parent; core=root/'analysis_parser';stdlib=Path(os.__file__).resolve().parent
    source=root/'input.json';opened=[];blocked=[]
    def within(path,parent):return path==parent or parent in path.parents
    def guard(event,args):
        if event in ('open','os.listdir','os.scandir'):
            if isinstance(args[0],int):return
            path=Path(os.fsdecode(args[0])).resolve()
            allowed=path==source or within(path,core) or within(path,stdlib) or (event!='open' and path==root)
            if not allowed:
                blocked.append({'event':event,'path':str(path)});raise PermissionError('Outside runtime allowlist: '+str(path))
            if event=='open':
                mode=args[1];flags=args[2] if len(args)>2 else 0
                if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
                    blocked.append({'event':event,'path':str(path),'mode':str(mode)});raise PermissionError('Runtime is read only')
                opened.append(str(path.relative_to(root)) if within(path,root) else 'stdlib/'+str(path.relative_to(stdlib)))
        if event.startswith('socket.') or event in ('subprocess.Popen','os.system','os.exec','os.spawn'):
            blocked.append({'event':event});raise PermissionError('Runtime network/external execution blocked')
    sys.addaudithook(guard);sys.path.insert(0,str(root));payload=json.loads(source.read_text(encoding='utf-8'))
    result={}
    try:
        from analysis_parser.pipeline import parse_packet
        from analysis_parser.execution import execute
        report=parse_packet(payload['packet']);execution=execute(report,payload['inputs'])
        result.update(status='completed',report=report,execution=execution,
                      reverse_query_execution=audit_query_order(report,payload['inputs'],execute))
    except Exception as error:result.update(status='runtime_error',error={'type':type(error).__name__,'message':str(error)})
    result['runtime_audit']={'policy':VERSION,'worker_started':True,'opened_files':sorted(set(opened)),'blocked_accesses':blocked,
        'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'python':sys.version,
        'scope':'Python audit-hook accidental leakage guard; not a hostile-code OS sandbox'}
    print(json.dumps(result,ensure_ascii=False))


def behavior_files(root):
    root=Path(root)
    names={p.relative_to(root).as_posix() for pattern in BEHAVIOR_PATTERNS for p in root.glob(pattern) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    # Machine-readable evidence named by frozen inventories is itself frozen.
    for name,key in [('evaluation/rescue-v3_1/grammar_inventory.json','probe_file'),('evaluation/rescue-v3_1/check_map.json','evidence')]:
        path=root/name
        if not path.is_file():continue
        try:
            document=json.loads(path.read_text(encoding='utf-8'));rows=document.get('productions',[]) if isinstance(document,dict) else document
            for row in rows:
                relative=row.get(key)
                if isinstance(relative,str) and not Path(relative).is_absolute() and '..' not in Path(relative).parts and (root/relative).is_file():names.add(relative)
        except (ValueError,TypeError,AttributeError):continue
    return sorted(names)


REQUIRED_BEHAVIOR_FILES=(
    'analysis_parser/pipeline.py','analysis_parser/execution.py','analysis_parser/operations.py',
    'evaluation/rescue-v3_1/fixed_scoring.py','evaluation/rescue-v3_1/observed_graph.py',
    'evaluation/rescue-v3_1/method_evidence.py','evaluation/rescue-v3_1/evidence_contracts.py',
    'evaluation/rescue-v3_1/chain_gate.py','evaluation/rescue-v3_1/runtime_protocol.py',
    'evaluation/rescue-v3_1/prospective_protocol.py','evaluation/rescue-v3_1/production_inventory.py',
    'evaluation/rescue-v3_1/grammar_inventory.json','evaluation/rescue-v3_1/check_map.json',
    'evaluation/rescue-v3_1/contracts/scoring_support.json','evaluation/rescue-v3_1/contracts/selection_policy.json',
    'evaluation/handoff-v3/prospective/selection.json','reports/v3/exposure_registry_for_next_round.json',
    'evaluation/handoff-v2/exposure-audit.json','evaluation/handoff-v3/exposure_registry_merged.json',
    'evaluation/rescue-v3_1/contracts/source_assets.json',
)


def inventory_errors(root, *, source_asset_paths=None):
    root=Path(root)
    errors=[{'path':p,'cause':'missing_required_behavior_file'} for p in REQUIRED_BEHAVIOR_FILES if not (root/p).is_file()]
    inventory=root/'evaluation/rescue-v3_1/grammar_inventory.json'
    if inventory.is_file():
        try:
            document=json.loads(inventory.read_text(encoding='utf-8'));rows=document['productions']
            if not rows or len(rows)!=document['production_count'] or len({r['production_id'] for r in rows})!=len(rows):raise ValueError('Invalid production identity inventory')
            for row in rows:
                name=row['probe_file'];path=root/name
                if Path(name).is_absolute() or '..' in Path(name).parts or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row.get('probe_sha256'):errors.append({'path':name,'cause':'invalid_production_probe_evidence'})
        except (KeyError,ValueError,TypeError,AttributeError):errors.append({'path':str(inventory.relative_to(root)),'cause':'invalid_required_metadata'})
    assets=root/'evaluation/rescue-v3_1/contracts/source_assets.json'
    if assets.is_file():
        try:
            rows=json.loads(assets.read_text(encoding='utf-8'))['files']
            if not rows:raise ValueError('Missing source identities')
            for row in rows:
                mapped=(source_asset_paths or {}).get(row['path'],row['path'])
                path=Path(mapped)
                if not path.is_absolute():path=root/path
                if row.get('present') is not True or not path.is_file() or path.stat().st_size!=row.get('bytes') or hashlib.sha256(path.read_bytes()).hexdigest()!=row.get('sha256'):errors.append({'path':row['path'],'resolved_path':str(path),'cause':'source_asset_identity_mismatch'})
        except (KeyError,ValueError,TypeError):errors.append({'path':str(assets.relative_to(root)),'cause':'invalid_source_asset_metadata'})
    return errors


def manifest(root, *, source_asset_paths=None):
    root=Path(root);errors=inventory_errors(root,source_asset_paths=source_asset_paths)
    return {'protocol':VERSION,'created_utc':datetime.now(timezone.utc).isoformat(),'closed_behavior_inventory':not errors,'inventory_errors':errors,
            **({'source_asset_paths':dict(source_asset_paths)} if source_asset_paths is not None else {}),
            'environment':{'python':sys.version,'platform':platform.platform(),'dependencies':'Python standard library'},
            'files':[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),'bytes':(root/p).stat().st_size} for p in behavior_files(root)]}


def verify(root,record):
    root=Path(root);errors=inventory_errors(root,source_asset_paths=record.get('source_asset_paths'));items=record.get('files',[])
    expected={x['path']:x['sha256'] for x in items}
    if record.get('protocol')!=VERSION or record.get('closed_behavior_inventory') is not True or len(expected)!=len(items):errors.append({'cause':'invalid_or_incomplete_behavior_manifest'})
    for name in sorted(set(expected)|set(behavior_files(root))):
        path=root/name
        if Path(name).is_absolute() or '..' in Path(name).parts:errors.append({'path':name,'cause':'invalid_manifest_path'});continue
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual!=expected.get(name): errors.append({'path':name,'expected':expected.get(name),'actual':actual})
    return errors


if __name__=='__main__':
    if sys.argv[1:]!=['--worker']:raise SystemExit('Use protocol functions from evaluation driver')
    _worker()
