import unittest
from analysis_parser.inputs import documents
from analysis_parser.pipeline import parse_packet

def packet(text):
    return {'schema_version':'3.0','primary_documents':[{'doc_id':'synthetic','text':text}]}

def program(text):
    from analysis_parser.context_compiler import compile_documents
    return compile_documents(documents(packet(text)),{}).to_dict()

class Frames(unittest.TestCase):
    def test_S01(self):
        for title in ('冬至','甲課'):
            p=program('推'+title+'，置甲量．')['definitions']
            self.assertEqual(p[0]['kind'],'ProcedureDef');self.assertEqual(p[0]['goal_surface'],title)
    def test_S02(self):
        p=program('推甲課，置三，名曰甲量．推甲課，置五，名曰甲量．')['definitions']
        self.assertEqual(len(p),2);self.assertNotEqual(p[0]['id'],p[1]['id'])
        r=parse_packet(packet('推甲課，置三，名曰甲量．推甲課，置五，名曰甲量．'))
        vs=[v for v in r['value_instances'] if '甲量' in v['labels']]
        self.assertEqual(len({v['scope']['procedure_id'] for v in vs}),2)
    def test_S03(self):
        p=program('推甲課，置三，名曰甲量，求弦，加一，求望，加二．')['definitions']
        self.assertEqual([x['kind'] for x in p],['ProcedureDef','QueryDef','QueryDef','QueryDef'])
        self.assertEqual(p[1]['parent'],p[0]['id']);self.assertEqual(p[1]['base_ref'],p[2]['base_ref'])
        a=program('推篇，大餘亦如之，小餘加一．求周至，加大餘五十九，小餘二十一．')['definitions']
        q=[d for d in a if d['kind']=='QueryDef'];self.assertEqual([d['goal_surface'] for d in q],['篇','周至']);self.assertEqual(q[0]['base_ref'],q[1]['base_ref'])
    def test_S04(self):
        p=program('置三，名曰甲量．')['definitions'][0]
        self.assertIsNone(p['goal_surface']);self.assertIn('甲量',p['return_ports'])
    def test_S05(self):
        p=program('推甲課，置甲量，皆以甲法為法．推乙課，置乙量，皆以乙法為法．')['definitions']
        a=[x for x in p if x['kind']=='Annotation'];self.assertEqual(len(a),2)
        self.assertNotEqual(a[0]['parent'],a[1]['parent'])
