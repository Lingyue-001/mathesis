"""Immutable value creation and explicit source-supported candidate resolution."""
class Environment:
    def __init__(self, report, scope):
        self.report=report;self.scope=dict(scope,query='main');self.main={};self.active=self.main
        self.parameters={};self.values={};self.events={};self.focus=None
        self.remainders=[];self.products=[];self.query='main';self.last_receiver=None
    def event(self,kind,reads,ports,spans,rule,attributes=None, metadata=None):
        eid='e'+str(len(self.report['events'])+1)
        event={'id':eid,'kind':kind,'reads':reads,'writes':{},'source_spans':spans,'scope':dict(self.scope),'evidence_status':'declared_edited' if any(s.get('editorial_provenance') for s in spans) else 'text_overt','rule_id':rule,'attributes':attributes or {},'text_order':len(self.report['events']),'dependency_order':len(self.report['events'])}
        upstream=[self.values[value_id] for value_id in reads.values() if value_id in self.values]
        decision_refs=sorted({reference for value in upstream
                              for reference in value.get('adjudication_decision_refs', [])})
        if decision_refs:
            event['evidence_status']='mechanically_derived'
            event['adjudication_decision_refs']=decision_refs
            event['evidence_basis']='derived_from_reviewed_input'
            event['decision_origin']='automatic_derivation'
        if self.report.get('schema_version')=='3.0':
            doc_order={d['doc_id']:i for i,d in enumerate(self.report.get('documents',[]))}
            event['source_order']=[{'document_index':doc_order.get(s['doc_id']),'start':s['start'],'end':s['end']} for s in spans]
        for port in ports:
            vid='v'+str(len(self.report['value_instances'])+1)
            meta=(metadata or {}).get(port,{})
            val={'id':vid,'producer':eid,'output_port':port,'role':meta.get('role',port),'scope':dict(self.scope),'labels':meta.get('labels',[]),'source_label':next(iter(meta.get('labels',[])),None),'unit':meta.get('unit','opaque'),'scale':meta.get('scale',1),'source_spans':spans}
            for k,v in meta.items():val[k]=v
            if decision_refs and 'adjudication_decision_refs' not in val:
                val['adjudication_decision_refs']=decision_refs
                val.setdefault('evidence_basis','derived_from_reviewed_input')
                val.setdefault('decision_origin','automatic_derivation')
            if self.report.get('schema_version')=='3.0':
                unit=val['unit'];scale=val['scale']
                val.setdefault('quantity_kind','duration' if unit in ('day','day_fraction') else 'angle' if unit in ('du','du_fraction') else 'count' if unit in ('integer','year','year_ordinal','month','month_fraction') else 'unknown')
                val.setdefault('representation',{'kind':'fraction_numerator','denominator_id':scale['denominator']} if isinstance(scale,dict) and scale.get('denominator') else {'kind':'whole'})
                val.setdefault('resolution_status','unknown' if unit in ('opaque','product','unknown') else 'resolved')
                val.setdefault('evidence',[{'basis':'editorial_reading' if event['evidence_status']=='declared_edited' else 'source_explicit','source_spans':spans}])
            self.report['value_instances'].append(val);self.values[vid]=val;event['writes'][port]=vid
        self.report['events'].append(event);self.events[eid]=event
        return event
    def value(self,kind,reads,spans,rule,attributes=None,meta=None):
        return self.event(kind,reads,['result'],spans,rule,attributes,{'result':meta or {}})['writes']['result']
    def issue(self,cause,spans,missing,**kwargs):
        item={'cause':cause,'source_spans':spans,'missing_or_conflicting_inputs':missing,**kwargs}
        self.report['unresolved'].append(item)
    def bind(self,mention,candidates,selected,spans,rule,reason=None):
        self.report['bindings'].append({'mention_span':spans[0],'mention':mention,'candidates':[{'id':v,'accepted':v==selected,'rejection_reason':None if v==selected else (reason or 'incompatible identity, scope or operation port')} for v in candidates], 'selected':selected,'unresolved_reason':reason if selected is None else None,'supporting_spans':sum([self.values[v]['source_spans'] for v in candidates if v in self.values],[]),'rule_id':rule})
    def alias(self,vid,label,spans,rule='R05'):
        source=self.values[vid]
        result=self.value('alias',{'value':vid},spans,rule,{'label':label}, {'labels':[label],'role':source['role'],'unit':source['unit'],'scale':source['scale'],'origin_producer':source.get('origin_producer',source['producer']),'origin_port':source.get('origin_port',source['output_port'])})
        for key in ('epoch_kind','epoch_proof','epoch','time_frame','rate_denominator','rate_target','rate_evidence'):
            if key in source:self.values[result][key]=source[key]
        self.active[label]=result;self.focus=result
        return result
