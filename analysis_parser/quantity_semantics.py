"""Checks representation, rate and model transitions independently of arithmetic."""
from fractions import Fraction

UNKNOWN={'unknown','opaque','product',None}

# The same vocabulary is used when a value is first emitted and when a later
# compiler fact refines its unit. Keeping these fields together prevents a
# value from becoming, for example, an integer with an inherited ``unknown``
# quantity kind.
UNIT_QUANTITY_KINDS = {
    'integer': 'count', 'cycle': 'count', 'ordinal': 'count',
    'year': 'count', 'year_ordinal': 'count', 'year_index': 'count',
    'month': 'count', 'month_fraction': 'count', 'month_ordinal': 'count',
    'month_name_index': 'count', 'intercalary_month': 'count',
    'medial': 'count', 'medial_fraction': 'count', 'station': 'count',
    'station_fraction': 'count', 'planet_event': 'count', 'table_column': 'count',
    'day': 'duration', 'day_fraction': 'duration', 'day_index': 'duration',
    'du': 'angle', 'du_fraction': 'angle',
    'boolean': 'predicate', 'status': 'status', 'boundary_status': 'status',
    'epoch_identity': 'reference', 'event_sequence': 'sequence',
}


def finalize_quantity_metadata(value, event, explicit_metadata=None):
    """Derive the compatible unit/kind/representation/status tuple in one place.

    ``explicit_metadata`` is the small, typed input supplied at the emission
    site (including a reviewed semantic decision). The function never needs an
    adjudication dependency: callers may use it for automatic parser facts and
    the reviewed compiler alike.
    """
    explicit = explicit_metadata or {}
    unit = value.get('unit')
    quantity_kind = explicit.get('quantity_kind', UNIT_QUANTITY_KINDS.get(unit, 'unknown'))
    value['quantity_kind'] = quantity_kind
    if 'representation' not in explicit:
        scale = value.get('scale')
        value['representation'] = ({'kind': 'fraction_numerator', 'denominator_id': scale['denominator']}
                                   if isinstance(scale, dict) and scale.get('denominator') else {'kind': 'whole'})
    parser_unresolved = event.get('attributes', {}).get('resolution_status') not in (None, 'resolved')
    value['resolution_status'] = ('unknown' if unit in UNKNOWN or quantity_kind == 'unknown' or parser_unresolved
                                  else 'resolved')
    return value


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
