"""Read-only shell: real compiler schemas and honest empty-session comparison."""
import copy
import importlib
import unittest
from pathlib import Path
from unittest.mock import patch
from html.parser import HTMLParser

from adjudication import compile_reviewed
from analysis_parser.pipeline import parse_packet
from evaluation.semantic_regression import project_report
from source_adapters.corpus import build_source_packet_from_units

ROOT = Path(__file__).resolve().parents[2]


def default_text(html):
    class Reader(HTMLParser):
        depth = 0
        parts = None

        def handle_starttag(self, tag, attrs):
            if tag == 'details':
                self.depth += 1

        def handle_endtag(self, tag):
            if tag == 'details':
                self.depth -= 1

        def handle_data(self, data):
            if not self.depth:
                self.parts.append(data)
    reader = Reader()
    reader.parts = []
    reader.feed(html)
    return ' '.join(reader.parts)


class ReadableTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('tools.parser_inspector.readable'))
        return importlib.import_module('tools.parser_inspector.readable')

    def packet(self):
        return build_source_packet_from_units(ROOT, 'sifen', ['sifen:section:39'], [],
                                              {'tradition': 'Han_Si_fen_li'})

    def test_one_compile_per_path_and_same_projection_for_actual_bundle_graph(self):
        module = self.module()
        packet = self.packet()
        before = copy.deepcopy(packet)
        with patch.object(module, 'parse_packet', wraps=parse_packet) as auto, \
                patch.object(module, 'compile_reviewed', wraps=compile_reviewed) as reviewed:
            view = module.compile_view(packet)
        self.assertEqual((auto.call_count, reviewed.call_count), (1, 1))
        self.assertEqual(packet, before)
        self.assertEqual(view['session']['decisions'], [])
        self.assertEqual(view['automatic'], project_report(view['automatic_report']))
        self.assertEqual(view['reviewed'], project_report(view['compilation']['graph']))
        self.assertIn('no human decisions', module.render_html(view))

    def test_empty_session_difference_is_visible_as_compiler_path_difference(self):
        module = self.module()

        def differing_compile(packet, session):
            bundle = compile_reviewed(packet, session)
            bundle['graph']['construction_candidates'][0]['status'] = 'unresolved'
            return bundle

        with patch.object(module, 'compile_reviewed', side_effect=differing_compile):
            view = module.compile_view(self.packet())
        self.assertTrue(view['diff']['R2']['changed'])
        html = module.render_html(view)
        self.assertIn('编译路径差异', html)
        self.assertIn('no human decisions', html)
        self.assertIn('unresolved', html)

    def test_unavailable_reviewed_graph_is_not_projected_as_empty_success(self):
        module = self.module()
        with patch.object(module, 'compile_reviewed', return_value={
                'graph': None, 'replay': {'status': 'stale'}, 'review_queue': {'items': []}}):
            view = module.compile_view(self.packet())
        self.assertIsNone(view['reviewed'])
        self.assertIsNone(view['diff'])
        self.assertIn('stale', module.render_html(view))

    def test_render_preserves_all_records_and_exact_evidence_links(self):
        module = self.module()
        view = module.compile_view(self.packet())
        html = module.render_html(view)
        for layer in ('R1', 'R2', 'R3', 'R4'):
            self.assertIn(f'id="{layer}"', html)
        self.assertEqual(html.count('data-record="R1"'), 210)
        self.assertEqual(html.count('data-record="R3"'), 4)
        self.assertIn('data-start=', html)
        self.assertIn('data-end=', html)
        self.assertNotIn('<button', html)  # The single global control belongs to the Streamlit shell.
        self.assertNotIn('data-decision', html)
        self.assertNotIn('<textarea', html)
        self.assertIn('review only', html)

    def test_readable_evidence_roles_hierarchy_and_no_mutation(self):
        module = self.module()
        view = module.compile_view(self.packet())
        before = copy.deepcopy(view)
        html = module.render_html(view)
        self.assertEqual(view, before)
        self.assertIn('reviewed = automatic / no human decisions', html)
        self.assertNotIn('class="comparison"', html)
        self.assertIn('data-ui-en="Lexical candidates"', html)
        self.assertIn('data-ui-zh="词法候选"', html)
        self.assertIn('查看全部 parser edges', html)
        self.assertIn('G_MULTIPLY_6', html)
        self.assertIn('以{left:a}乘{right:a}', html)
        self.assertIn('slot lexical provenance currently unavailable', html)
        self.assertIn('机器编译采用；未经人工确认', html)
        self.assertIn('dividend', html)
        self.assertIn('quotient', html)
        self.assertIn('lowered role unresolved / not currently represented', html)
        self.assertIn('class="children"', html)
        self.assertIn('MethodSlice', html)
        self.assertIn('在既有基态上建立的查询或阶段', html)
        self.assertIn('具有相乘构式的表达', html)

    def test_source_order_and_dependency_grouping(self):
        module = self.module()
        view = module.compile_view(self.packet())
        for layer in ('R1', 'R2', 'R3'):
            ordered = module.source_order(view['automatic'][layer])
            positions = [module.source_position(row) for row in ordered]
            self.assertEqual(positions, sorted(positions))
        groups, other = module.dependency_groups(view['automatic']['R4'], view['automatic_report'])
        month = next(g for g in groups if g['formal'] == '蔀月')
        self.assertEqual(len(month['imports']), 2)
        self.assertGreaterEqual(len(month['diagnostics']), 2)
        self.assertEqual(len([g for g in groups if g['formal'] == '蔀月']), 1)
        self.assertTrue(other)  # Unattributable diagnostics must not vanish.

    def test_missing_syntax_provenance_never_guesses_repeated_text(self):
        module = self.module()
        view = module.compile_view(self.packet())
        view['automatic_report']['syntax'] = {'nodes': []}
        html = module.render_html(view)
        self.assertIn('slot lexical provenance currently unavailable', html)
        self.assertNotIn('data-slot-evidence=', html)

    def test_lowering_requires_node_id_not_shared_span_or_slot_name(self):
        module = self.module()
        view = module.compile_view(self.packet())
        report = view['automatic_report']
        item, raw = next((item, raw) for item, raw in module._paired('R2', view['automatic']['R2'], report)
                         if raw.get('production_id') == 'G_DIVIDE_17')
        for event in report['events']:
            event.pop('syntax_node_id', None)
        html = module._construction(item, raw, report, view['packet']['primary_documents'][0])
        self.assertIn('divisor =', html)  # Grammar slot remains.
        self.assertNotIn('reads · dividend', html)
        self.assertIn('lowered role unresolved / not currently represented', html)

    def test_diagnostic_same_quantity_elsewhere_is_not_falsely_attached(self):
        module = self.module()
        view = module.compile_view(self.packet())
        report = view['automatic_report']
        diagnostic = copy.deepcopy(next(d for d in report['unresolved']
                                        if d.get('missing_or_conflicting_inputs') == ['蔀月']))
        diagnostic['source_spans'] = [{'doc_id': 'elsewhere', 'start': 0, 'end': 2, 'quote': '蔀月'}]
        diagnostic['reason'] = 'distinct source use'
        report['unresolved'].append(diagnostic)
        groups, other = module.dependency_groups(project_report(report)['R4'], report)
        self.assertTrue(any(d['reason'] == 'distinct source use' for d in other))
        self.assertFalse(any(d['reason'] == 'distinct source use' for g in groups for d in g['diagnostics']))

    def test_source_and_projection_text_are_escaped_and_keep_unicode_offsets(self):
        module = self.module()
        document = {'doc_id': 'test', 'text': '𠀀<script>甲</script>',
                    'source': {'unit_id': 'test:unit'}}
        projection = {'R1': [{'surface': '<script>', 'kind': 'Term', 'source_span': {
            'doc_id': 'test', 'start': 1, 'end': 9, 'quote': '<script>'}}],
            'R2': [], 'R3': [], 'R4': {'imports': [], 'missing_dependencies': []}}
        view = {'packet': {'primary_documents': [document]}, 'automatic': projection,
                'reviewed': None, 'diff': None, 'compilation': {'replay': {'status': 'stale'}}}
        html = module.render_html(view)
        self.assertIn('data-start="1" data-end="9"', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>甲', html)
        self.assertIn('id="source-1" data-offset="1">&lt;</span>', html)

    def test_default_reading_and_evidence_are_separate(self):
        module = self.module()
        view = module.compile_view(self.packet())
        report = view['automatic_report']
        document = view['packet']['primary_documents'][0]
        for item, raw in module._paired('R2', view['automatic']['R2'], report):
            html = module._construction(item, raw, report, document)
            visible = default_text(html)
            self.assertNotIn('grammar production', visible)
            self.assertNotIn('methodology', visible)
            self.assertNotIn('syntax_node_id', visible)
            self.assertIn('查看机器依据', html)
            if not item['slots']:
                self.assertNotIn('slot lexical provenance currently unavailable', html)
            if raw.get('production_id') == 'G_DIVIDE_17':
                for role in ('Dividend', 'Divisor', 'Quotient', 'Remainder'):
                    self.assertIn(role, visible)
            if item['kind'] == 'method_reference':
                self.assertIn('Inputs', visible)
                self.assertIn('Returns', visible)
                self.assertIn('Later use', visible)
                self.assertIn('大餘', visible)
        tree = module._program_tree(view['automatic']['R3'], report, document)
        visible = default_text(tree)
        self.assertIn('Calculation stage', visible)
        self.assertIn('Reusable method', visible)
        self.assertNotIn('parent', visible)
        self.assertNotIn('formal_inputs', visible)
        self.assertNotIn('free variables', visible)
        self.assertIn('Required quantities', visible)
        dependencies = module._dependencies(view['automatic']['R4'], report, document)
        visible = default_text(dependencies)
        self.assertIn('Current source', visible)
        self.assertIn('Expected port', visible)
        self.assertIn('未绑定', visible)
        self.assertIn('積月', visible)
        self.assertNotIn('selected producer', visible)
        self.assertNotIn('no declared root', visible)

    def test_output_use_follows_value_identity_not_same_label(self):
        module = self.module()
        report = {'value_instances': [{'id': 'a', 'labels': ['甲']}, {'id': 'b', 'labels': ['甲']}],
                  'events': [{'id': 'use', 'kind': 'add', 'reads': {'left': 'b'}, 'writes': {},
                              'source_spans': []}]}
        self.assertNotIn('相加', module._uses('a', report, self.packet()['primary_documents'][0]))

    def test_default_reading_uses_authored_english_labels_without_translating_source_targets(self):
        module = self.module()
        view = module.compile_view(self.packet())
        report = view['automatic_report']
        document = view['packet']['primary_documents'][0]
        divide, raw = next((item, raw) for item, raw in module._paired('R2', view['automatic']['R2'], report)
                           if raw.get('production_id') == 'G_DIVIDE_17')
        visible = default_text(module._construction(divide, raw, report, document))
        for label in ('Divide with remainder', 'Dividend', 'Divisor', 'Quotient', 'Remainder'):
            self.assertIn(label, visible)
        self.assertNotIn('divmod', visible)
        tree = default_text(module._program_tree(view['automatic']['R3'], report, document))
        self.assertIn('Procedure', tree)
        self.assertIn('Calculation stage', tree)
        self.assertIn('天正朔日', tree)
        self.assertNotIn('ProcedureDef', tree)
        unresolved = next(item for item in view['automatic']['R4']['missing_dependencies']
                          if item['cause'] == 'unresolved_parser')
        visible = default_text(module._dependencies({'imports': [], 'missing_dependencies': [unresolved]},
                                                     {'unresolved': []}, document))
        self.assertIn('Source text not yet parsed', visible)
        self.assertNotIn('unresolved_parser', visible)

    def test_unregistered_event_kind_never_leaks_its_backend_code_into_default_reading(self):
        module = self.module()
        view = module.compile_view(self.packet())
        report = view['automatic_report']
        document = view['packet']['primary_documents'][0]
        heading, raw = next((item, raw) for item, raw in module._paired('R2', view['automatic']['R2'], report)
                            if raw.get('node_id') == 'sifen:39:ast31')
        visible = default_text(module._construction(heading, raw, report, document))
        self.assertIn('Procedure heading', visible)
        self.assertNotIn('query', visible)

    def test_global_language_can_render_readable_chrome_without_changing_ontology_labels_or_source(self):
        module = self.module()
        view = module.compile_view(self.packet())
        html = module.render_html(view)
        self.assertNotIn('data-language=', html)
        self.assertIn('applyLanguage("en")', html)
        self.assertIn('data-ui-en="Machine interpretation"', html)
        self.assertIn('data-ui-zh="机器理解"', html)
        self.assertIn('data-ui-en="Uses"', html)
        self.assertIn('data-ui-zh="使用"', html)
        self.assertIn('data-ui-en="Produces"', html)
        self.assertIn('data-ui-zh="得到"', html)
        self.assertIn('data-ui-en="Later use"', html)
        self.assertIn('data-ui-zh="后续"', html)
        self.assertIn('data-ui-en="View machine evidence"', html)
        self.assertIn('data-ui-zh="查看机器依据"', html)
        self.assertIn('data-ui-en="reviewed = automatic / no human decisions"', html)
        self.assertIn('data-ui-zh="reviewed = automatic / 无人工决定"', html)
        self.assertIn('Divide with remainder', html)
        self.assertIn('滿蔀月得一', html)
        chinese = module.render_html(view, 'zh')
        self.assertIn('applyLanguage("zh")', chinese)
        self.assertIn('Divide with remainder', chinese)
        self.assertIn('滿蔀月得一', chinese)


if __name__ == '__main__':
    unittest.main()
