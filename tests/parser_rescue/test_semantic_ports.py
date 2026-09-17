import copy,json,unittest
from pathlib import Path
from analysis_parser.scoped import ScopedParser,lower_linked
from analysis_parser.program_ir import link_entry
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute


def conversion(title='甲課',denominator='日法',factor='月法'):
    packet={'schema_version':'3.0','provided_scope':{'tradition':'San_tong_li'},'primary_documents':[{'doc_id':'p','text':(f'推{title}，' if title else '')+f'置月數，以{factor}乘之，盈{denominator}得一，名曰甲量．'}],'context_documents':[{'doc_id':'d','text':f'{factor}二千三百九十二．{denominator}八十一．'}]}
    parser=ScopedParser(packet);linked=link_entry(parser.program,parser.program.definitions[0]['id'],{'月數':{'unit':'month'}})
    return lower_linked(linked,parser)

def development(n):
    p=json.loads(Path(f'evaluation/rescue-v3_1/development_packets/A0{n}.json').read_text());r=parse_packet(p['packet']);return p,r,execute(r,p['inputs'])

class Ports(unittest.TestCase):
    def test_T01(self):
        a=conversion('正月朔');b=conversion('無名課')
        def units(r):return [(e['kind'],[next(v['unit'] for v in r['value_instances'] if v['id']==vid) for vid in e['writes'].values()]) for e in r['events'] if e['kind'] in ('multiply','divmod')]
        self.assertEqual(units(a),units(b));self.assertEqual(execute(b,{'月數':81})['named_outputs']['main:甲量'],2392)
        nohead=conversion(None);self.assertEqual(units(b),units(nohead));self.assertFalse(execute(nohead,{'月數':81})['unresolved'])
    def test_T02(self):
        packet={'schema_version':'3.0','primary_documents':[{'doc_id':'mixed','text':'置甲量，加乙量．'}]};parser=ScopedParser(packet)
        linked=link_entry(parser.program,parser.program.definitions[0]['id'],{'甲量':{'unit':'month'},'乙量':{'unit':'day'}})
        report=lower_linked(linked,parser);self.assertTrue(any(u['cause']=='incompatible_quantity' for u in report['unresolved']));self.assertTrue(execute(report,{'甲量':1,'乙量':1})['unresolved'])
        good=conversion();bad=conversion(factor='甲法')
        self.assertFalse(execute(good,{'月數':81})['unresolved']);self.assertTrue(execute(bad,{'月數':81})['unresolved'])
    def test_T03(self):
        p,r,x=development(1);call=next(e for e in r['events'] if e['kind']=='method_call');wrong=copy.deepcopy(r)
        candidate=next(v for v in wrong['value_instances'] if v['id']==call['writes']['remainder']);self.assertEqual(x['values'][candidate['id']],x['values'][call['reads']['offset']])
        target=next(e for e in wrong['events'] if e['id']==call['id']);target['method_binding']['actuals']['offset']=candidate['id']
        self.assertTrue(any(u.get('event_id')==call['id'] for u in execute(wrong,p['inputs'])['unresolved']))
    def test_T04(self):
        from analysis_parser.quantity_semantics import check_transition
        values={'x':{'unit':'day','representation':{'denominator':81}},'y':{'unit':'day','representation':{'denominator':1539}}}
        event={'kind':'rescale','reads':{'value':'x'},'writes':{'result':'y'},'attributes':{'factor':19,'source_operation':'multiply','denominator_declaration':True,'evidence':[{'basis':'synthetic exact rational representation'}]}}
        self.assertEqual(check_transition(event,values,{})['status'],'resolved')
        wrong=copy.deepcopy(event);wrong['attributes']['factor']=1;self.assertEqual(check_transition(wrong,values,{})['status'],'inconsistent_representation')
        angular=copy.deepcopy(values);angular['y']['unit']='du';self.assertEqual(check_transition(event,angular,{})['status'],'requires_model_rate')
        p,r,x=development(3);values={v['id']:v for v in r['value_instances']};full=next(e['writes']['result'] for e in r['events'] if e['kind']=='alias' and e['attributes'].get('label')=='積次')
        reductions=[e for e in r['events'] if e['kind']=='cycle_reduce' and e['reads']['dividend']==full]
        self.assertEqual(len(reductions),2);self.assertEqual(values[full]['unit'],'station')
        self.assertEqual({x['values'][e['reads']['divisor']] for e in reductions},{12,60})
        removed=copy.deepcopy(p['packet']);removed['selected_profiles']=['ST_elapsed'];self.assertTrue(execute(parse_packet(removed),p['inputs'])['unresolved'])
    def test_T05(self):
        p,original,x=development(3);inclusive=copy.deepcopy(p['packet']);inclusive['selected_profiles'].append('C2017_ST_local_year_count_v1');inclusive['primary_documents'][0]['text']=inclusive['primary_documents'][0]['text'].replace('外所求年','盡所求年')
        converted=parse_packet(inclusive);y=execute(converted,p['inputs']);self.assertFalse(y['unresolved'])
        def year_remainder(report,result):
            values={v['id']:v for v in report['value_instances']}
            event=next(e for e in report['events'] if e['kind']=='cycle_reduce' and values[e['reads']['dividend']]['unit']=='year')
            return result['values'][event['writes']['remainder']]
        self.assertEqual(year_remainder(converted,y),year_remainder(original,x)+1)
        self.assertTrue(any(e['attributes'].get('local_phrase')=='盡所求年' for e in converted['events']))
        p,r,x=development(4);queries=[c for c in r['program']['calls'] if c.get('base_value_ids')]
        self.assertEqual(len(queries),2);self.assertEqual(queries[0]['base_value_ids'],queries[1]['base_value_ids'])
        values={v['id']:v for v in r['value_instances']};events={e['id']:e for e in r['events']};base=events[values[queries[0]['base_value_ids']['大餘']]['producer']]
        self.assertEqual(base['kind'],'initial_instant');self.assertEqual(events[values[base['reads']['head']]['producer']]['kind'],'alias')
        reuse=next(i for i in r['program']['imports'] if i.get('selected_role')=='increment');consumer=events[reuse['consumer_event_id']]
        self.assertEqual(consumer['reads']['right'],reuse['actual_value_id']);self.assertTrue(reuse['target_node_id'])
        reversed_packet=copy.deepcopy(p['packet']);reversed_packet['primary_documents'][0]['text']='推周至，加大餘五十九，小餘二十一．求篇，大餘亦如之，小餘加一．'
        reversed_packet['primary_documents'][0].pop('source_sha256',None)
        reverse=parse_packet(reversed_packet);rx=execute(reverse,p['inputs']);self.assertFalse(rx['unresolved'])
        def query_values(report,result):
            definitions={d['id']:d for d in report['program']['definitions']}
            return {definitions[c['definition_id']]['goal_surface']:{name:result['values'][port['value_id']] for name,port in c['return_ports'].items()} for c in report['program']['calls'] if c.get('base_value_ids')}
        self.assertEqual(query_values(r,x),query_values(reverse,rx))
        wrong=copy.deepcopy(p['inputs']);wrong['query_initial_rule_ordinal']=1;self.assertTrue(execute(r,wrong)['unresolved'])
