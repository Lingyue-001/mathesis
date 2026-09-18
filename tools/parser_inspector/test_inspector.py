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
    def test_compact_display_groups_fields_without_changing_data_or_files(self):
        from streamlit.testing.v1 import AppTest
        before = {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json')}
        text = '𠀀大周\n<script>甲</script>'
        packet = runner.text_packet(text)
        records = [
            {'id': 't1', 'kind': 'Term', 'text': text, 'start': 0, 'end': len(text),
             'source_span': {'doc_id': 'pasted', 'start': 0, 'end': len(text), 'quote': text}},
            {'id': 't2', 'kind': 'Number', 'text': '一', 'value': 1, 'start': 1, 'end': 2},
        ]
        snapshot = dict.fromkeys(runner.FILES)
        snapshot.update({'packet.json': packet, 'lexical_candidates.json': records,
                         'run.json': {'status': 'complete', 'completed_stages': ['lexical']}})
        app = AppTest.from_file(str(Path(__file__).with_name('app.py')))
        app.session_state['pasted_text'] = text
        app.session_state['snapshot_packet'] = packet
        app.session_state['snapshot'] = snapshot
        app.run()
        self.assertFalse(app.exception)
        compact = [item.value for item in app.code if json.loads(item.value) == records]
        self.assertEqual(len(compact), 1)
        lines = compact[0].splitlines()
        self.assertEqual(len(lines), 6)  # Brackets plus two lines per record.
        self.assertIn('"id": "t1"', lines[1])
        self.assertIn('"kind": "Term"', lines[1])
        self.assertIn('"start": 0', lines[1])
        self.assertIn('"text":', lines[2])
        self.assertIn('"source_span":', lines[2])
        self.assertIn(records, [json.loads(item.value) for item in app.json])
        self.assertEqual(app.session_state['snapshot'], snapshot)
        self.assertEqual(before, {p.name: p.read_bytes() for p in runner.OUTPUT.glob('*.json')})

    def test_paste_run_shows_raw_json_paths_and_clears_stale_view(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        self.assertFalse(app.exception)
        # A pasted textarea value is committed on blur; disabled buttons cannot
        # trigger that interaction in a real browser.
        self.assertFalse(app.button(key='compile').disabled)
        app.button(key='compile').click().run()
        self.assertEqual(len(app.json), 0)
        app.text_area(key='pasted_text').set_value('以大周乘年。').run()
        app.button(key='compile').click().run()
        self.assertFalse(app.exception)
        saved = json.loads((runner.OUTPUT / 'compiler_report.json').read_text(encoding='utf-8'))
        rendered = [json.loads(item.value) for item in app.json]
        self.assertIn(saved, rendered)
        self.assertIn(saved['events'], rendered)
        self.assertTrue(any('events.json' in item.value for item in app.caption))
        app.text_area(key='pasted_text').set_value('大周三百。').run()
        self.assertEqual(len(app.json), 0)
        app.button(key='lexical').click().run()
        self.assertFalse(app.exception)
        self.assertIsNone(json.loads((runner.OUTPUT / 'compiler_report.json').read_text(encoding='utf-8')))

    def test_registered_corpus_selection_preserves_packet_and_context(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run()
        app.radio(key='source_mode').set_value('Corpus').run()
        for procedure in list_procedures(ROOT):
            app.selectbox(key='procedure_id').select(procedure['id']).run()
            app.button(key='compile').click().run()
            self.assertFalse(app.exception)
            expected = build_source_packet(ROOT, procedure['id'])['source_packet']
            self.assertEqual(json.loads((runner.OUTPUT / 'packet.json').read_text(encoding='utf-8')), expected)
            report = json.loads((runner.OUTPUT / 'compiler_report.json').read_text(encoding='utf-8'))
            self.assertEqual(report, parse_packet(expected))


if __name__ == '__main__':
    unittest.main()
