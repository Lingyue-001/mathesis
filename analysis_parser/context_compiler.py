"""Compile source context into declarations and reusable formal method bodies."""
from .lexical import tokenize_candidates
from .construction_ir import propose_constructions, parse_syntax

def compile_context(documents, tables, profile, candidate_streams=None):
    context={'declarations':[],'equivalences':[],'method_library':[],'scope_graph':[],'denominator_declarations':[],'tables':tables,'profile':profile}
    for doc in documents:
        candidates = candidate_streams[doc['doc_id']] if candidate_streams is not None else propose_constructions(tokenize_candidates(doc,{}),doc)
        # The same AST supplies parameter declarations in either source role.
        last=None
        for c in candidates:
            if c['kind']=='declaration':
                d={'id':'decl'+str(len(context['declarations'])+1),'label':c['slots']['label']['text'],'value':c['slots']['value']['value'],'source_spans':c['source_spans'],'aliases':[],'syntax_node_id':c['node_id']}
                context['declarations'].append(d);last=d
            elif c['kind']=='parameter_alias' and last:
                last['aliases'].append(c['slots']['label']['text'])
            elif c['kind']=='scalar_value':
                last={'value':c['slots']['value']['value'],'source_spans':c['source_spans'],'syntax_node_id':c['node_id']}
            elif c['kind']=='scalar_name' and last and 'label' not in last:
                last.update(id='decl'+str(len(context['declarations'])+1),label=c['slots']['label']['text'],aliases=[])
                last['source_spans']+=c['source_spans'];context['declarations'].append(last)
            else:last=None
        context['denominator_declarations'].extend(c for c in candidates if c['kind']=='denominator_declaration')
        context['method_library'].extend(compile_cycle_slices(candidates,doc,profile))
        context['method_library'].extend(compile_schedule_slices(candidates,doc,profile))
    for d in context['declarations']:
        same=[x for x in context['declarations'] if x['id']!=d['id'] and x['label']==d['label'] and x['value']==d['value']]
        if same:context['equivalences'].append({'declaration':d['id'],'equivalent_to':[x['id'] for x in same],'basis':'identical scalar declarations; source identities retained'})
    return context



