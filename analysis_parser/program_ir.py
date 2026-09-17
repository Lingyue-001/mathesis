"""Source identities and static definition interfaces, independent of execution."""
import hashlib
from dataclasses import dataclass, field

@dataclass
class ProgramIndex:
    definitions: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    calls: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    syntaxes: dict = field(default_factory=dict)
    syntax_results: dict = field(default_factory=dict)
    def to_dict(self):
        return {k:getattr(self,k) for k in ('definitions','imports','calls','diagnostics')}


def compile_frames(doc, candidates, index, domains):
    current=None; owner=None
    def definition(kind,c,goal=None,parent=None):
        sp=c['source_spans']; key=(doc['doc_id'],doc['actual_sha256'],sp,kind)
        ident='def-'+hashlib.sha256(repr(key).encode()).hexdigest()[:20]
        d=dict(id=ident,kind=kind,goal_surface=goal,domain_label=domains.get(goal),parent=parent,
               body=[],formal_inputs={},free_variables={},defined_values={},return_ports={},source_spans=list(sp),
               source_role='context' if doc['category']=='context_documents' else 'primary')
        if kind=='QueryDef':d['base_ref']=parent+':base'
        index.definitions.append(d);return d
    for i,c in enumerate(candidates):
        kind=c['kind'];slots=c['slots'];target=slots.get('target',{}).get('text')
        is_head=kind in ('task_marker','query_marker')
        if is_head and owner is not None and target=='中部二十四氣':
            annotation=definition('Annotation',c,target,current['id']);annotation['body']=[c.get('node_id',i)]
            c['procedure_id']=owner['id'];c['definition_id']=current['id'];continue
        if is_head and (owner is None or slots.get('marker',{}).get('text')=='推'):
            owner=current=definition('ProcedureDef',c,target)
        elif is_head:
            if current is owner:
                initial=definition('QueryDef',{'source_spans':owner['source_spans']},owner['goal_surface'],owner['id'])
                initial['is_initial']=True
                for key in ('body','formal_inputs','free_variables','defined_values','return_ports'):
                    initial[key]=dict(owner[key]) if isinstance(owner[key],dict) else list(owner[key])
                for previous in candidates[:i]:
                    if previous.get('definition_id')==owner['id']:previous['definition_id']=initial['id']
                owner['body']=[initial['id']]
            current=definition('QueryDef',c,target,owner['id'])
            owner['body'].append(current['id'])
        elif current is None:
            owner=current=definition('ProcedureDef',c)
        c['procedure_id']=owner['id'];c['definition_id']=current['id']
        if kind=='denominator_declaration':
            annotation=definition('Annotation',c,parent=current['id']);annotation['body']=[c.get('node_id',i)]
        current['body'].append(c.get('node_id',i))
        for s in c['source_spans']:
            if s not in current['source_spans']:current['source_spans'].append(s)
        for slot,v in slots.items():
            label=v.get('text','').removeprefix('其')
            if v.get('kind') not in ('Term','Anaphor') or slot in ('label','target','marker','receiver'):continue
            if label and label not in current['defined_values']:
                current['free_variables'].setdefault(label,{'uses':[]})['uses'].append(c.get('node_id',i))
        if kind in ('name','remainder_name'):
            label=slots['label']['text'];ref={'node_id':c.get('node_id',i),'port':'remainder' if kind=='remainder_name' else 'result'}
            current['defined_values'][label]=ref;current['return_ports'][label]=ref
        current['formal_inputs']=dict(current['free_variables'])
    # A named temporary is not automatically a public return. The terminal
    # named result and names explicitly used by another definition are ports.
    definitions=[d for d in index.definitions if d['kind']!='Annotation']
    for d in definitions:
        names=d['defined_values'];used=set().union(*(set(x['free_variables']) for x in definitions if x['id']!=d['id'])) if len(definitions)>1 else set()
        returned=({next(reversed(names))} if names else set()) | (set(names)&used)
        d['return_ports']={name:ref for name,ref in names.items() if name in returned}
    return index

@dataclass
class LinkedProgram:
    index: ProgramIndex
    entry_ids: list
    allowed_inputs: dict
    order: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)
    bodies: dict = field(default_factory=dict)
    def to_dict(self):
        return {k:getattr(self,k) for k in ('entry_ids','allowed_inputs','order','imports','diagnostics','bodies')}


