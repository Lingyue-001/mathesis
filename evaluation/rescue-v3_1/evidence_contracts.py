"""Structural and execution evidence for registered cross-event contracts.

Never emits parser events or expected answers. Missing interfaces fail closed.
Semantic roles are resolved from actual calls, body ports and source anchors.
"""
import re
import hashlib
import json


def call_id(event):
    event=event or {}
    return event.get('call_id') or event.get('scope',{}).get('call_id')


def definition_id(event):
    event=event or {}
    return event.get('definition_id') or event.get('scope',{}).get('definition_id')


def related_values(graph,vid):
    pending=[vid];seen=set()
    while pending:
        value_id=pending.pop()
        if not isinstance(value_id,str) or value_id in seen or value_id not in graph.values:continue
        seen.add(value_id);value=graph.values[value_id]
        event=graph.events.get(value.get('producer'),{})
        pending.extend(event.get('reads',{}).values())
        for field in ('epoch','epoch_id','frame_id'):
            frame=value.get(field)
            if isinstance(frame,str):pending.append(frame)
            elif isinstance(frame,dict):pending.extend(v for v in frame.values() if isinstance(v,str) and v in graph.values)
    return seen


def root_events(graph,vid):
    return [graph.events.get(graph.values[x].get('producer'),{}) for x in related_values(graph,vid)]


def _program(graph):return graph.report.get('program',graph.report.get('program_index',{}))


def _call(graph,event):
    cid=call_id(event)
    choices=[c for c in _program(graph).get('calls',[]) if (c.get('id') or c.get('call_id'))==cid]
    return choices[0] if len(choices)==1 else {}


def enclosing_call(graph,event):
    call=_call(graph,event);seen=set()
    while call.get('parent_call_id') and call['parent_call_id'] not in seen:
        parent=call['parent_call_id'];seen.add(parent)
        choices=[c for c in _program(graph).get('calls',[]) if (c.get('id') or c.get('call_id'))==parent]
        if len(choices)!=1:return {}
        call=choices[0]
    return call


def _definition(graph,event):
    choices=[d for d in _program(graph).get('definitions',[]) if d.get('id')==definition_id(event)]
    return choices[0] if len(choices)==1 else {}


def _base(call):return call.get('base_value_ids',call.get('base_values',{}))


def _returns(call):
    result={}
    for key,value in call.get('return_ports',{}).items():
        if isinstance(value,str):result[key]=value
        elif isinstance(value,dict) and isinstance(value.get('value_id'),str):result[key]=value['value_id']
    return result


def _is_executed(graph,event,execution):
    return bool(event and event.get('id') in execution.get('event_results',{}) and not any(x.get('event_id')==event.get('id') for x in execution.get('unresolved',[])))


def _has_input(graph,vid,name):
    return any(e.get('kind')=='input' and e.get('attributes',{}).get('name')==name for e in root_events(graph,vid))