class MethodBuilder:
    """Source-order SSA for a bounded method region, using shared operations.

    Naming updates the local binding rather than adding arithmetic. Every other
    statement is either lowered or becomes an explicit blocked body node.
    """
    def __init__(self,formals,focus):
        self.body=[];self.formals=dict(formals);self.parameters={};self.names={}
        self.focus=focus;self.remainder=None;self.prior=None;self.aliases=[];self.denominator=None;self.pending=None
    def emit(self,c,kind,reads,attributes=None,ports=('result',)):
        nid=c['node_id']+':'+str(len(self.body));writes={p:nid+':'+p for p in ports}
        self.body.append({'id':nid,'kind':kind,'reads':reads,'writes':writes,'attributes':attributes or {},'source_spans':list(c['source_spans'])})
        return writes
    def operand(self,slot,c):
        if slot.get('kind')=='Number':return self.emit(c,'literal',{}, {'value':slot['value']})['result']
        name=slot.get('text','').removeprefix('其')
        if name in ('','之','所得'):return self.focus
        if name=='餘':return self.remainder
        if name in self.names:return self.names[name]
        key=next((key for key,label in self.parameters.items() if label==name),None)
        if key is None:
            key='source_parameter_'+str(len(self.parameters)+1);self.parameters[key]=name;self.formals[key]={'unit':'unknown','source_label':name}
        return '$'+key
    def bind(self,c,label,value,binding_kind):
        previous=self.names.get(label)
        self.names[label]=value
        self.aliases.append({'syntax_node_id':c['node_id'],'label':label,'value_id':value,'previous_value_id':previous,'binding_kind':binding_kind,'source_spans':c['source_spans']})
    def accept_outputs(self,c,kind,out):
        """Apply source write roles independently of a statement's position.

        Arithmetic supplies a new focus. Only naming or a source receiver write
        replaces a named binding; projections do not overwrite full quantities.
        """
        if 'remainder' in out:self.remainder=out['remainder']
        self.focus=out['remainder' if kind=='cycle_reduce' else 'quotient' if kind=='divmod' else 'result']
        k=c['kind'];s=c['slots'];receiver=None;port='result'
        if k in ('update','pair_increment','recur_increment','receiver_add'):receiver=s.get('receiver',{}).get('text')
        elif k=='numeral_predicate':receiver=s.get('value',{}).get('text')
        elif k=='cycle_divide':receiver=s.get('value',{}).get('text');port='remainder'
        elif k=='divide' and s.get('value',{}).get('text') in self.names:
            receiver=s['value']['text'];port='remainder'
        # The supported divide-by day-offset use is a receiver update in the
        # direct lowerer; other divide-by uses are separate full-quantity views.
        elif k=='divide_by' and s.get('value',{}).get('text')=='大餘':receiver='大餘';port='remainder'
        if receiver and receiver not in ('之','其餘','所得') and port in out:
            self.bind(c,receiver.removeprefix('其'),out[port],'receiver_update')
    def lower(self,c):
        k=c['kind'];s=c['slots']
        if k=='annotation':return
        if k in ('name','remainder_name'):
            value=self.remainder if k=='remainder_name' else self.focus
            if value is None:value=self.emit(c,'unsupported',{}, {'reason':'missing method naming producer'})['result']
            self.bind(c,s['label']['text'],value,'name');self.focus=value
            return
        if k=='denominator_declaration':self.denominator=self.operand(s['denominator'],c);return
        if k=='pending_cycle':
            self.pending=({'dividend':self.operand(s['value'],c),'divisor':self.operand(s['divisor'],c)},c);return
        reads={};kind=k
        if k=='complete_cycle' and self.pending:
            reads,old=self.pending;self.pending=None;kind='cycle_reduce';c=dict(c,source_spans=old['source_spans']+c['source_spans'])
        elif k=='multiply':
            self.prior=self.focus;reads={key:self.operand(s[key],c) for key in ('left','right')}
        elif k=='multiply_focus':kind='multiply';reads={'left':self.focus,'right':self.operand(s['factor'],c)}
        elif k=='numeral_predicate':kind='multiply';reads={'left':self.operand(s['factor'],c),'right':self.operand(s['value'],c)}
        elif k=='combine_product':kind='add';reads={'left':self.prior,'right':self.focus}
        elif k=='add':reads={'left':self.focus,'right':self.operand(s['amount'],c)}
        elif k=='receiver_add':kind='add';reads={'left':self.operand(s['receiver'],c),'right':self.focus}
        elif k in ('update','pair_increment','recur_increment'):kind='add';reads={'left':self.operand(s['receiver'],c),'right':self.operand(s['amount'],c)}
        elif k=='subtract':reads={key:self.operand(s[key],c) for key in ('left','right')}
        elif k=='load':reads={'value':self.operand(s['value'],c)}
        elif k in ('divide','divide_by','cycle_divide','use_denominator'):
            reads={'dividend':self.focus if k=='use_denominator' else self.operand(s['value'],c),'divisor':self.denominator if k=='use_denominator' else self.operand(s['divisor'],c)}
            kind='divmod' if k in ('divide','use_denominator') else 'cycle_reduce'
        else:kind='unsupported'
        if any(v is None for v in reads.values()):kind='unsupported';reads={}
        out=self.emit(c,kind,reads,{'source_kind':k},('quotient','remainder') if kind in ('divmod','cycle_reduce') else ('result',))
        self.accept_outputs(c,kind,out)



