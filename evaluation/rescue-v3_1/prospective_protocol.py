"""Freeze, lock, and single-attempt batch protocol; no candidate search or probing."""
import hashlib
import ast
import json
from pathlib import Path
import shutil
import re
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import runtime_protocol as runtime
import fixed_scoring as scoring
from chain_gate import assess


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source_digest(payload):
    texts=[d['text'] for d in payload['packet']['primary_documents']]
    return hashlib.sha256(runtime._json_bytes(texts)).hexdigest()


GATE_KEYS=('engineering35','old_A22','old_A4_chains','v3_94','inherited61','civil47','civil112','v2_W01_W04','core_review_accepted','evaluator_review_accepted')
CERTIFICATES=('lexical_construction','program_control','background_root_inputs','interpretation_profile','frozen_scoring_support','novel_dependency_composition')


def checked_path(root,name):
    if not isinstance(name,str) or Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Invalid relative evidence path')
    path=Path(root)/name
    if not path.is_file():raise ValueError('Missing evidence file: '+name)
    return path


def validate_gate(gate,evidence_root):
    if any(gate.get('checks',{}).get(key) is not True for key in GATE_KEYS):raise ValueError('Development gate not met')
    for key in GATE_KEYS:
        entry=gate.get('evidence',{}).get(key,{})
        if digest(checked_path(evidence_root,entry.get('path')))!=entry.get('sha256'):raise ValueError('Missing/mutated gate evidence: '+key)


