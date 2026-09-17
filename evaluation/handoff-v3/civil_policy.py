"""Curated finite-domain graph relations derived from the 47 scholarly task cards.

These are expected relations, not expected numeric answers. Only the evaluator
imports this module; no reference value or policy reaches the parser worker.
"""
import copy
import hashlib
import json
from pathlib import Path


def P(name, value=None):
    return {'parameter': name, **({'value': value} if value is not None else {})}


def L(value, anchor=None):
    return {'literal': value, **({'anchor': anchor} if anchor else {})}


def E(task, port):
    return {'export': [task, port]}


def O(kind, port='result', **reads):
    return {'origin': {'kind': kind, 'port': port, **({'reads': reads} if reads else {})}}


def event(kind, task, reads=None, writes=None, **extra):
    return {'kind': kind, 'scope': {'task': task}, **({'reads': reads} if reads else {}),
            **({'writes': writes} if writes else {}), **extra}


def build_policy(cards, boundary_profile='civil_whole_day'):
    anchors = {o['id']: o['anchor'] for card in cards for o in card['obligations']}
    rules = {}

    def put(oid, *predicates):
        rules[oid] = {'events': list(predicates)}

    local = E('era_entry', 'local_elapsed_years'); head = E('era_entry', 'head_day')
    years = {'input': 'epoch_elapsed_years'}
    origin = O('cycle_reduce', 'remainder', dividend=years, divisor=P('元法', 4617))
    st_select_reads = {'divisor': P('統法', 1539), 'local0': origin, 'head0': L(1),
                       'local1': O('subtract', left=origin, right=P('統法', 1539)), 'head1': L(41),
                       'local2': O('subtract', left=O('subtract', left=origin, right=P('統法', 1539)), right=P('統法', 1539)), 'head2': L(21)}
    put('C1_ST.01', event(['load', 'alias'], 'era_entry', {'value': years}, {'result': E('era_entry', 'elapsed_years')}))
    put('C1_ST.02', event('cycle_reduce', 'era_entry', {'dividend': years, 'divisor': P('元法', 4617)}, {'remainder': E('era_entry', 'origin_remainder')}))
    for oid in ('C1_ST.03', 'C1_ST.04'):
        put(oid, event('select', 'era_entry', st_select_reads,
                       {'index': E('era_entry', 'concordance_index'), 'local': local, 'head': head},
                       attributes={'exclusive': True}, branch_contract='three_concordances'))
    sf_elapsed = O('subtract', left={'input': 'epoch_inclusive_year'}, right=L(1))
    sf_origin = O('cycle_reduce', 'remainder', dividend=sf_elapsed, divisor=P('元法', 4560))
    era_r = O('divmod', 'remainder', dividend=sf_origin, divisor=P('紀法', 1520))
    era_q = O('divmod', 'quotient', dividend=sf_origin, divisor=P('紀法', 1520))
    ob_q = O('divmod', 'quotient', dividend=era_r, divisor=P('蔀法', 76))
    ob_r = O('divmod', 'remainder', dividend=era_r, divisor=P('蔀法', 76))
    put('C1_SF.01', event('cycle_reduce', 'era_entry', {'dividend': sf_elapsed, 'divisor': P('元法', 4560)}, {'remainder': E('era_entry', 'origin_remainder')}))
    put('C1_SF.02', event('divmod', 'era_entry', {'dividend': sf_origin, 'divisor': P('紀法', 1520)}, {'quotient': E('era_entry', 'era_quotient'), 'remainder': E('era_entry', 'era_remainder')}))
    put('C1_SF.03', event('count', 'era_entry', {'offset': era_q}, {'result': E('era_entry', 'era_index')},
                         attributes={'ordinal_origin': 0, 'cyclic': False, 'sequence': ['天紀', '地紀', '人紀'], 'convention': '筭外'}))
    put('C1_SF.04', event('divmod', 'era_entry', {'dividend': era_r, 'divisor': P('蔀法', 76)}, {'quotient': E('era_entry', 'obscuration_quotient'), 'remainder': E('era_entry', 'obscuration_year_remainder')}))
    put('C1_SF.05', event('lookup', 'era_entry', {'row': O('add', left=ob_q, right=L(1)), 'column': E('era_entry', 'era_index')},
                            {'head_day': head, 'head_year': E('era_entry', 'head_year')}, table_contract='full_source_table'))
    put('C1_SF.06', event('count', 'era_entry', {'offset': ob_r, 'origin': E('era_entry', 'head_year'), 'cycle': L(60)},
                            {'result': E('era_entry', 'current_year_name')}, attributes={'cyclic': True, 'zero_offset_at_origin': True}))
    months = E('new_moon', 'months'); lag = E('new_moon', 'intercalation_remainder')
    days = E('new_moon', 'whole_days'); small = E('new_moon', 'small_remainder')
    day_offset = E('new_moon', 'day_offset')
    month_st = O('multiply', left=P('章月', 235), right=local)
    month_sf = O('multiply', left=P('章月', 235), right=O('subtract', left=E('era_entry', 'years_into_obscuration'), right=L(1)))
    put('C2_ST.01', event('multiply', 'new_moon', {'left': P('章月', 235), 'right': local}))
    put('C2_ST.02', event('divmod', 'new_moon', {'dividend': month_st, 'divisor': P('章歲', 19)}, {'quotient': months, 'remainder': lag}))
    put('C2_ST.03', event('threshold', 'new_moon', {'value': lag, 'lower': L(12)}, {'result': E('new_moon', 'has_intercalation')}, attributes={'lower_inclusive': True}))
    put('C2_SF.01', event('subtract', 'new_moon', {'left': E('era_entry', 'years_into_obscuration'), 'right': L(1)}, attributes={'ordinal_to_elapsed': True}))
    put('C2_SF.02', event('divmod', 'new_moon', {'dividend': month_sf, 'divisor': P('章法', 19)}, {'quotient': months, 'remainder': lag}))
    for tr, index, factor, denominator, limit, rem in [('ST', 4, '月法', '日法', 38, 43), ('SF', 3, '蔀日', '蔀月', 441, 499)]:
        put(f'C2_{tr}.{index:02}', event('divmod', 'new_moon', {'dividend': O('multiply', left=P(factor), right=months), 'divisor': P(denominator)}, {'quotient': days, 'remainder': small}))
        put(f'C2_{tr}.{index+1:02}', event('cycle_reduce', 'new_moon', {'dividend': days, 'divisor': L(60)}, {'remainder': day_offset}))
        put(f'C2_{tr}.{index+2:02}', event('count', 'new_moon', {'offset': day_offset, 'origin': head, 'cycle': L(60)}, {'result': E('new_moon', 'new_moon_day')}, attributes={'cyclic': True, 'zero_offset_at_origin': True}))
        put(f'C2_{tr}.{index+3:02}', event('threshold', 'new_moon', {'value': small, 'lower': L(limit)}, {'result': E('new_moon', 'month_long')}, attributes={'lower_inclusive': True}))
        put(f'C2_{tr}.{index+4:02}', event('add', 'new_moon', {'left': day_offset, 'right': L(29)}, attributes={'receiver': '大餘', 'increment': True}),
                                             event('add', 'new_moon', {'left': small, 'right': L(rem)}, attributes={'receiver': '小餘', 'increment': True}))
    whole_w = E('winter', 'winter_whole_residual'); frac_w = E('winter', 'winter_remainder')
    st_w = O('multiply', left=P('策餘', 8080), right=local)
    sf_w = O('multiply', left=P('日餘', 168), right=O('subtract', left=E('era_entry', 'years_into_obscuration'), right=L(1)))
    put('C3_ST.01', event('multiply', 'winter', {'left': P('策餘', 8080), 'right': local}))
    put('C3_ST.02', event('divmod', 'winter', {'dividend': st_w, 'divisor': P('統法', 1539)}, {'quotient': whole_w, 'remainder': frac_w}))
    put('C3_ST.03', event('method_call', 'winter', {'offset': whole_w, 'fraction': frac_w, 'origin': head, 'cycle': L(60)}, {'result': E('winter', 'winter_day')}, method_contract={'definition_anchor': anchors['C2_ST.06']}))
    put('C3_SF.01', event('multiply', 'winter', {'left': P('日餘', 168), 'right': O('subtract', left=E('era_entry', 'years_into_obscuration'), right=L(1))}))
    put('C3_SF.02', event('divmod', 'winter', {'dividend': sf_w, 'divisor': P('中法', 32)}, {'quotient': whole_w, 'remainder': frac_w}))
    w_offset = O('cycle_reduce', 'remainder', dividend=whole_w, divisor=L(60))
    put('C3_SF.03', event('cycle_reduce', 'winter', {'dividend': whole_w, 'divisor': L(60)}))
    put('C3_SF.04', event('count', 'winter', {'offset': w_offset, 'origin': head, 'cycle': L(60)}, {'result': E('winter', 'winter_day')}, attributes={'cyclic': True}))
    st_wo = O('method_call', 'remainder', offset=whole_w, origin=head, cycle=L(60))
    put('C4_ST.01', event('add', 'nodes', {'left': st_wo, 'right': L(45)}, attributes={'receiver': '大餘'}),
                        event('add', 'nodes', {'left': frac_w, 'right': L(1010, anchors['C4_ST.01'])}, attributes={'receiver': '小餘'}))
    put('C4_ST.02', event('multiply', 'qi', {'left': frac_w, 'right': L(3)}))
    put('C4_ST.03', event('rescale', 'qi', {'value': O('multiply', left=frac_w, right=L(3)), 'old_denominator': P('統法', 1539), 'new_denominator': P('元法', 4617), 'factor': L(3)}, {'result': E('qi', 'qi_base_remainder4617')}, attributes={'transition': {'status': 'resolved', 'transition': 'value_preserving_rescale'}}))
    put('C4_ST.04', event('add', 'qi', {'left': st_wo, 'right': L(15)}, attributes={'receiver': '大餘'}),
                        event('add', 'qi', {'left': E('qi', 'qi_base_remainder4617'), 'right': L(1010, anchors['C4_ST.04'])}, attributes={'receiver': '小餘'}))
    put('C4_SF.01', event('add', 'qi', {'left': w_offset, 'right': L(15)}, attributes={'receiver': '大餘'}),
                        event('add', 'qi', {'left': frac_w, 'right': L(7)}, attributes={'receiver': '小餘'}))
    carry = O('divmod', 'quotient', dividend=O('add', left=frac_w, right=L(7)), divisor=P('中法', 32))
    put('C4_SF.02', event('method_call', 'qi', {'offset': O('add', left=O('add', left=w_offset, right=L(15)), right=carry), 'origin': head, 'cycle': L(60),
                                                  'fraction': O('divmod', 'remainder', dividend=O('add', left=frac_w, right=L(7)), divisor=P('中法', 32))},
                         {'result': E('qi', 'first_qi_day')}, method_contract={'definition_anchor': anchors['C3_SF.04']}))
    lag12 = O('multiply', left=L(12), right=lag)
    scaled_lag = O('rescale', value=lag12, old_denominator=P('章歲', 19), new_denominator=P('章中', 228), factor=L(12))
    scaled_lag.update(unit='month_fraction', denominator=P('章中', 228))
    put('C5_ST.01', event('multiply', 'intercalation', {'left': L(12), 'right': lag}),
                         event('rescale', 'intercalation', {'value': lag12, 'old_denominator': P('章歲', 19), 'new_denominator': P('章中', 228), 'factor': L(12)},
                               attributes={'transition': {'status': 'resolved', 'transition': 'value_preserving_rescale'}}))
    put('C5_ST.02', event('repeat', 'intercalation', {'initial': scaled_lag, 'increment': L(7), 'threshold': P('章中', 228)},
                          {'state': E('intercalation', 'loop_final_lag'), 'count': E('intercalation', 'loop_count')},
                          control={'kind': 'Repeat', 'counter': {'initial': 0, 'increment': 1}, 'stop': {'operator': 'gt'}, 'test': 'post', 'body': [
                              {'kind': 'add', 'reads': {'left': '$state', 'right': '$increment'}, 'writes': {'result': 'state'}},
                              {'kind': 'add', 'reads': {'left': '$counter', 'right': '$counter_increment'}, 'writes': {'result': 'counter'}}]}))
    put('C5_ST.03', event('add', 'intercalation', {'left': E('intercalation', 'loop_count'), 'right': L(1)}, {'result': E('intercalation', 'nominal_leap_slot')}))
    complement = O('multiply', left=L(12), right=O('subtract', left=P('章法', 19), right=lag))
    put('C5_SF.01', event('multiply', 'intercalation', {'left': L(12), 'right': O('subtract', left=P('章法', 19), right=lag)}, {'result': E('intercalation', 'intercalation_complement')}))
    put('C5_SF.02', event('divmod', 'intercalation', {'dividend': complement, 'divisor': P('章閏數', 7)}, {'quotient': E('intercalation', 'placement_q'), 'remainder': E('intercalation', 'placement_r')}))
    put('C5_SF.03', event('add', 'intercalation', {'left': E('intercalation', 'placement_q'), 'right': O('threshold', value=E('intercalation', 'placement_r'), lower=L(4))}, {'result': E('intercalation', 'adjusted_count')}))
    put('C5_SF.04', event('add', 'intercalation', {'left': E('intercalation', 'adjusted_count'), 'right': L(1)}, {'result': E('intercalation', 'nominal_leap_slot')}))
    for tr, oid in [('ST', 'C5_ST.04'), ('SF', 'C5_SF.05')]:
        put(oid, event('boundary_call', 'intercalation', {'nominal_slot': E('intercalation', 'nominal_leap_slot'), 'has_intercalation': E('new_moon', 'has_intercalation'),
                     'moon_events': O('event_sequence', whole=days, numerator=small, epoch=E('era_entry', 'time_epoch')),
                     'qi_events': O('event_sequence', whole=O('cycle_lift', whole=whole_w, elapsed_years=local, factor=L(360)), numerator=frac_w, epoch=E('era_entry', 'time_epoch'))},
                     {'result': E('intercalation', 'boundary_result')}, attributes={'profile': boundary_profile, 'time_frame': 'full_local_epoch'}))

    # The SF card expressly includes its later year-level threshold. It is a
    # separate source occurrence, enumerated here before any graph is inspected.
    packet = json.loads((Path(__file__).resolve().parents[2] / 'handoff_v3/runtime_inputs/SF_CIVIL_CORE.json').read_text())
    doc = next(d for d in packet['primary_documents'] if d['doc_id'] == 'HQ.3.5')
    quote = '十二以上，其歲有閏'
    if doc['text'].count(quote) != 1:
        raise ValueError('Supplemental reference occurrence is not unique')
    start = doc['text'].index(quote)
    sf_threshold_anchor = {'doc_id': doc['doc_id'], 'reading_id': doc['reading_id'],
                           'text_sha256': hashlib.sha256(doc['text'].encode()).hexdigest(),
                           'start': start, 'end': start + len(quote), 'quote': quote}
    rules['C2_SF.02']['events'].append(event('threshold', 'new_moon', {'value': lag, 'lower': L(12)},
                                           {'result': E('new_moon', 'has_intercalation')},
                                           attributes={'lower_inclusive': True}, anchor=sf_threshold_anchor))

    def exported(oid, task, port, value):
        rules[oid].setdefault('exports', []).append({'path': [task, port], 'value': value})

    exported('C1_SF.06', 'era_entry', 'years_into_obscuration', O('add', left=ob_r, right=L(1)))
    for tr, oid, denom, inc in [('ST', 'C2_ST.08', P('日法', 81), 43), ('SF', 'C2_SF.07', P('蔀月', 940), 499)]:
        query_rem = O('divmod', 'remainder', dividend=O('add', left=small, right=L(inc)), divisor=denom)
        query_carry = O('divmod', 'quotient', dividend=O('add', left=small, right=L(inc)), divisor=denom)
        query_whole = O('add', left=O('add', left=day_offset, right=L(29)), right=query_carry)
        exported(oid, 'new_moon', 'next_moon_remainder', query_rem)
        exported(oid, 'new_moon', 'next_moon_day', O('method_call', offset=query_whole, fraction=query_rem, origin=head, cycle=L(60)))
    for oid, task, prefix, base, denominator, inc, whole_inc in [
            ('C4_ST.01', 'nodes', 'first_node', frac_w, P('統法', 1539), 1010, 45),
            ('C4_ST.04', 'qi', 'first_qi', E('qi', 'qi_base_remainder4617'), P('元法', 4617), 1010, 15)]:
        query_rem = O('divmod', 'remainder', dividend=O('add', left=base, right=L(inc)), divisor=denominator)
        query_carry = O('divmod', 'quotient', dividend=O('add', left=base, right=L(inc)), divisor=denominator)
        query_whole = O('add', left=O('add', left=st_wo, right=L(whole_inc)), right=query_carry)
        exported(oid, task, prefix + '_day', O('method_call', offset=query_whole, fraction=query_rem, origin=head, cycle=L(60)))
    for oid, count in [('C5_ST.03', E('intercalation', 'loop_count')), ('C5_SF.04', E('intercalation', 'adjusted_count'))]:
        exported(oid, 'intercalation', 'medial_ordinal', O('add', left=count, right=L(1)))
        exported(oid, 'intercalation', 'nominal_leap_celestial_label', count)
        exported(oid, 'intercalation', 'nominal_leap_civil_label', O('count', origin=L(11), offset=O('subtract', left=count, right=L(1)), cycle=L(12)))

    rates = {
        'C2_ST.02': ('year', 'month', P('章月', 235), P('章歲', 19), local),
        'C2_SF.02': ('year', 'month', P('章月', 235), P('章法', 19), O('subtract', left=E('era_entry', 'years_into_obscuration'), right=L(1))),
        'C2_ST.04': ('month', 'day', P('月法', 2392), P('日法', 81), months),
        'C2_SF.03': ('month', 'day', P('蔀日', 27759), P('蔀月', 940), months),
        'C3_ST.02': ('year', 'day', P('策餘', 8080), P('統法', 1539), local),
        'C3_SF.02': ('year', 'day', P('日餘', 168), P('中法', 32), O('subtract', left=E('era_entry', 'years_into_obscuration'), right=L(1))),
    }
    for oid, (from_unit, to_unit, factor, denominator, operand) in rates.items():
        rules[oid]['events'][0]['rate_contract'] = {'from_unit': from_unit, 'to_unit': to_unit,
                                                   'factor': factor, 'denominator': denominator,
                                                   'operand': dict(operand, unit=from_unit)}

    def type_selectors(obj, tradition):
        if isinstance(obj, list):
            for item in obj:
                type_selectors(item, tradition)
        elif isinstance(obj, dict):
            path = obj.get('export')
            if path == ['new_moon', 'months']:
                obj.update(unit='month', quantity_kind='count')
            elif path == ['new_moon', 'intercalation_remainder']:
                obj.update(unit='month_fraction', quantity_kind='count', denominator=P('章歲' if tradition == 'ST' else '章法', 19))
            elif path == ['new_moon', 'small_remainder']:
                obj.update(unit='day_fraction', quantity_kind='duration', denominator=P('日法', 81) if tradition == 'ST' else P('蔀月', 940))
            elif path == ['new_moon', 'whole_days']:
                obj.update(unit='day', quantity_kind='duration', time_frame='full_local_epoch')
            elif path == ['winter', 'winter_remainder']:
                obj.update(unit='day_fraction', quantity_kind='duration', denominator=P('統法', 1539) if tradition == 'ST' else P('中法', 32))
            elif path == ['winter', 'winter_whole_residual']:
                obj.update(unit='day', quantity_kind='duration', time_frame='annual_residual')
            elif path == ['qi', 'qi_base_remainder4617']:
                obj.update(unit='day_fraction', denominator=P('元法', 4617))
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    type_selectors(value, tradition)
    # Deep-copy per obligation: shared Python selector helpers must not let SF
    # enrichments overwrite the separate ST convention.
    rules = {oid: copy.deepcopy(rule) for oid, rule in rules.items()}
    for oid, rule in rules.items():
        type_selectors(rule, 'ST' if '_ST.' in oid else 'SF')
    return {'version': 'civil-relations-v2', 'supplemental_anchors': [sf_threshold_anchor], 'supported_actions': ['literal', 'parameter', 'input', 'alias', 'load', 'multiply', 'subtract', 'add', 'divmod', 'cycle_reduce', 'threshold', 'count', 'query', 'method_call', 'select', 'lookup', 'rescale', 'fraction', 'repeat', 'cycle_lift', 'epoch_frame', 'event_sequence', 'boundary_call'], 'obligations': rules}
