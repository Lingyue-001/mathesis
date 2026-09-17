"""Inspect declared method bodies and their actual execution/port identities.

No source parsing, result synthesis, or golden graph construction occurs here.
Formal names may vary; semantic roles require unique typed, consumed formals.
"""
import importlib.util
import re
from pathlib import Path
_spec=importlib.util.spec_from_file_location('rescue_source_numbers',Path(__file__).with_name('evidence_contracts.py'))
_numbers=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_numbers)

def role_formals(method):
    signature=method.get('formal_inputs',{});body=method.get('body',[])
    result={name:name for name in signature}
    dynamic=[name for name,info in signature.items() if not info.get('source_label')]
    for role,unit,port,kind in [('month_offset','month','dividend','cycle_reduce'),('offset','day','dividend','cycle_reduce'),('head_day','day_index','origin','count')]:
        possible=[name for name in dynamic if signature[name].get('unit')==unit and any(n.get('kind')==kind and n.get('reads',{}).get(port)=='$'+name for n in body)]
        if len(possible)==1:result[role]=possible[0]
    return result


def semantic_body(graph,event,method):
    body=method.get('body',[]);returns=method.get('returns',{});signature=method.get('formal_inputs',{})
    roles=role_formals(method);actual=event.get('reads',{})
    # Resolve only declared transparent body links. No instructions are removed
    # from the actual body, its instance, or its execution witness.
    aliases={n.get('writes',{}).get('result'):n.get('reads',{}).get('value') for n in body if n.get('kind') in ('alias','load')}
    def root(value):
        seen=set()
        while value in aliases and value not in seen:seen.add(value);value=aliases[value]
        return value
    semantic=[]
    for node in body:
        if node.get('kind') in ('alias','load'):continue
        semantic.append(dict(node,reads={p:root(v) for p,v in node.get('reads',{}).items()}))
    body=semantic;returns={p:root(v) for p,v in returns.items()};kinds=[n.get('kind') for n in body]
    result={'cyclical_day':False,'appearance_month_ordinal':False}
    if not source_body_valid(graph,method) or not formal_types_valid(graph,event,method):return result
    if kinds==['cycle_reduce','count']:
        reduce,count=body;rd=reduce.get('reads',{});cr=count.get('reads',{})
        divisor=rd.get('divisor','');origin=cr.get('origin','')
        cycle=actual.get(divisor[1:]) if divisor.startswith('$') else None
        good=(rd.get('dividend')=='$'+roles.get('offset','!') and
              cr.get('offset')==reduce.get('writes',{}).get('remainder') and
              origin=='$'+roles.get('head_day','!') and cr.get('cycle')==divisor and
              graph.value(cycle,{'one_of':[{'literal':60},{'value':60,'parameter':'cycle'}]}) and
              count.get('attributes',{}).get('cyclic') is True)
        result['cyclical_day']=(good and returns.get('result')==count.get('writes',{}).get('result') and returns.get('remainder')==reduce.get('writes',{}).get('remainder') and return_types_valid(graph,event,method,{'result':'day_index','remainder':'day'}))
    if kinds==['cycle_reduce','cycle_reduce','year_scan','count']:
        first,second,scan,count=body
        def parameter(node,label):
            term=node.get('reads',{}).get('divisor','');name=term[1:] if term.startswith('$') else ''
            return signature.get(name,{}).get('source_label')==label and graph.value(actual.get(name),{'parameter':label})
        attrs=scan.get('attributes',{});schedule=attrs.get('cumulative_schedule',[])
        # Every schedule row must have an overt corresponding source clause;
        # its numbers are checked against that clause by an independent reader.
        chinese_integer=_numbers.chinese_integer
        valid_schedule=bool(schedule) and all(isinstance(row.get('year'),int) and isinstance(row.get('cumulative_intercalations'),int) and
            any(graph.valid_span(s) and '歲' in s['quote'] and s['quote'].endswith('閏') and
                chinese_integer(s['quote'].split('歲')[0])==row['year'] and
                chinese_integer(s['quote'].split('歲')[1][:-1])==row['cumulative_intercalations']
                for s in scan.get('source_spans',[])) for row in schedule)
        valid_schedule=valid_schedule and len({r['year'] for r in schedule})==len(schedule) and all(schedule[i]['year']<schedule[i+1]['year'] and schedule[i]['cumulative_intercalations']<schedule[i+1]['cumulative_intercalations'] for i in range(len(schedule)-1))
        result['appearance_month_ordinal']=(first.get('reads',{}).get('dividend')=='$'+roles.get('month_offset','!') and
            parameter(first,'元月') and parameter(second,'章月') and
            second.get('reads',{}).get('dividend')==first.get('writes',{}).get('remainder') and
            scan.get('reads',{}).get('months')==second.get('writes',{}).get('remainder') and
            count.get('reads',{}).get('offset')==scan.get('writes',{}).get('remainder') and
            attrs.get('ordinary_year_months')==12 and attrs.get('intercalary_year_months')==13 and valid_schedule and
            count.get('attributes',{}).get('ordinal_origin')==1 and count.get('attributes',{}).get('origin_label')=='天正' and
            count.get('attributes',{}).get('cyclic') is False and returns.get('result')==count.get('writes',{}).get('result') and returns.get('remainder')==scan.get('writes',{}).get('remainder') and return_types_valid(graph,event,method,{'result':'month_ordinal','remainder':'month'}))
    return result