def chinese_integer(token):
    digits={'零':0,'〇':0,'一':1,'二':2,'兩':2,'两':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
    units={'十':10,'百':100,'千':1000}
    if not token:return None
    if token.isdecimal():return int(token)
    total=block=current=0
    for ch in token:
        if ch in digits:current=digits[ch]
        elif ch in units:block+=(current or 1)*units[ch];current=0
        elif ch in ('萬','万'):total+=(block+current or 1)*10000;block=current=0
        else:return None
    return total+block+current


def _source_parameter_value(graph,vid,label):
    root=graph.root(vid)
    if root is None:return False
    value=graph.values[root];event=graph.events[value['producer']]
    if event.get('kind')!='parameter':return False
    # A separate source-number check prevents a correct label/anchor from
    # masking a corrupted parameter value. It handles only scalar declarations.
    observed=event.get('attributes',{}).get('value')
    for span in event.get('source_spans',[]):
        if not graph.valid_span(span):continue
        match=re.search(r'([零〇一二兩两三四五六七八九十百千萬万0-9]+)$',span['quote'])
        if not match:continue
        expected=chinese_integer(match.group(1))
        if type(observed) is int and observed==expected and label in value.get('labels',[])+[event.get('attributes',{}).get('name')]:return True
    return False


def check(graph,contract,key,chosen,execution,auxiliary):
    req=contract['requirements'];kind=contract['type'];ref=contract.get('event_ref',{})
    event=chosen.get((ref.get('obligation_id'),ref.get('event_index',0)))
    events=[chosen.get((oid,0)) for oid in contract['obligation_ids']]
    events=[e for e in events if e]
    if not events:return False,False
    if kind=='source_parameter_role':
        if key=='profile':return req[key] in graph.packet.get('selected_profiles',[]),True
        if key in ('whole_interval_source','fraction_interval_source'):
            label='積月' if key=='whole_interval_source' else '月餘'
            return any(graph.value(e.get('reads',{}).get('right'),{'parameter':label,'anchor':req[key]}) and _source_parameter_value(graph,e.get('reads',{}).get('right'),label) for e in events),True
        if key=='computed_values_distinct':
            return len(events)==2 and all(graph.root(e.get('reads',{}).get('left'))!=graph.root(e.get('reads',{}).get('right')) and graph.events.get(graph.values.get(graph.root(e.get('reads',{}).get('left')),{}).get('producer'),{}).get('kind') not in ('parameter','literal','input') for e in events),True
    if kind=='source_reuse' and event:
        right=event.get('reads',{}).get(contract.get('operand_role','right'));anchor=req['reuse_definition_anchor']
        program=_program(graph);syntaxes=graph.report.get('syntax',{})
        if isinstance(syntaxes,list):nodes={n['id']:n for s in syntaxes for n in s.get('nodes',[])}
        elif isinstance(syntaxes,dict) and 'nodes' in syntaxes:nodes={n['id']:n for n in syntaxes['nodes']}
        else:nodes={n['id']:n for s in syntaxes.values() if isinstance(s,dict) for n in s.get('nodes',[])} if isinstance(syntaxes,dict) else {}
        imported=[]
        for item in program.get('imports',[]):
            target=nodes.get(item.get('target_node_id') or item.get('source_node_id'),{})
            consumer=item.get('consumer_definition_id')==definition_id(event) or item.get('consumer_node_id')==event.get('syntax_node_id')
            if consumer and target and graph.at(target,anchor) and target.get('kind') in ('Increment','Add','Update') and item.get('role',item.get('selected_role')) in ('increment','amount'):
                imported.append((item,target))
        root=graph.root(right)
        source_ok=bool(root) and graph.events[graph.values[root]['producer']].get('kind')=='literal' and graph.at(graph.events[graph.values[root]['producer']],anchor)
        if source_ok:
            observed=graph.events[graph.values[root]['producer']].get('attributes',{}).get('value')
            proven=[]
            for item,target in imported:
                number=nodes.get(target.get('slots',{}).get('amount'),{})
                proven.append(number.get('kind')=='Number' and any(graph.valid_span(s) and chinese_integer(s['quote'])==observed for s in number.get('source_spans',[])))
            source_ok=any(proven)
        valid=bool(imported) and source_ok and event.get('kind')==req['reused_operation']
        if key=='reuse_definition_anchor':return bool(imported),bool(program.get('imports'))
        if key in ('reused_role','reused_operation','reject_literal_identity_only'):return valid,bool(imported or right)
        if key=='must_feed_matched_main_event':
            return valid and any(graph.root(item.get('actual_value_id',item.get('value_id')))==graph.root(right) for item,_ in imported),bool(right)
        if key=='reject_previous_result':return source_ok and graph.events.get(graph.values.get(graph.root(right),{}).get('producer'),{}).get('kind')=='literal',bool(right)
    if kind=='current_state':
        selector=req['retained_fraction'];retained=[v for v in graph.values if graph.value(v,selector)]
        methods=[e for e in events if e.get('kind')=='method_call']
        calls=[enclosing_call(graph,e) for e in methods]
        exported={graph.root(v) for call in calls for v in _returns(call).values()}
        if key=='retained_fraction':return any(graph.root(v) in exported and v in execution.get('values',{}) for v in retained),bool(retained)
        if key=='same_update_instance_as_month_call':return bool(methods) and any(enclosing_call(graph,graph.events[graph.values[v]['producer']]).get('id')==calls[0].get('id') and calls[0].get('id') for v in retained),bool(methods and retained)
        if key=='cannot_restore_previous_month_state':
            return bool(methods) and any(graph.root(v) in exported for v in retained) and all(_is_executed(graph,e,execution) for e in methods),bool(methods and retained)
    if kind=='source_epoch_frame' and event:
        offset=event.get('reads',{}).get('offset');head=event.get('reads',{}).get('head_day',event.get('reads',{}).get('origin'))
        ancestors=root_events(graph,offset);anchor=contract['source_evidence'][0]
        source_events=[e for e in ancestors if any(s.get('doc_id')==anchor['doc_id'] for s in e.get('source_spans',[]))]
        invocations={enclosing_call(graph,e).get('id') for e in source_events if e.get('kind') in ('multiply','divmod','cycle_reduce','method_call')}
        if key=='same_conjunction_invocation':return bool(source_events) and None not in invocations and len(invocations)==1,bool(source_events)
        if key=='origin_profile_selected':return req[key] in graph.packet.get('selected_profiles',[]),True
        frames=[graph.values[v] for v in related_values(graph,head)]
        if key=='head_actual_has_source_frame':
            framed=[graph.events.get(v.get('producer'),{}) for v in frames if graph.events.get(v.get('producer'),{}).get('kind')=='framed_origin']
            valid=[]
            for frame in framed:
                attrs=frame.get('attributes',{});proof=attrs.get('source_month_proof',{});operation=graph.events.get(proof.get('operation'),{})
                valid.append(attrs.get('epoch_kind')=='Origin' and attrs.get('profile',{}).get('epoch')=='Origin' and
                    operation.get('kind')=='cycle_reduce' and graph.value(operation.get('reads',{}).get('divisor'),{'parameter':'元月'}) and
                    operation.get('id') in {e.get('id') for e in ancestors} and _has_input(graph,head,'epoch_elapsed_years'))
            return bool(head) and any(valid),bool(head)
        if key=='conflicting_source_wording_retained':
            profile=graph.report.get('provenance',{}).get('selected_profiles',{}).get('C2017_ST_origin_month_day_frame_v1',{})
            return bool(profile.get('alternatives') or profile.get('conflicting_readings') or profile.get('conflicting_reading')),bool(profile)
        if key=='head_input_not_injected':return bool(head) and not any(e.get('kind')=='input' and e.get('attributes',{}).get('name') not in ('epoch_elapsed_years','epoch_inclusive_year') for e in root_events(graph,head)),bool(head)
    if kind=='query_base' and event:
        call=_call(graph,event);definition=_definition(graph,event);base=_base(call);left=event.get('reads',{}).get(contract.get('operand_role','left'))
        component=req['base_component_role'];base_vid=base.get(component)
        linked=bool(base_vid and graph.root(base_vid)==graph.root(left))
        chain=related_values(graph,left);base_events=root_events(graph,left)
        if key=='query_identity':return bool(call and definition.get('kind')=='QueryDef' and graph.at(definition,event['source_spans'][0])),bool(call)
        if key=='base_component_role':return linked,bool(base)
        if key=='root_selector':return linked and _has_input(graph,left,req[key]['input']),bool(left)
        if key=='head_root':return linked and _has_input(graph,left,req[key]['input']),bool(left)
        if key=='root_count_frame':
            return linked and any(graph.values[v].get('count_frame') in ('elapsed_rules','elapsed_rules_from_concordance_head') for v in chain),bool(left)
        if key=='head_definition_anchor':return linked and any(graph.at(e,req[key]) for e in base_events),bool(left)
        if key=='initial_instant_evidence':
            return linked and 'C2017_ST_concordance_midnight_frame_v1' in graph.packet.get('selected_profiles',[]) and any(graph.values[v].get('time_frame') in ('concordance_midnight','full_local_epoch') for v in chain),bool(left)
        if key=='same_initial_state_across_queries':
            peers=[c for c in _program(graph).get('calls',[]) if c.get('base_ref')==call.get('base_ref') and _base(c)]
            return linked and bool(call.get('base_ref')) and len(peers)>=2 and all({k:graph.root(v) for k,v in _base(c).items()}=={k:graph.root(v) for k,v in base.items()} for c in peers),bool(call)
        if key=='does_not_read_other_query_result':
            other_writes={v for e in graph.events.values() if call_id(e) and call_id(e)!=call_id(event) and _definition(graph,e).get('kind')=='QueryDef' for v in e.get('writes',{}).values()}
            return linked and not chain.intersection(other_writes),bool(left)
        if key=='real_source_producer_required':return linked and any(e.get('kind') not in ('literal','parameter','input','alias','load') and e.get('source_spans') for e in base_events),bool(left)
        if key=='component_unit':
            value=graph.values.get(left,{})
            accepted={'day'} if req[key]=='day' else {'day_fraction','day_fraction_numerator'}
            return linked and value.get('unit') in accepted,bool(left)
        if key=='fraction_denominator':
            value=graph.values.get(base.get('小餘'),{});scale=value.get('scale',{});den=value.get('representation',{}).get('denominator_id') or (scale.get('denominator') if isinstance(scale,dict) else None)
            return bool(den) and graph.value(den,req[key]),bool(base)
    if kind=='query_isolation':
        pairs=req['paired_updates'];group_events=[[chosen.get((oid,0)) for oid in pair] for pair in pairs]
        if any(any(e is None for e in group) for group in group_events):return False,False
        ids=[{call_id(e) for e in group} for group in group_events]
        distinct=all(len(group)==1 and None not in group for group in ids) and len(set.union(*ids))==len(ids)
        calls=[_call(graph,group[0]) for group in group_events]
        bases=[_base(c) for c in calls]
        same=all(bases) and all({k:graph.root(v) for k,v in b.items()}=={k:graph.root(v) for k,v in bases[0].items()} for b in bases[1:])
        if key in ('distinct_query_instances','paired_updates'):return distinct,True
        if key=='shared_immutable_initial_state':return distinct and same,True
        if key=='each_query_executes_and_exports':
            return distinct and all(_returns(c) and all(v in execution.get('values',{}) for v in _returns(c).values()) for c in calls),True
        if key=='fraction_carry_denominator':
            carry=[]
            for group in ids:
                carry.append(any(call_id(e) in group and e.get('kind')=='divmod' and graph.value(e.get('reads',{}).get('divisor'),req[key]) and _is_executed(graph,e,execution) for e in graph.events.values()))
            return distinct and all(carry),True
        if key=='no_sequential_cross_query_accumulation':
            return distinct and same and all(not related_values(graph,e['reads']['left']).intersection({v for other in group_events[1-i] for v in other.get('writes',{}).values()}) for i,group in enumerate(group_events) for e in group),True
        if key=='reverse_order_preserves_each_result':
            evidence=auxiliary.get('reverse_query_execution',{});reverse=evidence.get('execution',{})
            canonical=(json.dumps(graph.report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
            original_ids=[e['id'] for e in graph.report.get('events',[])];reordered=evidence.get('reordered_event_ids',[])
            authentic=(evidence.get('status')=='executed' and evidence.get('source_report_sha256')==hashlib.sha256(canonical).hexdigest() and sorted(original_ids)==sorted(reordered))
            def order(trace):
                seen=[]
                for step in trace:
                    cid=call_id(graph.events.get(step.get('event_id'),{}))
                    if cid in set.union(*ids) and cid not in seen:seen.append(cid)
                return seen
            forward=order(execution.get('execution_trace',[]));backward=order(reverse.get('execution_trace',[]))
            outputs={v for c in calls for v in _returns(c).values()}
            stable=bool(outputs) and all(v in execution.get('values',{}) and v in reverse.get('values',{}) and execution['values'][v]==reverse['values'][v] for v in outputs)
            return distinct and same and authentic and len(forward)==len(ids) and backward==list(reversed(forward)) and stable and not reverse.get('unresolved'),bool(evidence)
    return False,False


def witness_events(graph,contracts,chosen,execution):
    """Auxiliary actions get coverage only from demonstrated registered relations.

    The action vocabulary is not used to pardon arbitrary extra events.
    """
    covered={}
    for cid,contract in contracts.items():
        if contract['type']=='source_epoch_frame':
            ref=contract['event_ref'];main=chosen.get((ref['obligation_id'],ref.get('event_index',0)))
            if main and check(graph,contract,'head_actual_has_source_frame',chosen,execution,{})[0]:
                head=main.get('reads',{}).get('head_day',main.get('reads',{}).get('origin'))
                for event in root_events(graph,head):
                    if event.get('kind')=='framed_origin' and _is_executed(graph,event,execution):covered[event['id']]=cid
        if contract['type']=='query_base':
            ref=contract['event_ref'];main=chosen.get((ref['obligation_id'],ref.get('event_index',0)))
            if not main:continue
            base=_base(_call(graph,main));vid=base.get(contract['requirements']['base_component_role'])
            if not vid or graph.root(vid)!=graph.root(main.get('reads',{}).get('left')):continue
            producer=graph.events.get(graph.values.get(graph.root(vid),{}).get('producer'),{})
            if producer.get('kind')=='initial_instant' and _is_executed(graph,producer,execution):covered[producer['id']]=cid
        if contract['type']!='query_isolation':continue
        for whole_oid,fraction_oid in contract['requirements']['paired_updates']:
            whole=chosen.get((whole_oid,0));fraction=chosen.get((fraction_oid,0))
            if not whole or not fraction or call_id(whole)!=call_id(fraction):continue
            query=call_id(whole);call=_call(graph,whole)
            wroot=graph.root(whole.get('writes',{}).get('result'));froot=graph.root(fraction.get('writes',{}).get('result'))
            for carry in graph.events.values():
                if carry.get('kind')!='divmod' or call_id(carry)!=query or graph.root(carry.get('reads',{}).get('dividend'))!=froot:continue
                if not graph.value(carry.get('reads',{}).get('divisor'),contract['requirements']['fraction_carry_denominator']) or not _is_executed(graph,carry,execution):continue
                returned={graph.root(v) for v in _returns(call).values()}
                if graph.root(carry['writes'].get('remainder')) not in returned:continue
                for added in graph.events.values():
                    if added.get('kind')!='add' or call_id(added)!=query:continue
                    if {graph.root(v) for v in added.get('reads',{}).values()}!={wroot,graph.root(carry['writes'].get('quotient'))}:continue
                    if not _is_executed(graph,added,execution):continue
                    covered[carry['id']]=cid;covered[added['id']]=cid
                    for method in graph.events.values():
                        if method.get('kind')!='method_call' or enclosing_call(graph,method).get('id')!=query:continue
                        if graph.root(method.get('reads',{}).get('offset'))!=graph.root(added.get('writes',{}).get('result')):continue
                        if _is_executed(graph,method,execution) and _method_valid(graph,method,execution):
                            covered[method['id']]=cid
    return covered


def _method_valid(graph,event,execution):
    import importlib.util
    from pathlib import Path
    spec=importlib.util.spec_from_file_location('witness_method_evidence',Path(__file__).with_name('method_evidence.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.validated_call(graph,event,execution)