def compile_cycle_slices(candidates,doc,profile):
    import hashlib
    methods=[];start=None;cycle=None;unit=None
    for i,c in enumerate(candidates):
        k=c['kind'];s=c['slots']
        if k in ('task_marker','query_marker'):
            start=None;cycle=None;continue
        if k in ('pending_cycle','cycle_divide') and s.get('value',{}).get('text') in ('積日','大餘','積度') and s.get('divisor',{}).get('kind')=='Number':
            complete=k=='cycle_divide' or i+1<len(candidates) and candidates[i+1]['kind']=='complete_cycle'
            if complete and start is None:
                start=i;cycle=s['divisor']['value'];unit='du' if s['value']['text']=='積度' else 'day'
        if start is None or k not in ('count_origin','count_command') or s.get('origin',{}).get('text') not in ('統首日','所入蔀名','蔀名','角首'):continue
        region=candidates[start:i+1];seed=region[0]
        builder=MethodBuilder({'offset':{'unit':unit},'origin':{'unit':'day_index'},'cycle':{'unit':'integer'}},'$offset')
        builder.names[seed['slots']['value']['text']]='$offset'
        support=list(seed['source_spans']);skip=1
        if seed['kind']=='pending_cycle':support+=region[1]['source_spans'];skip=2
        seed=dict(seed,source_spans=support)
        out=builder.emit(seed,'cycle_reduce',{'dividend':'$offset','divisor':'$cycle'},ports=('quotient','remainder'))
        builder.accept_outputs(seed,'cycle_reduce',out);return_label=None
        for statement in region[skip:-1]:
            builder.lower(statement)
            if statement['kind'] in ('name','remainder_name'):return_label=statement['slots']['label']['text']
        if unit=='day' and '大餘' in builder.names:return_label='大餘'
        offset=builder.names.get(return_label,builder.focus)
        out=builder.emit(c,'count',{'offset':offset,'origin':'$origin','cycle':'$cycle'},{'cyclic':True})
        spans=sum([x['source_spans'] for x in region],[]);mid='method-'+hashlib.sha256(repr(spans).encode()).hexdigest()[:20]
        methods.append({'id':mid,'name':'cycle_and_count','kind':'MethodSlice','return_labels':{'remainder':return_label} if return_label else {},'formal_inputs':builder.formals,'parameter_labels':builder.parameters,'returns':{'remainder':offset,'result':out['result']},'source_spans':spans,'definition_scope':{'tradition':profile.get('tradition'),'doc_id':doc['doc_id']},'origin_label':s['origin']['text'],'cycle_value':cycle,'body':builder.body,'source_bindings':builder.aliases})
        start=None;cycle=None
    return methods

def _method_definitions(methods):
    return [{'id': method['id'], 'kind': 'MethodSlice', 'goal_surface': None,
             'domain_label': None, 'parent': None, 'source_role': 'context',
             'source_spans': method['source_spans'], 'formal_inputs': method['formal_inputs'],
             'free_variables': dict(method['formal_inputs']), 'defined_values': {},
             'return_ports': {name: {'body_value_id': value} for name, value in method['returns'].items()},
             'body': [node['id'] for node in method['body']]}
            for method in methods]


def build_documents_from_candidates(documents, candidate_streams, syntax_results, resources,
                                    context_tables=(), profile=None):
    """Build context, methods and Program IR from one already-selected syntax view."""
    from .program_ir import ProgramIndex, compile_frames
    from .scoped import TASKS
    index = ProgramIndex()
    for doc in documents:
        syntax = syntax_results[doc['doc_id']]
        candidates = candidate_streams[doc['doc_id']]
        index.syntax_results[doc['doc_id']] = syntax
        index.diagnostics.extend(dict(d, doc_id=doc['doc_id']) for d in syntax.diagnostics)
        compile_frames(doc, candidates, index, TASKS)
        index.syntaxes[doc['doc_id']] = candidates
    context = compile_context(documents, list(context_tables), profile or {}, index.syntaxes)
    methods = context['method_library']
    for stream in index.syntaxes.values():
        for c in stream:
            if c['kind']=='method_value_reference':
                labels={label for m in methods for label in m.get('return_labels',{}).values()}
                if len(labels)==1:c['method_return_label']=next(iter(labels))
    from .program_ir import static_interface
    for definition in index.definitions:
        body=[c for stream in index.syntaxes.values() for c in stream if c.get('definition_id')==definition['id']]
        if body:
            names,uses=static_interface(body)
            definition['defined_values']=names;definition['free_variables']=uses;definition['formal_inputs']=dict(uses)
    for definition in index.definitions:
        names=definition['defined_values']
        used=set().union(*(set(d['free_variables']) for d in index.definitions if d['id']!=definition['id']))
        returned=({next(reversed(names))} if names else set()) | (set(names)&used)
        definition['return_ports']={n:dict(r) for n,r in names.items() if n in returned}
    for method in methods:
        method['definition_id'] = method['id']
    index.definitions.extend(_method_definitions(methods))
    index.context_ir = context
    return index