def trace_identity(event,method,execution):
    """The recorded body's reads/ports must be those actually executed."""
    body=method.get('body',[]);actual=event.get('reads',{});returns=method.get('returns',{})
    traces=[s.get('method_body_trace') for s in execution.get('execution_trace',[]) if s.get('event_id')==event.get('id') and 'method_body_trace' in s]
    if len(traces)!=1 or len(traces[0])!=len(body):return False
    values=execution.get('values',{})
    if any(vid not in values for vid in actual.values()):return False
    env={'$'+name:values[vid] for name,vid in actual.items()}
    for node,step in zip(body,traces[0]):
        if node.get('id')!=step.get('body_event_id') or node.get('kind')!=step.get('kind') or node.get('writes')!=step.get('value_bindings'):return False
        if any(v not in env for v in node.get('reads',{}).values()):return False
        if step.get('reads')!={port:env[v] for port,v in node.get('reads',{}).items()}:return False
        if not set(node.get('writes',{}))<=set(step.get('writes',{})):return False
        for port,vid in node.get('writes',{}).items():env[vid]=step['writes'][port]
    if any(v not in env for v in returns.values()):return False
    observed=execution.get('event_results',{}).get(event.get('id'))
    return observed=={port:env[v] for port,v in returns.items()} and all(values.get(event.get('writes',{}).get(port))==env[v] for port,v in returns.items())


def source_body_valid(graph,method):
    """Validate body-to-definition provenance and overt operation source cues."""
    definition=method.get('source_spans',[])
    if not definition or not all(graph.valid_span(s) for s in definition):return False
    for node in method.get('body',[]):
        spans=node.get('source_spans',[])
        if not spans or not all(graph.valid_span(s) and any(s['doc_id']==d['doc_id'] and s['reading_id']==d['reading_id'] and d['start']<=s['start']<s['end']<=d['end'] for d in definition) for s in spans):return False
        text='，'.join(s['quote'] for s in spans)
        if node.get('kind')=='count' and not re.search(r'數(?:從.*起|起於)',text):return False
        if node.get('kind')=='cycle_reduce' and '除' not in text:return False
        if node.get('kind')=='year_scan' and not ('除' in text and '閏' in text):return False
    return bool(method.get('body'))


def return_types_valid(graph,event,method,expected):
    for port,unit in expected.items():
        vid=event.get('writes',{}).get(port);value=graph.values.get(vid,{})
        if value.get('producer')!=event.get('id') or value.get('output_port')!=port or value.get('unit')!=unit:return False
        root=graph.root(vid)
        if root is None or graph.values[root].get('unit')!=unit:return False
        declared=method.get('return_types',{}).get(port,{})
        if 'unit' in declared and declared['unit']!=unit:return False
    return True


def validated_call(graph,event,execution):
    methods=[m for m in graph.report.get('method_library',[]) if m.get('id')==event.get('attributes',{}).get('target')]
    if len(methods)!=1:return False
    method=methods[0];attrs=event.get('attributes',{});binding=event.get('method_binding',{})
    actuals=binding.get('formal_actuals',binding.get('actuals',{}));context=event.get('context_bindings',{})
    return (attrs.get('body')==method.get('body') and attrs.get('formal_returns')==method.get('returns') and
        binding.get('definition_id')==method.get('id') and binding.get('formal_inputs')==method.get('formal_inputs') and
        set(actuals)==set(method.get('formal_inputs',{})) and binding.get('actuals')==event.get('reads') and
        set(event.get('reads',{}))==set(actuals)|set(context) and all(event['reads'].get(k)==v for k,v in {**actuals,**context}.items()) and
        all(v in graph.return_links for v in event.get('writes',{}).values()) and
        any(semantic_body(graph,event,method).values()) and trace_identity(event,method,execution))


def formal_types_valid(graph,event,method):
    for name,formal in method.get('formal_inputs',{}).items():
        vid=event.get('reads',{}).get(name);actual=graph.values.get(vid,{})
        if formal.get('unit') is not None and actual.get('unit')!=formal['unit']:return False
        root=graph.root(vid)
        if root is None or formal.get('unit') is not None and graph.values[root].get('unit')!=formal['unit']:return False
    return True
