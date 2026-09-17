"""Checks executable ports, immutable provenance, source anchors, and semantic risks."""

def required_reads(event):
    required={'multiply':{'left','right'},'subtract':{'left','right'},'add':{'left','right'},'divmod':{'dividend','divisor'},'cycle_reduce':{'dividend','divisor'},'alias':{'value'},'load':{'value'},'threshold':{'value','lower'},'count':{'offset'},'year_scan':{'months'},'interval_scale':{'value','factor'},'method_call':{'offset','origin','cycle'}}.get(event['kind'],set())
    if event['kind']=='method_call' and event.get('attributes',{}).get('body'):
        required={v[1:] for node in event['attributes']['body'] for v in node.get('reads',{}).values() if isinstance(v,str) and v.startswith('$')}
    required=required|{'select':{'divisor'},'lookup':{'row','column'},'rescale':{'value','old_denominator','new_denominator','factor'},'fraction':{'whole','numerator','denominator'},'convert':{'numerator','denominator','rate_numerator','rate_denominator','output_denominator'},'epoch_frame':{'epoch_elapsed','local_elapsed'},'repeat':{'initial','increment','threshold'},'cycle_lift':{'whole','elapsed_years','factor'},'event_sequence':{'whole','numerator','denominator','increment_whole','increment_numerator','increment_denominator','epoch'}}.get(event['kind'],set())
    if event['kind']=='initial_instant':required={'head','epoch','ordinal','denominator'}
    if event['kind']=='count' and event.get('attributes',{}).get('cyclic'):
        required=required|{'cycle'}
    return required

def audit(report):
    diagnostics=[];values={v['id']:v for v in report['value_instances']};events={e['id']:e for e in report['events']}
    docs={d['doc_id']:d for d in report.get('documents',[])}
    def add(kind,e,message):
        diagnostics.append({'kind':kind,'event_id':e.get('id'),'message':message,
                            'source_spans':list(e.get('source_spans', [])),
                            'affected_outputs':list(e.get('writes', {}).values())})
    for e in report['events']:
        problem=temporal_error(e,values,events)
        if problem:add('invalid_time_frame',e,problem)
        required=required_reads(e)
        for role in required-set(e['reads']):add('missing_read_port',e,role)
        for role,vid in e['reads'].items():
            if vid not in values:add('dangling_read',e,role+': '+str(vid))
            elif e['kind']!='interval_scale':
                source_query=values[vid]['scope'].get('query','main')
                target_query=e['scope'].get('query','main')
                if source_query not in ('main',target_query):
                    imports=e.get('attributes',{}).get('scope_imports',[])
                    allowed=any(x.get('value_id')==vid and x.get('source_scope')==values[vid]['scope'] and x.get('basis') for x in imports)
                    if not allowed:add('cross_query_dependency',e,role+' reads sibling query '+source_query)
        for port,vid in e['writes'].items():
            if vid not in values or values[vid]['producer']!=e['id'] or values[vid]['output_port']!=port:add('invalid_output_port',e,port+': '+str(vid))
        for s in e['source_spans']:
            if s['doc_id'] not in docs or docs[s['doc_id']]['text'][s['start']:s['end']]!=s['quote']:add('invalid_source_span',e,str(s))
        if not e['source_spans']:add('missing_source',e,'event has no source support')
        if e['kind'] in ('divmod','cycle_reduce') and set(e['writes'])!={'quotient','remainder'}:add('lost_division_port',e,'quotient and remainder must coexist')
        if e['kind']=='alias' and e.get('rule_id')!='V3_DIFFERENCE' and any(s['quote'].startswith(('不盈','不滿','不盡','其餘','餘')) for s in e['source_spans'][:1]):
            value=values.get(e['reads'].get('value'),{})
            if value.get('output_port')!='remainder' and value.get('origin_port')!='remainder':add('remainder_producer_corruption',e,'remainder name binds a non-remainder port')
        if e['kind']=='add' and e.get('attributes',{}).get('receiver_label') in ('積中','積月'):
            left=values.get(e['reads'].get('left'),{})
            if left.get('source_label')!=e['attributes']['receiver_label']:add('full_accumulation_corruption',e,'explicit full accumulation name bound to another projection')
        if e['kind']=='multiply':
            for vid in e['reads'].values():
                v=values.get(vid,{})
                if v.get('role')=='parameter' and events.get(v.get('producer'),{}).get('kind')!='parameter':add('parameter_identity_corruption',e,'parameter no longer has a declaration producer')
    for v in values.values():
        if v['producer'] not in events:diagnostics.append({'kind':'missing_producer','value_id':v['id']})
    return diagnostics


def temporal_error(event, values, events):
    kind=event['kind'];reads=event.get('reads',{})
    if kind=='cycle_lift':
        from .resources import WINTER_LIFT
        factor=events.get(values.get(reads.get('factor'),{}).get('producer'),{}).get('attributes',{}).get('value')
        if factor!=WINTER_LIFT['days_per_elapsed_year'] or event.get('attributes',{}).get('model_rule')!=WINTER_LIFT:return 'invalid winter cycle lift model or factor'
        if values.get(reads.get('whole'),{}).get('time_frame')!='annual_residual':return 'winter lift requires residual input'
    if kind=='event_sequence':
        whole=values.get(reads.get('whole'),{})
        if whole.get('time_frame')!='full_local_epoch':return 'event comparison requires full local epoch coordinate'
        if event.get('attributes',{}).get('sequence_role')=='qi_events' and events.get(whole.get('producer'),{}).get('kind')!='cycle_lift':return 'winter sequence base requires explicit source-calibrated lift'
    return None
