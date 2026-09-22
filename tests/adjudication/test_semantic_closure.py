"""Artificial vocabulary: candidates and primitive shape confer no authority."""
from copy import deepcopy
import unittest

from adjudication.semantic_closure import compute_semantic_closure


def fixture():
    def span(start, end):
        return dict(doc_id='invented', reading_id='edition', start=start, end=end, quote='xyz')
    first, last = span(0, 4), span(5, 9)
    graph = {'events': [
        dict(id='root', kind='input', reads={}, writes={'result': 'a'}, source_spans=[first]),
        dict(id='load', kind='load', reads={'value': 'a'}, writes={'result': 'b'}, syntax_node_id='s1', source_spans=[first]),
        dict(id='one', kind='literal', reads={}, writes={'result': 'n'}, attributes={'value': 1}, source_spans=[first]),
        dict(id='sub', kind='subtract', reads={'left': 'b', 'right': 'n'}, writes={'result': 'c'}, syntax_node_id='s1', source_spans=[first]),
        dict(id='alias', kind='alias', reads={'value': 'c'}, writes={'result': 'd'}, syntax_node_id='s2', source_spans=[last]),
    ], 'value_instances': [dict(id=v, producer=p, output_port='result', unit='unknown')
                            for v, p in [('a', 'root'), ('b', 'load'), ('n', 'one'), ('c', 'sub'), ('d', 'alias')]],
        'construction_candidates': [
            dict(node_id='s1', kind='load', status='selected', source_spans=[first], slots={'value': {'kind': 'Term', 'source_spans': [span(1, 3)]}}),
            dict(node_id='s2', kind='name', status='selected', source_spans=[last], slots={'label': {'kind': 'Term', 'source_spans': [span(7, 9)]}})]}
    effective = {'quantity_semantics': {'review': {
        'decision_id': 'human-Q', 'semantic_output': {'construction_anchor': first, 'semantic_role': 'load', 'output_port': 'result'},
        'facets': dict(coordinate_kind='ordinal', index_base=1, step_unit='month', reference_origin='synthetic-origin', counting_boundary='start_of_current_month')}},
        'term_interpretations': []}
    return graph, effective


def facts(result, kind='quantity', target='c'):
    return {a['facet']: a['value'] for a in result['assertions'] if a['kind'] == kind
            and a['target'].get('value_id') == target and a['authority'] == 'derived' and a['usable']}


