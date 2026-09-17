"""Execute D01–D25. D26 is evaluated only by the frozen prospective runner."""
import copy
import hashlib
import json
from graph_checks import Graph, span_audit
from critical import checks
from numeric import explicit_inputs, SUPPLEMENT, assess_fixture


def synthetic(text):
    return {'input_mode': 'declared_edited_primary_context', 'provided_scope': {},
            'primary_documents': [{'doc_id': 'synthetic', 'text': text}], 'context_documents': []}


def refresh_hashes(packet):
    for category in ('primary_documents', 'context_documents'):
        for doc in packet[category]:
            doc['text_sha256'] = hashlib.sha256(doc['text'].encode()).hexdigest()


def semantic_view(report):
    events = [{k: e[k] for k in ('kind', 'reads', 'writes', 'scope', 'attributes')}
              for e in report['events']]
    return {'events': events,
            'values': [{k: v.get(k) for k in ('producer', 'output_port', 'labels', 'role', 'unit', 'scale', 'scope')}
                       for v in report['value_instances']]}


def assess_carry_boundary(report, window, executor=None):
    """Inject only base state values; execute the window's actual parsed update graph."""
    from analysis_parser.execution import execute
    executor = executor or execute
    before = copy.deepcopy(report)
    r = copy.deepcopy(report); g = Graph(r)
    base = {label: g.named(label) for label in ('小餘', '大餘')}
    for label, vid in base.items():
        e = g.producer(vid, unalias=False)
        # A diagnostic intervention, not a parser result or a gold repair.
        e.update(kind='input', reads={}, attributes={'name': label})
    query = '其次月' if window=='W01' else '後月朔'
    divisor = 81 if window=='W01' else 940
    increment = 43 if window=='W01' else 499
    samples = [37,38,39] if window=='W01' else [440,441,442]
    d = g.one('小餘盈日法得一' if window=='W01' else '小餘滿蔀月得一', 'divmod')
    receiver = g.one('從大餘' if window=='W01' else '上加大餘', 'add')
    threshold = g.one('小餘三十八以上' if window=='W01' else '小餘四百四十一以上','threshold')
    rows=[]
    for index, small in enumerate(samples):
        inputs={'小餘':small,'大餘':10, '入統歲數':1,'統首日':1} if window=='W01' else {'小餘':small,'大餘':10,'入蔀年':2,'所入蔀名':1}
        x=executor(r,inputs);v=x['values']
        actual={'threshold':v[g.output(threshold)], 'sum':v[d['reads']['dividend']],
                'carry':v[g.output(d,'quotient')], 'remainder':v[g.output(d,'remainder')],
                'receiver':v[g.output(receiver)], 'base_small':v[base['小餘']], 'base_greater':v[base['大餘']]}
        expected={'threshold':index>0, 'sum':small+increment,'carry':[0,1,1][index],
                  'remainder':[divisor-1,0,1][index], 'receiver':[39,40,40][index], 'base_small':small,'base_greater':10}
        assert actual==expected, {'actual':actual,'expected':expected}
        assert type(actual['threshold']) is bool
        rows.append({'input_small':small,'actual':actual,'expected':expected})
    assert report==before, 'diagnostic modified original state'
    return {'window':window,'diagnostic':'synthetic base values on source-parsed carry/update rules',
            'base_interventions':base,'rows':rows,'original_graph_preserved':True}


