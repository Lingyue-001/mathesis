"""Candidate behavior, source fidelity and negative authority contracts."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tracemalloc
import unittest
from unittest.mock import patch

from analysis_parser.inputs import documents

ROOT = Path(__file__).resolve().parents[2]


def make_doc(text, **kwargs):
    return documents({'primary_documents': [{'doc_id': 'test', 'text': text, **kwargs}]})[0]


def anchor(doc, start, end):
    return {key: doc[key] for key in ('doc_id', 'reading_id')} | {
        'source_sha256': doc['actual_sha256'], 'start': start, 'end': end,
        'quote': doc['text'][start:end]}


def concept(name):
    return {'op': 'concept', 'concept_id': name}


def rehash(bundle):
    """Corrupt-data tests must reach semantic guards, not just checksum guards."""
    remap = {}
    ordered = sorted(bundle['candidates'], key=lambda n: n['span']['end'] - n['span']['start'])
    for node in ordered + bundle['fixed_expression_candidates']:
        old = node['id']
        if 'child_ids' in node:
            node['child_ids'] = [remap.get(c, c) for c in node['child_ids']]
        content = {'identity': bundle['identity'], 'node': {k: v for k, v in node.items() if k != 'id'}}
        node['id'] = 'term:' + hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        remap[old] = node['id']


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = importlib.import_module('domain_kernel.engine')

    def test_constructor_relations_are_semantic_and_not_composition_edges(self):
        registry = self.engine.load_kernel()
        relations = {row['id']: row for row in registry['relations']}
        for constructor in registry['constructors']:
            self.assertEqual(relations[constructor['relation_kind']]['layer'], 'semantic', constructor['id'])
        self.assertEqual(relations['has_part']['layer'], 'term_composition')
        self.assertEqual(next(c for c in registry['constructors'] if c['id'] == 'accumulation')['relation_kind'],
                         'associated_with')
        doc, current = self.output('積月')
        previous = copy.deepcopy(registry)
        next(c for c in previous['constructors'] if c['id'] == 'accumulation')['relation_kind'] = 'has_part'
        old = self.engine.suggest_term_semantics(doc, registry=previous, term_regions=(anchor(doc, 0, 2),))
        self.assertNotEqual(current['identity']['registry_sha256'], old['identity']['registry_sha256'])
        def meanings(bundle):
            nodes = {n['id']: n for n in bundle['candidates']}
            return sorted(json.dumps([n['expression'], [nodes[c]['span'] for c in n['child_ids']]],
                                     ensure_ascii=False, sort_keys=True) for n in nodes.values())
        self.assertEqual(meanings(current), meanings(old))
        self.assertFalse({n['id'] for n in current['candidates']} & {n['id'] for n in old['candidates']})

    def output(self, text, **kwargs):
        doc = make_doc(text)
        return doc, self.engine.suggest_term_semantics(doc, term_regions=(anchor(doc, 0, len(text)),), **kwargs)

    def test_nested_composition_without_terms(self):
        doc = make_doc('入蔀積月')
        before = copy.deepcopy(doc)
        with patch('analysis_parser.lexical.TERMS', ()):
            out = self.engine.suggest_term_semantics(doc, term_regions=(anchor(doc, 0, 4),))
        expression = {'op': 'localized_quantity', 'arguments': {
            'scope': concept('scope.bu'), 'quantity': {'op': 'accumulation',
            'arguments': {'quantity': concept('time.month')}}}}
        roots = [n for n in out['candidates'] if n['expression'] == expression]
        self.assertTrue(roots)
        nodes = {n['id']: n for n in out['candidates']}
        for n in roots:
            self.assertEqual([nodes[c]['span']['quote'] for c in n['child_ids']], ['入', '蔀', '積月'])
            self.assertEqual(nodes[n['child_ids'][2]]['rule_id'], 'C01')
        self.assertEqual(doc, before)
        self.engine.validate_term_bundle(out, doc)

    def test_registry_rules_are_consumed_and_input_is_unchanged(self):
        registry = self.engine.load_kernel()
        for name in ('scoped_facts', 'human_actions', 'authority_rules'):
            self.assertNotIn(name, registry)
        before = copy.deepcopy(registry)
        _, original = self.output('積月', registry=registry)
        self.assertEqual(registry, before)
        registry['composition_rules'] = [r for r in registry['composition_rules'] if r['id'] != 'C01']
        _, changed = self.output('積月', registry=registry)
        self.assertTrue(any(n['expression']['op'] == 'accumulation' for n in original['candidates']))
        self.assertFalse(any(n['expression']['op'] == 'accumulation' for n in changed['candidates']))
        self.assertNotEqual(original['identity']['registry_sha256'], changed['identity']['registry_sha256'])

    def test_synthetic_substitutions_share_the_rules(self):
        for text, op, cid in [('積日', 'accumulation', 'time.day'), ('積度', 'accumulation', 'measure.du'),
                              ('入紀日', 'localized_quantity', 'time.day')]:
            with self.subTest(text=text), patch('analysis_parser.lexical.TERMS', ()):
                _, out = self.output(text)
                self.assertTrue(any(n['expression']['op'] == op and
                                    n['expression']['arguments']['quantity'] == concept(cid) for n in out['candidates']))

    def test_all_authored_probe_derivations_are_generated(self):
        suite = json.loads((ROOT/'tests/fixtures/domain_kernel/paper-probes.json').read_text(encoding='utf-8'))
        for probe in suite['probes']:
            for original in probe['documents']:
                doc = documents({'primary_documents': [original]})[0]
                expected = [n for n in probe['authored_expected_nodes'] if n['span']['doc_id'] == doc['doc_id']]
                regions = tuple({json.dumps(n['span'], sort_keys=True): n['span'] for n in expected if n['method'] == 'composition'}.values())
                with self.subTest(probe=probe['id'], doc=doc['doc_id']), patch('analysis_parser.lexical.TERMS', ()):
                    out = self.engine.suggest_term_semantics(doc, term_regions=regions)
                    actual = out['candidates']; by_id = {n['id']: n for n in actual}
                    authored = {n['id']: n for n in expected}
                    for n in expected:
                        matches = [c for c in actual if c['span'] == n['span'] and c['expression'] == n['expression'] and c['rule_id'] == n['rule_id']]
                        self.assertTrue(matches, (probe['id'], n['id']))
                        self.assertTrue(any([by_id[c]['expression'] for c in match['child_ids']] ==
                                            [authored[c]['expression'] for c in n['child_ids']] for match in matches))
                    self.engine.validate_term_bundle(out, doc)
                    self.assertEqual(original['text'], doc['text'])

    def test_p05_uses_native_grammar_preview_and_preserves_polysemy(self):
        doc = make_doc('以日率乘月率')
        with patch('analysis_parser.lexical.TERMS', ()):
            out = self.engine.suggest_term_semantics(doc)
        nodes = {n['id']: n for n in out['syntax_preview']['nodes']}
        mul = next(n for n in nodes.values() if n.get('lowering_kind') == 'multiply')
        self.assertEqual({k: nodes[v]['surface'] for k, v in mul['slots'].items()}, {'left': '日率', 'right': '月率'})
        for word, senses in [('日率', ['body.sun', 'time.day']), ('月率', ['body.moon', 'time.month'])]:
            for sense in senses:
                self.assertTrue(any(n['span']['quote'] == word and n['expression'] ==
                    {'op': 'rate_for', 'arguments': {'associate': concept(sense)}} for n in out['candidates']))
        self.assertTrue(all(r['basis'] == 'grammar_candidate' for r in out['regions']))

    def test_no_region_does_not_invent_nominality(self):
        out = self.engine.suggest_term_semantics(make_doc('入蔀積月'))
        self.assertFalse(any(n['method'] == 'composition' for n in out['candidates']))
        self.assertTrue(any(d['kind'] == 'missing_term_region' for d in out['diagnostics']))

    def test_unknown_stays_semantic_and_never_becomes_scope_or_quantity(self):
        _, out = self.output('中法')
        self.assertTrue(any(n['expression'] == {'op': 'factor_for', 'arguments': {
            'associate': {'op': 'unknown', 'source_text': '中', 'sort': 'semantic_expression'}}} for n in out['candidates']))
        for text in ('積中', '入中月'):
            _, out = self.output(text)
            self.assertFalse(any(n['expression']['op'] in ('accumulation', 'localized_quantity') for n in out['candidates']))

    def test_all_rules_have_observable_effect_without_whole_terms(self):
        examples = [('積月', 'C01'), ('日餘', 'C02'), ('日法', 'C03'), ('月率', 'C04'),
                    ('日分', 'C05'), ('入紀日', 'C06'), ('蔀月', 'C07'), ('月數', 'C09')]
        for text, rule_id in examples:
            with self.subTest(rule=rule_id), patch('analysis_parser.lexical.TERMS', ()):
                _, out = self.output(text)
                self.assertTrue(any(n['rule_id'] == rule_id for n in out['candidates']))
                registry = self.engine.load_kernel()
                registry['composition_rules'] = [r for r in registry['composition_rules'] if r['id'] != rule_id]
                _, without = self.output(text, registry=registry)
                self.assertFalse(any(n['rule_id'] == rule_id for n in without['candidates']))

    def test_p06_readings_preserve_constants_and_remain_independent(self):
        suite = json.loads((ROOT/'tests/fixtures/domain_kernel/paper-probes.json').read_text(encoding='utf-8'))
        probe = next(p for p in suite['probes'] if p['id'] == 'P06')
        packet = {'primary_documents': copy.deepcopy(probe['documents'])}
        before = copy.deepcopy(packet)
        docs = documents(packet)
        out = self.engine.suggest_packet_semantics(packet, term_regions={d['doc_id']: [anchor(d, 0, 2)] for d in docs})
        self.assertEqual(packet, before)
        self.assertIn('四十二', packet['primary_documents'][0]['text'])
        self.assertIn('三十二', packet['primary_documents'][1]['text'])
        first, second = (out[k] for k in ('P06.repo', 'P06.edited'))
        self.assertFalse({n['id'] for n in first['candidates']} & {n['id'] for n in second['candidates']})
        self.assertTrue(any(n['expression'] == {'op': 'factor_for', 'arguments': {'associate': concept('time.day')}}
                            for n in out['P06.fa']['candidates']))

    def test_no_cross_punctuation_operation_or_editorial_gap(self):
        for text in ('積，月', '積乘月', '積(刪)月'):
            _, out = self.output(text)
            self.assertFalse(any(n['expression']['op'] == 'accumulation' for n in out['candidates']))
        doc, out = self.output('積 \n月')
        self.assertTrue(any(n['expression']['op'] == 'accumulation' for n in out['candidates']))
        self.engine.validate_term_bundle(out, doc)

    def test_unicode_occurrences_readings_and_determinism(self):
        doc = make_doc('𠀀。積月。積月')
        regions = (anchor(doc, 2, 4), anchor(doc, 5, 7))
        first = self.engine.suggest_term_semantics(doc, term_regions=regions)
        self.assertEqual(first, self.engine.suggest_term_semantics(doc, term_regions=regions))
        roots = [n for n in first['candidates'] if n['expression'] == {'op': 'accumulation', 'arguments': {'quantity': concept('time.month')}}]
        self.assertEqual({n['span']['start'] for n in roots}, {2, 5})
        self.assertEqual(len({n['id'] for n in roots}), 2)
        changed = make_doc(doc['text'], reading_id='another')
        other = self.engine.suggest_term_semantics(changed, term_regions=(anchor(changed, 2, 4),))
        self.assertFalse({n['id'] for n in roots} & {n['id'] for n in other['candidates']})

    def test_truncation_is_explicit_and_never_authorizes(self):
        _, out = self.output('入蔀積月', max_candidates=3)
        self.assertTrue(out['truncated'])
        self.assertLessEqual(len(out['candidates']) + len(out['fixed_expression_candidates']), 3)
        self.assertTrue(any(d['kind'] == 'candidate_limit' for d in out['diagnostics']))
        for n in out['candidates']:
            self.assertEqual((n['support_status'], n['claim_authority'], n['authorization_status'], n['authorization_refs']),
                             ('proposed', 'S', 'not_authorized', []))

    def test_fixed_expression_is_a_proposal_not_a_literal(self):
        out = self.engine.suggest_term_semantics(make_doc('實如法而一'))
        self.assertEqual(out['fixed_expression_candidates'][0]['proposes'], 'division_construction')
        self.assertNotIn('numeric_value', out['fixed_expression_candidates'][0])

    def test_validator_rejects_corrupt_identity_structure_and_authority(self):
        doc, out = self.output('入蔀積月')
        def root(bundle):
            return next(n for n in bundle['candidates'] if n['rule_id'] == 'C06')
        changes = [lambda b: b['identity'].update(source_sha256='0'*64),
                   lambda b: root(b)['span'].update(quote='錯'),
                   lambda b: root(b)['child_ids'].reverse(),
                   lambda b: root(b)['child_ids'].__setitem__(0, 'missing'),
                   lambda b: root(b)['expression']['arguments'].update(extra=concept('time.day')),
                   lambda b: root(b)['expression']['arguments'].update(quantity=concept('missing')),
                   lambda b: root(b).update(unit='month'),
                   lambda b: root(b).update(authorization_status='authorized'),
                   lambda b: root(b).update(support_status='supported'),
                   lambda b: root(b).update(region_ids=[])]
        for change in changes:
            altered = copy.deepcopy(out); change(altered); rehash(altered)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.engine.validate_term_bundle(altered, doc)
        reordered = copy.deepcopy(out); reordered['candidates'].reverse()
        self.engine.validate_term_bundle(reordered, doc)

    def test_fixed_validator_rejects_rehashed_contract_and_authority_changes(self):
        doc = make_doc('實如法而一')
        out = self.engine.suggest_term_semantics(doc)
        for mutate in (lambda n: n.update(numeric_value=1), lambda n: n.pop('alternative_group'),
                       lambda n: n.update(alternative_group='invented'), lambda n: n.update(provenance_ids=[])):
            changed = copy.deepcopy(out); mutate(changed['fixed_expression_candidates'][0]); rehash(changed)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.engine.validate_term_bundle(changed, doc)
        changed = copy.deepcopy(out)
        changed['fixed_expression_candidates'] *= 2
        with self.assertRaises(ValueError):
            self.engine.validate_term_bundle(changed, doc)

    def test_region_provenance_must_resolve_to_actual_selection_or_syntax(self):
        doc, out = self.output('積月')
        for basis in ('explicit_selection', 'grammar_candidate'):
            changed = copy.deepcopy(out)
            changed['identity']['options']['term_regions'] = []
            for region in changed['regions']:
                old = region['id']; region['basis'] = basis
                if basis == 'grammar_candidate':
                    region['origins'] = [{'parent_id': 'absent', 'node_id': 'absent', 'slot': 'value'}]
                region['id'] = 'region:' + hashlib.sha256(json.dumps({k: v for k, v in region.items() if k != 'id'},
                    ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                for node in changed['candidates']:
                    node['region_ids'] = [region['id'] if r == old else r for r in node['region_ids']]
            rehash(changed)
            with self.subTest(basis=basis), self.assertRaisesRegex(ValueError, 'region'):
                self.engine.validate_term_bundle(changed, doc)
        changed = copy.deepcopy(out); changed['syntax_preview'] = {}
        with self.assertRaises(ValueError):
            self.engine.validate_term_bundle(changed, doc)

    def test_candidate_limit_avoids_quadratic_interval_allocation(self):
        # Punctuation keeps existing grammar work linear; a wide explicit region
        # must not allocate all subintervals after its single-candidate budget.
        tracemalloc.start()
        try:
            _, out = self.output('日。' * 500, max_candidates=1)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertTrue(out['truncated'])
        self.assertLess(peak, 20 * 1024 * 1024, 'candidate cap allocated a quadratic chart')

    def test_packet_rejects_duplicate_unknown_and_wrong_reading_regions(self):
        packet = {'primary_documents': [{'doc_id': 'x', 'text': '積月'}]}
        for changed, regions in [(dict(packet, context_documents=packet['primary_documents']), None),
                                 (packet, {'absent': []})]:
            with self.assertRaises(ValueError):
                self.engine.suggest_packet_semantics(changed, term_regions=regions)
        doc = documents(packet)[0]; region = anchor(doc, 0, 2); region['reading_id'] = 'wrong'
        with self.assertRaises(ValueError):
            self.engine.suggest_packet_semantics(packet, term_regions={'x': [region]})

    def test_schema_offline_and_shared_axes(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        schema = json.loads((ROOT/'domain_kernel/kernel.schema.json').read_text(encoding='utf-8'))
        output = json.loads((ROOT/'domain_kernel/output.schema.json').read_text(encoding='utf-8'))
        resources = Registry().with_resources([(schema['$id'], Resource.from_contents(schema)),
            ((ROOT/'domain_kernel/kernel.schema.json').as_uri(), Resource.from_contents(schema)),
            (output['$id'].rsplit('/', 1)[0]+'/kernel.schema.json', Resource.from_contents(schema))])
        validator = Draft202012Validator(output, registry=resources)
        _, bundle = self.output('入蔀積月'); validator.validate(bundle)
        node = copy.deepcopy(bundle['candidates'][0]); node.update(support_status='supported', constraint_status='underdetermined')
        shared = Draft202012Validator({'$defs': schema['$defs'], '$ref': '#/$defs/SemanticCandidate'})
        shared.validate(node)
        node.update(authorization_status='authorized', claim_authority='A')
        self.assertFalse(shared.is_valid(node))
        node.update(authorization_refs=['decision:test'], constraint_status='compatible')
        shared.validate(node)
        altered = copy.deepcopy(bundle); altered['candidates'][0] = node
        self.assertFalse(validator.is_valid(altered))

    def test_engine_isolated_from_compilers_resources_and_fixtures(self):
        script = '''
import sys, builtins
class Block:
 def find_spec(self, fullname, *args):
  if fullname.startswith(('analysis_parser.pipeline','analysis_parser.scoped','analysis_parser.resources','adjudication','evaluation')):
   raise AssertionError('forbidden import: '+fullname)
sys.meta_path.insert(0, Block())
def audit(event, args):
 if event == 'open' and isinstance(args[0], (str, bytes)):
  path = str(args[0]).replace(chr(92), '/')
  if any(s in path for s in ('paper-probes','/fixtures/','/evaluation/','/reports/')):
   raise AssertionError('forbidden read: '+path)
sys.addaudithook(audit)
from analysis_parser.inputs import documents
from analysis_parser import lexical
lexical.TERMS=()
from domain_kernel.engine import suggest_term_semantics
doc=documents({'primary_documents':[{'doc_id':'x','text':'置入蔀積月'}]})[0]
out=suggest_term_semantics(doc)
assert any(n['rule_id']=='C06' for n in out['candidates'])
'''
        result = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', script], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