class SemanticClosureTests(unittest.TestCase):
    def test_ordinal_and_alias_are_derived_with_real_dependencies(self):
        graph, effective = fixture()
        result = compute_semantic_closure(graph, effective)
        self.assertEqual(result['schema'], 'SemanticClosure/1')
        self.assertEqual(facts(result)['coordinate_kind'], 'elapsed')
        self.assertEqual(facts(result)['index_base'], 0)
        self.assertEqual(facts(result, target='d')['unit'], 'month')
        self.assertTrue(any(r['rule_id'] == 'SEM_ORDINAL_TO_ELAPSED' for r in result['assertions']))
        self.assertTrue(all(r['depends_on'] for r in result['assertions']))
        self.assertFalse(any(r['kind'] == 'term' and r['authority'] == 'derived' for r in result['assertions']))

    def test_same_shape_incompatible_or_incomplete_coordinates(self):
        for change in ({'index_base': 0}, {'unit': 'day'}, {'representation': {'kind': 'fraction_numerator'}}):
            graph, effective = fixture()
            effective['quantity_semantics']['review']['facets'].update(change)
            self.assertNotIn('coordinate_kind', facts(compute_semantic_closure(graph, effective)))
        graph, effective = fixture()
        del effective['quantity_semantics']['review']['facets']['reference_origin']
        self.assertEqual(facts(compute_semantic_closure(graph, effective)), {})

    def test_replay_retraction_and_no_input_mutation(self):
        graph, effective = fixture()
        original = deepcopy((graph, effective))
        a = compute_semantic_closure(graph, effective)
        self.assertEqual(a, compute_semantic_closure(graph, effective))
        self.assertEqual((graph, effective), original)
        effective['quantity_semantics'] = {}
        self.assertEqual(compute_semantic_closure(graph, effective)['assertions'], [])

    def test_rename_invariance(self):
        graph, effective = fixture()
        original = compute_semantic_closure(graph, effective)
        def rename(value):
            if isinstance(value, list):
                return [rename(v) for v in value]
            if isinstance(value, dict):
                return {k: ('another' if k in ('doc_id', 'quote', 'tradition', 'procedure_id') else rename(v)) for k,v in value.items()}
            return value
        other = compute_semantic_closure(rename(graph), rename(effective))
        shape = lambda r: sorted((a['kind'], a['facet'], str(a['value']), a['authority'], a['rule_id']) for a in r['assertions'])
        self.assertEqual(shape(original), shape(other))

    def test_single_candidate_uniqueness_truncation_do_not_seed(self):
        graph, _ = fixture()
        graph['kernel_candidates'] = [{'expression': {'op': 'concept', 'concept_id': 'invented'}, 'constraint_status': 'compatible'}]
        graph['truncated'] = True
        self.assertEqual(compute_semantic_closure(graph, {})['assertions'], [])

    def test_conflict_preserves_review_and_quarantines_descendants(self):
        graph, effective = fixture()
        effective['quantity_semantics']['other'] = {'decision_id': 'human-other',
            'semantic_output': {'construction_anchor': graph['events'][3]['source_spans'][0], 'semantic_role': 'subtract', 'output_port': 'result'},
            'facets': {'coordinate_kind': 'cyclic'}}
        result = compute_semantic_closure(graph, effective)
        self.assertTrue(result['conflicts'])
        self.assertNotIn('coordinate_kind', facts(result, target='d'))
        self.assertEqual(facts(result, target='d')['unit'], 'month')
        self.assertTrue(any(a['authority'] == 'reviewed' and a['value'] == 'cyclic' for a in result['assertions']))

    def test_unseeded_cycle_cannot_self_support(self):
        graph, _ = fixture()
        graph['events'][1]['reads']['value'] = 'd'
        self.assertEqual(compute_semantic_closure(graph, {})['assertions'], [])

    def test_conflicted_review_record_cannot_poison_independent_equal_facet(self):
        graph, effective = fixture()
        address = effective['quantity_semantics']['review']['semantic_output']
        conflict = {'decision_id': 'inactive', 'action': 'set_quantity_semantics',
                    'payload': {'semantic_output': address, 'facets': {'step_unit': 'month'}}, 'targets': []}
        result = compute_semantic_closure(graph, effective, conflicted_decisions=[conflict])
        self.assertEqual(facts(result)['coordinate_kind'], 'elapsed')
        rows = [a for a in result['assertions'] if a['authority'] == 'reviewed' and a['facet'] == 'step_unit']
        self.assertEqual(len(rows), 2)
        self.assertEqual({a['usable'] for a in rows}, {True, False})
        index = {a['id']: a for a in result['assertions']}
        for a in result['assertions']:
            if a['usable']:
                self.assertTrue(all(index[d['id']]['usable'] for d in a['depends_on'] if d['kind'] == 'assertion'))

    def test_exact_term_load_and_naming_entail_expression_not_candidate_elimination(self):
        graph, effective = fixture()
        graph['events'][4]['reads']['value'] = 'b'  # direct identity, no arithmetic meaning invented
        anchor = graph['construction_candidates'][0]['slots']['value']['source_spans'][0]
        expression = {'op': 'concept', 'concept_id': 'fictional.quantity'}
        effective['term_interpretations'] = [{'decision_id': 'human-T', 'target': anchor,
            'claim': {'anchor': anchor, 'origin': 'human_composition', 'expression': expression}}]
        result = compute_semantic_closure(graph, effective)
        terms = [a for a in result['assertions'] if a['kind'] == 'term' and a['authority'] == 'derived' and a['usable']]
        self.assertEqual(len(terms), 1)
        self.assertEqual(terms[0]['value'], expression)
        self.assertEqual(terms[0]['target']['anchor']['start'], 7)
        self.assertFalse(any(a['facet'] == 'expression' and a['target'].get('value_id') == 'a' for a in result['assertions']))

    def test_ambiguous_exact_link_does_not_guess(self):
        graph, effective = fixture()
        graph['events'].append({**graph['events'][1], 'id': 'second-use'})
        anchor = graph['construction_candidates'][0]['slots']['value']['source_spans'][0]
        effective['term_interpretations'] = [{'decision_id': 'T', 'target': anchor,
            'claim': {'anchor': anchor, 'origin': 'human_composition', 'expression': {'op': 'concept', 'concept_id': 'fictional'}}}]
        result = compute_semantic_closure(graph, effective)
        self.assertTrue(any(a['reason'] == 'term_graph_link_not_unique' for a in result['unresolved']))
        self.assertFalse(any(a['facet'] == 'expression' and a['kind'] == 'quantity' for a in result['assertions']))

    def test_rejected_expression_is_not_resurrected(self):
        graph, effective = fixture()
        graph['events'][4]['reads']['value'] = 'b'
        first = graph['construction_candidates'][0]['slots']['value']['source_spans'][0]
        last = graph['construction_candidates'][1]['slots']['label']['source_spans'][0]
        expression = {'op': 'concept', 'concept_id': 'fictional'}
        effective['term_interpretations'] = [
            {'decision_id': 'T', 'target': first, 'claim': {'anchor': first, 'origin': 'human_composition', 'expression': expression}},
            {'decision_id': 'R', 'target': last, 'claim': {'anchor': last, 'origin': 'machine_rejection', 'candidate_snapshots': [{'expression': expression}]}}]
        result = compute_semantic_closure(graph, effective)
        self.assertTrue(result['conflicts'])
        self.assertFalse(any(a['kind'] == 'term' and a['authority'] == 'derived' and a['usable'] for a in result['assertions']))

    def test_remainder_name_uses_exact_port_without_inheriting_quotient(self):
        graph, effective = fixture()
        event = graph['events'][3]
        event.update(kind='divmod', writes={'quotient': 'c', 'remainder': 'r'})
        graph['value_instances'].append({'id': 'r', 'producer': event['id'], 'output_port': 'remainder'})
        graph['construction_candidates'][1]['kind'] = 'remainder_name'
        graph['events'][4]['reads']['value'] = 'r'
        anchor = graph['construction_candidates'][1]['slots']['label']['source_spans'][0]
        effective['term_interpretations'] = [{'decision_id': 'remainder-meaning', 'target': anchor,
            'claim': {'anchor': anchor, 'origin': 'human_composition', 'expression': {'op': 'concept', 'concept_id': 'fictional.residue'}}}]
        result = compute_semantic_closure(graph, effective)
        self.assertTrue(any(a['facet'] == 'expression' and a['target'].get('value_id') == 'd' for a in result['assertions']))
        self.assertFalse(any(a['facet'] == 'expression' and a['target'].get('value_id') in ('b', 'c', 'r') for a in result['assertions']))