def assess_cross_call(report, specifications):
    """Executable cross-call overwrite, distinct from the forward-cycle control."""
    from analysis_parser.execution import execute
    from numeric import project
    g=Graph(report);parameter=g.named('月餘',parameter=True)
    first=execute(report,{'積合':8618},SUPPLEMENT)
    assert first['values'][g.named('月餘')]==29615
    assert first['values'][parameter]==41606
    clean=execute(report,{'積合':2},SUPPLEMENT)
    keys=('lesser_accumulation','second_product','fraction_month_quotient','month_remainder','months_total')
    expected=dict(zip(keys,(26,83212,1,999,27)))
    actual=project(report,clean,'W04')[0]
    assert {k:actual[k] for k in keys}==expected and clean['values'][parameter]==41606
    contaminated=copy.deepcopy(report);badg=Graph(contaminated)
    badg.producer(parameter)['attributes']['value']=first['values'][g.named('月餘')]
    bad=execute(contaminated,{'積合':2},SUPPLEMENT)
    assert all(u['cause']=='requires_external_data' or (u['cause']=='requires_explicit_input' and u.get('name')=='boundary_data') for u in bad['unresolved']), bad['unresolved']
    bad_actual=project(contaminated,bad,'W04')[0]
    bad_expected=dict(zip(keys,(26,59230,0,59230,26)))
    assert {k:bad_actual[k] for k in keys}==bad_expected
    identity_preserved=badg.producer(parameter)['kind']=='parameter' and badg.scalar(parameter)==41606
    assert not identity_preserved and bad['values'][parameter]!=41606
    rejected=next(x for x in checks(contaminated,'W04',specifications) if x['assertion_id']=='W04.C02')
    assert rejected['status']=='fail'
    assert any(bad_actual[k]!=expected[k] for k in keys)
    assert g.scalar(parameter)==41606
    return {'first_remainder':29615,'clean_second':expected,'contaminated_second':bad_expected,
            'parameter_identity_value_rejected':True,'second_result_rejected':True,
            'critical_rejection':rejected,'contaminated_execution_unresolved':bad['unresolved']}

