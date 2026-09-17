"""Additional typed operations for the shared executor; no source interpretation."""
from fractions import Fraction
from .control_ir import rational,boundary_membership

def packed(x):return {'numerator':x.numerator,'denominator':x.denominator}
def method_body(body,returns,actuals):
    local={'$'+k:v for k,v in actuals.items()}
    for node in body:
        r={k:local[v] for k,v in node['reads'].items()}
        if node['kind']=='cycle_reduce':
            q,rem=divmod(r['dividend'],r['divisor']);out={'quotient':q,'remainder':rem}
        elif node['kind']=='count':out={'result':1+((r['origin']-1+r['offset'])%r['cycle'])}
        else:raise ValueError('unsupported method body operation '+node['kind'])
        for port,vid in node['writes'].items():local[vid]=out[port]
    return {port:local[vid] for port,vid in returns.items()}

def operation(kind,r,a):
    if kind=='select':
        candidates=[c for c in a['choices'] if 0<=r[c['local_port']]<r['divisor']]
        if len(candidates)!=1:raise ValueError('conditional branches do not select exactly one case')
        c=candidates[0];return {'index':c['index'],'local':r[c['local_port']],'head':r[c['head_port']]}
    if kind=='lookup':
        row=r['row']-a.get('row_base',0);column=r['column']-a.get('column_base',0);rows=a['table']['rows']
        if not 0<=row<len(rows) or not 0<=column<a['day_column']:raise ValueError('table index out of range')
        return {'head_day':rows[row]['numeric'][a['day_column']],'head_year':rows[row]['numeric'][column]}
    if kind=='epoch_frame':return {'result':{'tradition':a['tradition'],'origin_elapsed_year':r['epoch_elapsed']-r['local_elapsed'],'time_unit':'day','coordinate':'days_from_local_cycle_origin'}}
    if kind=='convert':
        if not a.get('rate',{}).get('basis'):raise ValueError('rate conversion requires declared source evidence')
        amount=Fraction(r['numerator'],r['denominator'])*Fraction(r['rate_numerator'],r['rate_denominator']);numerator=amount*r['output_denominator']
        if numerator.denominator!=1:raise ValueError('declared target scale cannot exactly represent conversion')
        return {'result':{'numerator':numerator.numerator,'denominator':r['output_denominator']}}
    if kind=='rescale':return {'result':r['value']}
    if kind=='fraction':return {'result':{'numerator':r['whole']*r['denominator']+r['numerator'],'denominator':r['denominator']}}
    if kind=='repeat':
        control=a['control'];state=r['initial'];count=control['counter']['initial'];steps=[]
        if control['stop']['operator'] not in ('gt','ge'):raise ValueError('unsupported repeat stop predicate')
        if control['test'] not in ('pre','post'):raise ValueError('unsupported repeat test timing')
        def stop():return state>r['threshold'] if control['stop']['operator']=='gt' else state>=r['threshold']
        if r['increment']<=0:raise ValueError('bounded increasing repeat requires positive update')
        while True:
            if control['test']=='pre' and stop():break
            local={'$state':state,'$counter':count,'$increment':r['increment'],'$counter_increment':control['counter']['increment']}
            for node in control['body']:
                args={k:local[v] for k,v in node['reads'].items()}
                if node['kind']=='add':value=args['left']+args['right']
                elif node['kind']=='subtract':value=args['left']-args['right']
                elif node['kind']=='multiply':value=args['left']*args['right']
                else:raise ValueError('unsupported repeat body operation')
                local[node['writes']['result']]=value
            state=local['state'];count=local['counter'];steps.append({'state':state,'counter':count})
            if stop():break
            if len(steps)>=a.get('max_iterations',10000):raise ValueError('repeat iteration bound exceeded')
        return {'state':state,'count':count,'_trace':steps}
    if kind=='cycle_lift':return {'result':r['whole']+r['elapsed_years']*r['factor']}
    if kind=='event_sequence':
        base=Fraction(r['whole'])+Fraction(r['numerator'],r['denominator']);step=(Fraction(r['increment_whole'])+Fraction(r['increment_numerator'],r['increment_denominator']))*a['stride']
        return {'result':{'events':[packed(base+i*step) for i in range(a['count'])],'epoch':r['epoch'],'time_frame':a['time_frame'],'role':a['sequence_role']}}
    if kind=='boundary_call':
        if r.get('has_intercalation') is False:return {'result':{'status':'no_intercalation'}}
        moons=r.get('moon_events');qi=r.get('qi_events')
        if not moons or not qi or not a.get('profile'):return {'result':{'status':'requires_external_data','missing':['event_sequences_or_boundary_profile']}}
        if moons.get('epoch')!=qi.get('epoch') or not moons.get('epoch') or moons.get('time_frame')!='full_local_epoch' or qi.get('time_frame')!='full_local_epoch':return {'result':{'status':'requires_external_data','reason':'incompatible time frames'}}
        def incomplete(reason):return {'result':{'status':'requires_external_data','reason':reason}}
        if len(moons.get('events',[]))<2 or not qi.get('events'):return incomplete('missing moon intervals or qi event data')
        try:
            moon_times=[rational(x) for x in moons['events']];qi_times=[rational(x) for x in qi['events']]
        except (KeyError,TypeError,ValueError,ZeroDivisionError):return incomplete('invalid rational event data')
        if any(b<=c for c,b in zip(moon_times,moon_times[1:])) or any(b<=c for c,b in zip(qi_times,qi_times[1:])):return incomplete('invalid event ordering')
        if a['profile'] not in ('instant_lunation','civil_whole_day'):return incomplete('unsupported boundary profile')
        boundaries=[x.numerator//x.denominator for x in moon_times] if a['profile']=='civil_whole_day' else moon_times
        if any(b<=c for c,b in zip(boundaries,boundaries[1:])):return incomplete('invalid month boundary ordering')
        covered=[i for i,(left,right) in enumerate(zip(boundaries,boundaries[1:])) if qi_times[0]<=left and right<=qi_times[-1]]
        if not covered:return incomplete('qi series does not bracket a complete month interval')
        # Extra events outside the bounded moon window establish coverage, not
        # unresolved membership. Every event inside the window must resolve.
        membership=[boundary_membership(moons['events'],q,a['profile'],moons['epoch']) for q in qi_times if boundaries[0]<=q<boundaries[-1]]
        if any(x['status']!='resolved' for x in membership):return incomplete('unresolved membership within the bounded window')
        occupied={x['interval'] for x in membership}
        empty=[i for i in covered if i not in occupied]
        return {'result':{'status':'resolved' if empty else 'no_empty_interval_in_bounded_window','candidate_intervals':empty,'profile':a['profile'],'membership':membership,'historical_status':'bounded_model_comparison'}}
    raise ValueError('unknown typed operation '+kind)
