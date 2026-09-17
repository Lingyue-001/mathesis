import unittest
from analysis_parser.inputs import documents
from analysis_parser.lexical import tokenize_candidates
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from test_frames import packet

def syntax(text,lex=None):
    from analysis_parser.construction_ir import parse_syntax
    d=documents(packet(text))[0];return parse_syntax(tokenize_candidates(d,lex or {}),d).to_dict()
def typed_parse(p):
    from analysis_parser.scoped import ScopedParser
    parser=ScopedParser(p);context=parser.context
    def typed_context():
        context()
        for v in parser.env.values.values():v['unit']='integer'
    parser.context=typed_context
    return parser.run()
class Syntax(unittest.TestCase):
    def test_L01(self):
        v=syntax('以甲法乘其乙餘并之');ops=[n for n in v['nodes'] if n['kind'] in ('Multiply','Combine')]
        self.assertEqual([n['kind'] for n in ops],['Multiply','Combine'])
        p=packet('置五，以甲法乘其乙餘并之');p['context_documents']=[{'doc_id':'c','text':'甲法三．乙餘七．'}]
        r=typed_parse(p);x=execute(r,{})
        self.assertEqual([x['values'].get(e['writes']['result']) for e in r['events'] if e['kind'] in ('multiply','add')],[21,26])
    def test_L02(self):
        self.assertIn('Combine',[n['kind'] for n in syntax('以甲法乘其乙餘從之')['nodes']])
        self.assertIn('Count',[n['kind'] for n in syntax('從冬至起')['nodes']])
    def test_L03(self):
        p=packet('加甲量於乙量');p['context_documents']=[{'doc_id':'c','text':'甲量三．乙量十．'}]
        r=typed_parse(p);x=execute(r,{})
        add=next(e for e in r['events'] if e['kind']=='add');self.assertEqual(x['values'][add['reads']['left']],10);self.assertEqual(x['values'][add['writes']['result']],13)
    def test_L04(self):
        v=syntax('三其小餘，皆以元為法');self.assertIn('Multiply',[n['kind'] for n in v['nodes']])
        self.assertNotIn('Rescale',[n['kind'] for n in v['nodes']])
        import json
        p=json.load(open('handoff_v3/runtime_inputs/ST_CIVIL_CORE.json'));p['selected_profiles']=['ST_elapsed','ST_intercalation_Cullen_Liu_GT']
        report=parse_packet(p);events={e['id']:e for e in report['events']}
        rescale=next(e for e in report['events'] if e['kind']=='rescale' and e['rule_id']=='V3_RESCALE')
        self.assertEqual(events[rescale['attributes']['source_operation']]['kind'],'multiply')
        self.assertEqual(rescale['attributes']['transition']['status'],'resolved')
    def test_L05(self):
        v=syntax('以乘率乘乙量',{'乘率':{}})
        self.assertIn('乘率',[n['surface'] for n in v['nodes'] if n['kind']=='Term'])
        self.assertEqual(len([n for n in v['nodes'] if n['kind']=='Multiply']),1)
    def test_L06(self):
        from analysis_parser.construction_ir import parse_syntax
        d=documents(packet('以甲法乘乙量'))[0];ts=tokenize_candidates(d,{})
        self.assertFalse(parse_syntax(ts,d).diagnostics)
        for bad in ([],[t for t in ts if t['text']!='乘']):self.assertTrue(parse_syntax(bad,d).diagnostics)
    def test_L07(self):
        from analysis_parser.construction_ir import parse_syntax
        d=documents(packet('以甲乘乙乘丙'))[0]
        ts=tokenize_candidates(d,{'甲乘乙':{},'乙乘丙':{}})
        self.assertTrue(any(x['kind']=='AmbiguousParse' for x in parse_syntax(ts,d).diagnostics))
    def test_L08(self):
        r=parse_packet(packet('置三，甲量盈六十'))
        self.assertTrue(any(x['kind']=='incomplete_construction' for x in r['diagnostics']))
    def test_L09(self):
        r=parse_packet(packet('置三，名曰甲量，置五，名曰乙量，未定其法，以二乘之'))
        self.assertTrue(all(any(k in v['labels'] for v in r['value_instances']) for k in ('甲量','乙量')))
        self.assertTrue(r['coverage']['unparsed_spans']);x=execute(r,{})
        e=[e for e in r['events'] if e['kind']=='multiply'][-1]
        self.assertNotIn(e['writes']['result'],x['values'])

class AmbiguityCoverageReview(unittest.TestCase):
    def test_complete_term_competes_with_suffix_composition(self):
        view=syntax('以甲法乘乙量并之',{'乙量并之':{}})
        nodes={n['id']:n for n in view['nodes']}
        root=nodes[view['roots'][0]]
        self.assertEqual(root['kind'],'AmbiguousParse')
        alternatives=[nodes[n] for n in root['children']]
        self.assertEqual({n['kind'] for n in alternatives},{'Multiply','Sequence'})
        whole=next(n for n in alternatives if n['kind']=='Multiply')
        self.assertEqual(nodes[whole['slots']['right']]['surface'],'乙量并之')
        self.assertTrue(any(d['kind']=='AmbiguousParse' for d in view['diagnostics']))
        self.assertEqual(view['token_coverage'][0]['status'],'unresolved')

    def test_ambiguous_composition_has_unresolved_coverage(self):
        view=syntax('以甲乘乙乘丙并之',{'甲乘乙':{},'乙乘丙':{}})
        nodes={n['id']:n for n in view['nodes']}
        root=nodes[view['roots'][0]]
        self.assertEqual(root['kind'],'AmbiguousParse')
        self.assertEqual([nodes[n]['kind'] for n in root['children']],['Sequence','Sequence'])
        self.assertEqual(view['token_coverage'],[{'analysis_range':[0,8],'status':'unresolved'}])

    def test_mixed_duration_coverage_owns_internal_comma_once(self):
        text='三日，四分之一';view=syntax(text)
        nodes={n['id']:n for n in view['nodes']}
        self.assertEqual(nodes[view['roots'][0]]['kind'],'MixedDuration')
        ownership=[0]*len(text)
        for region in view['token_coverage']:
            a,b=region['analysis_range']
            for i in range(a,b):ownership[i]+=1
        self.assertEqual(ownership,[1]*len(text))
        self.assertEqual(sum(b-a for a,b in (r['analysis_range'] for r in view['token_coverage'])),len(text))
