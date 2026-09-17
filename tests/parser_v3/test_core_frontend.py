import unittest
from analysis_parser.inputs import documents

class FrontendTests(unittest.TestCase):
    def candidates(self,text):
        from analysis_parser.lexical import tokenize_candidates
        from analysis_parser.construction_ir import propose_constructions
        doc=documents({'primary_documents':[{'doc_id':'synthetic','text':text}]})[0]
        return tokenize_candidates(doc,{}),propose_constructions(tokenize_candidates(doc,{}),doc)
    def test_add_seven_count_one_not_parameter(self):
        for n in ('七','五'):
            tokens,cs=self.candidates('加'+n+'得一．盈章中，數所得。')
            self.assertTrue(any(c['kind']=='update_count' and c['slots']['increment']['value'] in (7,5) for c in cs))
            self.assertFalse(any(t['text']==n+'得' for t in tokens))
        _,cs=self.candidates('加七。')
        self.assertFalse(any(c['kind']=='update_count' for c in cs))
    def test_triple_anaphoric_remainder(self):
        for n,v in [('三',3),('二',2)]:
            _,cs=self.candidates(n+'其小餘。')
            self.assertEqual(cs[0]['slots']['factor']['value'],v)
            self.assertEqual(cs[0]['slots']['value']['text'],'小餘')
        _,cs=self.candidates('第三其小餘。')
        self.assertFalse(any(c['kind']=='numeral_predicate' for c in cs))
    def test_mixed_duration_two_values(self):
        _,cs=self.candidates('七十三日，統法分之七十七．十八日，統法分之四百四．')
        mixed=[c for c in cs if c['kind']=='mixed_duration']
        self.assertEqual([c['slots']['whole']['value'] for c in mixed],[73,18])
        _,cs=self.candidates('七十三度，統法分之七十七日。')
        self.assertFalse(any(c['kind']=='mixed_duration' for c in cs))
    def test_cong_receiver_vs_origin(self):
        _,cs=self.candidates('從大餘，數從統首日起。')
        self.assertEqual([c['kind'] for c in cs],['receiver_add','count_origin'])
    def test_factor_term_vs_method_reference(self):
        _,cs=self.candidates('以統法乘甲，除數如法。')
        self.assertEqual(cs[0]['slots']['left']['text'],'統法')
        self.assertEqual(cs[1]['kind'],'method_reference')
    def test_repeated_exact_spans(self):
        _,cs=self.candidates('小餘千一十．小餘千一十．')
        self.assertEqual([c['source_spans'][0]['start'] for c in cs],[0,6])

class TransitionTests(unittest.TestCase):
    def check(self,kind,units=('day','day'),old=1539,new=4617,factor=3,rate=None):
        from analysis_parser.quantity_semantics import check_transition
        values={'x':{'unit':units[0],'representation':{'denominator':old}},'y':{'unit':units[1],'representation':{'denominator':new}}}
        e={'kind':kind,'reads':{'value':'x'},'writes':{'result':'y'},'attributes':{'factor':factor,'source_operation':'multiply','denominator_declaration':True,'evidence':[{'basis':'synthetic'}]}}
        return check_transition(e,values,{'rate':rate})
    def test_representation_requires_ratio(self):
        self.assertEqual(self.check('rescale')['status'],'resolved')
        self.assertEqual(self.check('rescale',new=3078)['status'],'inconsistent_representation')
    def test_arithmetic_triple_is_not_rescale(self):
        self.assertEqual(self.check('multiply',new=1539)['transition'],'arithmetic')
    def test_rate_and_model(self):
        self.assertEqual(self.check('rescale',units=('day','du'))['status'],'requires_model_rate')
        self.assertEqual(self.check('convert',units=('month','day'),rate={'from_unit':'month','to_unit':'day','numerator':27759,'denominator':940,'basis':'source'})['status'],'resolved')
        self.assertEqual(self.check('add',units=('day','du'))['status'],'incompatible_without_conversion')
    def test_unknown_is_not_compatible(self):
        self.assertEqual(self.check('rescale',units=('unknown','day'))['status'],'unknown')

class DeclarationBindingTests(unittest.TestCase):
    def test_compact_fraction_inherits_actual_declared_factor(self):
        from analysis_parser.pipeline import parse_packet
        from analysis_parser.execution import execute
        p={'schema_version':'3.0','primary_documents':[{'doc_id':'synthetic','text':'推五行，十八日，乙法分之四．冬至後，中央二十七日六分。'}],'context_documents':[{'doc_id':'denominator','text':'乙法十。'}]}
        r=parse_packet(p);x=execute(r,{})
        self.assertEqual(list(x['task_outputs']['declarations'].values())[-1],{'numerator':276,'denominator':10})
        p['primary_documents'][0]['text']='推五行，中央二十七日六分。'
        r=parse_packet(p)
        self.assertTrue(any(u['cause']=='missing_denominator' for u in r['unresolved']))
