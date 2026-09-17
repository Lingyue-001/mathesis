"""Fixed reference-atom scoring, independent of parser construction and execution.

An endpoint is one atom including its recursively specified producer relation.
Missing whole events retain every preregistered atom. Helpers cannot replace a
main action. Extra reported actions/ports count as false positives.
"""
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location('rescue_source_contracts', Path(__file__).resolve().parents[1]/'handoff-v3/civil_contracts.py')
_old = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_old)
_graph_spec=importlib.util.spec_from_file_location('rescue_observed_graph',Path(__file__).with_name('observed_graph.py'))
_graph=importlib.util.module_from_spec(_graph_spec);_graph_spec.loader.exec_module(_graph)
Graph = _graph.Graph
subset = _old.subset
HELPERS = frozenset({'literal','parameter','input','alias','load','query','epoch_frame'})
VERSION = 'rescue-fixed-atoms-1'
_method_spec=importlib.util.spec_from_file_location('rescue_method_evidence',Path(__file__).with_name('method_evidence.py'))
_method=importlib.util.module_from_spec(_method_spec);_method_spec.loader.exec_module(_method)


def _items(value, inherited=None):
    """Visit wrappers and children independently; severity never hides children."""
    if isinstance(value, list):
        for item in value: yield from _items(item, inherited)
    elif isinstance(value, dict):
        if any(k in value for k in ('cause','severity','status','message','code','kind')):
            yield value
        for key, item in value.items():
            if key in ('error','errors','unresolved','incomplete','parser_error','unknown_domain') and item:
                yield {'cause':key, 'details':item}
            if isinstance(item, (list,dict)): yield from _items(item, key)
    elif value and inherited in ('error','errors','unresolved','incomplete'):
        yield {'cause':inherited, 'details':value}


def blocking_diagnostics(report):
    blocked = []
    for key in ('unresolved','unparsed_spans','parser_error'):
        if report.get(key): blocked.append({'container':key,'details':report[key]})
    for item in _items(report.get('diagnostics', [])):
        severity = str(item.get('severity','')).lower()
        cause = ' '.join(str(item.get(k,'')) for k in ('cause','code','kind')).lower()
        status = str(item.get('status','')).lower()
        if severity in ('error','fatal') or status in ('error','unresolved','incomplete','unsupported','ambiguous') or any(s in cause for s in ('error','unresolved','incomplete','missing','unknown','unsupported','unparsed','ambiguous','invalid','dangling','corruption','cross_query','lost_')):
            blocked.append(item)
    return blocked


def pointer(obj,path):
    for part in path.strip('/').split('/'):
        part=part.replace('~1','/').replace('~0','~')
        obj=obj[int(part)] if isinstance(obj,list) else obj[part]
    return obj


def _atom_paths(predicate,prefix):
    for key,value in predicate.items():
        path=prefix+'/'+key
        if key in ('reads','writes'):
            for port,selector in value.items(): yield from _selector_paths(selector,path+'/'+port)
        elif key in ('method_contract','attributes','scope','control','quantity','method_binding'):
            for field in value: yield path+'/'+field
        else:yield path


def _selector_paths(selector,prefix):
    for key,value in selector.items():
        if key=='origin':yield from _atom_paths(value,prefix+'/origin')
        else:yield prefix+'/'+key


SUPPORT_PATH=Path(__file__).with_name('contracts')/'scoring_support.json'
SUPPORT=json.loads(SUPPORT_PATH.read_text())


