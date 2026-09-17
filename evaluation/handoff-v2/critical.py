"""Independent source/producer/port assertions for the exposed development set.

Case IDs here select evaluation specifications only. No production imports this
module, and no check mutates an analysis or supplies a missing relation.
"""
from graph_checks import Graph, span_audit
from semantic_checks import validate_method, validate_dual, validate_threshold, validate_year_scan, validate_external_call


def checks(report, window, specifications):
    g = Graph(report)
    results = []
    evidence = []

    def event(quote, kind=None, doc=None, query=None):
        e = g.one(quote, kind, doc, query)
        evidence.append(e['id'])
        return e

    def name(label, query='main', parameter=False):
        v = g.named(label, query, parameter)
        evidence.append(g.values[v]['producer'])
        return v

    def scalar(value, expected):
        assert g.scalar(value) == expected, ('literal/parameter', value, expected, g.scalar(value))

    def divide(quote, denominator):
        e = event(quote, {'divmod', 'cycle_reduce'})
        scalar(e['reads']['divisor'], denominator)
        assert set(e['writes']) >= {'quotient', 'remainder'}
        return e

    def threshold(quote, label, lower, upper=None):
        e = event(quote, 'threshold')
        validate_threshold(g, e)
        assert g.same(e['reads']['value'], name(label))
        scalar(e['reads']['lower'], lower)
        if upper is not None:
            scalar(e['reads']['upper'], upper)
        return e

    def invoke(i):
        if window == 'W01':
            if i == 1:
                d = divide('盈章歲得一', 19)
                g.assert_port(name('積月'), d, 'quotient')
                g.assert_port(name('閏餘'), d, 'remainder')
            elif i == 2:
                e = threshold('閏餘十二以上', '閏餘', 12)
                m = event('以月法乘積月', 'multiply')
                assert not m.get('attributes', {}).get('guard') and not m.get('guard')
                assert g.output(e) not in g.ancestors(g.output(m))
            elif i == 3:
                e = event('加二', 'add')
                assert g.reads(e, name('積月'))
                assert any(g.scalar(v) == 2 for v in e['reads'].values())
                assert not g.same(g.output(e), name('積月'))
            elif i == 4:
                d = divide('盈日法得一', 81)
                g.assert_port(name('小餘'), d, 'remainder')
            elif i == 5:
                d = divide('積日盈六十', 60)
                assert g.reads(d, name('積日'))
                g.assert_port(name('大餘'), d, 'remainder')
                assert not g.same(name('小餘'), name('大餘'))
            elif i == 6:
                d = divide('小餘盈日法得一', 81)
                e = event('從大餘', 'add')
                assert g.reads(e, g.output(d, 'quotient'))
                assert not g.reads(e, g.output(d, 'remainder'))
            elif i == 7:
                e = event('數除如法', 'method_call')
                validate_method(g, e)
            elif i == 8:
                scales = g.at('倍弦', 'interval_scale')
                assert len(scales) == 2, 'paired day/fraction interval components'
                for e in scales:
                    evidence.append(e['id'])
                    assert e['reads'] and e['writes']
                    a = e['attributes']
                    assert a.get('factor') == 2 or any(g.scalar(v) == 2 for v in e['reads'].values())
                    assert a.get('base_state')
                    assert g.producer(e['reads']['value'])['kind'] == 'literal'
                    consumers = [x for x in g.at('倍弦', 'add') if g.reads(x, g.output(e))]
                    assert len(consumers) == 1
                    assert any(g.same(v, base) for v in consumers[0]['reads'].values()
                               for base in a['base_state'].values())
        elif window == 'W02':
            if i == 1:
                s = event('置入蔀年減一', 'subtract')
                scalar(s['reads']['right'], 1)
                m = event('以章月乘之', 'multiply')
                assert g.reads(m, g.output(s))
            elif i == 2:
                threshold('十二以上', '閏餘', 12)
            elif i == 3:
                e = event('置入蔀積月', 'load')
                assert g.reads(e, name('積月'))
                assert g.producer(name('積月'))['kind'] == 'divmod'
            elif i == 4:
                divide('滿蔀月得一', 940)
            elif i == 5:
                d = divide('積日以六十除去之', 60)
                g.assert_port(name('大餘'), d, 'remainder')
            elif i == 6:
                threshold('小餘四百四十一以上', '小餘', 441)
                d = divide('滿蔀月得一', 940)
                g.assert_port(name('小餘'), d, 'remainder')
            elif i == 7:
                d = divide('小餘滿蔀月得一', 940)
                e = event('上加大餘', 'add')
                assert g.reads(e, g.output(d, 'quotient'))
                assert not g.reads(e, g.output(d, 'remainder'))
            elif i == 8:
                e = event('命之如前', 'method_call')
                validate_method(g, e)
        elif window == 'W03':
            if i == 1:
                d = divide('盈見中法得一', 1583)
                g.assert_port(name('積中'), d, 'quotient')
                m = event('并積中', 'add')
                assert g.reads(m, name('積中'))
                assert not g.same(name('積中'), name('中元餘'))
                assert not g.same(name('積中'), name('積中', parameter=True))
            elif i == 2:
                d = event('以章中除之', 'cycle_reduce')
                assert g.same(d['reads']['dividend'], name('中元餘'))
                scalar(d['reads']['divisor'], 228)
            elif i == 3:
                m = event('以章歲乘中餘', 'multiply')
                assert g.reads(m, name('中餘'))
                d = divide('盈見中法得一', 1583)
                g.assert_port(name('中餘'), d, 'remainder')
                assert not g.reads(m, name('中餘', parameter=True))
            elif i == 4:
                a = event('從之', 'add')
                m1 = event('以閏分乘定見復數', 'multiply')
                m2 = event('以章歲乘中餘', 'multiply')
                assert g.reads(a, g.output(m1), g.output(m2))
                d = divide('盈見月法得一', 30077)
                assert g.same(d['reads']['dividend'], g.output(a))
            elif i == 5:
                a = event('并積中', 'add')
                d = divide('盈見月法得一', 30077)
                assert g.reads(a, g.output(d, 'quotient'), name('積中'))
                for wrong in ('中元餘', '入章中數', '星見中次'):
                    assert not g.reads(a, name(wrong))
                assert not g.reads(a, name('積中', parameter=True))
            elif i == 6:
                d = divide('盈見月法得一', 30077)
                g.assert_port(name('月餘'), d, 'remainder')
                assert not g.same(name('月餘'), name('積月'))
            elif i == 7:
                e = event('除十三', 'year_scan')
                validate_year_scan(g, e)
                schedule = e['attributes'].get('cumulative_schedule', [])
                assert schedule == [{'year': y, 'cumulative_intercalations': n}
                                    for n, y in enumerate([3, 6, 9, 11, 14, 17, 19], 1)]
                assert e['attributes']['ordinary_year_months'] == 12
                assert e['attributes']['intercalary_year_months'] == 13
                assert sum('歲' in s['quote'] and '閏' in s['quote'] for s in e['source_spans']) >= 7
                assert g.reads(e, name('入章月數'))
            elif i == 8:
                a = event('中數從冬至起', 'count')
                b = event('次數從星紀起', 'count')
                validate_dual(g, [a, b])
        elif window == 'W04':
            if i == 1:
                m = event('以合積月乘積合', 'multiply')
                assert g.same(name('小積'), g.output(m))
                assert g.reads(m, name('合積月', parameter=True))
            elif i == 2:
                m = event('又以月餘乘積合', 'multiply')
                assert g.reads(m, name('月餘', parameter=True))
                scalar(name('月餘', parameter=True), 41606)
                assert not g.reads(m, name('月餘'))
            elif i == 3:
                d = divide('滿其月法得一', 82213)
                m = event('又以月餘乘積合', 'multiply')
                assert g.same(d['reads']['dividend'], g.output(m))
                a = event('從小積', 'add')
                assert g.reads(a, g.output(d, 'quotient'), name('小積'))
            elif i == 4:
                d = divide('滿其月法得一', 82213)
                g.assert_port(name('月餘'), d, 'remainder')
                a = event('不盡為月餘', 'alias')
                assert a['evidence_status'] != 'text_overt'
                assert any(s.get('editorial_provenance') for s in a['source_spans'])
                assert not g.same(name('月餘'), name('月餘', parameter=True))
            elif i == 5:
                s = event('以閏減入紀月', 'subtract')
                assert g.same(s['reads']['left'], name('入紀月'))
                assert g.same(s['reads']['right'], name('閏'))
                d = divide('其餘以十二去之', 12)
                assert g.same(d['reads']['dividend'], g.output(s))
            elif i == 6:
                d = divide('滿章月得一為閏', 235)
                g.assert_port(name('閏餘'), d, 'remainder')
            elif i == 7:
                e = threshold('其閏餘滿二百二十四以上至二百三十一星合閏月', '閏餘', 224, 231)
                assert e['attributes'].get('lower_inclusive', True) is True
                assert e['attributes'].get('upper_inclusive', True) is True
                assert e['writes']
            elif i == 8:
                e = event('以朔制之', 'external_constraint_call')
                validate_external_call(g, e)
                assert any(u['cause'] == 'requires_external_data' and u['missing_or_conflicting_inputs'] for u in report['unresolved'])
                assert e['reads'] and e['writes']

    for spec in specifications:
        if spec['window_id'] != window:
            continue
        evidence.clear()
        try:
            invoke(int(spec['assertion_id'][-2:]))
            status, reason = 'pass', 'source-anchored producer/port constraints satisfied'
        except (AssertionError, KeyError, TypeError, IndexError) as error:
            status, reason = 'fail', str(error) or 'required graph relation not satisfied'
        results.append({'assertion_id': spec['assertion_id'], 'status': status,
                        'required_relation': spec['required_relation'], 'source_anchor': spec['anchor'],
                        'event_ids': sorted(set(evidence)), 'reason': reason})
    return results
