import copy
import json
import unittest
from pathlib import Path
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from analysis_parser.audit import audit
from test_core_composition import packet, PACKETS

class FidelityTests(unittest.TestCase):
    def test_layout_changes_preserve_values_and_source_spans(self):
        p=json.loads((PACKETS/'W03.json').read_text())
        for d in p['primary_documents']+p['context_documents']:
            d['text']='\n '.join(d['text']);d['doc_id']='renamed-'+d['doc_id'];d['editorial_trace']=[]
        r=parse_packet(p);x=execute(r,{'定見復數':131126})
        self.assertEqual(x['named_outputs'].get('main:積月'),1770377)
        self.assertFalse(r['coverage']['unparsed_spans'])
        self.assertFalse(audit(r))
    def test_heading_is_open_target_not_development_title(self):
        r=parse_packet(packet('推陌生目標術，置甲，以乙乘之，名曰丙。'))
        self.assertFalse(r['coverage']['unparsed_spans'])
        self.assertEqual(execute(r,{'甲':4,'乙':5})['named_outputs']['main:丙'],20)
    def test_raw_mode_never_adopts_editorial_addition(self):
        p=json.loads((PACKETS/'W04.json').read_text());edited=parse_packet(p)
        p['input_mode']='edition_transcription_only'
        p['primary_documents'][0]['text']=edited['documents'][0]['reconstructed_transcription']
        p['primary_documents'][0]['editorial_trace']=[]
        raw=parse_packet(p)
        self.assertFalse(any(e['kind']=='alias' and e['attributes'].get('label')=='積月' for e in raw['events']))
        self.assertFalse(any(any(c in label for c in '[]()') for v in raw['value_instances'] for label in v['labels']))
        self.assertTrue(raw['coverage']['unparsed_spans'] or raw['unresolved'])
    def test_source_reconstruction_and_editorial_nine(self):
        p=json.loads((PACKETS/'W02.json').read_text());r=parse_packet(p)
        d=next(d for d in r['documents'] if d['doc_id']=='HQ.3.6')
        self.assertIn('四百九十[九]',d['reconstructed_transcription'])
        e=next(e for e in r['events'] if e['kind']=='literal' and e['attributes']['value']==499)
        self.assertEqual(e['evidence_status'],'declared_edited')
        self.assertTrue(e['source_spans'][0]['editorial_provenance'])
    def test_two_operation_frames_do_not_steal_named_remainder(self):
        p=packet('以甲乘乙，盈丙得一，名曰丁。以戊乘己，盈庚得一，名曰辛。不盈者名曰壬。')
        r=parse_packet(p)
        self.assertTrue(any(u['cause']=='interpretive_ambiguity' for u in r['unresolved']))
    def test_duplicate_parameter_is_ambiguous(self):
        r=parse_packet(packet('以常數乘甲。',['常數三．','常數七．']))
        self.assertTrue(any(u['cause']=='interpretive_ambiguity' for u in r['unresolved']))
    def test_audit_detects_remainder_and_accumulation_corruption(self):
        r=parse_packet(json.loads((PACKETS/'W03.json').read_text()))
        changed=copy.deepcopy(r)
        add=next(e for e in changed['events'] if e['kind']=='add' and e['attributes'].get('receiver_label')=='積中')
        projection=next(v for v in changed['value_instances'] if v['source_label']=='中元餘')
        add['reads']['left']=projection['id']
        alias=next(e for e in changed['events'] if e['kind']=='alias' and e['attributes']['label']=='月餘')
        alias['reads']['value']=add['writes']['result']
        kinds={d['kind'] for d in audit(changed)}
        self.assertIn('full_accumulation_corruption',kinds)
        self.assertIn('remainder_producer_corruption',kinds)

    def test_thirteenth_month_ordinal_does_not_wrap(self):
        p=packet('置甲，以十二除之，至有閏之歲，除十三。入章，三歲一閏。不盈者數起於天正，算外。')
        # Explicit naming supplies the counted quantity's month role.
        p['primary_documents'][0]['text']='置甲，名曰入章月數。'+p['primary_documents'][0]['text'][3:]
        r=parse_packet(p);x=execute(r,{'甲':36})
        count=next(e for e in r['events'] if e['kind']=='count')
        self.assertEqual(x['values'][count['writes']['result']],13)
        scan=next(e for e in r['events'] if e['kind']=='year_scan')
        self.assertEqual(x['values'][scan['writes']['months_removed']],24)
    def test_nominal_and_civil_month_are_distinct_outputs(self):
        r=parse_packet(json.loads((PACKETS/'W04.json').read_text()));x=execute(r,{'積合':8618},{'章閏':7})
        count=next(e for e in r['events'] if e['kind']=='count')
        self.assertEqual(x['values'][count['writes']['result']],9)
        self.assertEqual(x['values'][count['writes']['civil_month_number']],7)

    def test_audit_rejects_missing_read_and_cross_query_dependency(self):
        r=parse_packet(json.loads((PACKETS/'W01.json').read_text()))
        changed=copy.deepcopy(r)
        mul=next(e for e in changed['events'] if e['kind']=='multiply')
        del mul['reads']['right']
        quarter=next(e for e in changed['events'] if e['kind']=='add' and e['scope']['query']=='弦')
        next_result=next(v for v in changed['value_instances'] if v['scope']['query']=='其次月' and v['source_label']=='大餘')
        quarter['reads']['left']=next_result['id']
        kinds={d['kind'] for d in audit(changed)}
        self.assertIn('missing_read_port',kinds)
        self.assertIn('cross_query_dependency',kinds)
    def test_explicit_parameter_binding_resolution_is_reported(self):
        r=parse_packet(json.loads((PACKETS/'W04.json').read_text()));x=execute(r,{'積合':8618},{'章閏':7})
        self.assertTrue(any(b['name']=='章閏' and b['status']=='supplied' for b in x.get('explicit_bindings',[])))
        self.assertFalse(any(u.get('name')=='章閏' for u in x['unresolved']))

    def test_inferred_quarter_carry_uses_own_interval_and_prior_method(self):
        r=parse_packet(json.loads((PACKETS/'W01.json').read_text()))
        inferred=[e for e in r['events'] if e['scope']['query']=='弦' and e['kind'] in ('divmod','method_call')]
        self.assertTrue(inferred)
        for e in inferred:
            quotes=[s['quote'] for s in e['source_spans']]
            self.assertIn('rule_inferred',e['evidence_status'])
            self.assertTrue(any('三十一' in q or '加大餘七' in q for q in quotes))
            self.assertFalse(any('求望' in q for q in quotes))
