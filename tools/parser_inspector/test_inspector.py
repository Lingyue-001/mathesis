"""Raw-output contract tests; all generated JSON stays in output/current/."""
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from analysis_parser.inputs import documents
from analysis_parser.lexical import tokenize_candidates
from analysis_parser.construction_ir import parse_syntax
from analysis_parser.pipeline import parse_packet
from source_adapters.corpus import build_source_packet, list_procedures
from tools.parser_inspector import runner


class InspectorTests(unittest.TestCase):
    def test_raw_files_equal_native_outputs_including_context_and_diagnostics(self):
        packet = build_source_packet(ROOT, list_procedures(ROOT)[0]['id'])['source_packet']
        result = runner.run(packet, 'compile')
        self.assertEqual(result['run.json']['status'], 'complete')
        native = parse_packet(packet)
        self.assertEqual(result['compiler_report.json'], native)
        self.assertEqual(result['lexical_candidates.json'], native['tokens'])
        for filename, key in [('events.json', 'events'), ('values.json', 'value_instances'),
                              ('diagnostics.json', 'diagnostics'), ('unresolved.json', 'unresolved'),
                              ('construction_selection.json', 'construction_candidates'),
                              ('program.json', 'program')]:
            self.assertEqual(result[filename], native[key])
        self.assertTrue(result['events.json'])
        self.assertTrue(any(c['status'] == 'selected' for c in result['construction_selection.json']))
        for filename, value in result.items():
            self.assertEqual(json.loads((runner.OUTPUT / filename).read_text(encoding='utf-8')), value)

    def test_stages_preserve_unicode_anchors_and_do_not_claim_selection(self):
        text = '𠀀e\u0301\n以大周乘年。\n以大周乘年。'
        packet = runner.text_packet(text)
        result = runner.run(packet, 'constructions')
        doc = documents(packet)[0]
        tokens = tokenize_candidates(doc, {})
        syntax = parse_syntax(tokens, doc)
        self.assertEqual(result['packet.json']['primary_documents'][0]['text'], text)
        self.assertEqual(result['lexical_candidates.json'], tokens)
        self.assertEqual(result['syntax.json'], {doc['doc_id']: syntax.to_dict()})
        self.assertEqual(result['construction_candidates.json'], syntax.candidates())
        self.assertIsNone(result['construction_selection.json'])
        for token in tokens:
            span = token['source_span']
            self.assertEqual(text[span['start']:span['end']], span['quote'])

    def test_new_lexical_run_clears_previous_compiler_outputs_and_is_repeatable(self):
        packet = runner.text_packet('以大周乘年。')
        runner.run(packet, 'compile')
        first = runner.run(packet, 'lexical')
        before = {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json')}
        second = runner.run(packet, 'lexical')
        self.assertEqual(first, second)
        self.assertEqual(before, {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json')})
        self.assertIsNone(second['compiler_report.json'])
        self.assertIsNone(second['construction_candidates.json'])
        self.assertEqual(runner.OUTPUT, Path(__file__).resolve().parent / 'output' / 'current')

    def test_failed_run_does_not_leave_previous_results(self):
        runner.run(runner.text_packet('以大周乘年。'), 'compile')
        result = runner.run({'primary_documents': [{'doc_id': 'broken'}]}, 'compile')
        self.assertEqual(result['run.json']['status'], 'error')
        self.assertIn('KeyError', result['run.json']['error'])
        self.assertIsNone(result['compiler_report.json'])
        self.assertIsNone(result['events.json'])


class AppTests(unittest.TestCase):
    def test_global_language_toggle_changes_shell_and_readable_view_without_writing_outputs(self):
        from streamlit.testing.v1 import AppTest
        before = {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json')}
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertEqual([button.label for button in app.button][:2], ['EN', 'CH'])
        self.assertNotIn('Create review job', [button.label for button in app.button])
        self.assertNotIn('Import job', [button.label for button in app.button])
        self.assertEqual(app.radio[0].label, 'Workspace')
        self.assertEqual(len(app.text_area), 0)
        frames = app.get('iframe')
        self.assertEqual(len(frames), 1)
        html = frames[0].proto.srcdoc
        self.assertIn('Primary', html)
        self.assertIn('no human decisions', html)
        self.assertIn('applyLanguage("en")', html)
        for layer in ('R1', 'R2', 'R3', 'R4'):
            self.assertIn(f'id="{layer}"', html)
        app.button[1].click().run()
        self.assertEqual([button.label for button in app.button][:2], ['EN', 'CH'])
        self.assertEqual(app.radio[0].label, '工作区')
        self.assertIn('applyLanguage("zh")', app.get('iframe')[0].proto.srcdoc)
        app.button[0].click().run()
        self.assertEqual(app.radio[0].label, 'Workspace')
        self.assertEqual(before, {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json')})

    def test_global_language_toggle_localizes_segmentation_and_full_text_chrome(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        app.radio(key='inspector_page').set_value('Segmentation Review').run()
        self.assertEqual(app.header[0].value, 'Corpus Segmentation Review')
        self.assertIn('Source', [box.label for box in app.selectbox])
        app.button(key='language_zh').click().run()
        self.assertEqual(app.header[0].value, '语料分块审阅')
        self.assertIn('来源', [box.label for box in app.selectbox])

        app.radio(key='inspector_page').set_value('Corpus Full Text').run()
        self.assertEqual(app.header[0].value, '语料全文')
        self.assertIn('返回审阅', [button.label for button in app.button])
        app.button(key='language_en').click().run()
        self.assertEqual(app.header[0].value, 'Corpus Full Text')
        self.assertIn('Back to review', [button.label for button in app.button])

    def test_inspector_has_no_registered_corpus_input(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        self.assertFalse(any(control.key == 'source_mode' for control in app.radio))
        self.assertFalse(any(control.key == 'procedure_id' for control in app.selectbox))


if __name__ == '__main__':
    unittest.main()
