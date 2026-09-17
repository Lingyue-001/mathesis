"""Source-derived semantic invariants, independent of event allocation IDs."""
from graph_checks import compact


def validate_threshold(g, event):
    a=event['attributes']
    assert a.get('scope_end') == 'judgment', 'threshold scope must end at its judgment'
    assert a.get('lower_inclusive') is True and a.get('upper_inclusive') is True
    judgment=a.get('judgment')
    assert judgment and any(judgment in s['quote'] for s in event['source_spans']), 'judgment must be source anchored'
    predicate=g.output(event)
    assert not any(predicate in x['reads'].values() or x.get('guard')==predicate or x['attributes'].get('guard')==predicate
                   for x in g.events.values() if x['id']!=event['id'] and x['kind']!='external_constraint_call'), 'judgment cannot guard subsequent computation'


def validate_count(g, event):
    a=event['attributes'];quote=''.join(s['quote'] for s in event['source_spans'])
    origins={'統首日':('day_index','算外',60), '所入蔀名':('day_index','筭盡之外',60),
             '冬至':('medial_ordinal','算外',12), '星紀':('station_ordinal','算外',12),
             '天正十一月':('month_ordinal','筭外',None), '天正':('month_ordinal','算外',None)}
    origin=next((s for s in origins if s in quote),None)
    assert origin is not None, 'count origin lacks supported source semantics'
    role, convention, cycle=origins[origin]
    assert a.get('origin_label')==origin and a.get('output_role')==role
    assert a.get('convention')==convention and a.get('zero_offset_at_origin') is True
    assert type(a.get('ordinal_origin')) is int and a['ordinal_origin']==1
    assert a.get('cyclic') is (cycle is not None)
    if cycle:
        assert g.scalar(event['reads']['cycle'])==cycle, 'count cycle differs from source'
    if role=='day_index':
        assert origin in g.values[event['reads']['origin']]['labels']
        assert g.producer(event['reads']['origin'])['kind']=='input'
    if origin=='天正十一月':
        assert a.get('civil_origin')==11 and a.get('civil_cycle')==12
    assert g.values[g.output(event)].get('role')==role


def validate_method(g, event):
    a=event['attributes'];target=g.events.get(a.get('target'))
    assert target and target['kind']=='count', 'method target must be a declared count/reduce method'
    declarations=[m for m in g.report.get('methods',[]) if m.get('event_id')==target['id']]
    assert len(declarations)==1, 'target lacks unique method declaration'
    declaration=declarations[0]
    validate_count(g,target)
    assert target['scope']['query']=='main' and event['scope']['query']!='main'
    assert target['text_order']<event['text_order'], 'method must be earlier than invocation'
    assert a.get('method')=='cycle_and_count'
    assert a.get('convention')==target['attributes']['convention']==declaration.get('convention')
    assert declaration.get('origin_label')==target['attributes']['origin_label']
    for port in ('origin','cycle'):
        assert g.same(event['reads'].get(port),target['reads'].get(port)), f'call {port} differs from target'
        assert g.same(declaration.get(port),target['reads'][port]), f'method declaration {port} differs from target'
    reduction=g.producer(target['reads']['offset'])
    assert reduction['kind']=='cycle_reduce' and g.same(reduction['reads']['divisor'],target['reads']['cycle'])
    assert g.values[g.unwrap(target['reads']['offset'])]['output_port']=='remainder'
    updated=g.producer(event['reads']['offset'])
    assert updated['kind']=='add' and updated['scope']['query']==event['scope']['query'], 'call must read updated query state'
    assert set(event['writes'])=={'result','remainder'}


def validate_dual(g, events):
    assert len(events)==2
    for e in events: validate_count(g,e)
    assert {e['attributes']['origin_label'] for e in events}=={'冬至','星紀'}
    assert {e['attributes']['output_role'] for e in events}=={'medial_ordinal','station_ordinal'}
    assert g.same(events[0]['reads']['offset'],events[1]['reads']['offset'])
    assert g.same(events[0]['reads']['cycle'],events[1]['reads']['cycle'])
    assert not g.same(g.output(events[0]),g.output(events[1]))


