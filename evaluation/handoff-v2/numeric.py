"""Map fixture vocabulary to actual graph outputs; performs no arithmetic."""
from graph_checks import Graph


def explicit_inputs(window, fixture_inputs):
    names = {'W01': {'years': '入統歲數', 'head': '統首日'},
             'W02': {'ordinal': '入蔀年', 'head': '所入蔀名'},
             'W03': {'E': '定見復數'}, 'W04': {'E': '積合'}}[window]
    return {names[k]: v for k, v in fixture_inputs.items()}


SUPPLEMENT = {'章閏': 7}
SUPPLEMENT_PROVENANCE = {
    'parameter': '章閏', 'value': 7, 'status': 'explicit_scholarly_execution_binding',
    'source': 'C2017 printed p.155 §25; selected-pages PDF p.18, visually verified',
    'basis': '235 lunations minus 19 civil years of 12 months leaves 7 intercalations',
    'limitation': 'Value is absent from W04 runtime text; parser did not extract it.'}


def project(report, execution, window):
    g = Graph(report)
    out, evidence, errors = {}, {}, {}

    def put(key, getter):
        try:
            vid = getter()
            out[key] = execution['values'][vid]
            evidence[key] = {'value_id': vid, 'producer': g.values[vid]['producer'],
                             'output_port': g.values[vid]['output_port']}
        except (AssertionError, KeyError, IndexError, TypeError) as e:
            errors[key] = str(e)

    def named(key, label, query='main'):
        put(key, lambda: g.named(label, query))

    def at(key, quote, kind, port='result', query=None):
        put(key, lambda: g.output(g.one(quote, kind, query=query), port))

    if window in ('W01', 'W02'):
        for key, label in {'months': '積月', 'intercalary_remainder': '閏餘',
                           'days': '積日', 'small': '小餘', 'greater': '大餘',
                           'day_index': 'day_index'}.items():
            named(key, label)
        at('long_month', '小餘三十八以上' if window == 'W01' else '小餘四百四十一以上', 'threshold')
        nxt = '其次月' if window == 'W01' else '後月朔'
        named('next_small', '小餘', nxt)
        named('next_greater', '大餘', nxt)
        named('next_day_index', '朔日', nxt)
        if window == 'W01':
            for prefix, query in [('quarter', '弦'), ('full', '望')]:
                for suffix, label in [('small', '小餘'), ('greater', '大餘'), ('day_index', '朔日')]:
                    named(prefix + '_' + suffix, label, query)
            named('terrestrial_months', '積月', '地正')
            named('anthropic_months', '積月', '人正')
        else:
            at('years', '置入蔀年減一', 'subtract')
    elif window == 'W03':
        for key, label in {'medials_total': '積中', 'medial_remainder': '中餘',
                           'medials_origin_remainder': '中元餘', 'medials_rule_remainder': '入章中數',
                           'medials_year_offset': '星見中次', 'medial_ordinal': 'medial_ordinal', 'station_ordinal': 'station_ordinal',
                           'months_total': '積月', 'month_remainder': '月餘',
                           'months_origin_remainder': '月元餘', 'months_rule_remainder': '入章月數',
                           'appearance_month_ordinal': 'month_ordinal'}.items():
            named(key, label)
        at('first_product', '以閏分乘定見復數', 'multiply')
        at('second_product', '以章歲乘中餘', 'multiply')
        at('month_numerator', '從之', 'add')
        at('extra_month_quotient', '盈見月法得一', 'divmod', 'quotient')
        at('whole_years_removed', '除十三', 'year_scan', 'years')
        at('months_removed', '除十三', 'year_scan', 'months_removed')
        at('months_year_offset', '除十三', 'year_scan', 'remainder')
    else:
        for key, label in {'lesser_accumulation': '小積', 'months_total': '積月',
                           'month_remainder': '月餘', 'months_era_remainder': '入紀月',
                           'intercalation_count': '閏', 'intercalation_remainder': '閏餘',
                           'months_year_offset': '入歲月數'}.items():
            named(key, label)
        at('second_product', '又以月餘乘積合', 'multiply')
        at('fraction_month_quotient', '滿其月法得一', 'divmod', 'quotient')
        at('nonintercalary_months', '以閏減入紀月', 'subtract')
        at('nominal_month_ordinal', '從天正十一月起', 'count')
        at('nominal_civil_month', '從天正十一月起', 'count', 'civil_month_number')
        at('intercalary_candidate', '其閏餘滿二百二十四以上至二百三十一星合閏月', 'threshold')
        at('final_month_status', '以朔制之', 'external_constraint_call')
    return out, evidence, errors


def assess_fixture(report, execution, fixture):
    actual, evidence, errors = project(report, execution, fixture['window_id'])
    rows = [{'field': key, 'expected': expected, 'actual': actual.get(key),
             'status': 'pass' if key in actual and type(actual[key]) is type(expected) and actual[key] == expected else 'fail',
             'evidence': evidence.get(key), 'error': errors.get(key)}
            for key, expected in fixture['expected'].items()]
    # Source dual-count origins both start at ordinal 1 with the same 12-cycle offset.
    # Extra diagnostics are evaluator expectations; frozen fixtures are unchanged.
    if fixture['fixture_id'] in ('N05', 'N06'):
        expected = {'N05': 11, 'N06': 2}[fixture['fixture_id']]
        rows.append({'field': 'station_ordinal', 'expected': expected, 'actual': actual.get('station_ordinal'),
                     'status': 'pass' if type(actual.get('station_ordinal')) is int and actual['station_ordinal']==expected else 'fail',
                     'evidence': evidence.get('station_ordinal'), 'basis': 'W03 reference step 08; common offset and 1-based origin at 星紀'})
    return {'fixture_id': fixture['fixture_id'], 'window_id': fixture['window_id'],
            'status': 'pass' if all(r['status'] == 'pass' for r in rows) else 'fail',
            'explicit_inputs': explicit_inputs(fixture['window_id'], fixture['inputs']),
            'parameter_supplement': SUPPLEMENT_PROVENANCE if fixture['window_id'] == 'W04' else None,
            'rows': rows, 'execution_unresolved': execution['unresolved']}