def reference_support_errors(reference):
    errors=[]
    def reject(path,reason):errors.append({'path':path,'reason':reason})
    def selector(value,path):
        if not isinstance(value,dict) or not value:reject(path,'empty/non-object value selector');return
        for key,item in value.items():
            if key not in SUPPORT['selector_fields']:reject(path+'/'+key,'unsupported selector field')
            elif key=='origin':predicate(item,path+'/origin',origin=True)
            elif key in ('one_of','denominator'):
                options=item if key=='one_of' else [item]
                if not isinstance(options,list) or not options:reject(path+'/'+key,'empty selector alternatives')
                else:
                    for i,option in enumerate(options):selector(option,path+'/'+key+'/'+str(i))
    def predicate(value,path,origin=False):
        if not isinstance(value,dict):reject(path,'predicate must be object');return
        kinds=value.get('kind');kinds=kinds if isinstance(kinds,list) else [kinds]
        if not kinds or any(k not in SUPPORT['actions'] for k in kinds):reject(path,'unsupported reference action');return
        for key,item in value.items():
            if key=='port' and origin:continue
            if key not in SUPPORT['event_fields']:reject(path+'/'+key,'unsupported event field');continue
            if key in ('reads','writes'):
                if not isinstance(item,dict):reject(path+'/'+key,'ports must be object');continue
                for port,sel in item.items():
                    if any('*' not in SUPPORT['actions'][k][key] and port not in SUPPORT['actions'][k][key] for k in kinds):reject(path+'/'+key+'/'+port,'unsupported action port')
                    selector(sel,path+'/'+key+'/'+port)
            elif key in ('attributes','control','scope','quantity','method_binding'):
                if not isinstance(item,dict):reject(path+'/'+key,'structured field must be object');continue
                allowed=set(SUPPORT['structured_fields'].get(key,[])) if key in SUPPORT['structured_fields'] else set.intersection(*(set(SUPPORT['actions'][k][key]) for k in kinds))
                for field in item:
                    if field not in allowed:reject(path+'/'+key+'/'+field,'unsupported action field')
            elif key=='method_contract':
                if kinds!=['method_call'] or not isinstance(item,dict):reject(path+'/'+key,'invalid method contract');continue
                for field in item:
                    if field not in SUPPORT['method_fields']:reject(path+'/'+key+'/'+field,'unsupported method relation')
                if set(item.get('required_return_roles',[]))-set(SUPPORT['method_roles']):reject(path+'/'+key,'unsupported method return role')
            elif key in ('exact_reads','exact_writes') and type(item) is not bool:reject(path+'/'+key,'exactness flag must be boolean')
    for oid,rule in reference['policy']['obligations'].items():
        for i,pred in enumerate(rule.get('events',[])):predicate(pred,f'/policy/obligations/{oid}/events/{i}')
    for cid,c in reference['policy'].get('contracts',{}).items():
        required=SUPPORT['contract_requirements'].get(c.get('type'))
        if required is None or not isinstance(c.get('requirements'),dict) or set(c['requirements'])!=set(required):reject('/policy/contracts/'+cid,'unsupported/incomplete evidence contract')
        else:
            # Nested selectors remain within the same frozen relation language.
            for key in ('retained_fraction','fraction_carry_denominator','fraction_denominator','root_selector','head_root'):
                if key in c['requirements']:selector(c['requirements'][key],'/policy/contracts/'+cid+'/requirements/'+key)
    return errors


def canonical_atoms(ref):
    expected={};obligations=ref['policy']['obligations']
    owners=[o['id'] for card in ref['cards'] for o in card['obligations']]
    if len(set(owners))!=len(owners) or set(owners)!=set(obligations):raise ValueError('Duplicate/missing obligation ownership')
    for oid in owners:
        for i,pred in enumerate(obligations[oid]['events']):
            for path in _atom_paths(pred,f'/policy/obligations/{oid}/events/{i}'):
                expected[path]={oid}
    for cid,contract in ref['policy'].get('contracts',{}).items():
        owned=contract.get('obligation_ids',[])
        if not owned or len(set(owned))!=len(owned) or not set(owned)<=set(owners):raise ValueError('Invalid contract ownership')
        if 'event_ref' in contract:
            link=contract['event_ref'];oid=link.get('obligation_id');index=link.get('event_index',0)
            if oid not in owned or type(index) is not int or not 0<=index<len(obligations[oid]['events']):raise ValueError('Invalid contract event reference')
        for key in contract.get('requirements',{}):expected[f'/policy/contracts/{cid}/requirements/{key}']=set(owned)
    return expected


def normalized(reference):
    ref=deepcopy(reference);policy=ref['policy']
    for card in ref['cards']:
        for obligation in card['obligations']:
            rule=policy['obligations'].get(obligation['id'],{})
            if not rule.get('events'):raise ValueError('Unscorable reference: '+obligation['id'])
            for pred in rule['events']:pred.setdefault('anchor',obligation['anchor'])
    if 'fixed_atoms' not in policy:
        atoms=[]
        for path,owners in canonical_atoms(ref).items():
            oid=sorted(owners)[0]
            atoms.append({'atom_id':f'{oid}.{len(atoms)+1}','obligation_id':oid,'predicate_path':path,'predicate_type':'generated_from_reference'})
        policy['fixed_atoms']=atoms;policy['fixed_atom_count']=len(atoms)
    return ref


