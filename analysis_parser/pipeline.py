"""Compositional token grammar and persistent environment for calendrical instructions.

Rules operate on local constructions and source-derived declarations. No document ID,
fixture, reference graph, or sentence lookup participates in semantic decisions.
"""
import hashlib
import re
from pathlib import Path
from .inputs import documents, clauses, span, number, NUMBER
from .state import Environment

# Small, explicit lexical roles. Unlisted technical names remain opaque.
UNITS={'積次':'station','次餘':'station_fraction','定次':'station','月元餘':'month','積月':'month','合積月':'month','入蔀積月':'month','小積':'month','入紀月':'month','入歲月數':'month','月元餘':'month','入章月數':'month','積中':'medial','中元餘':'medial','入章中數':'medial','星見中次':'medial','積日':'day','大餘':'day','入統歲數':'year','入蔀年':'year_ordinal','定見復數':'planet_event','積合':'planet_event','章歲':'year','章法':'year','章月':'month','章中':'medial','元中':'medial','元月':'month','紀月':'month','蔀月':'month','蔀日':'day','閏':'intercalary_month'}
INPUT_NAMES={'入統歲數','入蔀年','定見復數','積合','統首日','所入蔀名'}
CURRENT_REQUIRED={'積中','中餘','積月','入蔀積月'}
ROLE_ALIASES={'San_tong_li':{'閏分':'見閏分'},'Han_Si_fen_li':{'入蔀積月':'積月'}}