def static_interface(candidates):
    """Source-order def/use. Receivers are read before their new version exists."""
    defined={};uses={}
    for c in candidates:
        kind=c['kind'];slots=c['slots'];nid=c['node_id']
        for slot,v in slots.items():
            if slot in ('label','target','marker','branch','head'):continue
            if kind=='count_origin' and slot=='origin' and v['text'] not in ('統首日','所入蔀名','蔀名'):continue
            if v.get('kind') not in ('Term','Anaphor'):continue
            label=v.get('text','').removeprefix('其')
            if label in ('','之','所得','餘','法'):continue
            if label not in defined:uses.setdefault(label,{'uses':[],'roles':[]})['uses'].append(nid);uses[label]['roles'].append(slot)
        if kind in ('name','remainder_name'):
            label=slots['label']['text'];defined[label]={'node_id':nid,'port':'remainder' if kind=='remainder_name' else 'result'}
        elif kind in ('update','pair_increment','recur_increment','reuse_operation'):
            label=slots['receiver']['text'];defined[label]={'node_id':nid,'port':'result'}
        elif kind=='method_value_reference' and c.get('method_return_label'):
            defined[c['method_return_label']]={'node_id':nid,'port':'remainder'}
        elif kind=='concordance_select':
            for label,port in [('統首日','head'),('入統歲數','local')]:defined[label]={'node_id':nid,'port':port}
        if kind=='method_value_reference':uses.setdefault('統首日',{'uses':[],'roles':[]})['uses'].append(nid);uses['統首日']['roles'].append('origin')
    return defined,uses