def register(reference,track='A'):
    ref=normalized(reference);atoms=ref['policy']['fixed_atoms'];expected=canonical_atoms(ref)
    paths=[a.get('predicate_path') for a in atoms]
    if len(atoms)!=ref['policy']['fixed_atom_count'] or len({a.get('atom_id') for a in atoms})!=len(atoms) or any(not isinstance(a.get('atom_id'),str) or not a['atom_id'] for a in atoms):
        raise ValueError('Invalid fixed atom registration')
    if len(set(paths))!=len(paths) or set(paths)!=set(expected):raise ValueError('Fixed atoms must cover every canonical predicate exactly once')
    for atom in atoms:
        pointer(ref,atom['predicate_path'])
        if atom.get('obligation_id') not in expected[atom['predicate_path']]:raise ValueError('Invalid fixed atom owner')
    unsupported=reference_support_errors(ref)
    if track!='B' and unsupported:raise ValueError('Unscorable A reference: '+repr(unsupported))
    canonical=json.dumps({'version':VERSION,'reference':ref},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    return {'version':VERSION,'gold_atom_count':len(atoms),'atoms':atoms,'registration_sha256':hashlib.sha256(canonical).hexdigest(),'reference_unsupported':unsupported,'scoring_support_sha256':hashlib.sha256(SUPPORT_PATH.read_bytes()).hexdigest()}


def _kind(actual,expected):return actual in expected if isinstance(expected,list) else actual==expected


def _value_atom(graph,vid,selector,path):
    root=graph.root(vid)
    if root is None:return False,False
    value=graph.values[root];event=graph.events[value['producer']];attrs=event.get('attributes',{})
    key=path[0];wanted=selector.get(key)
    if key=='origin':
        origin=selector['origin']
        # An incorrect ancestor action cannot give credit for its descendants.
        if not _kind(event.get('kind'),origin.get('kind')):return False,True
        if path[1]=='port':return value.get('output_port')==origin.get('port','result'),True
        return _event_atom(graph,event,origin,path[1:])
    if key=='parameter':return event.get('kind')=='parameter' and wanted in value.get('labels',[])+[attrs.get('name'),value.get('source_label')],True
    if key=='value':return event.get('kind') in ('literal','parameter') and attrs.get('value')==wanted, 'value' in attrs
    if key=='literal':return event.get('kind')=='literal' and type(attrs.get('value')) is type(wanted) and attrs.get('value')==wanted,True
    if key=='input':return event.get('kind')=='input' and attrs.get('name')==wanted,True
    if key=='anchor':return graph.at(event,wanted),bool(event.get('source_spans'))
    if key in ('unit','quantity_kind','time_frame'):return graph.value(vid,{key:wanted, 'origin':{'kind':event.get('kind'),'port':value.get('output_port')}}),key in value
    if key in ('one_of','export','denominator'):return graph.value(vid,{key:wanted}),True
    return False,False


def _method_atom(graph,event,contract,field,execution):
    attrs=event.get('attributes',{});binding=event.get('method_binding',{});target=attrs.get('target')
    methods=[m for m in graph.report.get('method_library',[]) if m.get('id')==target]
    method=methods[0] if len(methods)==1 else {};body=method.get('body',[])
    signature=method.get('formal_inputs',{});returns=method.get('returns',method.get('return_ports',{}))
    present=bool(method)
    if not method:return False,False
    if field=='definition_anchor':return graph.at(method,contract[field]),present
    roles=_method.role_formals(method)
    if field=='formal_inputs':
        expected=contract[field]
        if isinstance(expected,dict):return subset(signature,expected),present
        return all(name in roles for name in expected),present
    if field in ('body_required','body_semantics_required','required_return_roles'):
        if not body or body!=attrs.get('body') or returns!=attrs.get('formal_returns'):return False,present
        if field=='body_required':return all(graph.valid_span(s) for n in body for s in n.get('source_spans',[])) and all(n.get('source_spans') for n in body),True
        semantics=_method.semantic_body(graph,event,method)
        if field=='required_return_roles':return all(semantics.get(role,False) for role in contract[field]),present
        expected=contract[field]
        if 'reduce current day offset in sixty-cycle' in expected:return semantics['cyclical_day'],True
        if '12/13 month year scan with source intercalation schedule' in expected:return semantics['appearance_month_ordinal'],True
        return False,True
    if field=='actual_binding_identity':
        context=event.get('context_bindings',{})
        actuals={name:vid for name,vid in event.get('reads',{}).items() if name not in context}
        return (binding.get('definition_id')==target and binding.get('actuals')==event.get('reads') and binding.get('formal_actuals',binding.get('actuals'))==actuals and binding.get('formal_inputs')==signature and set(signature)==set(actuals) and all(event['reads'].get(k)==v for k,v in context.items())),present
    if field=='source_parameters_required':
        used=set(v for n in body for v in n.get('reads',{}).values())
        checks=[]
        for label in contract[field]:
            formals=[name for name,info in signature.items() if info.get('source_label')==label and '$'+name in used]
            checks.append(len(formals)==1 and graph.value(event.get('reads',{}).get(formals[0]),{'parameter':label}))
        return all(checks),present
    if field=='output_must_depend_on_actuals':
        deps={f'${name}':{name} for name in signature}
        for node in body:
            if any(v not in deps for v in node.get('reads',{}).values()):return False,True
            incoming=set().union(*(deps[v] for v in node.get('reads',{}).values()))
            for value in node.get('writes',{}).values():deps[value]=set(incoming)
        required={roles.get(name,'!unresolved:'+name) for name in contract.get('formal_inputs',signature)}
        meaningful=any(required <= deps.get(v,set()) for v in returns.values())
        return meaningful and _method.trace_identity(event,method,execution),present
    return False,False


def _event_atom(graph,event,pred,path,execution=None):
    if not event:return False,False
    if not _kind(event.get('kind'),pred.get('kind')):return False,True
    event=graph.align(event,pred)
    key=path[0];wanted=pred.get(key);attrs=event.get('attributes',{})
    if key=='kind':return True,True
    if key=='control' and event.get('control') != attrs.get('control'):return False,True
    if key=='anchor':return graph.at(event,wanted),bool(event.get('source_spans'))
    if key in ('reads','writes'):
        port=path[1];actual_port=port
        if key=='reads' and event.get('kind')=='method_call' and port not in event.get('reads',{}):
            methods=[m for m in graph.report.get('method_library',[]) if m.get('id')==attrs.get('target')]
            if len(methods)==1:actual_port=_method.role_formals(methods[0]).get(port,port)
        vid=event.get(key,{}).get(actual_port)
        if key=='writes' and (graph.values.get(vid,{}).get('producer'),graph.values.get(vid,{}).get('output_port'))!=(event.get('id'),port):return False,vid is not None
        return _value_atom(graph,vid,pred[key][port],path[2:])
    if key in ('exact_reads','exact_writes'):
        direction=key[6:];return not wanted or set(event.get(direction,{}))==set(pred.get(direction,{})),True
    if key=='method_contract':return _method_atom(graph,event,wanted,path[1],execution or {})
    if key in ('scope','attributes','control','quantity','method_binding'):
        actual=event.get(key,attrs.get(key,{}));expected=wanted
        for part in path[1:]:
            expected=expected[part]
            if not isinstance(actual,dict) or part not in actual:return False,False
            actual=actual[part]
        return subset(actual,expected),True
    return False,False


def ancestors(graph,vid):
    stack=[vid];seen=set()
    while stack:
        current=stack.pop()
        if current in seen or current not in graph.values:continue
        seen.add(current);event=graph.events.get(graph.values[current].get('producer'),{})
        stack.extend(event.get('reads',{}).values())
    return seen


def _contract_atom(graph,contract,key,chosen,execution,auxiliary):
    spec=importlib.util.spec_from_file_location('rescue_evidence_contracts',Path(__file__).with_name('evidence_contracts.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.check(graph,contract,key,chosen,execution,auxiliary)


def evaluate(packet,report,reference,track='A',execution=None,auxiliary=None):
    ref=normalized(reference);registration=register(ref,track=track);policy=ref['policy'];atoms=policy['fixed_atoms'];execution=execution or {};auxiliary=auxiliary or {}
    graph=Graph(packet,report);supported=set(SUPPORT['actions']);totals={'TP':0,'FP':0,'FN':0};rows=[];chosen_global={};used=set();unknown=set();candidate_owners={}
    for card in ref['cards']:
        for obligation in card['obligations']:
            oid=obligation['id'];preds=policy['obligations'][oid]['events']
            owned=[a for a in atoms if a['obligation_id']==oid and '/obligations/' in a['predicate_path']]
            kinds={k for p in preds for k in (p['kind'] if isinstance(p['kind'],list) else [p['kind']])}
            candidates=[e for e in graph.events.values() if e['id'] in graph.main_event_ids and any(graph.at(e,p['anchor']) for p in preds) and (e.get('kind') not in HELPERS or e.get('kind') in kinds)]
            for e in candidates:candidate_owners.setdefault(e['id'],oid)
            eligible=[e for e in candidates if e.get('kind') in kinds and e['id'] not in used]
            options=[]
            for choice in itertools.product(*[[None]+eligible for _ in preds]):
                ids=[e['id'] for e in choice if e]
                if len(ids)!=len(set(ids)):continue
                checks=[];metrics={'TP':0,'FP':0,'FN':0}
                for atom in owned:
                    parts=atom['predicate_path'].strip('/').split('/');i=int(parts[4]);event=choice[i]
                    ok,present=_event_atom(graph,event,preds[i],parts[5:],execution)
                    if any(atom['predicate_path'].startswith(gap['path']) or gap['path'].startswith(atom['predicate_path']+'/') for gap in registration['reference_unsupported']):ok=False
                    checks.append(dict(atom,passed=bool(ok),present=bool(present),event_id=event['id'] if event else None))
                    metrics['TP' if ok else 'FN']+=1
                    if present and not ok:metrics['FP']+=1
                for i,event in enumerate(choice):
                    if not event:continue
                    for direction in ('reads','writes'):
                        if direction not in preds[i]:continue
                        covered=set(preds[i][direction])
                        for c in policy.get('contracts',{}).values():
                            if c.get('event_ref')=={'obligation_id':oid,'event_index':i} and c.get('operand_role') and direction=='reads':covered.add(c['operand_role'])
                        if 'method_contract' in preds[i] and direction=='reads':
                            covered.update(event.get('method_binding',{}).get('formal_inputs',{}))
                            covered.update(event.get('context_bindings',{}))
                        metrics['FP']+=len(set(event.get(direction,{}))-covered)
                options.append(((-metrics['TP'],metrics['FP'],tuple(ids)),choice,checks,metrics))
            _,choice,checks,metrics=min(options,key=lambda x:x[0]);ids=[e['id'] for e in choice if e];used.update(ids)
            for i,event in enumerate(choice):chosen_global[(oid,i)]=graph.align(event,preds[i]) if event else None
            rows.append({'id':oid,'matched_event_ids':ids,'checks':checks,'relations':metrics})
    by_id={r['id']:r for r in rows};contract_results={}
    for atom in atoms:
        if '/contracts/' not in atom['predicate_path']:continue
        parts=atom['predicate_path'].strip('/').split('/');cid=parts[2];key=parts[4];contract=policy['contracts'][cid]
        if any(atom['predicate_path'].startswith(gap['path']) or gap['path'].startswith(atom['predicate_path']+'/') for gap in registration['reference_unsupported']):ok,present=False,False
        else:ok,present=_contract_atom(graph,contract,key,chosen_global,execution,auxiliary)
        row=by_id[atom['obligation_id']];row['checks'].append(dict(atom,passed=bool(ok),present=bool(present),event_id=None))
        row['relations']['TP' if ok else 'FN']+=1
        if present and not ok:row['relations']['FP']+=1
        contract_results.setdefault(cid,[]).append(bool(ok))
    spec=importlib.util.spec_from_file_location('rescue_evidence_witnesses',Path(__file__).with_name('evidence_contracts.py'))
    evidence=importlib.util.module_from_spec(spec);spec.loader.exec_module(evidence)
    witnesses=evidence.witness_events(graph,policy.get('contracts',{}),chosen_global,execution)
    for eid,oid in candidate_owners.items():
        if eid in used or eid in witnesses:continue
        event=graph.events[eid]
        by_id[oid]['relations']['FP']+=1+len(event.get('reads',{}))+len(event.get('writes',{}))
        if event.get('kind') not in supported:unknown.add(event.get('kind'))
    if rows:rows[0]['relations']['FP']+=len(graph.identity_errors)
    for row in rows:
        blockers=[cid for cid,c in policy.get('contracts',{}).items() if row['id'] in c['obligation_ids'] and not all(contract_results.get(cid,[False]))]
        row['blocking_contracts']=blockers
        row['status']='pass' if not row['relations']['FN'] and not row['relations']['FP'] and not blockers else 'fail'
        for key in totals:totals[key]+=row['relations'][key]
    if totals['TP']+totals['FN']!=registration['gold_atom_count']:raise AssertionError('Fixed denominator changed')
    return {'version':VERSION,'track':track,'registration_sha256':registration['registration_sha256'],'gold_atom_count':registration['gold_atom_count'],
            'obligations':rows,'relations':totals,'all_obligations_passed':bool(rows) and all(r['status']=='pass' for r in rows) and not graph.source_errors,
            'source_errors':graph.source_errors,'reference_unsupported':registration['reference_unsupported'],'blocking_diagnostics':blocking_diagnostics(report),'unsupported_actual_actions':sorted(unknown),
            'commutative_alignments':graph.commutative_alignments,'contract_witness_events':witnesses,
            'full_chain_passed':False,'full_chain_note':'Separate closure, target exports, complete actual execution and reverse-query evidence required.'}
