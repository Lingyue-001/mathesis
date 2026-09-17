"""Additional typed operations for the shared executor; no source interpretation."""
from fractions import Fraction
from .control_ir import rational,boundary_membership

def packed(x):return {'numerator':x.numerator,'denominator':x.denominator}
def method_body(body,returns,actuals,trace=None):
    local={'$'+k:v for k,v in actuals.items()}
    for node in body:
        r={k:local[v] for k,v in node['reads'].items()}
        out=operation(node['kind'],r,node.get('attributes',{}))
        if trace is not None:trace.append({'body_event_id':node.get('id'),'kind':node['kind'],'reads':r,'writes':dict(out),'value_bindings':dict(node['writes'])})
        for port,vid in node['writes'].items():local[vid]=out[port]
    return {port:local[vid] for port,vid in returns.items()}

def operation(kind,r,a):
    if kind in ('literal','parameter'):return {'result':a['value']}
    if kind in ('load','alias'):return {'result':r['value']}
    if kind=='multiply':return {'result':r['left']*r['right']}
    if kind=='add':return {'result':r['left']+r['right']}
    if kind=='subtract':return {'result':r['left']-r['right']}
    if kind in ('divmod','cycle_reduce'):
        if r['divisor']<=0:raise ValueError('divisor must be positive')
        if a.get('integer_nonnegative') and r['dividend']<0:raise ValueError('counted amount must be nonnegative')
        q,rem=divmod(r['dividend'],r['divisor']);return {'quotient':q,'remainder':rem}
    if kind=='count':
        origin=r.get('origin',a.get('ordinal_origin',1));value=origin+r['offset']
        if a.get('cyclic'):value=1+((origin-1+r['offset'])%r['cycle'])
        out={'result':value}
        if 'civil_origin' in a:out['civil_month_number']=1+((a['civil_origin']-1+r['offset'])%a['civil_cycle'])
        return out
    if kind=='year_scan':
        remaining=r['months'];year=1;steps=[];schedule=a['cumulative_schedule'];last_count=0;leaps=set()
        for row in schedule:
            delta=row['cumulative_intercalations']-last_count
            if delta not in (0,1):raise ValueError('cumulative schedule does not identify each leap occurrence')
            if delta:leaps.add(row['year'])
            last_count=row['cumulative_intercalations']
        last_year=max(row['year'] for row in schedule)
        while True:
            if year>last_year:raise ValueError('scan exceeds declared schedule')
            length=a['intercalary_year_months'] if year in leaps else a['ordinary_year_months']
            if length is None:raise ValueError('intercalary branch length is not supplied by text')
            if remaining<length:break
            remaining-=length;steps.append({'year':year,'months_removed':length,'remaining':remaining});year+=1
        return {'years':year-1,'remainder':remaining,'months_removed':r['months']-remaining,'_trace':steps}
    if kind=='framed_origin':
        if not isinstance(r['epoch'],dict):raise ValueError('origin requires epoch frame')
        return {'result':r['head']}
    if kind=='initial_instant':
        if r['ordinal']!=0:raise ValueError('initial midnight profile requires zero elapsed Rule ordinal')
        if not isinstance(r['epoch'],dict) or r['denominator']<=0:raise ValueError('invalid initial instant frame')
        return {'day_offset':r['head']-1,'fraction':0}
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