def link_entry(index, entry_id, allowed_inputs):
    """Resolve unique source producers and schedule only demanded prefixes.

    No runtime numbers participate in name resolution. Unused source diagnostics
    stay in the index; a requested prefix carries its own relevant diagnostics.
    """
    roots=[entry_id] if isinstance(entry_id,str) else list(entry_id)
    linked=LinkedProgram(index,roots,dict(allowed_inputs) if isinstance(allowed_inputs,dict) else {n:{} for n in allowed_inputs})
    defs={d['id']:d for d in index.definitions if d['kind']!='Annotation'}
    candidates={d:[] for d in defs}
    for stream in index.syntaxes.values():
        for c in stream:
            if c.get('definition_id') in candidates:candidates[c['definition_id']].append(c)
    params={}
    for stream in index.syntaxes.values():
        last=None
        for c in stream:
            if c['kind']=='declaration':last=c['slots']['label']['text'];params.setdefault(last,[]).append(c['node_id'])
            elif c['kind']=='scalar_name':last=c['slots']['label']['text'];params.setdefault(last,[]).append(c['node_id'])
            elif c['kind']=='parameter_alias' and last:params.setdefault(c['slots']['label']['text'],[]).extend(params[last])
            else:last=None
    aliases=getattr(index,'aliases',{})
    visiting=[];requested={};visited={}
    def require(ident,output=None):
        d=defs[ident];cs=candidates[ident]
        if not cs and d['kind']=='ProcedureDef':
            for child in index.definitions:
                if child.get('parent')==ident and child['kind']=='QueryDef':require(child['id'])
            return
        limit=len(cs)
        if output:
            ref=d['defined_values'].get(output)
            if ref:limit=next((i+1 for i,c in enumerate(cs) if c['node_id']==ref['node_id']),limit)
        requested[ident]=max(requested.get(ident,0),limit)
        if ident in visiting:
            linked.diagnostics.append({'kind':'dependency_cycle','definition_id':ident,'cycle':visiting[visiting.index(ident):]+[ident]});return
        if visited.get(ident,0)>=requested[ident]:return
        visiting.append(ident);body=cs[:requested[ident]];_,uses=static_interface(body)
        initial_frame=getattr(index,'initial_frame',None)
        if initial_frame and d['source_role']=='primary':
            for receiver in ('大餘','小餘'):uses.pop(receiver,None)
            uses['統首日']={'uses':[c['node_id'] for c in body],'roles':['origin']}

        for name,use in uses.items():
            canonical=aliases.get(name,name)
            producers=[x for x in defs.values() if x['id']!=ident and candidates[x['id']] and canonical in x['defined_values']]
            all_producers=list(producers)
            producers=[x for x in producers if x['kind']!='QueryDef' or x.get('is_initial') or x.get('parent')==d.get('parent')]
            if d.get('parent'):
                siblings=[x for x in producers if x.get('parent')==d['parent'] and x.get('is_initial')]
                if siblings:producers=siblings
            # Explicit parameter slots and interval additions select declarations,
            # while receiver slots always request the current produced value.
            parameter_only=all(r=='divisor' for r in use['roles']) or name in getattr(index,'parameter_uses',set()) or (all(r=='amount' for r in use['roles']) and name in getattr(index,'interval_parameters',set()))
            if len(producers)>1 and getattr(index,'preferred_frame_inputs',set()):
                framed=[x for x in producers if set(x['free_variables'])&index.preferred_frame_inputs]
                if len(framed)==1:producers=framed
            # An optional caller supplied constraint is deliberately expressed
            # in Program IR terms.  The normal parser never sets it; a review
            # compiler may do so only after it has validated definition and port
            # compatibility.  This keeps resolution in the linker rather than
            # patching edges after graph construction.
            constraint=getattr(index,'binding_constraints',{}).get((ident,name))
            if constraint:
                constrained=defs.get(constraint.get('producer_definition_id'))
                port=constraint.get('output_port',canonical)
                if constrained not in producers or port not in constrained.get('return_ports',{}):
                    linked.diagnostics.append({'kind':'invalid_review_binding','definition_id':ident,'formal':name,
                                               'constraint':constraint,'source_spans':d['source_spans']})
                    producers=[]
                else:
                    producers=[constrained]
            if canonical in params and (parameter_only or not producers):continue
            if name in linked.allowed_inputs or canonical in linked.allowed_inputs:continue
            item={'consumer_definition_id':ident,'formal':name,'uses':use['uses'],'candidates':[x['id'] for x in all_producers],'candidate_evidence':[{'definition_id':x['id'],'compatible':x in producers,'rejection_reason':None if x in producers else 'source query base or declared epoch frame mismatch'} for x in all_producers],'selected_definition_id':None,'selected_port':canonical,'selection_reason':None}
            if len(producers)==1:
                source=producers[0];port=constraint.get('output_port',canonical) if constraint else canonical
                item.update(selected_definition_id=source['id'],selected_port=port,
                            selection_reason='reviewed producer/port constraint' if constraint else 'unique source-defined return used by this formal; parameter/result namespaces remain distinct');require(source['id'],port)
            else:
                item['selection_reason']='multiple source producers' if producers else 'no declared root or source producer'
                linked.diagnostics.append({'kind':'ambiguous_import' if producers else 'missing_import','definition_id':ident,'formal':name,'candidates':item['candidates'],'source_spans':d['source_spans']})
            if item not in linked.imports:linked.imports.append(item)
        visiting.pop();visited[ident]=requested[ident]
        linked.bodies[ident]=[c['node_id'] for c in body]
        if ident in linked.order:linked.order.remove(ident)
        linked.order.append(ident)
    for root in roots:require(root)
    for ident in linked.order:
        for c in candidates[ident]:
            if c['kind']!='reuse_operation':continue
            receiver=c['slots']['receiver']['text']
            choices=[x for stream in index.syntaxes.values() for x in stream if x['kind']=='recur_increment' and x['slots']['receiver']['text']==receiver and x['definition_id']!=ident]
            item={'consumer_definition_id':ident,'source_node_id':c['node_id'],'target_node_id':choices[0]['node_id'] if len(choices)==1 else None,'candidate_node_ids':[x['node_id'] for x in choices],'selected_role':'increment','selection_reason':'unique recurrence operation with matching receiver role; initializer/result values are excluded','formal':receiver}
            if len(choices)==1:item['selected_definition_id']=choices[0]['definition_id']
            else:linked.diagnostics.append({'kind':'ambiguous_operation_import' if choices else 'missing_operation_import','definition_id':ident,'source_node_id':c['node_id']})
            linked.imports.append(item)
    return linked
