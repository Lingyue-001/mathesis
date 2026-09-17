"""V3 scoped lowering adapter over the shared immutable writer and arithmetic parser.

Typed local candidates select rules; task headings only choose scope. No document
identity, case identifier, answer resource or whole-program dispatch is used.
"""
import re,copy
from .pipeline import Parser,UNITS,ROLE_ALIASES
from .inputs import span,number,NUMBER
from .lexical import tokenize_candidates
from .construction_ir import propose_constructions
from .context_compiler import compile_context, compile_documents
from .control_ir import resolve_control, following_region
from .resources import PROFILES,SEXAGENARY,WINTER_LIFT,CONTEXTUAL_RATES,PLANETARY_RATES,resource_hashes
from .quantity_semantics import check_transition

TASKS={'日月元統':'era_entry','入蔀術曰':'era_entry','天正':'new_moon','天正術':'new_moon','正月朔':'new_moon','天正朔日':'new_moon','冬至':'winter','二十四氣術曰':'winter','閏餘所在':'intercalation','閏月所在':'intercalation','八節':'nodes','中部二十四氣':'qi','五行':'declarations'}

class ScopedParser(Parser):
    def __init__(self,packet):
        super().__init__(packet)
        self.env.scope['task']='context'
        self.selected=packet.get('selected_profiles',[])
        self.profile={x:PROFILES[x] for x in self.selected if x in PROFILES}
        self.report.update(schema_version='3.0',adapter='typed_scoped_v3',tokens=[],construction_candidates=[],scope_graph=[],method_library=[],task_exports={},selected_profiles=self.selected)
        self.report['provenance']['resource_hashes']=resource_hashes()
        self.report['provenance']['selected_profiles']=self.profile
        self.context_ir=compile_context(self.docs,packet.get('context_tables',[]),{'tradition':self.env.scope.get('tradition'),'selected_profiles':self.selected})
        self.report['method_library']=self.context_ir['method_library'];self.report['context']=self.context_ir
        self.states={};self.task=None;self.task_division={};self.task_denominators={};self.snapshots={};self.cases=[];self.pending_concordance=None
        self.env.parser=self
        self.program=compile_documents(self.docs,{})
        self.program.aliases={k:v for profile in self.profile.values() if profile.get('tradition',self.env.scope.get('tradition'))==self.env.scope.get('tradition') and profile.get('planet',self.env.scope.get('planet'))==self.env.scope.get('planet') for k,v in profile.get('aliases',{}).items()}
        self.program.aliases={**ROLE_ALIASES.get(self.env.scope.get('tradition'),{}),**self.program.aliases}
        self.program.parameter_uses={name for profile in self.profile.values() for name in profile.get('parameter_uses',[])}

        self.program.initial_frame=self.profile.get('C2017_ST_concordance_midnight_frame_v1')
        self.program.interval_parameters={name for profile in self.profile.values() for name in profile.get('interval_parameters',{})}
        self.program.preferred_frame_inputs=set()
        frame=self.profile.get('C2017_ST_origin_month_day_frame_v1')
        if frame:
            for cs in self.program.syntaxes.values():
                for i,c in enumerate(cs[:-1]):
                    if c['kind']=='divide_by' and c['slots']['divisor']['text']==frame['origin_month_parameter'] and cs[i+1]['kind']=='name':self.program.preferred_frame_inputs.add(cs[i+1]['slots']['label']['text'])
        for method in self.report['method_library']:
            method['definition_id']=method['id']
            self.program.definitions.append({'id':method['id'],'kind':'MethodSlice','goal_surface':None,'domain_label':None,'parent':None,'source_role':'context','source_spans':method['source_spans'],'formal_inputs':method['formal_inputs'],'free_variables':dict(method['formal_inputs']),'defined_values':{},'return_ports':{name:{'body_value_id':vid} for name,vid in method['returns'].items()},'body':[n['id'] for n in method['body']]})
        self.report['program']=self.program.to_dict()
        self.report['ir_revision']='3.1-rescue'
        self.report['syntax']={key:[item for syntax in self.program.syntax_results.values() for item in getattr(syntax,key)] for key in ('nodes','roots','diagnostics','token_coverage')}
        self.all_candidates={};self.loop_controls={};self.query_start=None;self.qi_base_started=False;self.current_candidate=None
        self.report['provenance']['table_hashes']={}
        import hashlib,json
        for t in packet.get('context_tables',[]):self.report['provenance']['table_hashes'][t.get('table_id','table')]=hashlib.sha256(json.dumps(t,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        for d in self.docs:
            ts=tokenize_candidates(d,{})
            cs=self.program.syntaxes[d['doc_id']]
            self.report['tokens'].extend(ts);self.report['construction_candidates'].extend(cs);self.all_candidates[d['doc_id']]=cs
            stops=[p['stop'] for p in self.profile.values() if 'stop' in p]
            self.loop_controls[d['doc_id']]=resolve_control(cs,{'stop':stops[0] if len(stops)==1 else None},{})
    def export(self,port,vid,task=None):
        if vid:self.report['task_exports'].setdefault(task or self.task,{})[port]=vid
        return vid
    def ex(self,task,port):return self.report['task_exports'].get(task,{}).get(port)
    def analytical(self,event,basis,evidence='scholarly_interpretation'):
        event['evidence_status']='scholarly_calibrated';event['evidence']=[{'basis':evidence,'source_locator':basis}]
        for vid in event['writes'].values():self.env.values[vid]['evidence']=copy.deepcopy(event['evidence'])
        return event
    def inferred_value(self,kind,reads,spans,rule,attributes,meta,basis,evidence="scholarly_interpretation"):
        v=self.env.value(kind,reads,spans,rule,attributes,meta);self.analytical(self.env.events[self.env.values[v]['producer']],basis,evidence);return v
    def context(self):
        decl_ids={}
        for d in self.context_ir['declarations']:
            v=self.env.value('parameter',{},d['source_spans'],'V3_DECL',{'name':d['label'],'value':d['value'],'declaration_id':d['id']},{'labels':[d['label']]+d['aliases'],'role':'parameter','unit':UNITS.get(d['label'],'opaque')})
            decl_ids[d['id']]=v
            for label in [d['label']]+d['aliases']:self.env.parameters.setdefault(label,[]).append(v)
        self.report['declaration_equivalences']=[dict(e,value_id=decl_ids[e['declaration']],equivalent_value_ids=[decl_ids[x] for x in e['equivalent_to']]) for e in self.context_ir['equivalences']]
        for alias,label in self.program.aliases.items():
            for vid in self.env.parameters.get(label,[]):
                self.env.parameters.setdefault(alias,[]).append(vid)
                if alias not in self.env.values[vid]['labels']:self.env.values[vid]['labels'].append(alias)
        role_profile=self.profile.get('C2017_ST_Jupiter_parameter_roles_v1')
        if role_profile and self.env.scope.get('planet')=='Jupiter':
            for label,unit in role_profile['interval_parameters'].items():
                for vid in self.env.parameters.get(label,[]):
                    self.env.values[vid]['unit']=unit
                    self.env.values[vid]['parameter_role']='per_appearance_increment'
                    self.env.values[vid]['evidence'].append({'basis':'scholarly_interpretation','source_locator':role_profile['basis']})
                    if unit=='month_fraction' and len(self.env.parameters.get('見月法',[]))==1:self.env.values[vid]['scale']={'denominator':self.env.parameters['見月法'][0]}
        for d in self.packet.get('context_supplied_values',[]):
            # Explicit scholarly background is never reported as a source sentence.
            supports=[s for x in self.context_ir['declarations'] for s in x['source_spans'] if x['label'] in ('章月','章法')]
            v=self.inferred_value('parameter',{},supports,'V3_SUPPLIED',{'name':d['label'],'value':d['value'],'declaration':d},{'labels':[d['label']],'role':'parameter','unit':'integer'},d['basis'])
            self.env.parameters.setdefault(d['label'],[]).append(v)
    def get(self,name,spans,parameter=False,focus=None):
        allowed=getattr(self,'allowed_inputs',{})
        if name in allowed and name not in self.env.active and not parameter:
            meta=allowed[name] if isinstance(allowed[name],dict) else {}
            self.env.active[name]=self.env.value('input',{},spans,'RESCUE_ROOT',{'name':name,'parameter':False},dict(meta,labels=[name],role='external_input',unit=meta.get('unit','unknown')))
        aliases={'元':'元法','統':'統法','蔀名':'所入蔀名','入蔀年數':'入蔀年'}
        name=aliases.get(name,name)
        name=self.program.aliases.get(name,name)
        params=self.env.parameters.get(name,[])
        if len(params)>1 and (parameter or name not in self.env.active):
            numbers=[self.env.events[self.env.values[v]['producer']]['attributes'].get('value') for v in params]
            if len(set(numbers))==1:
                self.env.bind(name,params,params[0],spans,'V3_DECL_EQ','equivalent scalar declarations retain distinct provenance')
                return params[0]
        return super().get(name,spans,parameter,focus)
    def switch(self,task,spans,base=None,procedure_id=None):
        new_procedure=procedure_id is not None and procedure_id!=self.env.scope.get('procedure_id')
        if self.task==task and base is None and not new_procedure:return
        if self.task:
            self.finish_query(spans);self.save_base()
        parent=self.task;self.task=task
        inherited_denominator=self.day_denominator if base is not None else None
        if new_procedure:
            self.declared_divisor=None;self.prior_accumulator=None;self.pending_cycle=None;self.pending_condition=None
            self.scan_event=None;self.count_offset=None;self.fraction_denominator=None;self.temporal_anchor=None
            self.pending_concordance=None;self.cases=[];self.query_intervals={};self.branch_support=[]
            self.cycle_divisor=None;self.query_start=None;self.qi_base_started=False
            self.states.pop(task,None);self.task_denominators.pop(task,None)
            if inherited_denominator:self.task_denominators[task]=inherited_denominator
            self.task_division={k:v for k,v in self.task_division.items() if k[0]!=task}
            self.env.scope['procedure_id']=procedure_id
        if task not in self.states:
            inherited=dict(self.states.get('era_entry',{}))
            if task=='intercalation':inherited.update({k:v for k,v in self.states.get('new_moon',{}).items() if k in ('閏餘','積月')})
            if task in ('nodes','qi'):inherited.update(self.snapshots.get('winter',{}))
            self.states[task]=dict(base) if base is not None else inherited
        self.env.main=self.states[task];self.env.active=self.env.main;self.env.focus=None;self.env.query='main';self.env.scope.update(task=task,query='main')
        self.env.remainders=[];self.env.products=[];self.env.last_receiver=None;self.day_denominator=inherited_denominator or self.task_denominators.get(task)
        if task in ('nodes','qi'):self.day_denominator=self.task_denominators.get('winter')
        self.branch_finalized=True;self.branch_additions={};self.count_method=None
        self.report['scope_graph'].append({'task':task,'parent':parent,'source_spans':spans,'base_state':dict(self.env.main)})
    def save_base(self):
        if self.task and self.env.query=='main':self.snapshots[self.task]=dict(self.env.main)
    def medial_month_bridge(self,medial_id,month_id=None):
        profile=self.profile.get('C2017_ST_Jupiter_parameter_roles_v1')
        if profile and self.env.scope.get('planet')=='Jupiter':
            frame=self.underlying_event(medial_id)
            if frame['kind']=='divmod' and '見中法' in self.env.values[frame['reads']['divisor']]['labels']:
                values=[v for label in ('章歲','章月') for v in self.env.parameters.get(label,[])]
                if len(values)==2:
                    return {'from':self.env.values[medial_id]['unit'],'to':'month','basis':profile['basis'],'supporting_value_ids':values+[medial_id],'supporting_spans':sum([self.env.values[v]['source_spans'] for v in values+[medial_id]],[]),'rule_id':'RESCUE_MEDIAL_MONTH'}
        return super().medial_month_bridge(medial_id,month_id)
    def binary(self,kind,left,right,spans,rule='R02',attrs=None):
        result=super().binary(kind,left,right,spans,rule,attrs)
        if kind=='multiply' and self.env.values[left]['unit']=='integer' and self.env.values[right]['unit']=='integer':self.env.values[result]['unit']='integer'
        if kind=='multiply':
            for factor,operand in ((left,right),(right,left)):
                fv=self.env.values[factor];ov=self.env.values[operand]
                for rate in PLANETARY_RATES:
                    if rate['profile'] in self.selected and self.env.scope.get('planet')==rate['planet'] and fv['role']=='parameter' and rate['numerator_term'] in fv['labels'] and ov['unit']==rate['from_unit']:
                        ds=[v for label in rate['denominator_terms'] for v in self.env.parameters.get(label,[])]
                        if len(ds)==1:
                            self.env.values[result].update(unit=rate['to_unit']+'_numerator',rate_denominator=ds[0],rate_target=rate['to_unit'],rate_evidence=rate)
                            self.env.events[self.env.values[result]['producer']]['attributes']['quantity_transition']={'status':'resolved','transition':'rate_numerator','rate':rate,'operand':operand,'parameter':factor,'denominator':ds[0]}
        if kind=='multiply':
            framed=[self.env.values[v] for v in (left,right) if self.env.values[v].get('epoch_kind')]
            if len(framed)==1:
                for key in ('epoch_kind','epoch_proof'):self.env.values[result][key]=copy.deepcopy(framed[0][key])
        if kind not in ('add','subtract'):return result
        lv,rv=self.env.values[left],self.env.values[right];event=self.env.events[self.env.values[result]['producer']]
        u,v=lv['unit'],rv['unit'];unknown={'opaque','unknown','product'}
        transition={'status':'resolved','transition':'same_unit_arithmetic'}
        if (lv.get('role')=='literal' or rv.get('role')=='literal' or (rv.get('role')=='increment' and self.env.events[rv['producer']]['kind']=='interval_scale') or u=='boolean' or v=='boolean'):
            transition={'status':'resolved','transition':'source_scalar_increment','basis':'explicit numeric operand or predicate counter increment'}
        elif self.task=='era_entry' and right==getattr(self,'concordance_divisor',None):
            transition={'status':'resolved','transition':'cycle_length_subtraction','parameter_use':{'value_id':right,'unit':'year'},'basis':'source concordance reduction condition'}
        elif self.task=='intercalation' and kind=='subtract' and ('章法' in lv.get('labels',[]) or '章歲' in lv.get('labels',[])) and isinstance(rv.get('scale'),dict) and rv['scale'].get('denominator')==left:
            transition={'status':'resolved','transition':'fraction_numerator_complement','basis':'source subtracts the chapter-denominator remainder from its full denominator'}
        elif event['attributes'].get('unit_bridge'):transition={'status':'resolved','transition':'source_unit_bridge','proof':event['attributes']['unit_bridge']}
        elif u in unknown or v in unknown:transition={'status':'unknown','transition':'undetermined_addition'}
        elif u!=v:transition={'status':'incompatible_without_conversion','transition':'addition'}
        event['attributes']['quantity_transition']=transition
        if transition['status']!='resolved':
            event['attributes']['execution_blocked']=transition['status'];self.env.issue('unknown_quantity' if transition['status']=='unknown' else 'incompatible_quantity',spans,[left,right],units=[u,v])
        if lv.get('rate_denominator') and lv.get('rate_denominator')==rv.get('rate_denominator') and lv.get('rate_target')==rv.get('rate_target'):
            for key in ('rate_denominator','rate_target','rate_evidence'):self.env.values[result][key]=copy.deepcopy(lv[key])
        if lv.get('epoch_kind'):
            for key in ('epoch_kind','epoch_proof'):self.env.values[result][key]=copy.deepcopy(lv[key])
        return result
    def divide(self,x,d,spans,cycle=False):
        if self.task=='era_entry':
            event=self.env.event('cycle_reduce' if cycle else 'divmod',{'dividend':x,'divisor':d},['quotient','remainder'],spans,'V3_DIV',{'integer_nonnegative':True},{'quotient':{'unit':'integer','role':'quotient'},'remainder':{'unit':'year','role':'remainder'}})
            self.env.remainders.append({'event':event,'claimed':False});self.env.focus=event['writes']['remainder' if cycle else 'quotient'];return event
        event=super().divide(x,d,spans,cycle)
        source_frame=self.profile.get('C2017_ST_origin_month_day_frame_v1')
        if cycle and source_frame and source_frame['origin_month_parameter'] in self.env.values[d]['labels']:
            self.env.values[event['writes']['remainder']]['epoch_kind']=source_frame['epoch']
            self.env.values[event['writes']['remainder']]['epoch_proof']={'parameter':d,'operation':event['id'],'profile':source_frame}
        if not cycle:
            numerator=self.underlying_event(x)
            matches=[]
            if numerator['kind']=='multiply':
                for factor,operand in [('left','right'),('right','left')]:
                    fv=self.env.values[numerator['reads'][factor]];ov=self.env.values[numerator['reads'][operand]]
                    for rule in CONTEXTUAL_RATES:
                        if rule['numerator_term'] in fv.get('labels',[]) and fv.get('role')=='parameter' and self.env.values[d].get('role')=='parameter' and set(rule['denominator_terms'])&set(self.env.values[d].get('labels',[])) and ov['unit'] in (rule['from_unit'],rule['from_unit']+'_ordinal') and self.env.scope.get('tradition') in rule['traditions'] :
                            matches.append((rule,numerator['reads'][factor],numerator['reads'][operand]))
            source_value=self.env.values[x]
            if source_value.get('rate_denominator')==d:
                target=source_value['rate_target']
                event['attributes']['quantity_transition']={'status':'resolved','transition':'source_rate_division','rate':source_value['rate_evidence'],'denominator':d}
                for port in ('quotient','remainder'):
                    self.env.values[event['writes'][port]].update(unit=target if port=='quotient' else target+'_fraction')
            elif self.profile.get('C2017_ST_Jupiter_station_rate_v1') and numerator['kind']=='multiply' and self.env.scope.get('planet')=='Jupiter' and self.env.events[self.env.values[d]['producer']]['attributes'].get('value')==self.profile['C2017_ST_Jupiter_station_rate_v1']['rate']['denominator']:
                profile=self.profile['C2017_ST_Jupiter_station_rate_v1'];rate=profile['rate']
                factors=[self.env.values[v] for v in numerator['reads'].values()]
                proven=any(v['role']=='literal' and self.env.events[v['producer']]['attributes'].get('value')==rate['numerator'] for v in factors) and any(v['unit']==rate['from_unit'] for v in factors)
                if proven:
                    event['attributes']['quantity_transition']={'status':'resolved','transition':'source_rate_division','rate':dict(rate,basis=profile['basis'])}
                    for port in ('quotient','remainder'):self.env.values[event['writes'][port]]['unit']='station' if port=='quotient' else 'station_fraction'
                else:event['attributes']['execution_blocked']='unproven station rate operands'
            elif len(matches)==1:
                rule,factor,operand=matches[0]
                rate=dict(rule,numerator_parameter=factor,denominator_parameter=d,numerator=self.env.events[self.env.values[factor]['producer']]['attributes']['value'],denominator=self.env.events[self.env.values[d]['producer']]['attributes']['value'])
                checked=check_transition({'kind':'convert','reads':{'value':'input'},'writes':{'result':'output'},'attributes':{'evidence':[{'basis':rule['basis']}]}},{'input':self.env.values[operand],'output':{'unit':rule['to_unit']}},{'rate':rate})
                event['attributes']['quantity_transition']=dict(checked,rate=rate,operand=operand,source_operation=numerator['id'],scope=dict(self.env.scope))
                event['evidence']=[{'basis':'scholarly_interpretation','source_locator':rule['basis']}]
                for port in ('quotient','remainder'):
                    value=self.env.values[event['writes'][port]];value['quantity_kind']='duration' if rule['to_unit']=='day' else 'count';value['unit']=rule['to_unit'] if port=='quotient' else rule['to_unit']+'_fraction';value['representation']={'kind':'whole' if port=='quotient' else 'fraction_numerator','denominator_id':d}
                    if rule.get('residual'):value['time_frame']='annual_residual'
                    elif rule['to_unit']=='day':value['time_frame']='full_local_epoch'
            elif self.env.values[x]['unit'].endswith('_fraction') and isinstance(self.env.values[x].get('scale'),dict) and self.env.values[x]['scale'].get('denominator')==d:
                event['attributes']['quantity_transition']={'status':'resolved','transition':'fraction_carry','denominator':d}
                for port in ('quotient','remainder'):self.env.values[event['writes'][port]]['unit']=self.env.values[x]['unit'].removesuffix('_fraction') if port=='quotient' else self.env.values[x]['unit']
            elif self.env.values[x]['unit']=='integer' and self.env.values[d]['unit']=='integer':
                for port in ('quotient','remainder'):self.env.values[event['writes'][port]]['unit']='integer'
                event['attributes']['quantity_transition']={'status':'resolved','transition':'integer_count_division','basis':'typed integer dividend and divisor'}
            elif self.task!='intercalation':
                event['attributes']['quantity_transition']={'status':'unknown','transition':'unresolved_quantity_use'}
                for port in ('quotient','remainder'):self.env.values[event['writes'][port]]['unit']='unknown'
                event['attributes']['execution_blocked']='unknown_quantity_use'
                self.env.issue('unknown_quantity',spans,[x,d],reason='no declared contextual rate or compatible fraction carry')
            else:
                for port in ('quotient','remainder'):self.env.values[event['writes'][port]]['unit']='integer'
                event['attributes']['quantity_transition']={'status':'resolved','transition':'integer_count_division','basis':'source count-one construction'}
            if self.env.values[x].get('epoch_kind'):
                for port in event['writes']:
                    for key in ('epoch_kind','epoch_proof'):self.env.values[event['writes'][port]][key]=copy.deepcopy(self.env.values[x][key])
            self.task_division[(self.task,self.env.query)]=event
            if self.task in ('winter','nodes','qi') and event['attributes']['quantity_transition']['status']=='resolved':
                for port in ('quotient','remainder'):
                    self.env.values[event['writes'][port]]['unit']='day' if port=='quotient' else 'day_fraction'
                self.day_denominator=d;self.task_denominators[self.task]=d
            elif self.task=='new_moon' and self.env.values[event['writes']['quotient']]['unit']=='day':self.task_denominators[self.task]=d
        return event
    def name(self,label,spans,remainder=False):
        v=super().name(label,spans,remainder)
        source=self.env.events[self.env.values[v]['producer']]['reads']['value']
        if self.env.values[source]['unit']=='unknown':self.env.values[v]['unit']='unknown'
        for key in ('quantity_kind','representation','time_frame','epoch','rate_denominator','rate_target','rate_evidence','epoch_kind','epoch_proof'):
            if key in self.env.values[source]:self.env.values[v][key]=copy.deepcopy(self.env.values[source][key])
        if self.env.query=='main':
            ports={'new_moon':{'積月':'months','閏餘':'intercalation_remainder','積日':'whole_days','小餘':'small_remainder','大餘':'day_offset'},'winter':{'大餘':'winter_whole_residual','小餘':'winter_remainder'}}
            p=ports.get(self.task,{}).get(label)
            if p:self.export(p,v)
            if self.task=='winter' and label=='小餘':
                denom=self.env.events[self.env.values[self.day_denominator]['producer']]['attributes'].get('value')
                self.export('winter_remainder'+str(denom),v)
        definition=next((d for d in self.program.definitions if d['id']==self.env.scope.get('definition_id')),None)
        if definition:
            definition.setdefault('lowered_values',{})[label]=v
            if label in definition['return_ports']:definition['return_ports'][label]['value_id']=v
        return v
    def count(self,offset,origin_name,spans,role=None,convention='算外'):
        origin_name={'蔀名':'所入蔀名'}.get(origin_name,origin_name)
        e=super().count(offset,origin_name,spans,role,convention)
        if role=='day_index':
            self.env.values[e['writes']['result']]['unit']='day_index'
            if self.task=='new_moon' and self.env.query=='main':self.export('new_moon_day',e['writes']['result'])
            if self.task=='winter':self.export('winter_day',e['writes']['result'])
        return e
    def recall(self,spans,inferred=False):
        current=self.task
        if self.env.focus and self.env.values[self.env.focus]['unit']=='month':
            methods=[m for m in self.report['method_library'] if 'current_month_offset' in m['formal_inputs'] and m['definition_scope'].get('tradition')==self.env.scope.get('tradition')]
            if len(methods)!=1:
                self.env.issue('missing_method' if not methods else 'interpretive_ambiguity',spans,[m['id'] for m in methods] or ['month schedule method']);return
            m=methods[0];reads={'current_month_offset':self.env.focus}
            reads.update({key:self.get(label,spans,True) for key,label in m['parameter_labels'].items()})
            return self.emit_method_call(m,reads,spans,inferred)

        methods=[m for m in self.report['method_library'] if m['formal_inputs'].get('offset',{}).get('unit')=='day' and m['definition_scope'].get('tradition')==self.env.scope.get('tradition')]
        signatures={(m['cycle_value'],{'蔀名':'所入蔀名'}.get(m['origin_label'],m['origin_label'])) for m in methods}
        if not methods:
            self.env.issue('missing_method',spans,['cycle_and_count']);return
        if len(signatures)>1:
            self.env.issue('interpretive_ambiguity',spans,[m['id'] for m in methods],reason='ambiguous compatible method definitions');return
        local=[m for m in methods if m['definition_scope']['doc_id']==self.doc['doc_id']]
        m=(local or methods)[-1]
        big=self.get('大餘',spans)
        if self.env.values[big]['unit'] not in ('day','ordinal'):
            self.env.issue('incompatible_method',spans,[big],reason='count offset requires day');return
        cycle=self.literal(str(m['cycle_value']),m['source_spans']);origin=self.get(m['origin_label'],spans)
        if self.env.values[big].get('epoch_kind')=='Origin' and self.profile.get('C2017_ST_origin_month_day_frame_v1'):
            frame=self.profile['C2017_ST_origin_month_day_frame_v1'];root=self.ex('era_entry','elapsed_years');local=self.ex('era_entry','origin_remainder')
            if root and local:
                epoch=self.env.value('epoch_frame',{'epoch_elapsed':root,'local_elapsed':local},spans,'RESCUE_ORIGIN_EPOCH',{'tradition':self.env.scope.get('tradition')},{'unit':'epoch_identity'})
                first=self.inferred_value('literal',{},spans,'RESCUE_ORIGIN_DAY',{'value':frame['origin_day'],'source_label':'甲子'},{'unit':'day_index'},frame['basis'])
                origin=self.env.value('framed_origin',{'head':first,'epoch':epoch},spans,'RESCUE_FRAMED_ORIGIN',{'profile':frame,'epoch_kind':'Origin','source_month_proof':self.env.values[big]['epoch_proof']},{'unit':'day_index','epoch':epoch,'epoch_kind':'Origin'})
            else:self.env.issue('missing_epoch_frame',spans,['source epoch root/origin remainder'])
        reads={'offset':big,'origin':origin,'cycle':cycle}
        reads.update({key:self.get(label,spans,True) for key,label in m.get('parameter_labels',{}).items()})
        small=self.env.active.get('小餘')
        # The fractional component is a frame dependency, not a method formal.
        if small:reads['fraction']=small
        e=self.env.event('method_call',reads,['remainder','result'],spans,'V3_CALL',{'target':m['id'],'method':'cycle_and_count','body':m['body'],'formal_returns':m['returns'],'inferred':inferred},{'remainder':{'unit':'day','role':'remainder'},'result':{'unit':'day_index','role':'day_index'}})
        e['call_id']='method-call-'+e['id']
        e['method_binding']={'definition_id':m['id'],'actuals':reads,'formal_inputs':m['formal_inputs'],'definition_spans':m['source_spans'],'call_id':e['call_id'],'body_value_ids':{v:e['call_id']+':'+v for node in m['body'] for v in node['writes'].values()},'return_value_ids':{port:e['call_id']+':'+v for port,v in m['returns'].items()}}
        if small:
            e['context_bindings']={'fraction':small}
            e['method_binding']['formal_actuals']={k:v for k,v in reads.items() if k!='fraction'}
        for port in e['writes']:
            for key in ('epoch_kind','epoch_proof','epoch','time_frame'):
                if key in self.env.values[big]:self.env.values[e['writes'][port]][key]=copy.deepcopy(self.env.values[big][key])
        self.register_method_instance(e,m,{k:v for k,v in reads.items() if k in m['formal_inputs']})
        self.env.alias(e['writes']['remainder'],'大餘',spans,'V3_CALL');self.branch_finalized=True
        if current=='winter':self.export('winter_day',e['writes']['result'])
        elif current=='new_moon' and self.env.query in ('其次月','後月朔'):
            self.export('next_moon_day',e['writes']['result']);self.export('next_moon_remainder',small)
        elif current in ('nodes','qi'):
            self.export('first_node_day' if current=='nodes' else 'first_qi_day',e['writes']['result'])
        self.env.focus=e['writes']['result']
        return e
    def register_method_instance(self,event,method,actuals):
        call_id=event['call_id'];event['parent_call_id']=event['scope'].get('call_id');local={'$'+k:v for k,v in actuals.items()};values=[];events=[]
        metadata=dict(self.env.values)
        return_types={v:method.get('return_types',{}).get(port,{}) for port,v in method['returns'].items()}
        for node in method['body']:
            reads={port:local[vid] for port,vid in node['reads'].items()};eid=call_id+':'+node['id'];writes={}
            for port,vid in node['writes'].items():
                uid=call_id+':'+vid;writes[port]=uid;local[vid]=uid
                unit='unknown';scale=1
                if node['kind'] in ('cycle_reduce','divmod'):
                    dividend=metadata[reads['dividend']]
                    unit=dividend['unit'] if port=='remainder' else 'cycle'
                    scale=dividend.get('scale',1)
                elif node['kind']=='year_scan':unit='month' if port!='years' else 'year'
                elif node['kind']=='count':unit='day_index' if metadata[reads['offset']]['unit']=='day' else 'month_ordinal' if metadata[reads['offset']]['unit']=='month' else 'ordinal'
                elif node['kind'] in ('literal','parameter'):unit='integer'
                elif node['kind'] in ('add','subtract','load','alias'):unit=metadata[next(iter(reads.values()))]['unit']
                elif node['kind']=='multiply':
                    units=[metadata[v]['unit'] for v in reads.values()]
                    if 'integer' in units:unit=next((u for u in units if u!='integer'),'integer')
                meta={'id':uid,'producer':eid,'output_port':port,'role':port,'unit':unit,'scale':scale,'source_spans':node['source_spans'],'scope':dict(event['scope'],call_id=call_id),'definition_id':method['id'],'call_id':call_id,'labels':[]}
                values.append(meta);metadata[uid]=meta
            events.append({'id':eid,'kind':node['kind'],'reads':reads,'writes':writes,'attributes':copy.deepcopy(node.get('attributes',{})),'source_spans':node['source_spans'],'definition_id':method['id'],'call_id':call_id,'syntax_node_id':node['id'],'scope':dict(event['scope'],call_id=call_id)})
        returned={event['writes'][port]:local[vid] for port,vid in method['returns'].items()}
        instance={'call_id':call_id,'parent_call_id':event.get('parent_call_id'),'call_event_id':event['id'],'definition_id':method['id'],'events':events,'value_instances':values,'formal_bindings':dict(actuals),'return_bindings':returned,'call_spans':event['source_spans'],'definition_spans':method['source_spans']}
        self.report.setdefault('method_instances',[]).append(instance)
        self.program.calls.append({'id':call_id,'call_id':call_id,'parent_call_id':event.get('parent_call_id'),'definition_id':method['id'],'formal_bindings':dict(actuals),'return_ports':{port:{'value_id':event['writes'][port],'body_value_id':local[vid],'unit':metadata[local[vid]]['unit'],'role':metadata[local[vid]]['role']} for port,vid in method['returns'].items()},'event_ids':[n['id'] for n in events],'body':[n['id'] for n in method['body']],'source_spans':method['source_spans'],'call_event_id':event['id']})
        executed=self.report['program'].setdefault('executed_definition_ids',[])
        if method['id'] not in executed:executed.append(method['id'])
        event['method_binding']['return_bindings']=returned
        event['method_binding']['return_types']={port:{key:metadata[local[vid]][key] for key in ('unit','role','output_port')} for port,vid in method['returns'].items()}
    def emit_method_call(self,m,reads,spans,inferred=False):
        metadata=m.get('return_types',{'remainder':{'unit':'day','role':'remainder'},'result':{'unit':'day_index','role':'day_index'}})
        e=self.env.event('method_call',reads,list(m['returns']),spans,'V3_CALL',{'target':m['id'],'method':m['name'],'body':m['body'],'formal_returns':m['returns'],'inferred':inferred},metadata)
        e['call_id']='method-call-'+e['id']
        e['method_binding']={'definition_id':m['id'],'actuals':dict(reads),'formal_inputs':m['formal_inputs'],'definition_spans':m['source_spans'],'call_id':e['call_id'],'body_value_ids':{v:e['call_id']+':'+v for node in m['body'] for v in node['writes'].values()},'return_value_ids':{port:e['call_id']+':'+v for port,v in m['returns'].items()}}
        self.register_method_instance(e,m,reads)
        self.env.focus=e['writes'].get('result',next(iter(e['writes'].values()),None));return e
    def finish_query(self,spans):
        # Shared v2 normalization uses a count_method marker; v3 call selection
        # resolves its actual definition and current arguments independently.
        if self.env.query!='main' and self.day_denominator and not self.count_method and self.report.get('method_library'):
            m=self.report['method_library'][0]
            # Provide the source support event expected by the legacy adapter.
            support=next((e for e in reversed(self.report['events']) if e['kind'] in ('count','method_call')),None)
            if support:self.count_method={'event_id':support['id']}
        super().finish_query(spans)
    def start_query(self,label,spans):
        if self.task in ('winter','qi') and ('氣' in label):
            previous=dict(self.env.active)
            self.switch('qi',spans)
            if self.qi_base_started:self.env.main.update(previous)
            self.qi_base_started=True
        self.save_base();super().start_query(label,spans)
        definition=next((d for d in self.program.definitions if d['id']==self.env.scope.get('definition_id')),None)
        if definition and definition['kind']=='QueryDef':
            definition['base_value_ids']=dict(self.env.main)
            self.report['branches'][-1].update(definition_id=definition['id'],parent=definition['parent'],base_ref=definition['base_ref'])
    def export_threshold(self,e):
        if e and e['kind']=='threshold':
            judgment=e['attributes'].get('judgment','')
            if judgment in ('歲有閏','其歲有閏'):self.export('has_intercalation',e['writes']['result'],'new_moon')
            if judgment=='其月大':self.export('month_long',e['writes']['result'],'new_moon')
    def lower_entry(self,c,sp):
        kind=c['kind'];slots=c['slots']
        # Epoch source mentions, normalized only by explicitly selected convention.
        if kind in ('epoch_load','epoch_divide'):
            profile=next((p for p in self.profile.values() if 'input' in p),None)
            if not profile:self.env.issue('missing_profile',sp,['epoch count convention']);return True
            v=self.env.value('input',{},sp,'V3_EPOCH',{'name':profile['input'],'parameter':False},{'unit':'year','role':'external_input','labels':[profile['input']]})
            self.export('epoch_count',v)
            if profile['count']=='inclusive':
                one=self.literal('一',sp);v=self.inferred_value('subtract',{'left':v,'right':one},sp,'V3_ORDINAL',{}, {'unit':'year'},profile['basis'])
            self.env.focus=v;self.epoch_value=v;self.export('elapsed_years',v)
            if kind=='epoch_divide':
                e=self.divide(v,self.get(slots['divisor']['text'],sp,True),sp,True);self.export('origin_index',e['writes']['quotient']);self.export('origin_remainder',e['writes']['remainder']);self.entry_remainder=e['writes']['remainder']
            return True
        if kind=='epoch_inclusive':
            profile=self.profile.get('C2017_ST_local_year_count_v1')
            if not profile:self.env.issue('missing_profile',sp,['local inclusive year count']);return False
            value=self.inferred_value('add',{'left':self.env.focus,'right':self.literal('一',sp)},sp,'RESCUE_LOCAL_COUNT',{'count_convention':'inclusive','local_phrase':c['text']},{'unit':'year'},profile['basis']);self.env.focus=value;return True
        if kind=='epoch_elapsed':
            value=self.env.value('load',{'value':self.env.focus},sp,'V3_COUNT_CONVENTION',{'count_convention':'elapsed','selected_profile':'ST_elapsed'},{'unit':'year'})
            self.analytical(self.env.events[self.env.values[value]['producer']],PROFILES['ST_elapsed']['basis']);self.env.focus=value;self.export('elapsed_years',value);return True
        if kind=='entry_cycle':
            e=self.divide(self.env.focus,self.get(slots['divisor']['text'],sp,True),sp,True);self.export('origin_remainder',e['writes']['remainder']);self.entry_remainder=e['writes']['remainder'];return True
        if kind=='concordance_remainder':
            self.concordance_divisor=self.get('統法',sp,True);self.concordance_local=self.entry_remainder;self.concordance_condition_spans=sp;return True
        if kind=='concordance_case':
            self.cases.append({'label':slots['branch']['text'],'head':slots['head']['text'],'local':self.concordance_local,'source_spans':sp+getattr(self,'concordance_condition_spans',[])})
            return True
        if kind=='concordance_pending':self.pending_concordance=sp;return True
        if kind=='complete_cycle' and self.pending_concordance:
            self.concordance_local=self.binary('subtract',self.concordance_local,self.concordance_divisor,self.pending_concordance+sp,'V3_BRANCH_SUB')
            self.pending_concordance=None;return True
        if kind=='concordance_select':
            if not self.cases:return False
            reads={'divisor':self.concordance_divisor};choices=[]
            for i,row in enumerate(self.cases):
                reads['local'+str(i)]=row['local']
                idx=SEXAGENARY['sequence'].index(row['head'])+1 if row['head'] in SEXAGENARY['sequence'] else None
                if idx is None:self.env.issue('requires_external_data',row['source_spans'],['sexagenary label '+row['head']]);return True
                head=self.inferred_value('literal',{},row['source_spans'],'V3_LABEL',{'value':idx,'source_label':row['head']},{'unit':'day_index'},SEXAGENARY['basis'])
                reads['head'+str(i)]=head;choices.append({'index':i,'label':row['label'],'condition':{'operator':'ge_lt','lower':0,'upper':'divisor'},'local_port':'local'+str(i),'head_port':'head'+str(i),'source_spans':row['source_spans']})
            e=self.env.event('select',reads,['index','local','head'],sp+sum([r['source_spans'] for r in self.cases],[]),'V3_BRANCH',{'choices':choices,'exclusive':True},{'index':{'unit':'integer'},'local':{'unit':'year'},'head':{'unit':'day_index'}})
            self.export('concordance_index',e['writes']['index']);self.export('local_elapsed_years',e['writes']['local']);self.export('head_day',e['writes']['head']);self.env.alias(e['writes']['local'],'入統歲數',sp);self.env.alias(e['writes']['head'],'統首日',sp);return True
        if kind=='entry_remainder_divide':
            e=self.divide(self.entry_remainder,self.get(slots['divisor']['text'],sp,True),sp);self.entry_div=e;self.export('era_quotient',e['writes']['quotient']);self.export('era_remainder',e['writes']['remainder']);self.entry_remainder=e['writes']['remainder'];return True
        if kind=='era_index':
            self.era_index=self.env.value('count',{'offset':self.entry_div['writes']['quotient']},sp,'V3_TABLE_COLUMN',{'ordinal_origin':0,'cyclic':False,'sequence':['天紀','地紀','人紀'],'convention':'筭外'},{'unit':'table_column'});self.export('era_index',self.era_index);self.env.focus=self.entry_remainder;return True
        if kind=='annotation':return True
        if kind=='divide_by' and slots['value']['text']=='之':
            e=self.divide(self.entry_remainder,self.get(slots['divisor']['text'],sp,True),sp);self.entry_div=e;self.export('obscuration_quotient',e['writes']['quotient']);self.export('obscuration_year_remainder',e['writes']['remainder']);return True
        if kind=='obscuration_index':
            q=self.entry_div['writes']['quotient'];one=self.literal('一',sp)
            row=self.binary('add',q,one,sp,'V3_ORDINAL');self.export('obscuration_row',row)
            tables=self.context_ir['tables'];matching=[t for t in tables if '蔀首日' in t.get('columns',[])]
            if len(matching)!=1:self.env.issue('requires_external_data',sp,['unambiguous year/head table']);return True
            table=matching[0]
            e=self.env.event('lookup',{'row':row,'column':self.era_index},['head_day','head_year'],sp,'V3_LOOKUP',{'table':table,'day_column':table['columns'].index('蔀首日'),'row_base':1,'column_base':0},{'head_day':{'unit':'day_index'},'head_year':{'unit':'year_index'}})
            for k in ('head_day','head_year'):self.export(k,e['writes'][k])
            self.env.alias(e['writes']['head_day'],'所入蔀名',sp)
            local=self.entry_div['writes']['remainder'];u=self.binary('add',local,one,sp,'V3_ORDINAL')
            self.analytical(self.env.events[self.env.values[u]['producer']],PROFILES['SF_Liu_inclusive']['basis'])
            self.export('years_into_obscuration',u);self.export('local_elapsed_years',local);self.env.alias(u,'入蔀年',sp)
            return True
        if kind=='year_name':
            e=self.env.event('count',{'offset':self.ex('era_entry','local_elapsed_years'),'origin':self.ex('era_entry','head_year'),'cycle':self.literal('六十',sp)},['result'],sp,'V3_YEAR_NAME',{'cyclic':True,'cycle':60,'convention':'筭上','zero_offset_at_origin':True},{'result':{'unit':'year_index'}})
            self.export('current_year_name',e['writes']['result']);return True
        return False
    def normalize_query(self,sp):
        if self.task not in ('nodes','qi'):return
        self.finish_query(sp)
        small=self.env.active.get('小餘')
        if small and self.day_denominator:
            d=self.env.events[self.env.values[self.day_denominator]['producer']]['attributes'].get('value')
            self.export(('first_node_remainder' if self.task=='nodes' else 'first_qi_remainder')+str(d),small)
    def lower_intercalation(self,c,sp):
        kind=c['kind'];slots=c['slots']
        if kind=='update_count':
            control=next((x for x in self.loop_controls[self.doc['doc_id']] if x.get('candidate') is c),None)
            if not control or not control['stop']['operator']:
                self.env.issue('missing_profile' if control else 'incomplete_construction',sp,['repeat stop predicate']);return True
            initial=self.env.focus;inc=self.literal(c['slots']['increment']['text'],sp);limit=self.get(control['stop']['threshold']['text'],control['source_spans'],True)
            e=self.env.event('repeat',{'initial':initial,'increment':inc,'threshold':limit},['state','count'],control['source_spans'],'V3_REPEAT',{'control':control,'max_iterations':10000},{'state':{'unit':self.env.values[initial]['unit'],'scale':copy.deepcopy(self.env.values[initial]['scale']),'representation':copy.deepcopy(self.env.values[initial].get('representation',{'kind':'integer'}))},'count':{'unit':'integer'}})
            e['control']=control;self.export('loop_count',e['writes']['count']);self.export('loop_final_lag',e['writes']['state']);self.env.focus=e['writes']['count'];return True
        if kind in ('loop_threshold','loop_result'):return True
        if kind=='nominal':
            self.nominal(self.ex('intercalation','loop_count'),sp);return True
        if kind=='annotation':return True
        if kind=='boundary':
            self.boundary_spans=getattr(self,'boundary_spans',[])+sp;return True
        if kind=='conditional_count':
            e=self.task_division.get(('intercalation','main'))
            if not e:return False
            q,r=e['writes']['quotient'],e['writes']['remainder'];lower=self.literal(slots['lower']['text'],sp)
            pred=self.env.value('threshold',{'value':r,'lower':lower},sp,'V3_THRESHOLD',{'lower_inclusive':True},{'unit':'boolean'})
            count=self.binary('add',q,pred,sp,'V3_CONDITIONAL_COUNT')
            self.export('placement_q',q);self.export('placement_r',r);self.export('adjusted_count',count);self.env.focus=count;return True
        if c['kind']=='count_origin' and '十一月' in c['slots']['origin']['text']:
            self.nominal(self.env.focus,sp);return True
        if c['kind']=='multiply' and c['attributes'].get('continuation'):
            ok=self.lower_primitive(c,sp);self.export('intercalation_complement',self.env.focus);return ok
        return False
    def nominal(self,count,sp):
        if not count:self.env.issue('unresolved_parser',sp,['iteration_count']);return
        one=self.literal('一',sp);slot=self.binary('add',count,one,sp,'V3_COUNT')
        self.export('nominal_leap_slot',slot);self.export('medial_ordinal',slot)
        # A leap slot repeats the preceding month label; count names that label.
        celestial=self.inferred_value('alias',{'value':count},sp,'V3_REPEAT_NAME',{}, {'unit':'month_name_index'},'C2017 pp.93–96,168–169; L2003 p.70: inserted month repeats preceding name')
        self.export('nominal_leap_celestial_label',celestial)
        origin=self.inferred_value('literal',{},sp,'V3_CIVIL_ORIGIN',{'value':11},{'unit':'month_name_index'},'C2017 §§176,50; celestial first month is civil month eleven')
        prior=self.binary('subtract',count,one,sp,'V3_REPEAT_NAME')
        cycle=self.literal('十二',sp)
        e=self.env.event('count',{'origin':origin,'offset':prior,'cycle':cycle},['result'],sp,'V3_CIVIL_NAME',{'cyclic':True,'cycle':12},{'result':{'unit':'month_name_index'}})
        self.analytical(e,'C2017 pp.93–96,168–169; L2003 p.70');self.export('nominal_leap_civil_label',e['writes']['result'])
    def lower_primitive(self,c,sp):
        kind=c['kind'];slots=c['slots']
        if kind=='multiply':
            before=self.env.focus;self.prior_accumulator=before;left=self.get(slots['left']['text'],sp,focus=before);right=self.get(slots['right']['text'],sp,focus=before)
            self.binary('multiply',left,right,sp,'V3_MULTIPLY',{'word_order':[slots['left']['text'],slots['right']['text']]})
            if self.task=='intercalation':
                self.export('initial_scaled_lag',self.env.focus)
                source=right if self.env.values[right]['unit']=='month_fraction' else left if self.env.values[left]['unit']=='month_fraction' else None
                factor=left if source==right else right
                region=following_region(self.all_candidates[self.doc['doc_id']],c)
                controls=[x for x in self.loop_controls[self.doc['doc_id']] if x['kind']=='Repeat' and x['candidate'] in region]
                if source and controls:
                    old=self.env.values[source].get('scale',{}).get('denominator');decl=controls[0];denom=self.get(decl['stop']['threshold']['text'],decl['source_spans'],True)
                    oldnum=self.env.events[self.env.values[old]['producer']]['attributes'].get('value');newnum=self.env.events[self.env.values[denom]['producer']]['attributes'].get('value');mult=self.env.events[self.env.values[factor]['producer']]['attributes'].get('value')
                    attrs={'factor':mult,'source_operation':'multiply','denominator_declaration':True,'evidence':sp+decl['source_spans']}
                    checked=check_transition({'kind':'rescale','reads':{'value':'x'},'writes':{'result':'y'},'attributes':attrs},{'x':{'unit':'month','representation':{'denominator':oldnum}},'y':{'unit':'month','representation':{'denominator':newnum}}},{})
                    out=self.env.value('rescale',{'value':self.env.focus,'old_denominator':old,'new_denominator':denom,'factor':factor},sp+decl['source_spans'],'V3_LAG_SCALE',{'transition':checked,'source_operation':self.env.values[self.env.focus]['producer'],'execution_blocked':None if checked['status']=='resolved' else checked['status']},{'unit':'month_fraction','scale':{'denominator':denom,'value':newnum},'representation':{'kind':'fraction_numerator','denominator_id':denom}})
                    self.analytical(self.env.events[self.env.values[out]['producer']],'C2017 §176; L2003 eq2.9: chapter-month remainder expressed on chapter-medial scale')
                    self.env.focus=out;self.export('initial_scaled_lag',out)
            return True
        if kind=='subtract':
            self.binary('subtract',self.get(slots['left']['text'],sp),self.get(slots['right']['text'],sp),sp,'V3_SUBTRACT',{'direction':'B-A'});return True
        if kind=='load':
            source=self.get(slots['value']['text'],sp);value=self.env.values[source]
            self.env.focus=self.env.value('load',{'value':source},sp,'V3_LOAD',{}, {'unit':value['unit'],'scale':value['scale']})
            if 'decrement' in slots:
                self.binary('subtract',self.env.focus,self.literal(slots['decrement']['text'],sp),sp,'V3_ORDINAL',{'ordinal_to_elapsed':True});self.env.values[self.env.focus]['unit']='year'
            return True
        if kind=='divide':
            label=slots['value']['text'];dividend=self.get(label,sp) if label else self.env.focus
            divisor=slots['divisor']['text']
            denominator=self.env.values[dividend].get('scale',{}).get('denominator') if divisor in ('其法','法') and isinstance(self.env.values[dividend].get('scale'),dict) else None
            event=self.divide(dividend,denominator or self.get(divisor,sp,True),sp)
            if not label and self.env.values[dividend]['unit'].endswith('_fraction'):
                receivers=[n for n,v in self.env.active.items() if v==dividend]
                if len(receivers)==1:label=receivers[0]
            if label in self.env.active:
                self.env.alias(event['writes']['remainder'],label,sp);self.env.focus=event['writes']['quotient']
            return True
        if kind=='cycle_divide':
            e=self.divide(self.get(slots['value']['text'],sp),self.get(slots['divisor']['text'],sp,True),sp,True)
            if slots['value']['text']=='大餘':self.env.alias(e['writes']['remainder'],'大餘',sp)
            return True
        if kind=='divide_by':
            e=self.divide(self.get(slots['value']['text'],sp),self.get(slots['divisor']['text'],sp,True),sp,True)
            if slots['value']['text']=='大餘':self.env.alias(e['writes']['remainder'],'大餘',sp)
            return True
        if kind in ('name','remainder_name'):
            self.name(slots['label']['text'],sp,kind=='remainder_name');return True
        if kind=='pair_increment':
            self.add_increment(slots['receiver']['text'],slots['amount']['text'],sp);return True
        return False
    def lower(self,c):
        raw=c['text'];sp=c['source_spans'];self.current_candidate=c
        definition=next(x for x in self.program.definitions if x['id']==c['definition_id'])
        if self.env.scope.get('procedure_id')!=c['procedure_id']:
            domain=next(x for x in self.program.definitions if x['id']==c['procedure_id'])['domain_label']
            target_task=domain or (self.task if c['kind']=='numeral_predicate' and self.task=='winter' else c['procedure_id'])
            continuation=dict(self.env.main) if domain is None and c['kind']=='numeral_predicate' and self.task=='winter' else None
            self.switch(target_task,sp,base=continuation,procedure_id=c['procedure_id'])
            self.env.scope['procedure_id']=c['procedure_id']
        self.env.scope['definition_id']=c['definition_id']
        a,b=c['analysis_range'];self.indices=self.doc['analysis_to_source'][a:b];self.text=raw
        if c['kind']=='task_marker':
            target=c['slots']['target']['text'];marker=c['slots']['marker']['text'];task=TASKS.get(target)
            if task:
                # A postposed qi heading labels the already scoped preceding block.
                if task=='qi' and self.task=='qi':return True
                self.switch(task,sp)
                if task=='nodes':super().start_query(target,sp)
                return True
            if definition['kind']=='QueryDef' and not definition.get('is_initial'):self.start_query(target,sp)
            return True
        if (self.task=='era_entry' or c['kind'] in ('epoch_load','epoch_elapsed','epoch_inclusive')) and self.lower_entry(c,sp):return True
        if (self.task=='intercalation' or c['kind']=='update_count' or c['kind']=='loop_result') and self.lower_intercalation(c,sp):return True
        if c['kind']=='numeral_predicate':
            region=following_region(self.all_candidates[self.doc['doc_id']],c,postposed_targets=('中部二十四氣',))
            declarations=[x for x in region if x['kind']=='denominator_declaration']
            if declarations and self.task in ('nodes','winter'):
                self.normalize_query(sp);self.switch('qi',sp);super().start_query('二十四氣',sp)
            source=self.get(c['slots']['value']['text'],sp);factor=self.literal(c['slots']['factor']['text'],sp)
            value=self.binary('multiply',source,factor,sp,'V3_NUMERAL')
            self.env.values[value].update(unit=self.env.values[source]['unit'],scale=self.env.values[source]['scale'])
            self.env.alias(value,c['slots']['value']['text'],sp)
            if declarations:
                declaration=declarations[0];denom=self.get(declaration['slots']['denominator']['text'],declaration['source_spans'],True);old=self.day_denominator
                if old:
                    oldnum=self.env.events[self.env.values[old]['producer']]['attributes'].get('value');newnum=self.env.events[self.env.values[denom]['producer']]['attributes'].get('value')
                    data={'x':{'unit':'day','representation':{'denominator':oldnum}},'y':{'unit':'day','representation':{'denominator':newnum}}}
                    check=check_transition({'kind':'rescale','reads':{'value':'x'},'writes':{'result':'y'},'attributes':{'factor':c['slots']['factor']['value'],'source_operation':'multiply','denominator_declaration':True,'evidence':sp+declaration['source_spans']}},data,{})
                    out=self.env.value('rescale',{'value':value,'old_denominator':old,'new_denominator':denom,'factor':factor},sp+declaration['source_spans'],'V3_RESCALE',{'transition':check,'source_operation':self.env.values[value]['producer'],'execution_blocked':None if check['status']=='resolved' else check['status']},{'unit':'day_fraction','scale':{'denominator':denom,'value':newnum},'representation':{'kind':'fraction_numerator','denominator_id':denom}})
                    self.analytical(self.env.events[self.env.values[out]['producer']],'C2017 §178; L2003 eq2.14');self.env.alias(out,c['slots']['value']['text'],sp);self.day_denominator=denom;self.task_denominators[self.task]=denom
                    self.export('qi_base_remainder'+str(newnum),out)
            return True
        if c['kind']=='denominator_declaration':
            self.declared_divisor=self.get(c['slots']['denominator']['text'],sp,True);return True
        if c['kind']=='method_reference':
            if self.task in ('qi','nodes') and not self.branch_finalized:
                self.branch_support.extend(sp)
                self.normalize_query(sp)
            else:self.recall(sp)
            return True
        if c['kind'] in ('mixed_duration','mixed_compact'):
            whole=self.literal(c['slots']['whole']['text'],sp);numerator=self.literal(c['slots']['numerator']['text'],sp)
            declared=c['slots'].get('denominator')
            if declared:self.fraction_denominator=self.get(declared['text'],sp,True)
            denom=getattr(self,'fraction_denominator',None)
            if not denom:
                self.env.issue('missing_denominator',sp,['preceding fraction denominator declaration']);return True
            v=self.env.value('fraction',{'whole':whole,'numerator':numerator,'denominator':denom},sp,'V3_MIXED',{'source_representation':{'whole':c['slots']['whole']['text'],'numerator':c['slots']['numerator']['text'],'denominator':c['slots'].get('denominator',{}).get('text',{'inherited_value_id':denom})},'historical_role_alternatives':['中央','water_before_central'] if c['kind']=='mixed_compact' and c['slots'].get('label',{}).get('text')=='中央' and self.env.scope.get('tradition')=='San_tong_li' and getattr(self,'temporal_anchor',None) else [],'temporal_anchor':getattr(self,'temporal_anchor',None)},{'unit':'day','quantity_kind':'duration'})
            self.export('quantity_'+str(len(self.report['task_exports'].get('declarations',{}))+1),v,'declarations');return True
        if self.lower_primitive(c,sp):return True
        return self.lower_token_construct(c,sp)
    def lower_token_construct(self,c,sp):
        k=c['kind'];s=c['slots']
        if k=='reuse_operation':
            item=next((i for i in self.program.imports if i.get('source_node_id')==c['node_id']),None)
            target=next((x for stream in self.all_candidates.values() for x in stream if item and x['node_id']==item.get('target_node_id')),None)
            if not target:self.env.issue('missing_operation_import',sp,[s['receiver']['text']]);return False
            amount=target['slots']['amount'];literal=self.literal(amount['text'],target['source_spans']);producer=self.env.events[self.env.values[literal]['producer']]
            producer.update(definition_id=target['definition_id'],syntax_node_id=target['node_id']);producer['attributes']['operation_role']='increment';producer['attributes']['source_operand_slot']='amount'
            before=self.get(s['receiver']['text'],sp);value=self.binary('add',before,literal,sp,'RESCUE_REUSE',{'receiver':s['receiver']['text'],'increment':True,'reused_operation_node':target['node_id'],'reused_operation_definition':target['definition_id'],'source_role':'increment'})
            item.update(actual_value_id=literal,consumer_event_id=self.env.values[value]['producer'],target_definition_id=target['definition_id'],source_spans=target['source_spans'])
            self.env.alias(value,s['receiver']['text'],sp);return True
        if k=='method_value_reference':
            value=self.get(s['value']['text'],sp)
            self.env.alias(value,'大餘',sp,'RESCUE_METHOD_ARGUMENT')
            self.recall(sp);return True
        if k=='multiply_focus':
            self.binary('multiply',self.env.focus,self.get(s['factor']['text'],sp,True),sp);return True
        if k=='query_marker':self.start_query(s['target']['text'],sp);return True
        if k=='loop_threshold':
            self.pending_cycle=(self.env.focus,self.get(s['threshold']['text'],sp,True),sp);return True
        if k=='combine_product':
            if not getattr(self,'prior_accumulator',None):return False
            self.binary('add',self.prior_accumulator,self.env.focus,sp,'RESCUE_COMBINE',{'accumulator_before':self.prior_accumulator});return True
        if k=='update':
            label=s['receiver']['text'];before=self.get(label,sp)
            amount_name=s['amount']['text'];profile=self.profile.get('C2017_ST_Jupiter_parameter_roles_v1')
            interval=bool(profile and amount_name in ('積月','後月餘') and self.env.scope.get('planet')=='Jupiter')
            amount=self.get(amount_name,sp,parameter=interval)
            value=self.binary('add',before,amount,sp,'RESCUE_UPDATE',{'receiver_label':label,'receiver_before':before})
            self.env.alias(value,label,sp);return True
        if k=='declaration':
            label=s['label']['text'];value=self.literal(s['value']['text'],sp);self.env.alias(value,label,sp);return True
        if k in ('annotation','loop_result'):return True
        if k=='temporal_anchor':self.temporal_anchor={'label':c['text'],'source_spans':sp};return True
        if k=='pending_cycle':
            self.pending_cycle=(self.get(s['value']['text'],sp),self.get(s['divisor']['text'],sp,True),sp);return True
        if k=='complete_cycle' and self.pending_cycle:
            x,d,old=self.pending_cycle;self.divide(x,d,old+sp,True);self.pending_cycle=None;return True
        if k=='use_denominator':
            if not getattr(self,'declared_divisor',None):self.env.issue('missing_denominator',sp,['declared_divisor']);return False
            self.divide(self.env.focus,self.declared_divisor,sp);return True
        if k=='threshold':
            name=s['value']['text'];x=self.get(name,sp) if name else self.env.focus
            e=self.env.event('threshold',{'value':x,'lower':self.literal(s['lower']['text'],sp)},['result'],sp,'R07',{'lower_inclusive':True,'upper_inclusive':True,'judgment':None,'scope_end':'judgment'},{'result':{'role':'predicate','unit':'boolean'}})
            self.pending_condition=e;return True
        if k=='judgment' and self.pending_condition:
            self.pending_condition['attributes']['judgment']=c['text'];self.pending_condition['source_spans'].extend(sp);self.export_threshold(self.pending_condition);return True
        if k=='receiver_add':
            label=s['receiver']['text'];right=self.env.focus
            if label=='之':
                if len(self.env.products)<2:return False
                left,right=self.env.products[-2:];self.env.bind('之',self.env.products[:-1],left,sp,'R03')
            else:
                left=self.get(label,sp);self.env.bind('carried_amount',[right] if right else [],right,sp,'R11')
            v=self.binary('add',left,right,sp,'R11',{'receiver_label':label})
            if label!='之':self.env.alias(v,label,sp)
            return True
        if k=='add':self.binary('add',self.env.focus,self.get(s['amount']['text'],sp),sp);return True
        if k=='recur_increment':
            self.branch_finalized=False;self.branch_additions={};self.branch_support=list(sp)
            self.add_increment(s['receiver']['text'],s['amount']['text'],sp);return True
        if k=='count_origin':
            origin=s['origin']['text'];profile=self.profile.get('C2017_ST_Jupiter_station_rate_v1')
            if profile and origin in profile['origins'] and self.env.scope.get('planet')=='Jupiter':
                data=profile['origins'][origin];offset=self.env.focus
                origin_id=self.inferred_value('literal',{},sp,'RESCUE_ORIGIN',{'value':data['value'],'source_label':origin},{'unit':data['unit']},profile['basis'])
                e=self.env.event('count',{'offset':offset,'origin':origin_id,'cycle':self.literal(str(data['cycle']),sp)},['result'],sp,'RESCUE_SOURCE_COUNT',{'cyclic':True,'zero_offset_at_origin':True,'origin_label':origin},{'result':{'unit':data['unit']}});self.env.focus=e['writes']['result'];return True
            role='day_index' if origin=='統首日' else None
            self.count(self.get('大餘',sp) if role else self.env.focus,origin,sp,role);return True
        if k=='count_command':self.count(self.get('大餘',sp),s['origin']['text'],sp,'day_index','筭盡之外');return True
        if k=='double_interval':
            target=s['target']['text'];interval=self.query_intervals.get(target)
            if not interval:return False
            factor=self.literal('二',sp);self.branch_support.extend(sp)
            for label,delta in interval.items():
                doubled=self.env.value('interval_scale',{'value':delta,'factor':factor},sp,'R09',{'target_interval':target,'base_state':dict(self.env.main)},{'unit':self.env.values[delta]['unit'],'role':'increment'})
                value=self.binary('add',self.get(label,sp),doubled,sp,'R09',{'increment':True});self.env.alias(value,label,sp);self.branch_additions[label]=doubled
            return True
        return False
    def finish_task_document(self,sp):
        if self.task in ('nodes','qi'):self.normalize_query(sp)
        else:self.finish_query(sp)
        if self.task=='winter':self.save_base()
        if self.task=='new_moon' and self.env.query=='main':self.save_base()
    def temporal_views(self):
        winter=self.ex('winter','winter_whole_residual');years=self.ex('era_entry','local_elapsed_years')
        if years:
            esp=self.env.values[years]['source_spans']
            frame=self.env.value('epoch_frame',{'epoch_elapsed':self.ex('era_entry','elapsed_years'),'local_elapsed':years},esp,'V3_EPOCH_FRAME',{'tradition':self.env.scope.get('tradition')},{'unit':'epoch_identity'})
            self.export('time_epoch',frame,'era_entry')
        if winter and years:
            sp=self.env.values[winter]['source_spans']+self.env.values[years]['source_spans'];self.env.scope.update(task='winter',query='main')
            factor=self.inferred_value('literal',{},sp,'V3_LIFT_FACTOR',{'value':WINTER_LIFT['days_per_elapsed_year']},{'unit':'day_per_year'},WINTER_LIFT['basis'],'model_rule')
            lift=self.env.value('cycle_lift',{'whole':winter,'elapsed_years':years,'factor':factor},sp,'V3_LIFT',{'time_frame':'full_local_epoch','epoch':self.ex('era_entry','time_epoch'),'model_rule':WINTER_LIFT},{'unit':'day','time_frame':'full_local_epoch','epoch':self.ex('era_entry','time_epoch')})
            self.analytical(self.env.events[self.env.values[lift]['producer']],WINTER_LIFT['basis'],'model_rule');self.export('winter_absolute_whole_days',lift,'winter')
        # Query whole offsets derive from their original winter state plus the
        # actual parsed paired increment and its carry, not from day labels.
        for task,prefix in [('nodes','first_node'),('qi','first_qi')]:
            if not self.ex(task,prefix+'_day') or not self.ex('winter','winter_absolute_whole_days'):continue
            increments=[e for e in self.report['events'] if e['scope'].get('task')==task and e['kind']=='add' and e['attributes'].get('increment')]
            big=next((e for e in increments if e['attributes'].get('receiver')=='大餘'),None)
            carry=next((e for e in reversed(self.report['events']) if e['scope'].get('task')==task and e['kind']=='add' and e['rule_id']=='R11'),None)
            if big and carry:
                self.env.scope.update(task=task,query='main');sp=big['source_spans']+carry['source_spans']
                v=self.env.value('add',{'left':self.ex('winter','winter_absolute_whole_days'),'right':big['reads']['right']},sp,'V3_FULL_QUERY',{}, {'unit':'day','time_frame':'full_local_epoch'})
                v=self.env.value('add',{'left':v,'right':carry['reads']['right']},sp,'V3_FULL_QUERY',{}, {'unit':'day','time_frame':'full_local_epoch'})
                self.export(prefix+'_absolute_whole_days',v,task)
        self.boundary_view()
        for e in self.report['events']:
            if e['rule_id'] in ('V3_FULL_QUERY','V3_SEQUENCE'):
                e['attributes']['scope_imports']=[{'value_id':v,'source_scope':self.env.values[v]['scope'],'basis':'explicit temporal projection of previously computed query increment/carry'} for v in e['reads'].values() if self.env.values[v]['scope'].get('query')!=e['scope'].get('query')]
    def boundary_view(self):
        spans=getattr(self,'boundary_spans',[])
        if not spans:return
        self.env.scope.update(task='intercalation',query='main');reads={}
        nominal=self.ex('intercalation','nominal_leap_slot')
        if nominal:reads['nominal_slot']=nominal
        predicate=self.ex('new_moon','has_intercalation')
        if predicate:reads['has_intercalation']=predicate
        profiles=[x for x in self.selected if x in ('instant_lunation','civil_whole_day')]
        for task,whole,rem,denom,series in [('new_moon',self.ex('new_moon','whole_days'),self.ex('new_moon','small_remainder'),self.task_denominators.get('new_moon'),'moon_events'),('qi',self.ex('winter','winter_absolute_whole_days'),self.ex('winter','winter_remainder'),self.task_denominators.get('winter'),'qi_events')]:
            increments=[e for e in self.report['events'] if e['scope'].get('task')==task and e['kind']=='add' and e['attributes'].get('increment')]
            big=next((e for e in increments if e['attributes'].get('receiver')=='大餘'),None);small=next((e for e in increments if e['attributes'].get('receiver')=='小餘'),None)
            if whole and rem and denom and big and small:
                increment_denom=self.task_denominators.get(task,denom)
                sr={'whole':whole,'numerator':rem,'denominator':denom,'increment_whole':big['reads']['right'],'increment_numerator':small['reads']['right'],'increment_denominator':increment_denom,'epoch':self.ex('era_entry','time_epoch')}
                e=self.env.event('event_sequence',sr,['result'],spans+big['source_spans']+small['source_spans'],'V3_SEQUENCE',{'count':15 if series=='moon_events' else 29,'stride':1 if series=='moon_events' else 2,'time_frame':'full_local_epoch','base_task':'new_moon' if series=='moon_events' else 'winter','sequence_role':series},{'result':{'unit':'event_sequence','time_frame':'full_local_epoch'}})
                self.analytical(e,'C2017 §§175–178,47–50; bounded repeated application of source increments');reads[series]=e['writes']['result']
        e=self.env.event('boundary_call',reads,['result'],spans,'V3_BOUNDARY',{'profile':profiles[0] if len(profiles)==1 else None,'missing_data':['common_epoch_moon_qi_events'],'time_frame':'full_local_epoch'},{'result':{'unit':'boundary_status'}})
        self.export('boundary_result',e['writes']['result'],'intercalation')
    def run(self):
        from .program_ir import link_entry
        entries=[d['id'] for d in self.program.definitions if d['kind']=='ProcedureDef' and d['source_role']=='primary']
        allowed={p['input']:{'unit':'year'} for p in self.profile.values() if 'input' in p}
        if self.program.initial_frame:allowed[self.program.initial_frame['initial_input']]={'unit':'integer'}
        return lower_linked(link_entry(self.program,entries,allowed),self)


def lower_linked(linked, environment):
    """Lower the linked source bodies through the existing scoped adapter.

    Each invocation allocates immutable event/value IDs in the shared writer.
    Imports bind those actual values; definition metadata never serves as a value.
    """
    parser=environment
    if not isinstance(parser,ScopedParser):
        parser=getattr(environment,'parser',None)
        if parser is None:raise TypeError('lower_linked requires ScopedParser or its attached Environment')
    p=parser;p.allowed_inputs=linked.allowed_inputs
    if not p.report['events']:p.context()
    p.report['program']['linked']=linked.to_dict()
    p.program.imports.extend(linked.imports)
    p.report['program']['executed_definition_ids']=list(linked.order)
    byid={d['id']:d for d in p.program.definitions};docs={d['doc_id']:d for d in p.docs}
    outputs={};calls={};last_doc=None
    for ident in linked.order:
        definition=byid[ident]
        candidates=[c for stream in p.all_candidates.values() for c in stream if c.get('definition_id')==ident and c['node_id'] in linked.bodies[ident]]
        if not candidates:continue
        p.doc=docs[candidates[0]['source_spans'][0]['doc_id']]
        if last_doc!=p.doc['doc_id']:
            p.temporal_anchor=None;p.fraction_denominator=None;p.env.query='main';p.env.scope['query']='main';p.env.active=p.env.main;p.env.remainders=[];p.env.products=[]
            last_doc=p.doc['doc_id']
        call_id='call-'+str(len(p.program.calls)+1)
        call={'id':call_id,'call_id':call_id,'definition_id':ident,'formal_bindings':{},'return_ports':{},'event_ids':[],'source_spans':definition['source_spans'],'body':list(linked.bodies[ident])}
        p.program.calls.append(call);calls[ident]=call
        imports=[item for item in linked.imports if item['consumer_definition_id']==ident]
        imported={}
        for item in imports:
            if 'selected_port' not in item:continue
            source=item['selected_definition_id'];actual=outputs.get(source,{}).get(item['selected_port'])
            if actual:
                imported[item['formal']]=actual;imported[p.program.aliases.get(item['formal'],item['formal'])]=actual;item['actual_value_id']=actual;item['producer_call_id']=calls[source]['id']
                call['formal_bindings'][item['formal']]=actual
        # Open the source scope before binding imports; its state then owns only
        # this invocation's values, with query inheritance handled by the adapter.
        owner=byid[candidates[0]['procedure_id']];task=owner['domain_label'] or (p.task if candidates[0]['kind']=='numeral_predicate' and p.task=='winter' else owner['id'])
        if p.env.scope.get('procedure_id')!=owner['id']:
            continuation=dict(p.env.main) if owner['domain_label'] is None and candidates[0]['kind']=='numeral_predicate' and p.task=='winter' else None
            p.switch(task,candidates[0]['source_spans'],base=continuation,procedure_id=owner['id'])
            p.env.scope['procedure_id']=owner['id']
        p.env.active.update(imported);p.env.scope.update(definition_id=ident,call_id=call_id)
        if p.program.initial_frame and definition['source_role']=='primary' and definition['kind']=='QueryDef':
            if not getattr(p,'linked_initial_base',None):
                profile=p.program.initial_frame;sp=definition['source_spans'];head=p.env.active.get('統首日')
                if head and p.ex('era_entry','elapsed_years') and p.ex('era_entry','local_elapsed_years'):
                    query_scope=dict(p.env.scope);p.env.scope.update(definition_id=definition['parent'],call_id='initialization-'+definition['parent'],query='main',initialization_role='shared_query_base')
                    epoch=p.env.value('epoch_frame',{'epoch_elapsed':p.ex('era_entry','elapsed_years'),'local_elapsed':p.ex('era_entry','local_elapsed_years')},sp,'RESCUE_INITIAL_EPOCH',{'tradition':p.env.scope.get('tradition')},{'unit':'epoch_identity'})
                    ordinal=p.get(profile['initial_input'],sp);denominator=p.get('日法',sp,True)
                    base=p.env.event('initial_instant',{'head':head,'epoch':epoch,'ordinal':ordinal,'denominator':denominator},spans=sp,ports=['day_offset','fraction'],rule='RESCUE_INITIAL_INSTANT',attributes={'profile':profile,'count_frame':'elapsed_rules','time_frame':'concordance_midnight','source_epoch_frame':epoch},metadata={'day_offset':{'unit':'day','epoch':epoch,'role':'initial_day_offset','time_frame':'concordance_midnight','count_frame':'elapsed_rules'},'fraction':{'unit':'day_fraction','scale':{'denominator':denominator},'epoch':epoch,'role':'initial_fraction','time_frame':'concordance_midnight','count_frame':'elapsed_rules'}})
                    p.linked_initial_base={'大餘':base['writes']['day_offset'],'小餘':base['writes']['fraction'],'統首日':head};p.day_denominator=denominator
                    p.env.scope=query_scope
                else:p.env.issue('missing_query_base',sp,['source-derived head/epoch'])
            if getattr(p,'linked_initial_base',None):
                p.env.main=dict(p.linked_initial_base);p.env.active=dict(p.linked_initial_base);p.states[p.task]=p.env.main
                definition['base_value_ids']=dict(p.linked_initial_base)
        if definition['kind']=='QueryDef':
            call['base_ref']=definition.get('base_ref');call['base_value_ids']=dict(p.env.main)
            call['parent_definition_id']=definition.get('parent')
        before_call=len(p.report['events']);before_bindings=len(p.report['bindings'])
        for c in candidates:
            before=len(p.report['events'])
            if p.pending_cycle and c['kind']!='complete_cycle':p.abandon_pending_cycle('pending cycle interrupted',c['source_spans'])
            try:ok=p.lower(c)
            except (KeyError,IndexError,TypeError,ValueError,AttributeError) as error:
                ok=False;p.report['diagnostics'].append({'kind':'parser_exception','message':str(error),'source_spans':c['source_spans'],'definition_id':ident,'call_id':call_id})
            for event in p.report['events'][before:]:
                event.setdefault('syntax_node_id',c['node_id']);event.setdefault('definition_id',ident);event.update(production_id=c['production_id'],procedure_id=c['procedure_id']);event.setdefault('call_id',call_id)
                # A compiler caller may attach already-validated metadata to a
                # syntax output.  The automatic parser sets no hook.  Applying
                # it while the event is emitted preserves type/audit execution
                # as the sole graph construction path.
                for port,vid in event['writes'].items():
                    review=getattr(p,'review_output_metadata',{}).get((c['node_id'],port))
                    if review:
                        p.env.values[vid].update({key:value for key,value in review.items()
                                                  if key not in ('decision_id','decision_refs')})
                        refs=review.get('decision_refs') or [review.get('decision_id')]
                        p.env.values[vid]['adjudication_decision_refs']=[ref for ref in refs if ref]
                        event['adjudication_decision_refs']=p.env.values[vid]['adjudication_decision_refs']
                        event['evidence_status']='scholarly_calibrated'
            c['status']='selected' if ok else 'unresolved';c['selection_reason']='typed slots and linked source state' if ok else 'no compatible lowering'
            p.report['coverage']['accounted_spans' if ok else 'unparsed_spans'].extend(c['source_spans'])
            if not ok:
                p.env.issue('unresolved_parser',c['source_spans'],['unparsed_instruction'],definition_id=ident,call_id=call_id)
                p.env.focus=p.env.value('input',{},c['source_spans'],'V3_UNKNOWN_FOCUS',{'name':'unresolved_focus','parameter':False},{'unit':'unknown','role':'missing_upstream'})
        if p.program.initial_frame and definition['source_role']=='primary' and definition['kind']=='QueryDef' and getattr(p,'linked_initial_base',None):
            before=len(p.report['events']);sp=definition['source_spans'];small=p.get('小餘',sp);big=p.get('大餘',sp)
            denominator=p.get('日法',sp,True);division=p.divide(small,denominator,sp)
            p.env.alias(division['writes']['remainder'],'小餘',sp,'RESCUE_QUERY_CARRY')
            carried=p.binary('add',big,division['writes']['quotient'],sp,'RESCUE_QUERY_CARRY',{'receiver':'大餘','query_base_ref':definition.get('base_ref')})
            p.env.alias(carried,'大餘',sp,'RESCUE_QUERY_CARRY');p.recall(sp,True)
            for event in p.report['events'][before:]:
                event.setdefault('definition_id',ident);event.setdefault('call_id',call_id);event['attributes']['query_base_ref']=definition.get('base_ref');event['attributes']['normalization_basis']=p.program.initial_frame['basis']
        outputs[ident]={name:p.env.active[name] for name in definition['defined_values'] if name in p.env.active}
        if definition['kind']=='QueryDef':call['current_state_value_ids']=dict(p.env.active)
        for name,vid in outputs[ident].items():
            value=p.env.values[vid]
            call['return_ports'][name]={'value_id':vid,'unit':value['unit'],'role':value['role'],'producer':value['producer'],'output_port':value['output_port']}
        call['event_ids']=[e['id'] for e in p.report['events'][before_call:]]
        for name in definition['formal_inputs']:
            canonical=p.program.aliases.get(name,name)
            matched=[b['selected'] for b in p.report['bindings'][before_bindings:] if b.get('mention') in (name,canonical) and b.get('selected')]
            if matched:call['formal_bindings'].setdefault(name,matched[0])
            if name in p.allowed_inputs and name in p.env.active:call['formal_bindings'][name]=p.env.active[name]
        remaining=[c for stream in p.all_candidates.values() for c in stream if c['source_spans'][0]['doc_id']==p.doc['doc_id'] and c['analysis_range'][0]>candidates[-1]['analysis_range'][0] and c['definition_id'] in linked.order]
        if not remaining:p.finish_task_document(candidates[-1]['source_spans'])
        p.abandon_pending_cycle('pending cycle reached EOF')
    p.temporal_views()
    from .audit import audit
    p.report['diagnostics'].extend(audit(p.report))
    return p.report
