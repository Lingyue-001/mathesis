"""Checks representation, rate and model transitions independently of arithmetic."""
from fractions import Fraction

UNKNOWN={'unknown','opaque','product',None}
def check_transition(event, values, context):
    a=event.get('attributes',{});kind=event['kind']; reads=event.get('reads',{});writes=event.get('writes',{})
    source=values.get(reads.get('value',reads.get('left')),{});target=values.get(writes.get('result',reads.get('right')), {})
    u,v=source.get('unit'),target.get('unit');rate=context.get('rate') or a.get('rate')
    def verdict(status,transition,**kw):return {'status':status,'transition':transition,'evidence':a.get('evidence',[]),**kw}
    if kind not in ('rescale','convert','add'):return verdict('resolved','arithmetic')
    if u in UNKNOWN or v in UNKNOWN:return verdict('unknown','undetermined')
    if kind=='add' and u!=v:return verdict('incompatible_without_conversion','addition')
    if u!=v:
        model=(u in ('day','year') and v=='du')
        if not rate:return verdict('requires_model_rate' if model else 'requires_unit_rate','model_mapping' if model else 'rate_conversion')
        if rate.get('from_unit')!=u or rate.get('to_unit')!=v or not rate.get('basis') or not rate.get('denominator'):
            return verdict('incompatible_rate','model_mapping' if model else 'rate_conversion')
        return verdict('resolved','model_mapping' if model else 'rate_conversion',rate=rate)
    if kind=='rescale':
        s=source.get('representation',{}).get('denominator');t=target.get('representation',{}).get('denominator')
        if not s or not t:return verdict('unknown','representation_rescale')
        if not a.get('source_operation') or not a.get('denominator_declaration') or not a.get('evidence'):
            return verdict('missing_representation_evidence','representation_rescale')
        if Fraction(a.get('factor',1),t)!=Fraction(1,s):return verdict('inconsistent_representation','representation_rescale')
        return verdict('resolved','value_preserving_rescale')
    return verdict('resolved','same_unit')
