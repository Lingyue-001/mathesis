import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKETS = ROOT / 'evaluation/handoff-v2/package/runtime_inputs'

def packet(text, context=()):
    return {'input_mode':'declared_edited_primary_context','provided_scope':{}, 'primary_documents':[{'doc_id':'synthetic','reading_id':'test','text':text}], 'context_documents':[{'doc_id':str(i),'text':t} for i,t in enumerate(context)]}

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('analysis_parser.pipeline'), 'compositional parser API is absent')
        from analysis_parser.pipeline import parse_packet
        from analysis_parser.execution import execute
        self.parse, self.execute = parse_packet, execute
    def w(self, n):
        return self.parse(json.loads((PACKETS/f'W{n:02}.json').read_text()))
    def named(self,r,x,name,query='main'):
        return x['named_outputs'][query+':'+name]
    def test_compositional_contrast(self):
        a=self.parse(packet('以甲乘乙，名曰丙。以丁乘戊，名曰己。以庚除己，所得加丙，餘名曰辛。'))
        b=self.parse(packet('以甲乘乙，名曰丙。以丁乘戊，加丙，以庚除之，餘名曰辛。'))
        inputs={'甲':3,'乙':4,'丁':5,'戊':6,'庚':7}
        self.assertEqual(self.named(a,self.execute(a,inputs),'辛'),2)
        self.assertEqual(self.named(b,self.execute(b,inputs),'辛'),0)
        self.assertFalse(a['coverage']['unparsed_spans'])
    def test_ambiguous_remainder(self):
        r=self.parse(packet('以甲除乙，以丙除丁，其餘為戊。'))
        self.assertTrue(any(x['cause']=='interpretive_ambiguity' for x in r['unresolved']))
    def test_w03_retains_full_values_delayed_ports_and_scan(self):
        r=self.w(3); x=self.execute(r,{'定見復數':131126})
        for label,value in [('積中',1717642),('中餘',1450),('積月',1770377),('月餘',17051)]:
            self.assertEqual(self.named(r,x,label),value)
        scans=[e for e in r['events'] if e['kind']=='year_scan']
        self.assertEqual(len(scans),1)
        self.assertEqual(x['values'][scans[0]['writes']['remainder']],11)
        self.assertEqual(x['values'][scans[0]['writes']['years']],9)
        self.assertEqual(len([e for e in r['events'] if e['kind']=='count' and e['attributes'].get('origin_label') in ['冬至','星紀']]),2)
        self.assertFalse(r['coverage']['unparsed_spans'])
    def test_missing_upstream_never_uses_cycle_parameter(self):
        p=json.loads((PACKETS/'W03.json').read_text());p['primary_documents']=p['primary_documents'][1:]
        r=self.parse(p)
        for label in ['中餘','積中']:
            self.assertTrue(any(label in str(x['missing_or_conflicting_inputs']) for x in r['unresolved']))
    def test_w04_numeric_and_open_boundary(self):
        r=self.w(4);x=self.execute(r,{'積合':8618},{'章閏':7})
        for label,value in [('小積',112034),('積月',116395),('月餘',29615),('入紀月',3595),('閏',107),('閏餘',20),('入歲月數',8)]:
            self.assertEqual(self.named(r,x,label),value)
        self.assertTrue(any(e['kind']=='external_constraint_call' for e in r['events']))
        self.assertFalse(r['coverage']['unparsed_spans'])
    def test_queries_are_siblings_and_increment_is_doubled(self):
        r=self.w(1);x=self.execute(r,{'入統歲數':10,'統首日':1})
        self.assertEqual(self.named(r,x,'積月'),123)
        self.assertEqual(self.named(r,x,'積月','地正'),124)
        self.assertEqual(self.named(r,x,'積月','人正'),125)
        self.assertEqual(self.named(r,x,'小餘','弦'),55)
        self.assertEqual(self.named(r,x,'小餘','望'),5)
        self.assertEqual(self.named(r,x,'大餘','望'),47)
        self.assertFalse(r['coverage']['unparsed_spans'])
    def test_hq_ordinal_and_scale(self):
        r=self.w(2);x=self.execute(r,{'入蔀年':63,'所入蔀名':38})
        self.assertEqual(self.named(r,x,'積月'),766)
        self.assertEqual(self.named(r,x,'小餘'),594)
        self.assertEqual(self.named(r,x,'小餘','後月朔'),153)
        self.assertFalse(r['coverage']['unparsed_spans'])
    def test_spans_and_opaque_terms(self):
        r=self.w(4);docs={d['doc_id']:d for d in r['documents']}
        for e in r['events']:
            for s in e['source_spans']:
                self.assertEqual(docs[s['doc_id']]['text'][s['start']:s['end']],s['quote'])
        r=self.parse(packet('以見月法乘甲，盈月法得一。',['見月法三十七．','月法七．']))
        x=self.execute(r,{'甲':2})
        div=next(e for e in r['events'] if e['kind']=='divmod')
        self.assertEqual(x['values'][div['writes']['quotient']],10)
    def test_unknown_instruction_is_failure(self):
        r=self.parse(packet('旋轉天地而求未知。'))
        self.assertTrue(r['coverage']['unparsed_spans'])
