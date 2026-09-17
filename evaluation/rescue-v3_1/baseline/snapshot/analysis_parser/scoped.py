"""V3 scoped lowering adapter over the shared immutable writer and arithmetic parser.

Typed local candidates select rules; task headings only choose scope. No document
identity, case identifier, answer resource or whole-program dispatch is used.
"""
import re,copy
from .pipeline import Parser,UNITS
from .inputs import span,number,NUMBER
from .lexical import tokenize_candidates
from .construction_ir import propose_constructions
from .context_compiler import compile_context
from .control_ir import resolve_control, following_region
from .resources import PROFILES,SEXAGENARY,WINTER_LIFT,CONTEXTUAL_RATES,resource_hashes
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
        self.all_candidates={};self.loop_controls={};self.query_start=None;self.qi_base_started=False;self.current_candidate=None
        self.report['provenance']['table_hashes']={}
        import hashlib,json
        for t in packet.get('context_tables',[]):self.report['provenance']['table_hashes'][t.get('table_id','table')]=hashlib.sha256(json.dumps(t,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        for d in self.docs:
            ts=tokenize_candidates(d,{})
            cs=propose_constructions(ts,d)
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
        for d in self.packet.get('context_supplied_values',[]):
            # Explicit scholarly background is never reported as a source sentence.
            supports=[s for x in self.context_ir['declarations'] for s in x['source_spans'] if x['label'] in ('章月','章法')]
            v=self.inferred_value('parameter',{},supports,'V3_SUPPLIED',{'name':d['label'],'value':d['value'],'declaration':d},{'labels':[d['label']],'role':'parameter','unit':'integer'},d['basis'])
            self.env.parameters.setdefault(d['label'],[]).append(v)
    def get(self,name,spans,parameter=False,focus=None):
        aliases={'元':'元法','統':'統法','蔀名':'所入蔀名','入蔀年數':'入蔀年'}
        name=aliases.get(name,name)
        params=self.env.parameters.get(name,[])
        if len(params)>1:
            numbers=[self.env.events[self.env.values[v]['producer']]['attributes'].get('value') for v in params]
            if len(set(numbers))==1:
                self.env.bind(name,params,params[0],spans,'V3_DECL_EQ','equivalent scalar declarations retain distinct provenance')
                return params[0]
        return super().get(name,spans,parameter,focus)
    def switch(self,task,spans,base=None):
        if self.task==task and base is None:return
        if self.task:
            self.finish_query(spans);self.save_base()
        parent=self.task;self.task=task
        if task not in self.states:
            inherited=dict(self.states.get('era_entry',{}))
            if task=='intercalation':inherited.update({k:v for k,v in self.states.get('new_moon',{}).items() if k in ('閏餘','積月')})
            if task in ('nodes','qi'):inherited.update(self.snapshots.get('winter',{}))
            self.states[task]=inherited
        self.env.main=self.states[task];self.env.active=self.env.main;self.env.focus=None;self.env.query='main';self.env.scope.update(task=task,query='main')
        self.env.remainders=[];self.env.products=[];self.env.last_receiver=None;self.day_denominator=self.task_denominators.get(task)
        if task in ('nodes','qi'):self.day_denominator=self.task_denominators.get('winter')
        self.branch_finalized=True;self.branch_additions={};self.count_method=None
        self.report['scope_graph'].append({'task':task,'parent':parent,'source_spans':spans,'base_state':dict(self.env.main)})
    def save_base(self):
        if self.task and self.env.query=='main':self.snapshots[self.task]=dict(self.env.main)
    def binary(self,kind,left,right,spans,rule='R02',attrs=None):
        result=super().binary(kind,left,right,spans,rule,attrs)
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
        elif u in unknown or v in unknown:transition={'status':'unknown','transition':'undetermined_addition'}
        elif u!=v:transition={'status':'incompatible_without_conversion','transition':'addition'}
        event['attributes']['quantity_transition']=transition
        if transition['status']!='resolved':
            event['attributes']['execution_blocked']=transition['status'];self.env.issue('unknown_quantity' if transition['status']=='unknown' else 'incompatible_quantity',spans,[left,right],units=[u,v])
        return result
    def divide(self,x,d,spans,cycle=False):
        if self.task=='era_entry':
            event=self.env.event('cycle_reduce' if cycle else 'divmod',{'dividend':x,'divisor':d},['quotient','remainder'],spans,'V3_DIV',{'integer_nonnegative':True},{'quotient':{'unit':'integer','role':'quotient'},'remainder':{'unit':'year','role':'remainder'}})
            self.env.remainders.append({'event':event,'claimed':False});self.env.focus=event['writes']['remainder' if cycle else 'quotient'];return event
        event=super().divide(x,d,spans,cycle)
        if not cycle:
            numerator=self.underlying_event(x)
            matches=[]
            if numerator['kind']=='multiply':
                for factor,operand in [('left','right'),('right','left')]:
                    fv=self.env.values[numerator['reads'][factor]];ov=self.env.values[numerator['reads'][operand]]
                    for rule in CONTEXTUAL_RATES:
                        if rule['numerator_term'] in fv.get('labels',[]) and fv.get('role')=='parameter' and self.env.values[d].get('role')=='parameter' and set(rule['denominator_terms'])&set(self.env.values[d].get('labels',[])) and ov['unit'] in (rule['from_unit'],rule['from_unit']+'_ordinal') and self.env.scope.get('tradition') in rule['traditions'] and self.task in rule['tasks']:
                            matches.append((rule,numerator['reads'][factor],numerator['reads'][operand]))
            if len(matches)==1:
                rule,factor,operand=matches[0]
                rate=dict(rule,numerator_parameter=factor,denominator_parameter=d,numerator=self.env.events[self.env.values[factor]['producer']]['attributes']['value'],denominator=self.env.events[self.env.values[d]['producer']]['attributes']['value'])
                checked=check_transition({'kind':'convert','reads':{'value':'input'},'writes':{'result':'output'},'attributes':{'evidence':[{'basis':rule['basis']}]}},{'input':self.env.values[operand],'output':{'unit':rule['to_unit']}},{'rate':rate})
                event['attributes']['quantity_transition']=dict(checked,rate=rate,operand=operand,source_operation=numerator['id'],scope=dict(self.env.scope))
                event['evidence']=[{'basis':'scholarly_interpretation','source_locator':rule['basis']}]
                for port in ('quotient','remainder'):
                    value=self.env.values[event['writes'][port]];value['quantity_kind']='duration' if rule['to_unit']=='day' else 'count';value['unit']=rule['to_unit'] if port=='quotient' else rule['to_unit']+'_fraction';value['representation']={'kind':'whole' if port=='quotient' else 'fraction_numerator','denominator_id':d}
                    if rule.get('residual'):value['time_frame']='annual_residual'
                    elif rule['to_unit']=='day':value['time_frame']='full_local_epoch'
            elif self.env.values[x]['unit']=='day_fraction':
                event['attributes']['quantity_transition']={'status':'resolved','transition':'fraction_carry','denominator':d}
            elif self.task!='intercalation':
                event['attributes']['quantity_transition']={'status':'unknown','transition':'unresolved_quantity_use'}
                for port in ('quotient','remainder'):self.env.values[event['writes'][port]]['unit']='unknown'
                event['attributes']['execution_blocked']='unknown_quantity_use'
                self.env.issue('unknown_quantity',spans,[x,d],reason='no declared contextual rate or compatible fraction carry')
            else:
                for port in ('quotient','remainder'):self.env.values[event['writes'][port]]['unit']='integer'
                event['attributes']['quantity_transition']={'status':'resolved','transition':'integer_count_division','basis':'source count-one construction'}
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
        for key in ('quantity_kind','representation','time_frame','epoch'):
            if key in self.env.values[source]:self.env.values[v][key]=copy.deepcopy(self.env.values[source][key])
        if self.env.query=='main':
            ports={'new_moon':{'積月':'months','閏餘':'intercalation_remainder','積日':'whole_days','小餘':'small_remainder','大餘':'day_offset'},'winter':{'大餘':'winter_whole_residual','小餘':'winter_remainder'}}
            p=ports.get(self.task,{}).get(label)
            if p:self.export(p,v)
            if self.task=='winter' and label=='小餘':
                denom=self.env.events[self.env.values[self.day_denominator]['producer']]['attributes'].get('value')
                self.export('winter_remainder'+str(denom),v)
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
        methods=[m for m in self.report['method_library'] if m['formal_inputs']['offset']['unit']=='day' and m['definition_scope'].get('tradition')==self.env.scope.get('tradition')]
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
        reads={'offset':big,'origin':origin,'cycle':cycle}
        small=self.env.active.get('小餘')
        if small:reads['fraction']=small
        e=self.env.event('method_call',reads,['remainder','result'],spans,'V3_CALL',{'target':m['id'],'method':'cycle_and_count','body':m['body'],'formal_returns':m['returns'],'inferred':inferred},{'remainder':{'unit':'day','role':'remainder'},'result':{'unit':'day_index','role':'day_index'}})
        e['method_binding']={'definition_id':m['id'],'actuals':reads,'formal_inputs':m['formal_inputs'],'definition_spans':m['source_spans']}
        self.env.alias(e['writes']['remainder'],'大餘',spans,'V3_CALL');self.branch_finalized=True
        if current=='winter':self.export('winter_day',e['writes']['result'])
        elif current=='new_moon' and self.env.query in ('其次月','後月朔'):
            self.export('next_moon_day',e['writes']['result']);self.export('next_moon_remainder',small)
        elif current in ('nodes','qi'):
            self.export('first_node_day' if current=='nodes' else 'first_qi_day',e['writes']['result'])
        return e
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
    def export_threshold(self,e):
        if e and e['kind']=='threshold':
            judgment=e['attributes'].get('judgment','')
            if judgment in ('歲有閏','其歲有閏'):self.export('has_intercalation',e['writes']['result'],'new_moon')
            if judgment=='其月大':self.export('month_long',e['writes']['result'],'new_moon')
    def lower_entry(self,c,sp):
        raw=c['text']
        # Epoch source mentions, normalized only by explicitly selected convention.
        if re.fullmatch(r'置太極上元以來',raw) or re.fullmatch(r'以(.+)除去上元',raw):
            profile=next((p for p in self.profile.values() if 'input' in p),None)
            if not profile:self.env.issue('missing_profile',sp,['epoch count convention']);return True
            v=self.env.value('input',{},sp,'V3_EPOCH',{'name':profile['input'],'parameter':False},{'unit':'year','role':'external_input','labels':[profile['input']]})
            self.export('epoch_count',v)
            if profile['count']=='inclusive':
                one=self.literal('一',sp);v=self.inferred_value('subtract',{'left':v,'right':one},sp,'V3_ORDINAL',{}, {'unit':'year'},profile['basis'])
            self.env.focus=v;self.epoch_value=v;self.export('elapsed_years',v)
            m=re.fullmatch(r'以(.+)除去上元',raw)
            if m:
                e=self.divide(v,self.get(m.group(1),sp,True),sp,True);self.export('origin_index',e['writes']['quotient']);self.export('origin_remainder',e['writes']['remainder']);self.entry_remainder=e['writes']['remainder']
            return True
        if raw=='外所求年':
            value=self.env.value('load',{'value':self.env.focus},sp,'V3_COUNT_CONVENTION',{'count_convention':'elapsed','selected_profile':'ST_elapsed'},{'unit':'year'})
            self.analytical(self.env.events[self.env.values[value]['producer']],PROFILES['ST_elapsed']['basis']);self.env.focus=value;self.export('elapsed_years',value);return True
        m=re.fullmatch(r'盈(.+)除之',raw)
        if m:
            e=self.divide(self.env.focus,self.get(m.group(1),sp,True),sp,True);self.export('origin_remainder',e['writes']['remainder']);self.entry_remainder=e['writes']['remainder'];return True
        if raw=='餘不盈統者':
            self.concordance_divisor=self.get('統法',sp,True);self.concordance_local=self.entry_remainder;self.concordance_condition_spans=sp;return True
        case=re.fullmatch(r'(?:則|餘則)([天地人]統)(..)以來年數也',raw)
        if case:
            self.cases.append({'label':case.group(1),'head':case.group(2),'local':self.concordance_local,'source_spans':sp+getattr(self,'concordance_condition_spans',[])})
            return True
        if re.fullmatch(r'(?:又)?盈統',raw):self.pending_concordance=sp;return True
        if raw=='除之' and self.pending_concordance:
            self.concordance_local=self.binary('subtract',self.concordance_local,self.concordance_divisor,self.pending_concordance+sp,'V3_BRANCH_SUB')
            self.pending_concordance=None;return True
        if raw=='各以其統首日為紀':
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
        m=re.fullmatch(r'其餘以(.+)除之',raw)
        if m:
            e=self.divide(self.entry_remainder,self.get(m.group(1),sp,True),sp);self.entry_div=e;self.export('era_quotient',e['writes']['quotient']);self.export('era_remainder',e['writes']['remainder']);self.entry_remainder=e['writes']['remainder'];return True
        if raw=='所得數從天紀':
            self.era_index=self.env.value('count',{'offset':self.entry_div['writes']['quotient']},sp,'V3_TABLE_COLUMN',{'ordinal_origin':0,'cyclic':False,'sequence':['天紀','地紀','人紀'],'convention':'筭外'},{'unit':'table_column'});self.export('era_index',self.era_index);self.env.focus=self.entry_remainder;return True
        if raw in ('筭外則所入紀也','不滿紀法者','入紀年數也','筭外'):return True
        m=re.fullmatch(r'以(.+)除之',raw)
        if m:
            e=self.divide(self.entry_remainder,self.get(m.group(1),sp,True),sp);self.entry_div=e;self.export('obscuration_quotient',e['writes']['quotient']);self.export('obscuration_year_remainder',e['writes']['remainder']);return True
        if raw=='所得數從甲子蔀起':
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
        if raw.startswith('所入蔀也不滿') or raw=='筭上':return True
        if raw=='即所求年太歲所在':
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
        raw=c['text']
        if c['kind']=='update_count':
            control=next((x for x in self.loop_controls[self.doc['doc_id']] if x.get('candidate') is c),None)
            if not control or not control['stop']['operator']:
                self.env.issue('missing_profile' if control else 'incomplete_construction',sp,['repeat stop predicate']);return True
            initial=self.env.focus;inc=self.literal(c['slots']['increment']['text'],sp);limit=self.get(control['stop']['threshold']['text'],control['source_spans'],True)
            e=self.env.event('repeat',{'initial':initial,'increment':inc,'threshold':limit},['state','count'],control['source_spans'],'V3_REPEAT',{'control':control,'max_iterations':10000},{'state':{'unit':self.env.values[initial]['unit'],'scale':copy.deepcopy(self.env.values[initial]['scale']),'representation':copy.deepcopy(self.env.values[initial].get('representation',{'kind':'integer'}))},'count':{'unit':'integer'}})
            e['control']=control;self.export('loop_count',e['writes']['count']);self.export('loop_final_lag',e['writes']['state']);self.env.focus=e['writes']['count'];return True
        if c['kind']=='loop_threshold' or raw=='數所得':return True
        if raw=='起冬至':
            self.nominal(self.ex('intercalation','loop_count'),sp);return True
        if raw in ('算外','則中至終閏盈','則前月閏也','閏月也','筭盡之外'):return True
        if raw in ('中氣在朔若二日','或進退','以中氣定之'):
            self.boundary_spans=getattr(self,'boundary_spans',[])+sp;return True
        m=re.fullmatch(r'滿('+NUMBER+r')以上亦得一筭之數',raw)
        if m:
            e=self.task_division.get(('intercalation','main'))
            if not e:return False
            q,r=e['writes']['quotient'],e['writes']['remainder'];lower=self.literal(m.group(1),sp)
            pred=self.env.value('threshold',{'value':r,'lower':lower},sp,'V3_THRESHOLD',{'lower_inclusive':True},{'unit':'boolean'})
            count=self.binary('add',q,pred,sp,'V3_CONDITIONAL_COUNT')
            self.export('placement_q',q);self.export('placement_r',r);self.export('adjusted_count',count);self.env.focus=count;return True
        if c['kind']=='count_origin' and '十一月' in c['slots']['origin']['text']:
            self.nominal(self.env.focus,sp);return True
        if raw.startswith('餘以'):
            # Here 餘 explicitly continues the preceding subtraction result.
            self.text=raw[1:];before=len(self.report['events']);ok=super().parse_clause(raw[1:],self.indices[1:]);self.export('intercalation_complement',self.env.focus)
            for event in self.report['events'][before:]:
                if event['kind']=='alias':event['rule_id']='V3_DIFFERENCE'
            return ok
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
            before=self.env.focus;left=self.get(slots['left']['text'],sp,focus=before);right=self.get(slots['right']['text'],sp,focus=before)
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
            event=self.divide(dividend,self.get(slots['divisor']['text'],sp,True),sp)
            if label in self.env.active:
                self.env.alias(event['writes']['remainder'],label,sp);self.env.focus=event['writes']['quotient']
            return True
        if kind=='cycle_divide':
            self.divide(self.get(slots['value']['text'],sp),self.get(slots['divisor']['text'],sp,True),sp,True);return True
        if kind=='divide_by':
            self.divide(self.get(slots['value']['text'],sp),self.get(slots['divisor']['text'],sp,True),sp,True);return True
        if kind in ('name','remainder_name'):
            self.name(slots['label']['text'],sp,kind=='remainder_name');return True
        if kind=='pair_increment':
            self.add_increment(slots['receiver']['text'],slots['amount']['text'],sp);return True
        return False
    def lower(self,c):
        raw=c['text'];sp=c['source_spans'];self.current_candidate=c
        a,b=c['analysis_range'];self.indices=self.doc['analysis_to_source'][a:b];self.text=raw
        if c['kind']=='task_marker':
            target=c['slots']['target']['text'];marker=c['slots']['marker']['text'];task=TASKS.get(target)
            if task:
                # A postposed qi heading labels the already scoped preceding block.
                if task=='qi' and self.task=='qi':return True
                self.switch(task,sp)
                if task=='nodes':super().start_query(target,sp)
                return True
            if marker=='求':self.start_query(target,sp);return True
        if self.task=='era_entry' and self.lower_entry(c,sp):return True
        if (self.task=='intercalation' or c['kind'] in ('update_count','loop_threshold') or raw=='數所得') and self.lower_intercalation(c,sp):return True
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
        if c['kind']=='denominator_declaration':return True
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
        if raw=='冬至後':self.temporal_anchor={'label':raw,'source_spans':sp};return True
        if c['kind']=='unclassified' and self.task=='declarations':
            # Leading subject (其四行各 / 中央各) precedes a mixed-duration candidate.
            if re.fullmatch(r'(?:其.+各|中央各)',raw):return True
        if raw in ('則所求冬至日也','則前年冬至之日也','小寒日也'):return True
        if self.task=='winter' and raw.startswith('其餘以'):
            raw=raw[2:];return bool(self.count(self.get('大餘',sp),re.fullmatch(r'以(.+)命之',raw).group(1),sp,'day_index'))
        cycle_match=re.fullmatch(r'(.+?)(?:滿|盈)('+NUMBER+r')除去之',raw)
        if cycle_match:
            value=self.get(cycle_match.group(1),sp);divisor=self.literal(cycle_match.group(2),sp);e=self.divide(value,divisor,sp,True)
            if cycle_match.group(1)=='大餘':self.env.alias(e['writes']['remainder'],'大餘',sp)
            return True
        if raw.startswith('又加'):
            self.branch_finalized=False;self.branch_additions={};self.branch_support=list(sp)
            # Recurrence consumes the active query's previous state.
            return super().parse_clause(raw[1:],self.indices[1:])
        if self.lower_primitive(c,sp):return True
        before=len(self.report['events'])
        ok=super().parse_clause(raw,self.indices)
        if ok:
            self.export_threshold(self.pending_condition)
            if self.task=='intercalation' and c['kind']=='multiply':self.export('intercalation_complement',self.env.focus)
        for e in self.report['events'][before:]:
            if e['kind']=='threshold':self.export_threshold(e)
        return ok
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
        self.context()
        for d in self.docs:
            if d['category']!='primary_documents':continue
            self.doc=d;self.temporal_anchor=None;self.fraction_denominator=None;self.env.query='main';self.env.scope['query']='main';self.env.active=self.env.main;self.env.remainders=[];self.env.products=[]
            candidates=self.all_candidates[d['doc_id']]
            for c in candidates:
                try:ok=self.lower(c)
                except (KeyError,IndexError,TypeError,ValueError,AttributeError) as error:
                    ok=False;self.report['diagnostics'].append({'kind':'parser_exception','message':str(error),'source_spans':c['source_spans']})
                c['status']='selected' if ok else 'unresolved';c['selection_reason']='typed slots and scoped state' if ok else 'no compatible lowering'
                self.report['coverage']['accounted_spans' if ok else 'unparsed_spans'].extend(c['source_spans'])
                if not ok:
                    self.env.issue('unresolved_parser',c['source_spans'],['unparsed_instruction'])
                    self.env.focus=self.env.value('input',{},c['source_spans'],'V3_UNKNOWN_FOCUS',{'name':'unresolved_focus','parameter':False},{'unit':'unknown','role':'missing_upstream'})
            if candidates:self.finish_task_document(candidates[-1]['source_spans'])
        self.temporal_views()
        from .audit import audit
        self.report['diagnostics'].extend(audit(self.report))
        return self.report
