import copy
import json
import unittest
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from analysis_parser.audit import audit
from test_core_composition import packet, PACKETS


class ReviewFixTests(unittest.TestCase):
    def test_f1_alias_uses_declaration_before_its_own_position(self):
        p=packet('以甲法乘甲，名曰乙。',['常數三，因為甲法，另數七。'])
        r=parse_packet(p);x=execute(r,{'甲':2})
        self.assertEqual(x['named_outputs']['main:乙'],6)
        alias=next(b for b in r['bindings'] if b['mention']=='甲法' and b['mention_span']['doc_id']=='0')
        self.assertTrue(any('常數三' in s['quote'] for s in alias['supporting_spans']))
        self.assertTrue(any('因為甲法' in s['quote'] for s in alias['supporting_spans']))
    def test_f1_unattached_alias_is_unresolved(self):
        r=parse_packet(packet('以甲法乘甲。',['因為甲法，常數三。']))
        self.assertTrue(any(u.get('reason')=='alias has no preceding declaration in its source scope' for u in r['unresolved']))
    def test_f2_explicit_load_replaces_current_carried_amount(self):
        r=parse_packet(packet('置甲，名曰小積。以乙除丙。置丁，從小積，名曰戊。'))
        x=execute(r,{'甲':10,'乙':3,'丙':8,'丁':7})
        self.assertEqual(x['named_outputs']['main:戊'],17)
        add=next(e for e in r['events'] if e['kind']=='add')
        values={v['id']:v for v in r['value_instances']};events={e['id']:e for e in r['events']}
        self.assertEqual(events[values[add['reads']['right']]['producer']]['kind'],'load')
    def test_f3_unscoped_incompatible_units_cannot_execute_as_bridge(self):
        r=parse_packet(packet('置甲，名曰積中。置乙，名曰積月。并積中，名曰丙。'))
        x=execute(r,{'甲':3,'乙':4})
        self.assertNotIn('main:丙',x['named_outputs'])
        self.assertTrue(any(u.get('reason')=='unsupported unit bridge' for u in r['unresolved']))
        add=next(e for e in r['events'] if e['kind']=='add')
        self.assertNotIn('unit_bridge',add['attributes'])
    def test_f3_bridge_requires_parameters_and_medial_structure(self):
        p=packet('置甲，名曰積中。置乙，名曰積月。并積中，名曰丙。',['章歲十九。','章月二百三十五。'])
        p['provided_scope']={'tradition':'San_tong_li','planet':'Jupiter'}
        r=parse_packet(p)
        self.assertNotIn('main:丙',execute(r,{'甲':3,'乙':4})['named_outputs'])
    def test_f3_development_bridge_has_real_scope_and_support(self):
        r=parse_packet(json.loads((PACKETS/'W03.json').read_text()))
        add=next(e for e in r['events'] if e['kind']=='add' and 'unit_bridge' in e['attributes'])
        bridge=add['attributes']['unit_bridge']
        self.assertTrue(add.get('supporting_spans'))
        self.assertTrue(bridge.get('supporting_value_ids'))
        self.assertTrue(bridge.get('medial_cycle'))
        self.assertEqual(add['evidence_status'],'scholarly_calibrated')
        self.assertEqual(execute(r,{'定見復數':131126})['named_outputs']['main:積月'],1770377)
    def test_f4_known_wrong_remainder_type_is_rejected_with_evidence(self):
        r=parse_packet(packet('置甲，盈章歲得一，不盈者名曰小餘。',['章歲十九。']))
        self.assertNotIn('main:小餘',execute(r,{'甲':20})['named_outputs'])
        b=next(b for b in r['bindings'] if b['mention']=='remainder')
        self.assertIsNone(b['selected'])
        self.assertTrue(b['candidates'])
        self.assertTrue(all(not c['accepted'] for c in b['candidates']))
        self.assertTrue(any('day_fraction' in c['rejection_reason'] for c in b['candidates']))
    def test_f4_unknown_unit_does_not_count_as_known_incompatibility(self):
        r=parse_packet(packet('置甲，以乙除之，餘名曰丙。'))
        self.assertEqual(execute(r,{'甲':8,'乙':3})['named_outputs']['main:丙'],2)
    def test_f5_missing_cycle_is_explicit_and_executor_does_not_raise(self):
        r=parse_packet(packet('置甲，中數從冬至起，算外。'))
        self.assertTrue(any('count_cycle' in str(u['missing_or_conflicting_inputs']) for u in r['unresolved']))
        x=execute(r,{'甲':2})
        self.assertTrue(x['unresolved'])
        self.assertNotIn('main:medial_ordinal',x['named_outputs'])
    def test_f5_audit_and_execution_validate_conditional_cycle_port(self):
        r=parse_packet(json.loads((PACKETS/'W03.json').read_text()))
        broken=copy.deepcopy(r)
        count=next(e for e in broken['events'] if e['kind']=='count' and e['attributes'].get('cyclic'))
        count['reads'].pop('cycle')
        self.assertTrue(any(d['kind']=='missing_read_port' and d['event_id']==count['id'] for d in audit(broken)))
        x=execute(broken,{'定見復數':131126})
        self.assertTrue(any(u['event_id']==count['id'] and u['cause']=='invalid_event_contract' for u in x['unresolved']))