def run_behavior(packets, reports, specifications, fixtures, outdir):
    from analysis_parser.pipeline import parse_packet
    from analysis_parser.execution import execute
    from analysis_parser.audit import audit
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []

    def check_case(identifier, fn):
        try:
            evidence = fn()
            row = {'case_id': identifier, 'status': 'pass', 'evidence': evidence}
        except (AssertionError, KeyError, TypeError, IndexError, ValueError) as e:
            row = {'case_id': identifier, 'status': 'fail', 'reason': str(e) or 'required behavior failed'}
        rows.append(row)

    def original(w):
        r = reports[w]
        assertions = checks(r, w, specifications)
        assert all(x['status'] == 'pass' for x in assertions)
        assert not r['coverage']['unparsed_spans'] and not span_audit(r)
        return {'window': w, 'critical': len(assertions), 'unparsed_spans': []}

    for n, w in enumerate(packets, 1):
        check_case(f'D{n:02}', lambda w=w: original(w))

    def rename():
        evidence = []
        for w, packet in packets.items():
            p = copy.deepcopy(packet)
            for category in ('primary_documents', 'context_documents'):
                for i, doc in enumerate(p[category]):
                    doc['doc_id'] = f'opaque-{category}-{i}-93'
                    doc['reading_id'] = f'opaque-reading-{i}'
                    if 'source' in doc:
                        doc['source']['locator'] = 'opaque-locator'
            r = parse_packet(p)
            assert semantic_view(r) == semantic_view(reports[w]), w
            evidence.append({'window': w, 'same_semantic_graph': True})
        return evidence
    check_case('D05', rename)

    def layout():
        evidence = []
        for w, packet in packets.items():
            p = copy.deepcopy(packet)
            for category in ('primary_documents', 'context_documents'):
                for doc in p[category]:
                    doc['text'] = '  ' + doc['text'].replace('，', ' , \n ').replace('．', ' 。\n ')
            refresh_hashes(p)
            r = parse_packet(p)
            assert semantic_view(r) == semantic_view(reports[w]), w
            assert not span_audit(r), w
            evidence.append({'window': w, 'same_semantic_graph': True, 'all_spans_valid': True})
        return evidence
    check_case('D06', layout)

    def distractor():
        p = copy.deepcopy(packets['W03'])
        changed = []
        for doc in p['context_documents']:
            if doc['text'].startswith('積中十三'):
                doc['text'] = doc['text'].replace('十三', '九十九').replace('百五十七', '八百八十八')
                changed.append(doc['doc_id'])
        assert changed
        refresh_hashes(p)
        r = parse_packet(p)
        f = next(f for f in fixtures if f['fixture_id'] == 'N05')
        result = assess_fixture(r, execute(r, explicit_inputs('W03', f['inputs'])), f)
        assert result['status'] == 'pass', result
        return {'changed_parameters': changed, 'N05_all_fields_unchanged': True}
    check_case('D07', distractor)

    def denominator():
        g = Graph(reports['W02'])
        e = g.one('滿蔀月得一', 'divmod')
        assert g.scalar(e['reads']['divisor']) == 940
        assert g.scalar(g.named('日法', parameter=True)) == 4
        return {'division': e['id'], 'denominator': 940, 'distractor': 4}
    check_case('D08', denominator)

    def missing_upstream():
        p = copy.deepcopy(packets['W03']); p['primary_documents'] = p['primary_documents'][1:]
        r = parse_packet(p)
        gaps = [u for u in r['unresolved'] if u['cause'] == 'unresolved_parser']
        for label in ['中餘', '積中']:
            assert any(label in u['missing_or_conflicting_inputs'] for u in gaps)
        (outdir/'D09-output.json').write_text(json.dumps(r, ensure_ascii=False, indent=2))
        return {'missing_current_inputs': gaps}
    check_case('D09', missing_upstream)

    def unedited():
        p = copy.deepcopy(packets['W04']); d = p['primary_documents'][0]
        d['text'] = d['text'].replace('為積月，不盡', '')
        d['editorial_trace'] = []; p['input_mode'] = 'edition_transcription_only'; refresh_hashes(p)
        r = parse_packet(p); g = Graph(r)
        assert not g.at('為積月', 'alias')
        assert r['unresolved'] or r['coverage']['unparsed_spans']
        (outdir/'D10-output.json').write_text(json.dumps(r, ensure_ascii=False, indent=2))
        return {'mode': r['input_mode'], 'no_inserted_accumulated_month_alias': True,
                'unresolved': r['unresolved']}
    check_case('D10', unedited)

    def query(assertion):
        result = next(x for x in checks(reports['W01'], 'W01', specifications) if x['assertion_id'] == assertion)
        assert result['status'] == 'pass'; return result
    check_case('D11', lambda: query('W01.C03'))
    check_case('D12', lambda: query('W01.C08'))

    def contrast(which):
        texts = ['以甲乘乙，名曰丙。以丁乘戊，名曰己。以庚除己，所得加丙，餘名曰辛。',
                 '以甲乘乙，名曰丙。以丁乘戊，加丙，以庚除之，餘名曰辛。']
        r = parse_packet(synthetic(texts[which])); g = Graph(r)
        d = g.one(kind='cycle_reduce'); numerator = g.producer(d['reads']['dividend'])
        assert numerator['kind'] == ('multiply' if which == 0 else 'add')
        if which == 0:
            a = g.one(kind='add'); assert g.reads(a, g.output(d, 'quotient'), g.named('丙'))
        x = execute(r, {'甲': 3, '乙': 4, '丁': 5, '戊': 6, '庚': 7})
        assert x['named_outputs']['main:辛'] == (2 if which == 0 else 0)
        assert not r['coverage']['unparsed_spans']
        return {'dividend_producer': numerator, 'remainder': x['named_outputs']['main:辛']}
    check_case('D13', lambda: contrast(0)); check_case('D14', lambda: contrast(1))

    def subtraction():
        evidence = []
        for text, expected in [('以甲減乙。', 7), ('以乙減甲。', -7)]:
            r = parse_packet(synthetic(text)); g = Graph(r); e = g.one(kind='subtract')
            x = execute(r, {'甲': 3, '乙': 10})
            assert x['values'][g.output(e)] == expected
            evidence.append({'text': text, 'actual': expected, 'reads': e['reads']})
        return evidence
    check_case('D15', subtraction)

    def ambiguous():
        r = parse_packet(synthetic('以甲除乙，以丙除丁，其餘為戊。'))
        u = [x for x in r['unresolved'] if x['cause'] == 'interpretive_ambiguity']
        assert u and len(u[0]['missing_or_conflicting_inputs']) == 2
        return u
    check_case('D16', ambiguous)

    def boundary(text, samples, expected):
        r = parse_packet(synthetic(text)); g = Graph(r); e = g.one(kind='threshold'); got = []
        for v in samples:
            x = execute(r, {'甲': v}); got.append(x['values'][g.output(e)])
        assert got == expected, got
        return {'text': text, 'inputs': samples, 'results': got, 'event': e}
    check_case('D17', lambda: assess_carry_boundary(reports['W01'], 'W01'))
    check_case('D18', lambda: assess_carry_boundary(reports['W02'], 'W02'))
    check_case('D19', lambda: boundary('甲滿二百二十四以上至二百三十一星合閏月。', [223, 224, 231, 232], [False, True, True, False]))

    def corrupt(identifier):
        w = 'W04' if identifier == 'D22' else 'W03'
        r = copy.deepcopy(reports[w]); g = Graph(r)
        if identifier == 'D20':
            e = g.one('并積中', 'add'); original = e['reads']['left']; e['reads']['left'] = g.named('中元餘')
            target = 'W03.C05'
        elif identifier == 'D21':
            e = g.one('不盈者名曰月餘', 'alias'); original = e['reads']['value']
            e['reads']['value'] = g.output(g.one('并積中', 'add')); target = 'W03.C06'
        else:
            e = g.one('又以月餘乘積合', 'multiply'); original = e['reads']['left']
            e['reads']['left'] = g.named('月餘'); target = 'W04.C02'
        result = next(x for x in checks(r, w, specifications) if x['assertion_id'] == target)
        assert result['status'] == 'fail', 'Evaluator incorrectly accepted injected wrong relation'
        f = next(f for f in fixtures if f['window_id'] == w)
        execution = execute(r, explicit_inputs(w, f['inputs']), SUPPLEMENT if w == 'W04' else None)
        numeric = assess_fixture(r, execution, f)
        assert numeric['status'] == 'fail', 'Numerical check unexpectedly failed to detect mutation'
        rerun = execute(r, {'積合': 2}, SUPPLEMENT) if identifier == 'D22' else None
        evidence = {'mutated_event': e['id'], 'original_value_id': original, 'mutated_reads': e['reads'],
                    'critical_rejection': result, 'production_audit': audit(r), 'numeric': numeric,
                    'second_invocation': rerun}
        (outdir/(('D22-forward-cycle' if identifier=='D22' else identifier)+'-rejected.json')).write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
        (outdir/(('D22-forward-cycle' if identifier=='D22' else identifier)+'-mutated-graph.json')).write_text(json.dumps(r, ensure_ascii=False, indent=2))
        return evidence
    for identifier in ['D20', 'D21']:
        check_case(identifier, lambda identifier=identifier: corrupt(identifier))

    def cross_call():
        evidence=assess_cross_call(reports['W04'],specifications)
        (outdir/'D22-cross-call-rejected.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
        evidence['separate_forward_cycle_control']=corrupt('D22')
        return evidence
    check_case('D22', cross_call)

    def from_word():
        g = Graph(reports['W03']); a = g.one('從之', 'add'); c = g.one('中數從冬至起', 'count')
        assert a['kind'] != c['kind'] and c['attributes']['origin_label'] == '冬至'
        return {'merge': a, 'count': c}
    check_case('D23', from_word)

    def punctuation():
        p = copy.deepcopy(packets['W03']); d = p['primary_documents'][1]
        d['text'] = d['text'].replace('除十三．入章，', '除十三入章，')
        d['editorial_trace'] = []; p['input_mode'] = 'edition_transcription_only'; refresh_hashes(p)
        r = parse_packet(p)
        assert r['provenance']['source_hashes'][d['doc_id']] != reports['W03']['provenance']['source_hashes'][d['doc_id']]
        assert r['input_mode'] == 'edition_transcription_only'
        assert r['unresolved'] or r['coverage']['unparsed_spans'], 'Undeclared punctuation reading silently treated as calibrated'
        (outdir/'D24-output.json').write_text(json.dumps(r, ensure_ascii=False, indent=2))
        return {'status': 'alternative reading retained with parser limitations', 'unparsed': r['coverage']['unparsed_spans']}
    check_case('D24', punctuation)

    def external():
        r = reports['W04']; g = Graph(r); e = g.one('以朔制之', 'external_constraint_call')
        x = execute(r, {'積合': 8618}, SUPPLEMENT)
        assert x['values'][g.output(e)] == 'requires_external_data'
        assert any(u['cause'] == 'requires_external_data' for u in x['unresolved'])
        return {'event': e, 'execution_unresolved': x['unresolved']}
    check_case('D25', external)
    rows.append({'case_id': 'D26', 'status': 'not_run', 'reason': 'Separate freeze/reference-before-output prospective stage required'})
    return rows
