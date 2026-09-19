"""Optional suggestions must not change either native compilation path."""
import copy
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from analysis_parser.inputs import documents
from source_adapters.corpus import build_source_packet_from_units, build_source_packet, list_procedures
from tools.parser_inspector import runner, readable
from domain_kernel import engine

ROOT = Path(__file__).resolve().parents[2]


def term_section(html):
    match = re.search(r'<section id="term-semantics">.*?</section>', html, re.S)
    return match.group() if match else ''


class TermSemanticsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name)/'current'
        self.patcher = patch.object(runner, 'OUTPUT', self.output)
        self.patcher.start(); self.addCleanup(self.patcher.stop)

    def packet(self, section=39):
        return build_source_packet_from_units(ROOT, 'sifen', [f'sifen:section:{section}'], [], {'tradition': 'Han_Si_fen_li'})

    def assert_native_equal(self, plain, extra):
        for key in plain:
            if key == 'run.json':
                state = copy.deepcopy(extra[key]); state.pop('term_semantics', None)
                self.assertEqual(plain[key], state)
            else:
                self.assertEqual(plain[key], extra[key], key)

    def test_native_reports_artifacts_html_and_both_entrypoints(self):
        for section in (38, 39, 41, 40):
            with self.subTest(section=section):
                packet = self.packet(section); before = copy.deepcopy(packet)
                raw_plain = runner.run(packet, 'compile')
                raw_extra = runner.run(packet, 'compile', include_term_semantics=True)
                self.assertEqual(raw_extra['run.json']['term_semantics']['status'], 'complete')
                self.assert_native_equal(raw_plain, raw_extra)
                plain = readable.compile_view(packet)
                extra = readable.compile_view(packet, include_term_semantics=True)
                for key in plain:
                    self.assertEqual(plain[key], extra[key], key)
                html = readable.render_html(extra)
                self.assertTrue(term_section(html))
                self.assertEqual(readable.render_html(plain), html.replace(term_section(html), ''))
                self.assertNotIn('term_semantics', plain)
                self.assertEqual(extra['term_semantics'], raw_extra['term_semantic_candidates.json'])
                self.assertEqual(extra['term_semantics_status']['status'], 'complete')
                self.assertEqual(before, packet)

    def test_compile_and_generate_once(self):
        packet = self.packet()
        with patch.object(readable, 'parse_packet', wraps=readable.parse_packet) as auto, \
             patch.object(readable, 'compile_reviewed', wraps=readable.compile_reviewed) as reviewed, \
             patch.object(readable, 'new_session', wraps=readable.new_session) as session, \
             patch.object(engine, 'suggest_term_semantics', wraps=engine.suggest_term_semantics) as suggest:
            view = readable.compile_view(packet, include_term_semantics=True)
        self.assertEqual((auto.call_count, reviewed.call_count, session.call_count), (1, 1, 1))
        self.assertEqual(suggest.call_count, len(documents(packet)))
        self.assertTrue(view['term_semantics'])
        self.assertFalse(self.output.exists())

    def test_switching_off_removes_owned_file_and_preserves_old_bytes(self):
        packet = self.packet()
        plain = runner.run(packet, 'compile')
        original = {p.name: p.read_bytes() for p in self.output.iterdir()}
        runner.run(packet, 'compile', include_term_semantics=True)
        self.assertTrue((self.output/'term_semantic_candidates.json').exists())
        self.assertEqual(plain, runner.run(packet, 'compile'))
        self.assertEqual(original, {p.name: p.read_bytes() for p in self.output.iterdir()})

    def test_candidate_failure_is_separate_and_clears_previous_result(self):
        packet = self.packet()
        plain = runner.run(packet, 'compile')
        runner.run(packet, 'compile', include_term_semantics=True)
        view_plain = readable.compile_view(packet)
        with patch.object(engine, 'suggest_packet_semantics', side_effect=ValueError('candidate failure')):
            failed = runner.run(packet, 'compile', include_term_semantics=True)
            view = readable.compile_view(packet, include_term_semantics=True)
        self.assert_native_equal(plain, failed)
        self.assertEqual(failed['run.json']['status'], 'complete')
        self.assertEqual(failed['run.json']['term_semantics']['status'], 'error')
        self.assertIsNone(json.loads((self.output/'term_semantic_candidates.json').read_text(encoding='utf-8')))
        self.assertIsNone(view['term_semantics'])
        self.assertEqual(view['term_semantics_status']['status'], 'error')
        for key in view_plain:
            self.assertEqual(view_plain[key], view[key])

    def test_native_failure_blocks_new_candidates(self):
        runner.run(self.packet(), 'compile', include_term_semantics=True)
        with patch.object(engine, 'suggest_packet_semantics', wraps=engine.suggest_packet_semantics) as suggest:
            out = runner.run({'primary_documents': [{'doc_id': 'broken'}]}, 'compile', include_term_semantics=True)
        self.assertEqual(suggest.call_count, 0)
        self.assertEqual(out['run.json']['status'], 'error')
        self.assertEqual(out['run.json']['term_semantics']['status'], 'blocked')
        self.assertIsNone(out['term_semantic_candidates.json'])
        with patch.object(readable, 'parse_packet', side_effect=ValueError('native failure')):
            with self.assertRaisesRegex(ValueError, 'native failure'):
                readable.compile_view(self.packet(), include_term_semantics=True)

    def test_packet_and_reading_changes_do_not_reuse_candidates(self):
        packet = runner.text_packet('置積月')
        first = runner.run(packet, 'constructions', include_term_semantics=True)
        packet['primary_documents'][0].update(text='置積日', reading_id='changed')
        second = runner.run(packet, 'lexical', include_term_semantics=True)
        bundle = second['term_semantic_candidates.json']['pasted']
        self.assertEqual(bundle['identity']['reading_id'], 'changed')
        self.assertNotEqual(first['term_semantic_candidates.json'], second['term_semantic_candidates.json'])
        self.assertFalse(any(n['span']['quote'] == '月' for n in bundle['candidates']))

    def test_legacy_presets_remain_compatible(self):
        for procedure in list_procedures(ROOT):
            packet = build_source_packet(ROOT, procedure['id'])['source_packet']
            plain = runner.run(packet, 'compile')
            extra = runner.run(packet, 'compile', include_term_semantics=True)
            self.assert_native_equal(plain, extra)
            self.assertEqual(extra['run.json']['term_semantics']['status'], 'complete')

    def test_provenance_never_changes_ports(self):
        packet = runner.text_packet('置積月')
        native = readable.compile_view(packet)
        registry = engine.load_kernel()
        old = engine.suggest_packet_semantics(packet, registry=registry)
        registry['composition_rules'][0]['evidence_ids'].append('S-C79')
        new = engine.suggest_packet_semantics(packet, registry=registry)
        self.assertNotEqual(old, new)
        with patch.object(engine, 'load_kernel', return_value=registry):
            extra = readable.compile_view(packet, include_term_semantics=True)
        self.assertEqual(native['automatic_report'], extra['automatic_report'])
        self.assertEqual(native['compilation'], extra['compilation'])

    def test_disabled_entrypoints_do_not_import_domain_module(self):
        script = '''
import sys,tempfile
from pathlib import Path
class Block:
 def find_spec(self, fullname,*args):
  if fullname.startswith('domain_kernel'):raise AssertionError('disabled import')
sys.meta_path.insert(0,Block())
from tools.parser_inspector import runner,readable
with tempfile.TemporaryDirectory() as folder:
 runner.OUTPUT=Path(folder)
 packet=runner.text_packet('置積月')
 assert runner.run(packet,'compile')['run.json']['status']=='complete'
 assert 'term_semantics' not in readable.compile_view(packet)
assert not any(n.startswith('domain_kernel') for n in sys.modules)
'''
        proc = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', script], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TermPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        packet = build_source_packet_from_units(ROOT, 'sifen', ['sifen:section:39'], [],
                                               {'tradition': 'Han_Si_fen_li'})
        cls.view = readable.compile_view(packet, include_term_semantics=True)

    def sample(self, text, **options):
        packet = runner.text_packet(text)
        packet['primary_documents'][0]['source'] = {'unit_id': 'presentation:test'}
        doc = documents(packet)[0]
        anchor = {k: doc[k] for k in ('doc_id', 'reading_id')}
        anchor.update(start=0, end=len(text), quote=text, source_sha256=doc['actual_sha256'])
        view = readable.compile_view(packet)
        view['term_semantics'] = engine.suggest_packet_semantics(packet, term_regions={doc['doc_id']: [anchor]}, **options)
        view['term_semantics_status'] = {'status': 'complete'}
        return view

    def test_real_primary_readonly_section_position_and_all_alternatives(self):
        before = copy.deepcopy(self.view)
        with patch.object(engine, 'suggest_packet_semantics', side_effect=AssertionError('second generator')), \
             patch.object(engine, 'suggest_term_semantics', side_effect=AssertionError('second generator')), \
             patch.object(engine, 'validate_term_bundle', side_effect=AssertionError('grammar preview in presentation')), \
             patch.object(readable, 'compile_reviewed', side_effect=AssertionError('second compile')), \
             patch.object(readable, 'new_session', side_effect=AssertionError('second session')):
            html = readable.render_html(self.view)
        section = term_section(html)
        visible = re.sub(r'<[^>]+>', '', unescape(section))
        self.assertTrue(section)
        self.assertLess(html.index('id="R2"'), html.index('id="term-semantics"'))
        self.assertLess(html.index('id="term-semantics"'), html.index('id="R3"'))
        for text in ('Term semantic candidates', '术语语义候选', 'localized_quantity',
                     'C01 → C06', 'proposed', 'compatible', 'not_authorized', 'Support',
                     'Local composition constraints', 'Authorization', 'grammar_candidate',
                     'Region basis: grammar_candidate',
                     'Still suggestion-only: K1 has no authority to set runtime semantics or enter lowering.'):
            self.assertTrue(text in section or text in visible, text)
        bundle = next(iter(self.view['term_semantics'].values()))
        for node in bundle['candidates'] + bundle['fixed_expression_candidates']:
            self.assertEqual(section.count(f'data-term-candidate="{node["id"]}"'), 1)
        self.assertIn('data-start="7" data-end="11"', section)
        for forbidden in ('<button', '<textarea', 'data-decision', 'parser confirmed', 'Current blocker'):
            self.assertNotIn(forbidden, section)
        self.assertEqual(before, self.view)

    def test_tree_uses_ordered_child_ids_not_expression_arguments(self):
        view = self.sample('入蔀積月')
        bundle = next(iter(view['term_semantics'].values()))
        nodes = {n['id']: n for n in bundle['candidates']}
        root = next(n for n in nodes.values() if n['span']['quote'] == '入蔀積月')
        root['expression'] = {'op': 'presentation_test_sentinel', 'arguments': {}}
        html = term_section(readable.render_html(view))
        tree = re.search(r'<div data-term-tree="' + root['id'] + r'">(.*?)</div>', html, re.S).group(1)
        expected = []
        def visit(node, depth=0):
            expected.append((node['id'], depth))
            for child in node['child_ids']:
                visit(nodes[child], depth + 1)
        visit(root)
        class TreeReader(HTMLParser):
            def __init__(self):
                super().__init__()
                self.depth, self.nodes = 0, []

            def handle_starttag(self, tag, attrs):
                if tag == 'li':
                    self.nodes.append((dict(attrs)['data-term-node'], self.depth))
                    self.depth += 1

            def handle_endtag(self, tag):
                if tag == 'li':
                    self.depth -= 1
        reader = TreeReader()
        reader.feed(tree)
        self.assertEqual(reader.nodes, expected)
        self.assertIn('<ol class="children">', tree)
        self.assertIn('presentation_test_sentinel', html)
        self.assertEqual([nodes[c]['span']['quote'] for c in root['child_ids']], ['入', '蔀', '積月'])

    def test_occurrence_shows_its_actual_region_basis(self):
        view = self.sample('積月')
        html = term_section(readable.render_html(view))
        self.assertIn('Region basis: explicit_selection', re.sub(r'<[^>]+>', '', unescape(html)))

    def test_same_span_preserves_bundle_order_and_repeated_occurrences(self):
        view = self.sample('日率，日率')
        bundle = next(iter(view['term_semantics'].values()))
        bundle['candidates'].reverse()  # Renderer must not rank by expression, ID or sense.
        html = term_section(readable.render_html(view))
        self.assertIn('body.sun', html)
        self.assertIn('time.day', html)
        for start in (0, 3):
            expected = [n['id'] for n in bundle['candidates'] if n['span']['start'] == start and n['span']['quote'] == '日率']
            self.assertEqual(len(expected), 2)
            self.assertLess(html.index('data-term-candidate="' + expected[0]), html.index('data-term-candidate="' + expected[1]))
            self.assertIn(f'data-start="{start}" data-end="{start+2}"', html)

    def test_fixed_expression_underdetermined_and_truncation_are_honest(self):
        view = self.sample('實如法而一')
        html = term_section(readable.render_html(view))
        for text in ('C08', 'division_construction', 'technical_computational_expression', 'underdetermined', 'alternative_group'):
            self.assertIn(text, html)
        limited = self.sample('積月', max_candidates=1)
        self.assertIn('Candidate set truncated; displayed alternatives are not exhaustive.', term_section(readable.render_html(limited)))

    def test_empty_and_cue_only_are_not_errors(self):
        view = self.sample('月')
        html = term_section(readable.render_html(view))
        self.assertIn('No composition candidates', html)
        self.assertIn('LC02', html)
        bundle = next(iter(view['term_semantics'].values()))
        bundle['candidates'] = []
        bundle['fixed_expression_candidates'] = []
        self.assertIn('No term semantic candidates', term_section(readable.render_html(view)))

    def test_failures_are_local_including_malformed_trees(self):
        for failure in ('generation', 'missing_child', 'cycle', 'source_identity'):
            with self.subTest(failure=failure):
                view = copy.deepcopy(self.view)
                bundle = next(iter(view['term_semantics'].values()))
                node = next(n for n in bundle['candidates'] if n['child_ids'])
                if failure == 'generation':
                    view['term_semantics'] = None
                    view['term_semantics_status'] = {'status': 'error', 'error': '<broken>'}
                elif failure == 'missing_child':
                    node['child_ids'] = ['absent']
                elif failure == 'cycle':
                    node['child_ids'] = [node['id']]
                else:
                    bundle['identity']['source_sha256'] = 'stale'
                html = readable.render_html(view)
                self.assertIn('Term semantic candidates unavailable', term_section(html))
                plain = {k: v for k, v in view.items() if not k.startswith('term_semantics')}
                self.assertEqual(html.replace(term_section(html), ''), readable.render_html(plain))
                self.assertNotIn('<broken>', html)

    def test_registry_metadata_is_resolved_only_for_matching_hash_and_escaped(self):
        view = copy.deepcopy(self.view)
        html = term_section(readable.render_html(view))
        self.assertIn('S-ENG', html)
        kernel = engine.load_kernel()
        title = kernel['sources'][0]['title']
        self.assertIn(title, unescape(html))
        bundle = next(iter(view['term_semantics'].values()))
        bundle['identity']['registry_sha256'] = 'different-registry'
        html = term_section(readable.render_html(view))
        self.assertIn('Registry metadata unavailable', html)
        self.assertNotIn(title, html)
        bundle['candidates'][0]['expression'] = {'op': '<script>unsafe</script>'}
        html = term_section(readable.render_html(view))
        self.assertNotIn('<script>unsafe</script>', html)
        self.assertIn('&lt;script&gt;unsafe&lt;/script&gt;', html)
        with patch.object(engine, 'load_kernel', side_effect=OSError('registry unavailable')):
            html = term_section(readable.render_html(self.view))
        self.assertIn('Registry metadata unavailable', html)
        self.assertIn('localized_quantity', html)
        self.assertIn('S-ENG', html)

    def test_fixed_inspector_enables_candidates_without_output_writes(self):
        from streamlit.testing.v1 import AppTest
        before = {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json')}
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=20)
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertTrue(term_section(app.get('iframe')[0].proto.srcdoc))
        app.button[1].click().run(timeout=20)
        self.assertIn('applyLanguage("zh")', app.get('iframe')[0].proto.srcdoc)
        self.assertTrue(term_section(app.get('iframe')[0].proto.srcdoc))
        self.assertEqual(before, {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json')})


if __name__ == '__main__':
    unittest.main()
