import copy,json,unittest
from pathlib import Path
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
ROOT=Path(__file__).resolve().parents[2]
def packet(tradition='ST'):
    p=json.loads((ROOT/'handoff_v3/runtime_inputs'/f'{tradition}_CIVIL_CORE.json').read_text())
    p['selected_profiles']=['ST_elapsed','ST_intercalation_Cullen_Liu_GT'] if tradition=='ST' else ['SF_Liu_inclusive','SF_completed_four']
    return p
class ScopedTests(unittest.TestCase):
    def test_numerical_actual_graph(self):
        cases=json.loads((ROOT/'handoff_v3/reference/numerical_cases.json').read_text())['cases']
        for case in cases:
            with self.subTest(case=case['id']):
                p=packet('SF' if 'epoch_inclusive_year' in case['inputs'] else 'ST');r=parse_packet(p);x=execute(r,case['inputs'])
                outputs={k:v for task in x['task_outputs'].values() for k,v in task.items()}
                for k,v in case['expected'].items():self.assertEqual(outputs.get(k),v,k)
                self.assertFalse([u for u in x['unresolved'] if u['cause']!='requires_external_data'],x['unresolved'])
    def test_sf_row_changes_and_boundaries(self):
        r=parse_packet(packet('SF'))
        for y,u in zip([1,76,77,1520,1521,4560,4561],[1,76,1,76,1,76,1]):
            x=execute(r,{'epoch_inclusive_year':y});self.assertEqual(x['task_outputs']['era_entry']['years_into_obscuration'],u)
        x=execute(r,{'epoch_inclusive_year':78})
        self.assertEqual(x['task_outputs']['era_entry']['head_day'],40)
        self.assertEqual(x['task_outputs']['era_entry']['obscuration_row'],2)
    def test_method_definition_removed(self):
        p=packet();p['primary_documents']=[d for d in p['primary_documents'] if '推冬至' in d['text']]
        r=parse_packet(p)
        self.assertTrue(any(x.get('cause')=='missing_method' for x in r['unresolved']))
    def test_edition_fields_mark_exact_edit(self):
        r=parse_packet(packet());e=next(e for e in r['events'] if any('加七得一' in s['quote'] for s in e['source_spans']))
        self.assertTrue(any(s.get('editorial_provenance') for s in e['source_spans']))