def freeze(destination,gate):
    destination=Path(destination);validate_gate(gate,ROOT)
    before=runtime.manifest(ROOT)
    if runtime.verify(ROOT,before):raise ValueError('Incomplete behavior inventory')
    destination.mkdir(parents=True,exist_ok=False)
    for item in before['files']:
        target=destination/'snapshot'/item['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/item['path'],target)
    for entry in gate['evidence'].values():
        target=destination/'gate_evidence'/entry['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(checked_path(ROOT,entry['path']),target)
    if runtime.verify(ROOT,before):raise ValueError('Behavior changed while freezing')
    runtime.exclusive(destination/'manifest.json',before);runtime.exclusive(destination/'development_gate.json',gate)
    runtime.exclusive(destination/'accepted_development_freeze.json',{'protocol':runtime.VERSION,'manifest_sha256':digest(destination/'manifest.json'),'development_gate_sha256':digest(destination/'development_gate.json')})
    return before


def accepted_freeze(freeze_dir):
    freeze_dir=Path(freeze_dir)
    required=('manifest.json','development_gate.json','accepted_development_freeze.json')
    if any(not (freeze_dir/p).is_file() for p in required):raise ValueError('An accepted development freeze is required; manifest alone is insufficient')
    frozen=json.loads((freeze_dir/'manifest.json').read_text());accepted=json.loads((freeze_dir/'accepted_development_freeze.json').read_text())
    if accepted!={'protocol':runtime.VERSION,'manifest_sha256':digest(freeze_dir/'manifest.json'),'development_gate_sha256':digest(freeze_dir/'development_gate.json')}:raise ValueError('Invalid development freeze acceptance')
    gate=json.loads((freeze_dir/'development_gate.json').read_text());validate_gate(gate,freeze_dir/'gate_evidence')
    if runtime.verify(ROOT,frozen) or runtime.verify(freeze_dir/'snapshot',frozen):raise ValueError('Behavior differs from accepted complete freeze')
    return frozen


def all_spans(value):
    if isinstance(value,dict):
        if {'doc_id','reading_id','start','end','quote'}<=set(value):yield value
        else:
            for v in value.values():yield from all_spans(v)
    elif isinstance(value,list):
        for v in value:yield from all_spans(v)


def validate_goal_contracts(entry):
    payload=entry['payload'];packet=payload['packet'];inputs=payload['inputs'];runtime.validate(packet,inputs)
    graph=scoring.Graph(packet,{'events':[],'value_instances':[]});goal=entry.get('chain_contract',{});structure=entry.get('structural_contract',{})
    docs=packet.get('primary_documents',[])+packet.get('context_documents',[])
    if not packet.get('primary_documents') or len({d['doc_id'] for d in docs})!=len(docs):raise ValueError('Missing/duplicate source document identity')
    if set(goal)!={'required_exports','root'} or goal.get('root') not in inputs or goal['root'] not in runtime.ROOT_INPUTS:raise ValueError('Invalid goal/root contract')
    lawful=entry.get('reference',{}).get('lawful_inputs')
    if lawful is not None and lawful!=inputs:raise ValueError('Input values differ from preregistered lawful inputs')
    profiles=entry.get('reference',{}).get('profile_selection',{}).get('selected_profiles')
    if profiles is not None and profiles!=packet.get('selected_profiles',[]):raise ValueError('Input profiles differ from preregistered selection')
    exports=goal.get('required_exports')
    if not isinstance(exports,list) or not exports:raise ValueError('Empty goal exports')
    labels=[]
    for export in exports:
        if not isinstance(export,dict) or not set(export)<={'label','unit','instances'} or not all(isinstance(export.get(k),str) and export[k] for k in ('label','unit')) or type(export.get('instances',1)) is not int or export.get('instances',1)<1 or export.get('unit') not in scoring.SUPPORT['value_units']:raise ValueError('Invalid export requirement')
        labels.append(export['label'])
    if len(labels)!=len(set(labels)):raise ValueError('Duplicate export registration')
    if set(structure)!={'frames','predicates'} or not all(isinstance(structure[k],list) and structure[k] for k in structure):raise ValueError('Invalid structural contract')
    primary={d['doc_id'] for d in packet['primary_documents']}
    for frame in structure['frames']:
        if set(frame)!={'kind','goal_surface','doc_id'} or frame['kind'] not in ('ProcedureDef','QueryDef') or frame['doc_id'] not in primary or not isinstance(frame['goal_surface'],str) or not frame['goal_surface']:raise ValueError('Invalid frame registration')
    inventory=json.loads((HERE/'grammar_inventory.json').read_text())
    kinds={p['ast_kind'] for p in inventory['productions']}
    for predicate in structure['predicates']:
        if set(predicate)!={'kind','anchor'} or not isinstance(predicate['kind'],str) or predicate['kind'] not in kinds or not graph.valid_span(predicate['anchor']):raise ValueError('Invalid predicate boundary registration')
    for span in all_spans(entry.get('reference',{})):
        if not graph.valid_span(span):raise ValueError('Invalid reference source span')
    return graph


def validate_certificates(entry,frozen):
    graph=validate_goal_contracts(entry);known={f['path']:f['sha256'] for f in frozen['files']}
    inventory_path='evaluation/rescue-v3_1/grammar_inventory.json';support_path='evaluation/rescue-v3_1/contracts/scoring_support.json'
    inventory=json.loads((ROOT/inventory_path).read_text());productions={p['production_id']:p for p in inventory['productions']}
    registration=scoring.register(entry['reference']);atoms={a['predicate_path'] for a in registration['atoms']}
    support_ids={'action:'+k for k in scoring.SUPPORT['actions']}|{'contract:'+k for k in scoring.SUPPORT['contract_requirements']}|{'method_role:'+k for k in scoring.SUPPORT['method_roles']}
    required_files={
        'lexical_construction':{inventory_path},
        'program_control':{'analysis_parser/program_ir.py','analysis_parser/control_ir.py','analysis_parser/operations.py'},
        'background_root_inputs':{'evaluation/rescue-v3_1/runtime_protocol.py','analysis_parser/inputs.py'},
        'interpretation_profile':{'analysis_parser/resources.py'},
        'frozen_scoring_support':{support_path,'evaluation/rescue-v3_1/fixed_scoring.py','evaluation/rescue-v3_1/evidence_contracts.py'},
        'novel_dependency_composition':{inventory_path,'evaluation/rescue-v3_1/contracts/selection_policy.json'}}
    # Read frozen literal resource definitions without importing or running parser code.
    resource_tree=ast.parse((ROOT/'analysis_parser/resources.py').read_text());profiles=set()
    for node in resource_tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('PROFILES','SOURCE_PROFILES') for t in node.targets):profiles.update(ast.literal_eval(node.value))
    if set(entry['payload']['packet'].get('selected_profiles',[]))-profiles:raise ValueError('Profile is absent from frozen interpretation resources')
    for key in CERTIFICATES:
        cert=entry.get('certificates',{}).get(key,{})
        evidence=cert.get('evidence')
        if cert.get('passed') is not True or not isinstance(evidence,dict):raise ValueError('Incomplete A qualification: '+key)
        spans=evidence.get('source_spans');files=evidence.get('frozen_files')
        if not isinstance(spans,list) or not spans or not all(isinstance(span,dict) and graph.valid_span(span) for span in spans):raise ValueError('Invalid certificate source spans: '+key)
        if not isinstance(files,list) or not files:raise ValueError('Missing frozen certificate files: '+key)
        for item in files:
            if not isinstance(item,dict) or item.get('path') not in known or item.get('sha256')!=known[item['path']]:raise ValueError('Unverifiable frozen certificate evidence: '+key)
        cited={item['path'] for item in files}
        if not required_files[key]<=cited:raise ValueError('Missing applicable frozen behavior evidence: '+key)
        for production_id in evidence.get('production_ids',[]):
            if production_id not in productions or inventory_path not in cited or productions[production_id].get('positive_reachable') is not True:raise ValueError('Unsupported frozen production identifier')
        if key=='lexical_construction':
            if not evidence.get('production_ids'):raise ValueError('Missing lexical production coverage')
            for card in entry['reference']['cards']:
                for obligation in card['obligations']:
                    anchor=obligation['anchor']
                    if not any(s['doc_id']==anchor['doc_id'] and s['reading_id']==anchor['reading_id'] and s['start']<=anchor['start'] and anchor['end']<=s['end'] for s in spans):raise ValueError('Missing source obligation closure evidence')
        if key=='frozen_scoring_support':
            ids=evidence.get('support_ids',[])
            if support_path not in cited or not ids or set(ids)-support_ids or set(evidence.get('atom_paths',[]))!=atoms or len(evidence.get('atom_paths',[]))!=len(atoms):raise ValueError('Incomplete frozen scoring support evidence')
            needed={'contract:'+c['type'] for c in entry['reference']['policy'].get('contracts',{}).values()}
            def actions(value):
                if isinstance(value,dict):
                    if 'kind' in value and isinstance(value['kind'],str) and value['kind'] in scoring.SUPPORT['actions']:needed.add('action:'+value['kind'])
                    for v in value.values():actions(v)
                elif isinstance(value,list):
                    for v in value:actions(v)
            actions(entry['reference']['policy']['obligations'])
            if not needed<=set(ids):raise ValueError('Missing action/contract support identifier')
        if key=='background_root_inputs' and evidence.get('root_inputs')!=entry['payload']['inputs']:raise ValueError('Root-input qualification mismatch')
        if key=='interpretation_profile' and evidence.get('selected_profiles')!=entry['payload']['packet'].get('selected_profiles',[]):raise ValueError('Profile qualification mismatch')
        if key=='novel_dependency_composition' and (evidence.get('combination')!=entry.get('combination') or not isinstance(evidence.get('description'),str) or not evidence['description'].strip()):raise ValueError('Missing documented composition novelty')


def candidate_order(candidate):
    parts=str(candidate['id']).split('.')
    if not all(p.isdecimal() for p in parts):raise ValueError('Candidate ID must retain numeric book/procedure identity')
    return tuple(int(p) for p in parts)


def validate_qualification_log(entries,log,frozen):
    policy=json.loads((HERE/'contracts/selection_policy.json').read_text());known={f['path']:f['sha256'] for f in frozen['files']}
    exposure_paths=list(dict.fromkeys([*policy['inherited_exposure'],'evaluation/handoff-v3/exposure_registry_merged.json']))
    paths=[policy['candidate_universe'],*exposure_paths,'evaluation/rescue-v3_1/contracts/selection_policy.json']
    if not isinstance(log,dict) or log.get('schema_version')!='rescue-qualification-log-1' or log.get('parser_runs_before_lock')!=0 or log.get('seed')!=policy['seed']:raise ValueError('Missing deterministic qualification/exposure log')
    sources={r.get('path'):r.get('sha256') for r in log.get('frozen_inputs',[]) if isinstance(r,dict)}
    if any(sources.get(p)!=known.get(p) or p not in known for p in paths):raise ValueError('Qualification log does not bind frozen selection/exposure inputs')
    universe=json.loads((ROOT/policy['candidate_universe']).read_text())['candidate_universe'];universe=sorted(universe,key=candidate_order)
    by_id={c['id']:c for c in universe};excluded={c['id'] for c in universe if c.get('exposed') or c.get('source_unavailable')}
    for path in exposure_paths:
        exposure=json.loads((ROOT/path).read_text());excluded.update(exposure.get('procedure_ids',[]))
    selected={e.get('candidate_id'):e for e in entries}
    if len(selected)!=8 or None in selected or not set(selected)<=set(by_id):raise ValueError('Missing/duplicate frozen candidate identities')
    rows=log.get('A_reviews');brows=log.get('B_selection')
    if not isinstance(rows,list) or not isinstance(brows,list):raise ValueError('Missing A review/B selection records')
    cursor=0;chosen=[];exposed=set(excluded)
    def expose(row,candidate):
        pages=set(candidate.get('source_locator',{}).get('pdf_pages',[]))
        if set(row.get('read_pages',[]))!=pages:raise ValueError('Incomplete page exposure log')
        expected={c['id'] for c in universe if pages.intersection(c.get('source_locator',{}).get('pdf_pages',[]))}
        contexts=row.get('context_candidate_ids',[])
        if not set(contexts)<=set(by_id):raise ValueError('Unknown context candidate')
        expected.update(contexts)
        if set(row.get('exposed_candidate_ids',[]))!=expected:raise ValueError('Incomplete candidate exposure propagation')
        exposed.update(expected)
    for row in rows:
        while cursor<len(universe) and universe[cursor]['id'] in exposed:cursor+=1
        if cursor>=len(universe) or row.get('candidate_id')!=universe[cursor]['id'] or len(chosen)>=4:raise ValueError('A review is not complete deterministic order')
        candidate=universe[cursor];cid=candidate['id'];cursor+=1
        if row.get('decision') not in ('qualified','rejected') or not isinstance(row.get('reason'),str) or not row['reason']:raise ValueError('Missing qualification decision/reason')
        if row['decision']=='qualified':
            if cid not in selected or selected[cid]['track']!='A':raise ValueError('Qualified candidate omitted/replaced')
            chosen.append(cid)
        expose(row,candidate)
    if len(chosen)!=4 or set(chosen)!={e['candidate_id'] for e in entries if e['track']=='A'}:raise ValueError('Insufficient eligible A material')
    remaining=[c for c in universe if c['id'] not in exposed]
    if len(brows)!=4:raise ValueError('Incomplete B selection')
    for row in brows:
        remaining=[c for c in remaining if c['id'] not in exposed]
        if not remaining or row.get('candidate_id')!=remaining[0]['id']:raise ValueError('B selection is not earliest remaining candidate')
        candidate=remaining.pop(0);cid=candidate['id']
        if cid not in selected or selected[cid]['track']!='B':raise ValueError('B candidate replaced')
        expose(row,candidate)
    for cid,entry in selected.items():
        if entry.get('source_locator')!=by_id[cid]['source_locator']:raise ValueError('Candidate source locator mismatch')


def lock_batch(destination,freeze_dir,entries,qualification_log):
    destination=Path(destination);freeze_dir=Path(freeze_dir);frozen=accepted_freeze(freeze_dir)
    if len(entries)!=8 or sum(e['track']=='A' for e in entries)!=4 or sum(e['track']=='B' for e in entries)!=4:raise ValueError('Both tracks require four windows before any first run')
    if len({source_digest(e['payload']) for e in entries})!=8 or len({e['window_id'] for e in entries})!=8:raise ValueError('Duplicate source/identifier')
    source_ids=set();source_bodies=set()
    for entry in entries:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',entry['window_id']):raise ValueError('Invalid output window identifier')
        for doc in entry['payload']['packet']['primary_documents']:
            identity=doc['doc_id'];body=hashlib.sha256(doc['text'].encode()).hexdigest()
            if identity in source_ids or body in source_bodies:raise ValueError('Repeated primary source identity/body')
            source_ids.add(identity);source_bodies.add(body)
    combinations={e.get('combination') for e in entries if e['track']=='A'}
    if None in combinations or len(combinations)<2:raise ValueError('At least two certified task/query combinations required')
    for entry in entries:
        validate_goal_contracts(entry);registration=scoring.register(entry['reference'],track=entry['track'])
        if not registration['gold_atom_count']:raise ValueError('Empty fixed reference')
        if entry['track']=='A':
            validate_certificates(entry,frozen)
            if entry.get('reference_unsupported'):raise ValueError('A reference exceeds frozen scoring support')
    validate_qualification_log(entries,qualification_log,frozen)
    destination.mkdir(parents=True,exist_ok=False)
    runtime.exclusive(destination/'qualification.json',qualification_log)
    for entry in entries:runtime.exclusive(destination/'entries'/(entry['window_id']+'.json'),entry)
    files=[{'path':str(p.relative_to(destination)),'sha256':digest(p)} for p in sorted(destination.rglob('*')) if p.is_file()]
    record={'freeze_manifest_sha256':digest(freeze_dir/'manifest.json'),'files':files,
        'windows':[{'window_id':e['window_id'],'track':e['track'],'source_digest':source_digest(e['payload'])} for e in entries]}
    runtime.exclusive(destination/'manifest.json',record);return record


def structures(packet,report,score,contract):
    graph=scoring.Graph(packet,report);program=report.get('program',{});nodes=report.get('syntax',{}).get('nodes',[])
    frames=contract.get('frames',[]);boundaries=contract.get('predicates',[])
    frame_ok=bool(frames) and all(any(d.get('kind')==f['kind'] and d.get('goal_surface')==f['goal_surface'] and any(s.get('doc_id')==f['doc_id'] for s in d.get('source_spans',[])) for d in program.get('definitions',[])) for f in frames)
    boundary_ok=bool(boundaries) and all(any(n.get('kind')==p['kind'] and graph.at(n,p['anchor']) for n in nodes) for p in boundaries)
    relations=[check for row in score['obligations'] for check in row['checks'] if '/reads/' in check['predicate_path'] or 'actual_binding' in check['predicate_path']]
    producer_ok=bool(relations) and all(c['passed'] for c in relations) and not graph.source_errors
    return {'frame':frame_ok,'predicate_boundary':boundary_ok,'producer_link':producer_ok,'all_passed':frame_ok and boundary_ok and producer_ok}


def run_first(destination,freeze_dir,batch_dir):
    destination=Path(destination);freeze_dir=Path(freeze_dir);batch_dir=Path(batch_dir)
    frozen=accepted_freeze(freeze_dir);batch=json.loads((batch_dir/'manifest.json').read_text())
    if runtime.verify(ROOT,frozen):raise ValueError('Behavior differs from freeze')
    if digest(freeze_dir/'manifest.json')!=batch['freeze_manifest_sha256']:raise ValueError('Wrong freeze')
    for record in batch['files']:
        if digest(batch_dir/record['path'])!=record['sha256']:raise ValueError('Locked input/reference changed')
    if len(batch['windows'])!=8:raise ValueError('Incomplete batch')
    # One journal per freeze, regardless of output-directory renaming.
    runtime.exclusive(freeze_dir/'first_attempt_started.json',{'batch_manifest_sha256':digest(batch_dir/'manifest.json'),'output':str(destination)})
    destination.mkdir(parents=True,exist_ok=False)
    for window in batch['windows']:runtime.claim_first_attempt(freeze_dir,window['source_digest'],window['window_id'])
    rows=[]
    for window in batch['windows']:
        name=window['window_id'];entry=json.loads((batch_dir/'entries'/(name+'.json')).read_text());payload=entry['payload']
        if runtime.verify(ROOT,frozen):raise ValueError('Behavior mutation during first batch; do not resume')
        result=runtime.run_isolated(payload['packet'],payload['inputs'],core_dir=ROOT/'analysis_parser')
        runtime.exclusive(destination/(name+'.raw.json'),result)
        report=result.get('report',{'events':[],'value_instances':[],'unresolved':[{'cause':'runtime_failed'}]});execution=result.get('execution',{'unresolved':[{'cause':'runtime_failed'}]})
        try:
            score=scoring.evaluate(payload['packet'],report,entry['reference'],track=window['track'],execution=execution,auxiliary=result)
            chain=assess(payload['packet'],report,execution,score,entry['chain_contract'],scoring.Graph)
            structural=structures(payload['packet'],report,score,entry['structural_contract'])
            score.update(chain_gate=chain,structural_gate=structural,full_chain_passed=chain['full_chain_passed'],full_chain_note='Preregistered chain gate')
        except Exception as error:
            score={'status':'scoring_error','type':type(error).__name__,'message':str(error),'fixed_registration':scoring.register(entry['reference'],track=window['track']),'full_chain_passed':False}
        runtime.exclusive(destination/(name+'.score.json'),score)
        rows.append({'window_id':name,'track':window['track'],'raw_sha256':digest(destination/(name+'.raw.json')),'score_sha256':digest(destination/(name+'.score.json')),'runtime_status':result['status'],'score_status':score.get('status','scored'),'full_chain_passed':score['full_chain_passed']})
    runtime.exclusive(destination/'summary.json',{'windows':rows,'behavior_mutations':runtime.verify(ROOT,frozen),'post_first_repairs':False})
    return rows