class Parser:
    def __init__(self,packet):
        self.packet=packet;self.docs=documents(packet)
        self.report={'analysis_id':'analysis-'+hashlib.sha256(str([(d['text'],d['category']) for d in self.docs]).encode()).hexdigest()[:16],'input_mode':packet.get('input_mode','declared_edited_primary_context'),'provenance':{'source_hashes':{d['doc_id']:d['actual_sha256'] for d in self.docs},'parser_hash':self.hash_code(),'rules_hash':self.hash_code()},'value_instances':[],'events':[],'bindings':[],'unresolved':[],'coverage':{'accounted_spans':[],'unparsed_spans':[]},'diagnostics':[],'documents':self.docs,'observations':[],'branches':[],'methods':[]}
        self.env=Environment(self.report,packet.get('provided_scope',{}));self.doc=None;self.indices=[];self.text=''
        self.day_denominator=None;self.cycle_divisor=None;self.count_method=None;self.day_base={};self.query_intervals={};self.branch_additions={};self.branch_finalized=True;self.pending_cycle=None;self.pending_condition=None;self.schedule=[];self.schedule_spans=[];self.scan_event=None;self.count_offset=None
    @staticmethod
    def hash_code():
        return hashlib.sha256(b''.join(p.read_bytes() for p in sorted(Path(__file__).parent.glob('*.py')))).hexdigest()
    def s(self,a=0,b=None):
        b=len(self.indices) if b is None else b
        return span(self.doc,self.indices[a],self.indices[b-1]+1)
    def obs(self,text,spans,kind):
        self.report['observations'].append({'text':text,'kind':kind,'source_spans':spans})
    def literal(self,text,spans):
        return self.env.value('literal',{},spans,'R01',{'value':number(text)},{'role':'literal','unit':'integer','labels':[text]})
    def missing(self,name,spans,parameter=False,cause='unresolved_parser'):
        parameter = parameter and name not in INPUT_NAMES and len(name) != 1
        role='parameter_missing' if parameter else 'external_input' if name in INPUT_NAMES or len(name)==1 else 'missing_upstream'
        if role not in ('external_input',):
            self.env.issue('requires_external_data' if parameter else cause,spans,[name],reason='No source-defined current instance' if not parameter else 'Parameter value is not declared in runtime context')
        return self.env.value('input',{},spans,'R06',{'name':name,'parameter':parameter},{'labels':[name],'role':role,'unit':UNITS.get(name,'opaque')})
    def get(self,name,spans,parameter=False,focus=None):
        name=name.strip()
        if re.fullmatch(NUMBER,name):return self.literal(name,spans)
        if name in ('之','其餘','所得',''):
            selected=focus or self.env.focus
            if selected:
                self.env.bind(name,[selected],selected,spans,'R06');return selected
            return self.missing(name or 'elided_operand',spans)
        if name.startswith('其'):name=name[1:]
        original=name
        aliases=ROLE_ALIASES.get(self.env.scope.get('tradition'),{})
        if name not in self.env.active and name not in self.env.parameters and name in aliases:
            name=aliases[name]
        current=self.env.active.get(name)
        params=self.env.parameters.get(name,[])
        candidates=([current] if current else [])+params
        if current and not parameter:
            selected=current
        elif (name in CURRENT_REQUIRED or original in CURRENT_REQUIRED) and not parameter:
            selected=None
        elif len(params)==1:selected=params[0]
        elif len(params)>1:
            self.env.issue('interpretive_ambiguity',spans,[name],candidate_ids=params);selected=None
        else:selected=None
        if selected is None:
            is_parameter=parameter or name.endswith('法') or name in ('章閏','章歲','章月','蔀月','蔀日')
            selected=self.missing(name,spans,is_parameter)
            if not params:self.env.active.setdefault(name,selected)
        self.env.bind(original,candidates,selected,spans,'R13' if params else 'R06')
        return selected
    def context(self):
        # Declarations and their postposed aliases share one source-ordered stream.
        declaration_pattern = r'(?:^|[，,．。；;])\s*([^，,．。；;\s' + '零〇一二三四五六七八九十百千萬万0-9' + r']{1,12})[，,]?\s*(' + NUMBER + r')(?=[，,．。；;]|$)'
        for d in self.docs:
            if d['category']!='context_documents':continue
            self.doc=d
            context_text=d['analysis_text'];source_indices=d['analysis_to_source']
            items=[(m.start(1),'declaration',m) for m in re.finditer(declaration_pattern,context_text)]
            items += [(m.start(),'alias',m) for m in re.finditer(r'因為([^，,．。；;]+)',context_text)]
            last=None
            for _,kind,m in sorted(items,key=lambda item:item[0]):
                if kind=='declaration':
                    label=m.group(1);sp=[span(d,source_indices[m.start(1)],source_indices[m.end(2)-1]+1)]
                    if any(x in label for x in ('推','乘','減','滿','得','除','以')):continue
                    v=self.env.value('parameter',{},sp,'R13',{'name':label,'value':number(m.group(2))},{'labels':[label],'role':'parameter','unit':UNITS.get(label,'opaque')})
                    self.env.parameters.setdefault(label,[]).append(v);last=v
                    self.obs(m.group(),sp,'parameter_declaration')
                else:
                    label=m.group(1);sp=[span(d,source_indices[m.start()],source_indices[m.end()-1]+1)]
                    if last is None:
                        reason='alias has no preceding declaration in its source scope'
                        self.env.issue('unresolved_parser',sp,[label],reason=reason)
                        self.env.bind(label,[],None,sp,'R13',reason)
                    else:
                        self.env.parameters.setdefault(label,[]).append(last)
                        self.env.values[last]['labels'].append(label)
                        self.env.bind(label,[last],last,sp,'R13')
                        self.report['bindings'][-1]['supporting_spans'].extend(sp)
                    self.obs(m.group(),sp,'parameter_alias')
    def prescan(self):
        for d in self.docs:
            if d['category']!='primary_documents':continue
            for m in re.finditer('('+NUMBER+')歲('+NUMBER+')閏',d['analysis_text']):
                self.schedule.append({'year':number(m.group(1)),'cumulative_intercalations':number(m.group(2))})
                self.schedule_spans.append(span(d,d['analysis_to_source'][m.start()],d['analysis_to_source'][m.end()-1]+1))
        self.schedule.sort(key=lambda x:x['year'])
    def depends_on(self,value_id,ancestor):
        pending=[value_id];seen=set()
        while pending:
            value=pending.pop()
            if value==ancestor:return True
            if value in seen or value not in self.env.values:continue
            seen.add(value)
            pending.extend(self.env.events[self.env.values[value]['producer']]['reads'].values())
        return False
    def underlying_event(self,value_id):
        value=self.env.values[value_id]
        event=self.env.events[value['producer']]
        while event['kind'] in ('alias','load'):
            value=self.env.values[event['reads']['value']]
            event=self.env.events[value['producer']]
        return event
    def medial_month_bridge(self,medial_id,month_id=None):
        # R15 is a calibrated conversion inside a declared planetary tradition,
        # supported by both period declarations and the parsed medial projection.
        if self.env.scope.get('tradition')!='San_tong_li' or not self.env.scope.get('planet'):return None
        params={}
        for label,expected in (('章歲',19),('章月',235)):
            candidates=self.env.parameters.get(label,[])
            if len(candidates)!=1:return None
            value=candidates[0]
            if self.env.events[self.env.values[value]['producer']]['attributes'].get('value')!=expected:return None
            params[label]=value
        frame=self.underlying_event(medial_id)
        if frame['kind']!='divmod' or self.env.values[frame['writes']['quotient']]['unit']!='medial':return None
        medial_cycle=None
        for candidate in self.report['events']:
            if candidate['kind']!='cycle_reduce':continue
            divisor=self.env.events[self.env.values[candidate['reads']['divisor']]['producer']]
            if divisor['attributes'].get('value')==12 and self.depends_on(candidate['reads']['dividend'],frame['writes']['quotient']):
                medial_cycle=candidate
        if medial_cycle is None:return None
        if month_id is not None:
            month_frame=self.underlying_event(month_id)
            if month_frame['kind']!='divmod':return None
            divisor=self.env.values[month_frame['reads']['divisor']]
            if '見月法' not in divisor['labels']:return None
        supporting=frame['source_spans']+medial_cycle['source_spans']
        supporting+=sum([self.env.values[v]['source_spans'] for v in params.values()],[])
        return {'from':'medial','to':'month','scope':dict(self.env.scope),'basis':'calibrated 19-year/235-month and 12-medial yearly structure','parameter_ids':params,'medial_cycle':medial_cycle['id'],'supporting_value_ids':list(params.values())+[frame['writes']['quotient']],'supporting_spans':supporting,'rule_id':'R15'}
    def binary(self,kind,left,right,spans,rule='R02',attrs=None):
        lv,rv=self.env.values[left],self.env.values[right]
        unit=lv['unit'] if kind in ('add','subtract') else 'product'
        scale=lv['scale'] if kind in ('add','subtract') else 1
        attrs=attrs or {};requires_bridge=False;bridge=None;bridge_spans=[]
        if kind=='add' and {lv['unit'],rv['unit']}=={'month','medial'}:
            requires_bridge=True
            bridge=self.medial_month_bridge(left if lv['unit']=='medial' else right,right if rv['unit']=='month' else left)
            if bridge:unit='month'
        if kind=='multiply' and ('章歲' in lv['labels'] and rv['unit']=='medial_fraction'):
            requires_bridge=True;bridge=self.medial_month_bridge(right)
            if bridge:
                bridge=dict(bridge,**{'from':'medial_fraction','to':'month_numerator','parameter':left});unit='month_numerator'
        if requires_bridge:
            if bridge:
                bridge_spans=bridge.pop('supporting_spans')
                attrs['unit_bridge']=bridge
            else:
                attrs['resolution_status']='unresolved_parser';attrs['execution_blocked']='unsupported unit bridge'
                self.env.issue('unresolved_parser',spans,[left,right],reason='unsupported unit bridge',units=[lv['unit'],rv['unit']])
        v=self.env.value(kind,{'left':left,'right':right},spans,rule,attrs,{'unit':unit,'scale':scale})
        if bridge:
            event=self.env.events[self.env.values[v]['producer']]
            event['evidence_status']='scholarly_calibrated'
            event['supporting_spans']=bridge_spans
        self.env.focus=v
        if kind=='multiply':self.env.products.append(v)
        return v
    def divide(self,x,d,spans,cycle=False):
        dl=self.env.values[d]['labels'];labels=set(dl)
        unit=self.env.values[x]['unit']
        if not cycle:
            if labels & {'章歲','章法','見月法','月法'}:unit='month' if labels & {'章歲','章法','見月法'} or self.env.scope.get('planet') else 'day'
            elif labels & {'日法','蔀月'}:unit='day'
            elif '見中法' in labels:unit='medial'
            elif '章月' in labels:unit='intercalary_month'
            else:unit='opaque'
        factor=self.env.events[self.env.values[d]['producer']]['attributes'].get('value')
        remunit=unit if cycle else unit+'_fraction'
        event=self.env.event('cycle_reduce' if cycle else 'divmod',{'dividend':x,'divisor':d},['quotient','remainder'],spans,'R08' if cycle else 'R04',{'integer_nonnegative':True},{'quotient':{'role':'cycle_count' if cycle else 'quotient','unit':'cycle' if cycle else unit,'scale':1},'remainder':{'role':'remainder','unit':remunit,'scale':1 if cycle else {'denominator':d,'value':factor}}})
        self.env.remainders.append({'event':event,'claimed':False})
        self.env.focus=event['writes']['remainder' if cycle else 'quotient']
        if not cycle and unit=='day':self.day_denominator=d
        if cycle and unit=='day':self.cycle_divisor=d
        return event
    def abandon_pending_cycle(self,reason,interruption_spans=None):
        if self.pending_cycle is None:return
        _,_,spans=self.pending_cycle
        self.env.issue('incomplete_construction',spans,['除之'],reason=reason)
        diagnostic={'kind':'incomplete_construction','message':reason,'source_spans':spans,'missing_continuation':'除之'}
        if interruption_spans:diagnostic['interruption_spans']=interruption_spans
        self.report['diagnostics'].append(diagnostic)
        self.pending_cycle=None
    def remainder(self,spans,label=None):
        frames=[r for r in self.env.remainders if not r['claimed']]
        if not frames:frames=self.env.remainders[-1:]
        all_candidates=[r['event']['writes']['remainder'] for r in frames]
        expected={'小餘':'day_fraction','中餘':'medial_fraction','月餘':'month_fraction'}.get(label,UNITS.get(label))
        unknown_units={'opaque','opaque_fraction','product','unknown'}
        candidates=[v for v in all_candidates if expected is None or self.env.values[v]['unit']==expected or self.env.values[v]['unit'] in unknown_units]
        selected=candidates[0] if len(candidates)==1 else None
        reason=None
        if selected:
            for r in frames:
                if r['event']['writes']['remainder']==selected:r['claimed']=True
        else:
            reason='multiple compatible unclaimed operation remainders' if len(candidates)>1 else ('no remainder compatible with '+expected if expected else 'missing remainder producer')
            self.env.issue('interpretive_ambiguity' if len(candidates)>1 else 'unresolved_parser',spans,candidates or all_candidates or ['remainder_producer'],reason=reason)
        self.env.bind('remainder',all_candidates,selected,spans,'R05',reason=reason)
        for candidate in self.report['bindings'][-1]['candidates']:
            unit=self.env.values[candidate['id']]['unit']
            if expected and unit!=expected and unit not in unknown_units:
                candidate['rejection_reason']='known unit mismatch: '+unit+' cannot satisfy '+expected
        if selected is None:
            # A missing-value node keeps downstream dependencies inspectable. It
            # is not an accepted binding and does not reuse an incompatible port.
            return self.env.value('input',{},spans,'R05',{'name':'unbound_remainder','parameter':False},{'role':'missing_upstream','unit':expected or 'opaque'})
        return selected
    def name(self,label,spans,remainder=False):
        if remainder:v=self.remainder(spans,label)
        else:v=self.env.focus or self.missing('unnamed_result',spans)
        result=self.env.alias(v,label,spans)
        if label in UNITS:self.env.values[result]['unit']=UNITS[label]
        return result
    def start_query(self,label,spans):
        self.finish_query(spans)
        self.env.query=label;self.env.scope['query']=label;self.env.active=dict(self.env.main)
        self.env.focus=self.env.active.get(self.env.last_receiver) if self.env.last_receiver else self.env.focus
        self.branch_additions={};self.branch_finalized=False;self.branch_support=list(spans)
        q=self.env.event('query',dict(self.env.main),[],spans,'R09',{'target':label,'base_state':dict(self.env.main)})
        self.report['branches'].append({'id':q['id'],'target':label,'base_state':dict(self.env.main),'scope':dict(self.env.scope),'source_spans':spans})
    def count(self,offset,origin_name,spans,role=None,convention='算外'):
        role=role or 'month_ordinal'
        reads={'offset':offset}
        if origin_name in ('統首日','所入蔀名'):
            reads['origin']=self.get(origin_name,spans)
            reads['cycle']=self.cycle_divisor
        elif role in ('medial_ordinal','station_ordinal'):
            # The already parsed year-position projection declares its cycle.
            frame=next((r['event'] for r in reversed(self.env.remainders) if r['event']['kind']=='cycle_reduce' and self.depends_on(offset,r['event']['writes']['remainder'])),None)
            if frame:reads['cycle']=frame['reads']['divisor']
        if role!='month_ordinal' and not reads.get('cycle'):
            reads['cycle']=self.missing('count_cycle',spans,cause='requires_external_data')
        attrs={'origin_label':origin_name,'convention':convention,'zero_offset_at_origin':True,'output_role':role,'ordinal_origin':1,'cyclic':role!='month_ordinal','numeric_projection_evidence':'scholarly_calibrated_counting_convention'}
        ports=['result'];metadata={'result':{'role':role,'unit':'ordinal','labels':[role]}}
        civil=re.search('('+NUMBER+')月',origin_name)
        if civil:
            attrs['civil_origin']=number(civil.group(1));attrs['civil_cycle']=12
            attrs['civil_cycle_basis']='twelve civil month-name counting convention; intercalary placement remains externally constrained'
            ports.append('civil_month_number');metadata['civil_month_number']={'role':'civil_month_number','unit':'month_name_index','labels':['civil_month_number']}
        event=self.env.event('count',reads,ports,spans,'R10',attrs,metadata)
        event['evidence_status']='scholarly_calibrated'
        if origin_name in ('統首日','所入蔀名'):
            self.count_method={'event_id':event['id'],'origin':reads['origin'],'cycle':reads['cycle'],'origin_label':origin_name,'convention':convention}
            self.report['methods'].append(dict(self.count_method))
        return event
    def recall(self,spans,inferred=False):
        method=self.count_method
        if not method:
            self.env.issue('unresolved_parser',spans,['previous_count_method']);return
        big=self.get('大餘',spans)
        call=self.env.event('method_call',{'offset':big,'origin':method['origin'],'cycle':method['cycle']},['remainder','result'],spans,'R12',{'target':method['event_id'],'method':'cycle_and_count','convention':method['convention'],'inferred':inferred},{'remainder':{'role':'remainder','unit':'day'},'result':{'role':'day_index','unit':'ordinal','labels':['朔日']}})
        self.env.alias(call['writes']['remainder'],'大餘',spans,'R12')
        self.branch_finalized=True
    def finish_query(self,spans):
        if self.env.query=='main' or self.branch_finalized:return
        if not {'大餘','小餘'} <= set(self.branch_additions):return
        self.query_intervals[self.env.query]=dict(self.branch_additions)
        if self.day_denominator and self.count_method:
            inferred_start=len(self.report['events'])
            spans=list(self.branch_support)
            spans+=self.env.events[self.env.values[self.day_denominator]['producer']]['source_spans']
            spans+=self.env.events[self.count_method['event_id']]['source_spans']
            small=self.get('小餘',spans);big=self.get('大餘',spans)
            d=self.divide(small,self.day_denominator,spans)
            d['attributes']['inferred_reuse']=True
            self.env.alias(d['writes']['remainder'],'小餘',spans,'R12')
            carry=self.binary('add',big,d['writes']['quotient'],spans,'R11')
            self.env.alias(carry,'大餘',spans,'R11')
            self.recall(spans,True)
            for inferred in self.report['events'][inferred_start:]:
                inferred['evidence_status']='rule_inferred'
                inferred['attributes']['inference_basis']='Normalize the declared query interval using the earlier day-fraction and cyclic counting methods'
                inferred['attributes']['supporting_method']=self.count_method['event_id']
    def add_increment(self,label,numeral,spans):
        receiver=self.get(label,spans);amount=self.literal(numeral,spans)
        val=self.binary('add',receiver,amount,spans,'R09' if self.env.query!='main' else 'R02',{'receiver':label,'increment':True})
        self.env.alias(val,label,spans);self.env.last_receiver=label
        if self.env.query!='main':
            self.branch_additions[label]=amount
            self.branch_support.extend(spans)
    def parse_clause(self,text,indices):
        self.text=text;self.indices=indices;sp=[self.s()];self.obs(text,sp,'clause')
        # Query/heading markers open scope; they do not manufacture arithmetic.
        if text.startswith('求'):
            self.start_query(text[1:],sp);return True
        if text.startswith('推'):
            self.obs(text[1:],sp,'procedure_target')
            return bool(text[1:]) and not any(operator in text[1:] for operator in ('乘','減','得一','除之','去之'))
        if text in ('算外','筭外','筭盡之外'):
            if self.report['events'] and self.report['events'][-1]['kind']=='count':self.report['events'][-1]['attributes']['convention']=text
            return True
        if text in ('則朔日也','則前年天正十一月朔日也','則星所見中次也','則星所見月也','星合所在之月也'):
            return True
        # Postposed control data remain source events and drive earlier year_scan.
        if text=='入章' or re.fullmatch('('+NUMBER+')歲('+NUMBER+')閏',text):
            self.env.event('schedule',{},[],sp,'R14',{'schedule':self.schedule,'source_role':'cumulative_intercalation_schedule'});return True
        if text=='至有閏之歲':
            return self.scan_event is not None
        if re.fullmatch('除('+NUMBER+')',text) and self.scan_event is not None:
            self.scan_event['attributes']['intercalary_year_months']=number(text[1:]);self.scan_event['source_spans'].extend(sp);return True
        # Bounded conditions are independent predicates, not control of subsequent paragraphs.
        m=re.fullmatch(r'(?:其)?(.*?)(?:滿)?('+NUMBER+r')以上(?:至('+NUMBER+r')(.+))?',text)
        if m:
            name=m.group(1).removesuffix('滿');x=self.get(name,sp) if name else self.env.focus
            low=self.literal(m.group(2),sp);reads={'value':x,'lower':low}
            if m.group(3):reads['upper']=self.literal(m.group(3),sp)
            e=self.env.event('threshold',reads,['result'],sp,'R07',{'lower_inclusive':True,'upper_inclusive':True,'judgment':m.group(4),'scope_end':'judgment'},{'result':{'role':'intercalary_candidate' if m.group(3) else 'predicate','unit':'boolean'}})
            self.pending_condition=e;return True
        if text in ('歲有閏','其歲有閏','其月大'):
            if self.pending_condition:
                self.pending_condition['attributes']['judgment']=text;self.pending_condition['source_spans'].extend(sp);return True
            return False
        if text=='閏或進退':
            self.pending_boundary=sp;return True
        if text=='以朔制之':
            nominal=[e for e in self.report['events'] if e['kind']=='count']
            predicate=[e for e in self.report['events'] if e['kind']=='threshold']
            reads={}
            if nominal:reads['nominal_month']=nominal[-1]['writes']['result']
            if predicate:reads['candidate']=predicate[-1]['writes']['result']
            bounds=self.missing('boundary_data',sp,cause='requires_external_data');reads['boundary_data']=bounds
            self.env.event('external_constraint_call',reads,['result'],getattr(self,'pending_boundary',[])+sp,'R12',{'method':'constrain_by_conjunction','missing_data':['adjacent_conjunction_events','medial_qi_events'],'allowed_adjustments':['advance','retreat']},{'result':{'role':'final_month_status','unit':'status'}});return True
        if text in ('數除如法','命之如前'):
            self.recall(sp);return True
        # Count constructors distinguished from additive 從 by 起 and a role prefix.
        m=re.fullmatch(r'(中數|次數|數)?從(.+)起',text)
        if m:
            role={'中數':'medial_ordinal','次數':'station_ordinal'}.get(m.group(1))
            offset=self.count_offset if role and self.count_offset else self.env.focus
            if role:self.count_offset=offset
            if m.group(2)=='統首日':offset=self.get('大餘',sp);role='day_index'
            self.count(offset,m.group(2),sp,role);return True
        m=re.fullmatch(r'不盈者數起[於于](.+)',text)
        if m:
            offset=self.scan_event['writes']['remainder'] if self.scan_event else self.remainder(sp)
            self.count(offset,m.group(1),sp,'month_ordinal');return True
        m=re.fullmatch(r'以(.+)命之',text)
        if m:
            self.count(self.get('大餘',sp),m.group(1),sp,'day_index','筭盡之外');return True
        if text.startswith('倍'):
            target=text[1:];interval=self.query_intervals.get(target)
            if not interval:
                self.env.issue('unresolved_parser',sp,['interval:'+target]);return False
            two=self.literal('二',sp)
            self.env.events[self.env.values[two]['producer']]['evidence_status']='rule_inferred'
            self.env.events[self.env.values[two]['producer']]['attributes']['basis']='semantic multiplier of 倍'
            self.branch_support.extend(sp)
            for label,delta in interval.items():
                doubled=self.env.value('interval_scale',{'value':delta,'factor':two},sp,'R09',{'target_interval':target,'base_state':dict(self.env.main)},{'unit':self.env.values[delta]['unit'],'role':'increment'})
                result=self.binary('add',self.get(label,sp),doubled,sp,'R09',{'increment':True})
                self.env.alias(result,label,sp);self.branch_additions[label]=doubled
            return True
        # Explicitly selected quotient before addition (synthetic grammar included).
        if text.startswith('所得'):
            if self.env.remainders:self.env.focus=self.env.remainders[-1]['event']['writes']['quotient']
            return self.parse_clause(text[2:],indices[2:])
        # R05 suffixes compose with arithmetic within one punctuation segment.
        m=re.fullmatch(r'(不盈者|不滿|不盡|其餘|餘)(?:名曰|名為|為|則)(.+?)(?:也)?',text)
        if m:
            self.name(m.group(2),sp,True);return True
        m=re.fullmatch(r'(?:名曰|名為|為|則)(.+?)(?:也)?',text)
        if m:
            self.name(m.group(1),sp);return True
        # Initialize a complete operand, optionally followed by explicit decrement.
        m=re.fullmatch(r'置(.+?)(?:減('+NUMBER+'))?',text)
        if m:
            value=self.get(m.group(1),sp)
            self.env.focus=self.env.value('load',{'value':value},sp,'R01',{}, {'unit':self.env.values[value]['unit'],'scale':self.env.values[value]['scale']})
            if m.group(2):
                self.binary('subtract',self.env.focus,self.literal(m.group(2),sp),sp,'R01',{'ordinal_to_elapsed':True})
                self.env.values[self.env.focus]['unit']='year'
            return True
        # Split only grammatical suffixes; operands themselves remain whole terms.
        m=re.fullmatch(r'((?:又|每)?以.+?乘.+?)(從之|為.+|名曰.+)',text)
        if m:
            cut=len(m.group(1));return self.parse_clause(m.group(1),indices[:cut]) and self.parse_clause(m.group(2),indices[cut:])
        m=re.fullmatch(r'(.*?(?:盈|滿).+?得一)(為.+|名曰.+)',text)
        if m:
            cut=len(m.group(1));return self.parse_clause(m.group(1),indices[:cut]) and self.parse_clause(m.group(2),indices[cut:])
        m=re.fullmatch(r'((?:從|上加).+?)(為.+)',text)
        if m:
            cut=len(m.group(1));return self.parse_clause(m.group(1),indices[:cut]) and self.parse_clause(m.group(2),indices[cut:])
        m=re.fullmatch(r'(?:又|每)?以(.+?)乘(.+)',text)
        if m:
            before=self.env.focus
            left=self.get(m.group(1),sp,focus=before);right=self.get(m.group(2),sp,focus=before)
            self.binary('multiply',left,right,sp,attrs={'word_order':[m.group(1),m.group(2)],'quantifier':'each' if text.startswith('每') else None});return True
        m=re.fullmatch(r'以(.+?)減(.+)',text)
        if m:
            self.binary('subtract',self.get(m.group(2),sp),self.get(m.group(1),sp),sp,attrs={'word_order':[m.group(1),m.group(2)],'direction':'B-A'});return True
        m=re.fullmatch(r'(.*?)(?:盈|滿)(?:其)?(.+?)得一',text)
        if m:
            x=self.get(m.group(1),sp) if m.group(1) else self.env.focus
            e=self.divide(x,self.get(m.group(2),sp,parameter=True),sp)
            if m.group(1) in self.env.active:
                self.env.alias(e['writes']['remainder'],m.group(1),sp);self.env.focus=e['writes']['quotient']
            return True
        # Cycle reduction variants, including separate 盈C / 除之 clauses.
        m=re.fullmatch(r'以(.+?)除(.+)',text)
        if m:
            d=self.get(m.group(1),sp,parameter=True);x=self.get(m.group(2),sp)
            if self.schedule and self.env.values[x]['unit']=='month' and re.fullmatch(NUMBER,m.group(1)) and m.group(2)=='之' and '至有閏之歲' in re.sub(r'\s+','',self.doc['text'][indices[-1]+1:]):
                e=self.env.event('year_scan',{'months':x},['years','remainder','months_removed'],sp+self.schedule_spans,'R14',{'ordinary_year_months':number(m.group(1)),'intercalary_year_months':None,'cumulative_schedule':self.schedule,'stop_condition':'remaining_months < months_in_current_year','branches':['ordinary','intercalary'],'start_year':1},{'years':{'unit':'year','role':'elapsed_years'},'remainder':{'unit':'month','role':'remainder'},'months_removed':{'unit':'month','role':'months_removed'}})
                self.scan_event=e;self.env.focus=e['writes']['remainder']
            else:self.divide(x,d,sp,True)
            return True
        m=re.fullmatch(r'(.+?)(?:盈|滿)(.+?)(?:去之)?',text)
        if m and '以上' not in text:
            x=self.get(m.group(1),sp);d=self.get(m.group(2),sp,parameter=True)
            if text.endswith('去之'):self.divide(x,d,sp,True)
            else:self.pending_cycle=(x,d,sp)
            return True
        if text=='除之' and self.pending_cycle:
            x,d,p=self.pending_cycle;self.divide(x,d,p+sp,True);self.pending_cycle=None;return True
        m=re.fullmatch(r'(.+?)以(.+?)(?:除去之|去之)',text)
        if m:
            self.divide(self.get(m.group(1),sp),self.get(m.group(2),sp,parameter=True),sp,True);return True
        m=re.fullmatch(r'(?:并|從|上加)(.+)',text)
        if m:
            name=m.group(1)
            if name=='之':
                if len(self.env.products)<2:return False
                left,right=self.env.products[-2:]
                self.env.bind('之',self.env.products[:-1],left,sp,'R03')
            else:
                left=self.get(name,sp);right=self.env.focus
                if text.startswith(('從','上加')):
                    self.env.bind('carried_amount',[right] if right else [],right,sp,'R11')
            result=self.binary('add',left,right,sp,'R11' if text.startswith(('從','上加')) else 'R03',{'receiver_label':name})
            if name=='大餘':self.env.alias(result,name,sp)
            return True
        m=re.fullmatch(r'加(.*?)('+NUMBER+')',text)
        if m:
            label=m.group(1) or self.env.last_receiver
            if not label:return False
            self.add_increment(label,m.group(2),sp);return True
        m=re.fullmatch(r'(小餘|大餘)('+NUMBER+')',text)
        if m:
            self.add_increment(m.group(1),m.group(2),sp);return True
        m=re.fullmatch(r'加(.+)',text)
        if m:
            self.binary('add',self.env.focus,self.get(m.group(1),sp),sp);return True
        return False
    def run(self):
        self.context();self.prescan()
        for d in self.docs:
            if d['category']!='primary_documents':continue
            if self.doc and self.indices:self.finish_query([self.s()])
            self.doc=d;self.env.query='main';self.env.scope['query']='main';self.env.active=self.env.main
            self.env.products=[];self.count_offset=None
            for text,indices in clauses(d):
                original_span=span(d,indices[0],indices[-1]+1)
                if self.pending_cycle is not None and text!='除之':
                    self.abandon_pending_cycle('pending cycle reduction was interrupted before 除之',[original_span])
                try:ok=self.parse_clause(text,indices)
                except (KeyError,IndexError,TypeError,ValueError) as error:
                    ok=False;self.report['diagnostics'].append({'kind':'parser_exception','message':str(error),'source_spans':[original_span]})
                self.report['coverage']['accounted_spans' if ok else 'unparsed_spans'].append(original_span)
                if not ok:self.env.issue('unresolved_parser',[original_span],['unparsed_instruction'])
            if self.indices:self.finish_query([self.s()])
            self.abandon_pending_cycle('pending cycle reduction reached end of document before 除之')
        from .control_ir import legacy_repeat_adapter
        for event in self.report['events']:
            if event['kind']=='year_scan':event['control']=legacy_repeat_adapter(event)
        from .audit import audit
        self.report['diagnostics'].extend(audit(self.report))
        return self.report

def parse_packet(packet):
    if str(packet.get('schema_version','')).startswith('3.'):
        from .scoped import ScopedParser
        return ScopedParser(packet).run()
    return Parser(packet).run()