def validate_year_scan(g, event):
    """The source's residual-month scan starts at chapter year one.

    Parse only the comparison syntax, never eval it. Operand reversal with the
    equivalent operator and whitespace changes are normalized representations.
    Schedule expectations come from source documents, not other emitted events.
    """
    import ast
    import re
    a=event['attributes']
    try:
        predicate=ast.parse(a.get('stop_condition','').strip(),mode='eval').body
    except (SyntaxError,AttributeError,TypeError):
        raise AssertionError('invalid year-scan stopping predicate')
    assert isinstance(predicate,ast.Compare) and len(predicate.ops)==len(predicate.comparators)==1, 'scan requires one stopping comparison'
    left,right=predicate.left,predicate.comparators[0]
    assert isinstance(left,ast.Name) and isinstance(right,ast.Name), 'scan predicate requires residual and current-year-length operands'
    normal=isinstance(predicate.ops[0],ast.Lt) and (left.id,right.id)==('remaining_months','months_in_current_year')
    reversed_equivalent=isinstance(predicate.ops[0],ast.Gt) and (left.id,right.id)==('months_in_current_year','remaining_months')
    assert normal or reversed_equivalent, 'scan must stop when residual months are less than current branch year length'
    assert type(a.get('start_year')) is int and a['start_year']==1, 'chapter scan must begin at year one'
    assert set(a.get('branches',[]))=={'ordinary','intercalary'} and len(a['branches'])==2
    assert type(a.get('ordinary_year_months')) is int and a['ordinary_year_months']==12
    assert type(a.get('intercalary_year_months')) is int and a['intercalary_year_months']==13
    assert set(event['reads'])=={'months'} and set(event['writes'])=={'years','remainder','months_removed'}
    assert g.values[event['reads']['months']]['scope']==event['scope'], 'year scan must use its source/query month state'
    doc_ids={s['doc_id'] for s in event['source_spans']}
    source=''.join(d['text'] for d in g.report['documents'] if d['doc_id'] in doc_ids)
    assert '入章' in source and '以十二除之' in source and '除十三' in source, 'chapter and branch source evidence absent'
    digits={c:i for i,c in enumerate('零一二三四五六七八九')}
    def number(text):
        if '十' in text:
            left,right=text.split('十')
            return (digits[left] if left else 1)*10+(digits[right] if right else 0)
        return digits[text]
    expected=[{'year':number(y),'cumulative_intercalations':number(n)}
              for y,n in re.findall(r'([一二三四五六七八九十]+)歲([一二三四五六七八九十]+)閏',source)]
    assert expected and a.get('cumulative_schedule')==expected, 'branch schedule must agree with source cumulative intercalations'
    prior=0
    for row in expected:
        assert row['cumulative_intercalations']-prior==1
        prior=row['cumulative_intercalations']


def validate_external_call(g, event):
    """Validate the explicitly unresolved conjunction-based boundary interface."""
    a=event['attributes'];source=''.join(s['quote'] for s in event['source_spans'])
    assert '以朔制之' in source and '進退' in source, 'conjunction/advance-retreat source evidence absent'
    assert a.get('method')=='constrain_by_conjunction', 'external call must constrain by conjunction'
    assert set(a.get('missing_data',[]))=={'adjacent_conjunction_events','medial_qi_events'} and len(a['missing_data'])==2, 'both external boundary-event categories are required'
    assert set(a.get('allowed_adjustments',[]))=={'advance','retreat'} and len(a['allowed_adjustments'])==2, 'both adjustment alternatives are required'
    assert set(event['reads'])=={'nominal_month','candidate','boundary_data'} and set(event['writes'])=={'result'}
    for port,role in [('nominal_month','month_ordinal'),('candidate','intercalary_candidate'),('boundary_data','missing_upstream')]:
        value=g.values[event['reads'][port]]
        assert value['role']==role and value['scope']==event['scope'], f'wrong {port} role or scope'
    boundary=g.producer(event['reads']['boundary_data'])
    assert boundary['kind']=='input' and boundary['attributes'].get('name')=='boundary_data'
    assert g.values[g.output(event)]['role']=='final_month_status'
    anchor={(s['doc_id'],s['start'],s['end']) for s in event['source_spans']}
    unresolved=[u for u in g.report['unresolved'] if
                any((s['doc_id'],s['start'],s['end']) in anchor for s in u['source_spans'])]
    assert len(unresolved)==1, 'external call requires one unique source-anchored unresolved record'
    unresolved=unresolved[0]
    assert unresolved['cause']=='requires_external_data', 'external call unresolved cause must require external data'
    missing=unresolved.get('missing_or_conflicting_inputs',[])
    assert set(missing)=={'boundary_data'} and len(missing)==1, 'unresolved inputs must exactly match the boundary interface'


# Prepared-reference input order determines directional destination ports.
# Commutative arithmetic deliberately has no positional restriction.
DIRECTIONAL_INPUT_PORTS = {
    'subtract': ('left','right'), 'set_then_subtract': ('left','right'),
    'count_full_units': ('dividend','divisor'), 'reduce_cycle': ('dividend','divisor'),
    'threshold_predicate': ('value','lower'), 'bounded_predicate': ('value','lower','upper'),
    'reuse_count_reduce': ('offset','origin','cycle'),
    'external_constraint_call': ('nominal_month','candidate','boundary_data'),
    'cyclic_count': ('origin','offset'), 'count_month_ordinal': ('offset',),
    'scan_years_with_branch': ('months',None,None,None),
    'name_result': ('value',), 'name_remainder': ('value',),
    'delayed_remainder_name': ('value',), 'import_named_quantity': ('value',),
}