def compile_documents(documents, resources, *, context_tables=(), profile=None):
    """Compile source-local procedure identities without evaluating definitions."""
    syntax_results = {}
    candidate_streams = {}
    for doc in documents:
        syntax = parse_syntax(tokenize_candidates(doc, resources.get('lexicon', {})), doc)
        syntax_results[doc['doc_id']] = syntax
        candidate_streams[doc['doc_id']] = syntax.candidates()
    return build_documents_from_candidates(documents, candidate_streams, syntax_results, resources,
                                           context_tables=context_tables, profile=profile)


def compile_schedule_slices(candidates, doc, profile):
    """Lower a source cycle/scan/count suffix to a reusable arithmetic body.

    The free month operand is the formal input. Every modulus, scan length and
    schedule row is read from an AST node; none is supplied by the caller's goal.
    """
    import hashlib
    methods=[]
    for end,c in enumerate(candidates):
        if c['kind']!='count_remainder':continue
        prior=candidates[:end]
        heads=[i for i,x in enumerate(prior) if x['kind'] in ('task_marker','query_marker')]
        begin=heads[-1] if heads else 0
        divisions=[i for i in range(begin,end) if candidates[i]['kind']=='divide_by']
        if not divisions:continue
        begin=divisions[0];region=candidates[begin:end+1]
        rows=[{'year':x['slots']['year']['value'],'cumulative_intercalations':x['slots']['count']['value']} for x in region if x['kind']=='schedule_row']
        lengths=[x for x in region if x['kind']=='scan_length']
        if not rows or len(lengths)!=1:continue
        builder=MethodBuilder({'current_month_offset':{'unit':'month'}},'$current_month_offset')
        body=builder.body;formal=builder.formals;parameters=builder.parameters;focus=builder.focus;remainder=None
        initial=candidates[begin]['slots']['value']['text'];builder.names[initial]=focus
        for x in region:
            if x['kind']!='divide_by':
                if x['kind'] not in ('schedule_row','scan_length','count_remainder'):builder.lower(x)
                focus=builder.focus
                continue
            divisor=x['slots']['divisor'];nid=x['node_id'];reads={'dividend':builder.operand(x['slots']['value'],x)}
            if divisor['kind']=='Number':
                # A following intercalary branch and schedule turn this repeated
                # removal into the existing year_scan arithmetic primitive.
                node={'id':nid,'kind':'year_scan','reads':{'months':reads['dividend']},'writes':{'years':nid+':years','remainder':nid+':remainder','months_removed':nid+':removed'},'attributes':{'ordinary_year_months':divisor['value'],'intercalary_year_months':lengths[0]['slots']['months']['value'],'cumulative_schedule':rows},'source_spans':x['source_spans']+lengths[0]['source_spans']+sum([r['source_spans'] for r in region if r['kind']=='schedule_row'],[])}
            else:
                key='parameter_'+str(len(parameters)+1);formal[key]={'unit':'month','source_label':divisor['text']};parameters[key]=divisor['text'];reads['divisor']='$'+key
                node={'id':nid,'kind':'cycle_reduce','reads':reads,'writes':{'quotient':nid+':quotient','remainder':nid+':remainder'},'attributes':{'integer_nonnegative':True},'source_spans':x['source_spans']}
            body.append(node);builder.accept_outputs(x,'cycle_reduce',node['writes']);focus=builder.focus;remainder=focus
        origin=c['slots']['origin']['text']
        if origin!='天正':continue
        nid=c['node_id'];body.append({'id':nid,'kind':'count','reads':{'offset':focus},'writes':{'result':nid+':result'},'attributes':{'ordinal_origin':1,'cyclic':False,'origin_label':origin},'source_spans':c['source_spans']})
        spans=sum([x['source_spans'] for x in region],[]);mid='method-'+hashlib.sha256(repr(spans).encode()).hexdigest()[:20]
        methods.append({'id':mid,'kind':'MethodSlice','name':'cycle_schedule_count','formal_inputs':formal,'parameter_labels':parameters,'returns':{'remainder':remainder,'result':nid+':result'},'return_types':{'remainder':{'unit':'month'},'result':{'unit':'month_ordinal'}},'source_spans':spans,'definition_scope':{'tradition':profile.get('tradition'),'doc_id':doc['doc_id']},'body':body})
    return methods
