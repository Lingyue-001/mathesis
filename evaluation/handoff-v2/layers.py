"""Read-only reference-annotated assertion scoring.

assess_layers(report, reference, step_results) consumes an ordinary AnalysisReport,
a BEFORE-output prepared reference in the existing quantity/node/source-span schema,
and assess_steps' result. It never repairs reports or derives expected units from
observed output. TP/FN units are prepared quantity roles, node-input/node-output
relations, cross-document subsets, condition nodes, call nodes, and whole windows.
Unsupported emitted semantic edges/ports/events are FP. Internal aliases, loads,
query snapshots and expanded query arithmetic are explicit supported decompositions.
The denominator is NOT every token mention: all-token annotation is unavailable.
"""
from collections import Counter
from graph_checks import Graph, compact, span_audit
from semantic_checks import validate_threshold, validate_method, validate_count, DIRECTIONAL_INPUT_PORTS

PORTS = {
    'multiply': ({'left','right'},{'result'}), 'add': ({'left','right'},{'result'}),
    'subtract': ({'left','right'},{'result'}), 'alias': ({'value'},{'result'}),
    'load': ({'value'},{'result'}), 'divmod': ({'dividend','divisor'},{'quotient','remainder'}),
    'cycle_reduce': ({'dividend','divisor'},{'quotient','remainder'}),
    'threshold': ({'value','lower','upper'},{'result'}),
    'count': ({'offset','origin','cycle'},{'result','civil_month_number'}),
    'method_call': ({'offset','origin','cycle'},{'result','remainder'}),
    'interval_scale': ({'value','factor'},{'result'}),
    'year_scan': ({'months'},{'years','remainder','months_removed'}),
    'external_constraint_call': ({'nominal_month','candidate','boundary_data'},{'result'}),
}


def metric(tp, fp, fn, **extra):
    return {'status':'scored','TP':tp,'FP':fp,'FN':fn,
            'precision':tp/(tp+fp) if tp+fp else None,
            'recall':tp/(tp+fn) if tp+fn else None, **extra}


