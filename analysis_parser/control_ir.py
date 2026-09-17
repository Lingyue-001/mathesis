"""Explicit control objects and exact bounded event membership."""
from fractions import Fraction


def following_region(candidates, current, postposed_targets=()):
    """Forward local evidence, bounded by explicit task/query markers.

    A named postposed target may label the current unfinished construction;
    another marker always begins a distinct region.
    """
    start=current['analysis_range'][1];out=[]
    for candidate in candidates:
        if candidate['analysis_range'][0]<start:continue
        if candidate['kind']=='task_marker' and candidate['slots']['target']['text'] not in postposed_targets:break
        out.append(candidate)
    return out

def resolve_control(candidates, context, values):
    controls=[]
    for i,c in enumerate(candidates):
        if c['kind']=='update_count':
            tail=following_region(candidates,c); stop=next((x for x in tail if x['kind']=='loop_threshold'),None)
            count=next((x for x in tail if x['text']=='數所得'),None)
            if stop and count:
                controls.append({'kind':'Repeat','candidate':c,'initial':'current','update':{'operation':'add','increment':c['slots']['increment']},'counter':{'initial':0,'increment':1},'stop':{'operator':context.get('stop'),'threshold':stop['slots']['threshold']},'test':'post','body':[{'id':'update','kind':'add','reads':{'left':'$state','right':'$increment'},'writes':{'result':'state'}},{'id':'count','kind':'add','reads':{'left':'$counter','right':'$counter_increment'},'writes':{'result':'counter'}}],'source_spans':c['source_spans']+stop['source_spans']+count['source_spans']})
        elif c['kind']=='method_reference':
            controls.append({'kind':'Call','candidate':c,'name':'cycle_and_count','source_spans':c['source_spans']})
    return controls

def rational(value):
    if isinstance(value,dict):return Fraction(value['numerator'],value['denominator'])
    if isinstance(value,(list,tuple)):return Fraction(*value)
    return Fraction(value)

def boundary_membership(moons, qi, profile, epoch=None):
    if not epoch:return {'status':'requires_external_data','reason':'missing common epoch'}
    if profile not in ('instant_lunation','civil_whole_day'):return {'status':'missing_profile'}
    m=[rational(x) for x in moons];q=rational(qi)
    if any(b<=a for a,b in zip(m,m[1:])):return {'status':'invalid_event_order'}
    if profile=='civil_whole_day':m=[x.numerator//x.denominator for x in m]
    matches=[i for i,(a,b) in enumerate(zip(m,m[1:])) if a<=q<b]
    return {'status':'resolved','interval':matches[0]} if len(matches)==1 else {'status':'requires_external_data','reason':'event outside supplied half-open intervals'}


def legacy_repeat_adapter(event):
    a=event['attributes']
    return {'kind':'Repeat','adapter':'legacy_year_scan','initial':{'remaining':event['reads']['months'],'year':1},'update':{'kind':'schedule_selected_subtract','ordinary':a['ordinary_year_months'],'intercalary':a['intercalary_year_months'],'schedule':a['cumulative_schedule']},'counter':{'initial':0,'increment':1},'stop':{'operator':'lt','left':'remaining','right':'selected_year_length'},'test':'pre','body':['choose_year_length','subtract_from_remaining','increment_year_and_counter'],'returns':{'state':'remainder','counter':'years','removed':'months_removed'},'source_spans':event['source_spans']}


def compare_events(left, right, epoch=None):
    if not epoch:return {'status':'requires_external_data','reason':'missing common epoch'}
    a,b=rational(left),rational(right)
    return {'status':'resolved','ordering':'before' if a<b else 'after' if a>b else 'equal','same_whole_day':a.numerator//a.denominator==b.numerator//b.denominator,'epoch':epoch}
