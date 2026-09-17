"""Numeric projection of parsed generic event graphs, with no source interpretation."""

from .audit import required_reads, temporal_error
from .operations import operation, method_body

def execute(report, inputs, parameter_bindings=None):
    parameter_bindings=parameter_bindings or {}
    values={};results={};unresolved=[];trace=[];explicit_bindings=[]
    value_metadata={v['id']:v for v in report['value_instances']};event_metadata={e['id']:e for e in report['events']}
    for event in report['events']:
        kind=event['kind'];a=event.get('attributes',{});writes=event['writes'];eid=event['id']
        frame_error=temporal_error(event,value_metadata,event_metadata)
        if frame_error:
            unresolved.append({'event_id':eid,'cause':'invalid_time_frame','reason':frame_error});continue
        missing_roles=required_reads(event)-set(event['reads'])
        if missing_roles:
            unresolved.append({'event_id':eid,'cause':'invalid_event_contract','missing_read_ports':sorted(missing_roles)})
            continue
        if a.get('execution_blocked'):
            unresolved.append({'event_id':eid,'cause':'unresolved_parser','reason':a['execution_blocked']})
            continue
        missing=[v for v in event['reads'].values() if v not in values]
        if kind in ('query','schedule'):
            results[eid]={};continue
        if missing and kind not in ('external_constraint_call','boundary_call'):
            unresolved.append({'event_id':eid,'cause':'unavailable_dependency','value_ids':missing});continue
        r={k:values.get(v) for k,v in event['reads'].items()}
        output={}
        try:
            if kind in ('literal','parameter'):output={'result':a['value']}
            elif kind=='input':
                source=parameter_bindings if a.get('parameter') else inputs
                if a['name'] not in source:
                    unresolved.append({'event_id':eid,'cause':'requires_explicit_input','name':a['name']});continue
                output={'result':source[a['name']]}
                explicit_bindings.append({'event_id':eid,'name':a['name'],'value':source[a['name']],'status':'supplied','source':'parameter_bindings' if a.get('parameter') else 'inputs'})
            elif kind in ('alias','load'):output={'result':r['value']}
            elif kind=='multiply':output={'result':r['left']*r['right']}
            elif kind=='subtract':output={'result':r['left']-r['right']}
            elif kind=='add':output={'result':r['left']+r['right']}
            elif kind in ('divmod','cycle_reduce'):
                if r['divisor']<=0:raise ValueError('divisor must be positive')
                if a.get('integer_nonnegative') and r['dividend']<0:raise ValueError('counted amount must be nonnegative')
                q,rem=divmod(r['dividend'],r['divisor']);output={'quotient':q,'remainder':rem}
            elif kind=='threshold':output={'result':r['value']>=r['lower'] and ('upper' not in r or r['value']<=r['upper'])}
            elif kind=='count':
                origin=r.get('origin',a.get('ordinal_origin',1))
                result=origin+r['offset']
                if a.get('cyclic'):
                    result=1+((origin-1+r['offset'])%r['cycle'])
                output={'result':result}
                if 'civil_origin' in a:output['civil_month_number']=1+((a['civil_origin']-1+r['offset'])%a['civil_cycle'])
            elif kind=='method_call':
                typed_call=(str(report.get('schema_version','')).startswith('3.') or report.get('adapter')=='typed_scoped_v3' or 'method_binding' in event or 'body' in a)
                if typed_call:
                    if not a.get('body'):raise ValueError('missing v3 method body')
                    definitions=[m for m in report.get('method_library',[]) if m['id']==a.get('target')]
                    if len(definitions)!=1 or not definitions[0].get('body') or definitions[0]['body']!=a['body']:raise ValueError('missing or mismatched method body')
                    if event.get('method_binding',{}).get('definition_id')!=a.get('target') or a.get('formal_returns')!=definitions[0].get('returns'):raise ValueError('incompatible v3 method binding')
                    output=method_body(a['body'],a['formal_returns'],r)
                else:
                    if event.get('rule_id')!='R12':raise ValueError('method call lacks explicit legacy contract')
                    rem=r['offset']%r['cycle'];output={'remainder':rem,'result':1+((r['origin']-1+rem)%r['cycle'])}
            elif kind=='interval_scale':output={'result':r['value']*r['factor']}
            elif kind=='year_scan':
                remaining=r['months'];year=1;steps=[]
                schedule=a['cumulative_schedule'];last_count=0;leaps=set()
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
                output={'years':year-1,'remainder':remaining,'months_removed':r['months']-remaining}
                trace.append({'event_id':eid,'steps':steps,'stopped_at_year':year,'stop_test':{'remaining':remaining,'next_year_months':length}})
            elif kind in ('select','lookup','rescale','fraction','convert','repeat','cycle_lift','epoch_frame','event_sequence','boundary_call'):
                output=operation(kind,r,a)
                if '_trace' in output:trace.append({'event_id':eid,'steps':output.pop('_trace')})
                if kind=='boundary_call' and output['result']['status']=='requires_external_data':unresolved.append({'event_id':eid,'cause':'requires_external_data','details':output['result']})
            elif kind=='external_constraint_call':
                output={'result':'requires_external_data'}
                unresolved.append({'event_id':eid,'cause':'requires_external_data','missing':a.get('missing_data',[])})
            else:
                unresolved.append({'event_id':eid,'cause':'unsupported_event_kind','kind':kind});continue
        except KeyError as error:
            unresolved.append({'event_id':eid,'cause':'invalid_event_contract','message':str(error)});continue
        except (ValueError,TypeError,ZeroDivisionError) as error:
            unresolved.append({'event_id':eid,'cause':'execution_error','message':str(error)});continue
        results[eid]=output
        trace.append({'event_id':eid,'kind':kind,'reads':r,'writes':dict(output)})
        for port,val in output.items():
            if port in writes:values[writes[port]]=val
    named={}
    for val in report['value_instances']:
        if val['id'] not in values or val['role'] in ('parameter','literal','external_input','parameter_missing'):continue
        for label in val.get('labels',[]):named[val['scope'].get('query','main')+':'+label]=values[val['id']]
    task_outputs={task:{port:values[vid] for port,vid in ports.items() if vid in values} for task,ports in report.get('task_exports',{}).items()}
    return {'task_outputs':task_outputs,'values':values,'named_outputs':named,'event_results':results,'unresolved':unresolved,'execution_trace':trace,'explicit_bindings':explicit_bindings}