def assess_layers(report, reference, step_results):
    g=Graph(report); mapping=step_results['quantity_mapping']
    nodes={n['node_id']:n for n in reference['nodes']}
    rows={r['reference_node']:r for r in step_results['rows']}
    producer={q:n for n in reference['nodes'] for q in n['outputs']}
    quantities={q['quantity_id']:q for q in reference['quantities']}
    extras=[]; bindings=[]; quantities_rows=[]; cross=[]
    matched={e for row in rows.values() for e in row['event_ids']}
    supported=set(matched)

    def same(q,v):
        if not isinstance(v,str) or v not in g.values:return False
        if q.startswith('lit:'):
            return g.scalar(v)==int(q[4:])
        return isinstance(mapping.get(q),str) and g.same(mapping[q],v)

    def anchored(event,node):
        return any(s['doc_id']==a['passage_id'] and
                   (compact(s['quote']) in compact(a['quote']) or compact(a['quote']) in compact(s['quote']))
                   for s in event['source_spans'] for a in node['source_spans'])

    def logical_role(qid,seen=None):
        seen=set() if seen is None else seen
        if qid in seen:return set()
        seen.add(qid);q=quantities[qid];n=producer.get(qid)
        if n is None:
            return {'parameter','parameter_missing'} if 'parameter' in q['role'] else {'external_input','missing_upstream'}
        action=n['action'];index=n['outputs'].index(qid)
        if action in ('name_result','name_remainder','delayed_remainder_name'):
            return logical_role(n['inputs'][0],seen)
        if action=='count_full_units':return {'quotient'} if index==0 else {'remainder'}
        if action=='reduce_cycle':return {'cycle_count'} if index==0 else {'remainder'}
        if action=='reuse_count_reduce':return {'remainder'} if index==0 else {'day_index'}
        if action=='dual_count_origin':return {'medial_ordinal'} if index==0 else {'station_ordinal'}
        if action=='cyclic_count':return {'day_index'}
        if action=='count_month_ordinal':return {'month_ordinal'}
        if action in ('threshold_predicate','bounded_predicate'):return {'predicate','intercalary_candidate'}
        if action=='external_constraint_call':return {'final_month_status'}
        if action=='scan_years_with_branch':return {'elapsed_years'} if index==0 else {'remainder'}
        if action in ('paired_increment','double_interval_from_base') and len(n['outputs'])==3:
            return {'day_index'} if index==2 else {'remainder'}
        if action=='read_intercalation_schedule':return {'schedule'}
        return {'result'}

    for qid,q in quantities.items():
        actual=mapping.get(qid);n=producer.get(qid)
        ok=isinstance(actual,dict) and 'schedule' in actual or isinstance(actual,str) and actual in g.values and g.values[actual]['role'] in logical_role(qid)
        if n:
            ok=ok and rows[n['node_id']]['status']=='pass'
            if n['action'] in ('name_result','name_remainder','delayed_remainder_name','multiply_and_name') and q.get('source_label'):
                ok=ok and isinstance(actual,str) and any(q['source_label'] in v.get('labels',[]) and g.same(v['id'],actual) for v in g.values.values())
        quantities_rows.append({'quantity':qid,'reference_role':q['role'],'expected_public_roles':sorted(logical_role(qid)),
                                'value_id':actual,'prediction_present':isinstance(actual,str) or bool(n and rows[n['node_id']]['event_ids']), 'status':'pass' if ok else 'fail'})

    for nid,node in nodes.items():
        row=rows[nid];events=[g.events[e] for e in row['event_ids'] if e in g.events]
        compound=node['action'] in ('paired_increment','double_interval_from_base') and len(node['outputs'])==3
        # Source-required expansion: two component additions, one carry receiver,
        # one fraction division, one method call; full interval scales both components.
        if compound:
            limits={'add':3,'divmod':1,'method_call':1,'alias':5,'query':1,
                    'interval_scale':2 if node['action']=='double_interval_from_base' else 0}
            seen=Counter()
            for e in events:
                if e['kind']=='literal':continue
                seen[e['kind']]+=1
                if seen[e['kind']]>limits.get(e['kind'],0):
                    extras.append({'event':e['id'],'reason':'unsupported compound semantic event'})
        elif node['action']!='read_intercalation_schedule' and len(events)>(2 if node['action'] in ('paired_increment','dual_count_origin') else 1):
            limit=2 if node['action'] in ('paired_increment','dual_count_origin') else 1
            extras.extend({'event':e['id'],'reason':'duplicate semantic assertion'} for e in events[limit:])
        reads=[v for e in events if e['kind']!='query' for v in e['reads'].values()]
        directional=DIRECTIONAL_INPUT_PORTS.get(node['action'],())
        for index,qid in enumerate(node['inputs']):
            if qid=='intercalation.schedule':
                ok=any(e['attributes'].get('cumulative_schedule')==mapping.get(qid,{}).get('schedule') for e in events)
            elif node['action']=='scan_years_with_branch' and qid in ('lit:12','lit:13'):
                field='ordinary_year_months' if qid=='lit:12' else 'intercalary_year_months'
                ok=any(e['attributes'].get(field)==int(qid[4:]) for e in events)
            elif index<len(directional) and directional[index] is not None:
                ok=any(same(qid,e['reads'].get(directional[index])) for e in events)
            else:ok=any(same(qid,v) for v in reads)
            expected_port=directional[index] if index<len(directional) else None
            b={'node':nid,'direction':'input','quantity':qid,'expected_consumer_port':expected_port,
               'actual_consumers':[{'event':e['id'],'port':port,'value':v} for e in events for port,v in e['reads'].items() if same(qid,v)],
               'status':'pass' if ok else 'fail'}
            bindings.append(b)
            pn=producer.get(qid)
            if pn and {s['passage_id'] for s in pn['source_spans']}.isdisjoint({s['passage_id'] for s in node['source_spans']}):cross.append(b)
        for index,qid in enumerate(node['outputs']):
            actual=row['output_value_ids'][index] if index<len(row['output_value_ids']) else None
            ok=isinstance(actual,str) and actual in g.values and any(actual in e['writes'].values() for e in events)
            if compound and isinstance(actual,str):ok=actual in g.values and g.values[actual]['producer'] in row['event_ids']
            if node['action']=='read_intercalation_schedule':ok=row['status']=='pass'
            if ok and isinstance(actual,str):
                v=g.values[actual];ok=g.events[v['producer']]['writes'].get(v['output_port'])==actual and v['role'] in logical_role(qid)
            bindings.append({'node':nid,'direction':'output','quantity':qid,'status':'pass' if ok else 'fail'})
        for e in events:
            if e['kind'] in ('literal','query','schedule'):continue
            for port,v in e['reads'].items():
                internal=compound and v in g.values and g.values[v]['producer'] in row['event_ids']
                permitted=any(same(q,v) and (not directional or i>=len(directional) or directional[i]==port)
                              for i,q in enumerate(node['inputs'])) or internal
                if e['kind'] in ('count','method_call') and port=='cycle':
                    try:
                        (validate_count if e['kind']=='count' else validate_method)(g,e)
                        permitted=True
                    except (AssertionError,KeyError,TypeError):permitted=False
                if node['action']=='read_intercalation_schedule':permitted=True
                if not permitted:
                    extras.append({'event':e['id'],'read_port':port,'value':v,'reason':'unsupported reference binding'})

    # Transparent aliases are allowed only when they preserve an annotated endpoint
    # and carry a label present in source, or a declared reference quantity label.
    ref_labels={q.get('source_label') for q in quantities.values() if q.get('source_label')}
    for e in g.events.values():
        if e['kind'] in ('alias','load') and e['id'] not in supported:
            values=list(e['writes'].values());labels=[l for v in values for l in g.values.get(v,{}).get('labels',[])]
            source=''.join(s['quote'] for s in e['source_spans'])
            if len(e['reads'])==1 and all(any(same(q,v) for q in mapping if isinstance(mapping[q],str)) for v in values) and all(l in source or l in ref_labels for l in labels):
                supported.add(e['id'])
        if e['kind'] in ('literal','parameter','input','query','schedule'):
            # Declarations and discourse/query snapshots are not operation assertions.
            # Validate their output contract; unused contextual declarations are outside
            # the prepared primary-procedure denominator.
            allowed=set() if e['kind'] in ('query','schedule') else {'result'}
            for port in set(e['writes'])-allowed:extras.append({'event':e['id'],'write_port':port,'reason':'unsupported declaration output'})
            continue
        if e['id'] not in supported:
            extras.append({'event':e['id'],'reason':'unsupported semantic event'})
        allowed_reads,allowed_writes=PORTS.get(e['kind'],(set(),set()))
        for port in set(e['reads'])-allowed_reads:extras.append({'event':e['id'],'read_port':port,'reason':'unsupported input port'})
        for port in set(e['writes'])-allowed_writes:extras.append({'event':e['id'],'write_port':port,'reason':'unsupported output port'})
        for port,vid in e['writes'].items():
            v=g.values.get(vid,{})
            if v.get('producer')!=e['id'] or v.get('output_port')!=port:
                extras.append({'event':e['id'],'write_port':port,'reason':'inconsistent producer/port'})
    # A schedule can decompose into one event per explicit cumulative source clause.
    seen_schedule=set()
    for e in g.events.values():
        if e['kind']=='schedule' and e['id'] in matched:
            anchor=tuple((s['doc_id'],s['start'],s['end']) for s in e['source_spans'])
            if anchor in seen_schedule:extras.append({'event':e['id'],'reason':'duplicate schedule assertion'})
            seen_schedule.add(anchor)
    # A relation must be counted once even if it violates more than one rule.
    unique={ (x['event'],x.get('read_port'),x.get('write_port')):x for x in extras }
    extras=list(unique.values())
    cross_extras=[x for x in extras if x.get('value') in g.values and
                  {s['doc_id'] for s in g.producer(x['value'])['source_spans']}.isdisjoint({s['doc_id'] for s in g.events[x['event']]['source_spans']})]
    condition_rows=[r for r in rows.values() if r['action'] in ('threshold_predicate','bounded_predicate','scan_years_with_branch')]
    call_rows=[r for r in rows.values() if r['action'] in ('reuse_count_reduce','external_constraint_call')]
    # Inferred calls in compound query nodes are scored within those reference units.
    call_rows += [r for r in rows.values() if r['action'] in ('paired_increment','double_interval_from_base') and len(nodes[r['reference_node']]['outputs'])==3]
    def score(items,fp=0, semantic=False):
        if semantic:fp+=sum(x['status']!='pass' and bool(x.get('event_ids') or x.get('prediction_present')) for x in items)
        tp=sum(x['status']=='pass' for x in items);return metric(tp,fp,len(items)-tp)
    layers={'quantity_mention_roles':score(quantities_rows, sum('write_port' in x or x.get('reason')=='unsupported semantic event' for x in extras), semantic=True),
            'producer_port_relations':score(bindings,len(extras)), 'cross_document_relations':score(cross,len(cross_extras)),
            'condition_scope':score(condition_rows,sum(g.events[x['event']]['kind'] in ('threshold','year_scan') for x in extras), semantic=True),
            'method_external_calls':score(call_rows,sum(g.events[x['event']]['kind'] in ('method_call','external_constraint_call') for x in extras), semantic=True)}
    faults=[u for u in report['unresolved'] if u['cause']!='requires_external_data']
    full=all(r['status']=='pass' for r in rows.values()) and all(v['FP']==v['FN']==0 for v in layers.values()) and not (faults or report['coverage']['unparsed_spans'] or report['diagnostics'] or span_audit(report))
    layers['full_structure']=metric(int(full),int(not full and bool(report['events'])),int(not full))
    layers['all_token_mentions']={'status':'not_scored','TP':None,'FP':None,'FN':None,'precision':None,'recall':None,
                                  'missing_annotation':'Exhaustive token mention spans/roles are absent; reference quantities are not all-token gold.'}
    return {'window':reference['window_id'],'layers':layers,'full_chain_passed':full,'unsupported_relations':extras,
            'quantity_assertions':quantities_rows,'binding_assertions':bindings,'cross_document_assertions':cross,
            'coverage_boundary':'Prepared primary-procedure quantities/relations only; roles normalized through reference producer/action/port. Unused contextual declarations and all-token recall excluded.',
            'supported_decompositions':['transparent source-labeled aliases/loads','query snapshots','compound carry and method-call expansions'],
            'unresolved_parser':faults}


def macro_layers(windows):
    names={name for w in windows for name in w['layers']}
    out={}
    for name in sorted(names):
        rows=[w['layers'][name] for w in windows if w['layers'].get(name,{}).get('status')=='scored']
        out[name]={'scored_windows':len(rows),'precision':None,'recall':None}
        for field in ('precision','recall'):
            values=[r[field] for r in rows if r[field] is not None]
            out[name][field]=sum(values)/len(values) if values else None
        for field in ('TP','FP','FN'):out[name][field]=sum(r[field] for r in rows) if rows else None
    return out
