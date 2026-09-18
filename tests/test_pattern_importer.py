"""Deterministic importer tests; expectations are literal, not parser outputs."""
import copy
import json
from pathlib import Path
import unittest
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch

from evaluation.pattern_importer import (import_annotations, parse_expression,
                                         recover_mention, source_document)
from evaluation.pattern_reference import compare_reference
from evaluation.pattern_reference import run_batch
from source_adapters.corpus import build_source_packet
from analysis_parser.pipeline import parse_packet

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'evaluation/pattern-reference'


class ImporterTests(unittest.TestCase):
    def test_small_grammar_references_assignments_and_comparisons(self):
        self.assertEqual(parse_expression('out12'), {'kind': 'reference', 'name': 'out12'})
        self.assertEqual(parse_expression('quotient=quot4;remainder=rem4'),
                         {'kind': 'assignments', 'items': {'quotient': {'kind': 'reference', 'name': 'quot4'},
                                                          'remainder': {'kind': 'reference', 'name': 'rem4'}}})
        self.assertEqual(parse_expression('value(閏餘)>=十二'),
                         {'kind': 'comparison', 'left': {'kind': 'call', 'name': 'value', 'argument': {'kind': 'label', 'name': '閏餘'}},
                          'operator': '>=', 'right': {'kind': 'number', 'value': 12}})
        self.assertEqual(parse_expression('>=四百四十一')['right']['value'], 441)
        self.assertEqual(parse_expression('presence(朔)=true;presence(中)=false')['kind'], 'sequence')
        self.assertEqual(parse_expression('start=所入蔀名;cycle=六十;advance=input;return=after_exhaustion')['kind'], 'assignments')
        self.assertEqual(parse_expression('閏餘；積月')['kind'], 'list')

    def test_unknown_format_never_falls_back_to_a_label(self):
        for text in ['out1 + 2', '四百九十 [九]', 'foo(x)', 'a=1;a=2', 'quotient=', '中之始(日)', '一二十']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_expression(text)

    def test_exact_leading_clause_scopes_repeated_step_without_emending_text(self):
        docs = [source_document('a', '推甲術，置甲，乙〈丙〉。'), source_document('b', '推乙術，置甲。')]
        annotations = [{'chunk_id': 'c', 'chunk_type': 'procedure', 'terms': [], 'relations': [],
                        'steps': [{'order': 1, 'phrase': '置甲', 'op': 'set', 'input': '甲', 'parameter': '', 'output': 'out1'},
                                  {'order': 2, 'phrase': '乙[丙]', 'op': 'set', 'input': '乙', 'parameter': '', 'output': 'out2'}]}]
        sources = {'chunks': [{'id': 'c', 'source_text_zh': '推甲術，置甲，乙[丙]。'}]}
        crosswalk = json.loads((ASSETS / 'operation-crosswalk.json').read_text(encoding='utf-8'))
        result = import_annotations(annotations, sources, {'primary_documents': docs}, crosswalk)['chunks'][0]
        first, second = result['procedure_reference']['steps']
        self.assertEqual(first['source_anchors'][0]['doc_id'], 'a')
        self.assertEqual(first['issues'], [])
        self.assertIn('needs_review', second['issues'])

    def test_clean_processes_are_byte_identical_and_preserve_compiler_before_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = [Path(tmp) / 'one', Path(tmp) / 'two']
            for seed, path in zip(('1', '77'), outputs):
                subprocess.run([sys.executable, '-X', 'utf8', '-m', 'evaluation.pattern_reference', '--output', str(path)],
                               cwd=ROOT, env=dict(os.environ, PYTHONHASHSEED=seed), check=True, capture_output=True)
            first, second = [{p.name: p.read_bytes() for p in path.iterdir()} for path in outputs]
            self.assertEqual(first, second)
            summary = json.loads(first['summary.json'])
            self.assertEqual(summary['local_proc35'], {'matched': 7, 'total': 7})
            self.assertEqual(summary['pipeline_order'][:3], ['compiled_registered_local_packet', 'compiled_full_canonical_corpus', 'read_full_annotations_and_fixed_crosswalk'])

    def test_annotation_files_are_actually_opened_only_after_both_compiles(self):
        original_read = Path.read_text
        read_assets = []
        with patch('analysis_parser.pipeline.parse_packet', wraps=parse_packet) as compiler:
            def guarded_read(path, *args, **kwargs):
                if path.name in ('ch3-chunk-breakdown.json', 'operation-crosswalk.json', 'source-chunks.json'):
                    self.assertEqual(compiler.call_count, 2)
                    read_assets.append(path.name)
                return original_read(path, *args, **kwargs)
            with patch.object(Path, 'read_text', guarded_read):
                run_batch(ROOT)
        self.assertEqual(set(read_assets), {'ch3-chunk-breakdown.json', 'operation-crosswalk.json', 'source-chunks.json'})

    def test_missing_step_fields_are_unparsed_not_a_crash(self):
        raw = [{'chunk_id': 'c', 'chunk_type': 'procedure', 'steps': [{'order': 'first', 'op': 'set'}]}]
        sources = {'chunks': [{'id': 'c', 'source_text_zh': '置甲'}]}
        output = import_annotations(raw, sources, {'primary_documents': [source_document('s', '置甲')]}, {'operations': {}})
        self.assertEqual(output['chunks'][0]['original'], raw[0])
        self.assertIn('manual_schema_unparsed', output['chunks'][0]['procedure_reference']['steps'][0]['issues'])

    def test_occurrence_suffix_disambiguates_only_exact_candidates(self):
        doc = source_document('chunk:1', '甲之甲之甲')
        term = {'mention_id': 'c0001_jia3_002', 'text': '甲', 'anchor': '甲之'}
        result = recover_mention(term, doc)
        self.assertEqual(result['status'], 'resolved')
        self.assertEqual(result['anchors'][0]['start'], 2)
        for changed in [dict(term, mention_id='bad'), dict(term, anchor='乙之'), dict(term, mention_id='c0001_jia3_003')]:
            self.assertEqual(recover_mention(changed, doc)['status'], 'needs_review')

    def test_unique_anchor_beats_ordinal_over_unannotated_occurrences(self):
        doc = source_document('chunk:2', '日甲，乙日')
        term = {'mention_id': 'c0002_ri4_001', 'text': '日', 'anchor': '乙日'}
        self.assertEqual(recover_mention(term, doc)['anchors'][0]['start'], 4)

    def test_exact_unicode_coordinates_and_missing_text(self):
        doc = source_document('chunk:3', '𠀀é\n甲甲')
        term = {'mention_id': 'c0003_jia3_002', 'text': '甲', 'anchor': '甲甲'}
        self.assertEqual(recover_mention(term, doc)['anchors'][0]['start'], 5)
        term['text'] = '乙'
        self.assertEqual(recover_mention(term, doc)['status'], 'needs_review')

    def test_full_original_preserved_and_proc35_generated_without_authored_expectations(self):
        # Machine is completed BEFORE any annotation/reference assets are read.
        packet = build_source_packet(ROOT, 'sifen-3-5')['source_packet']
        graph = parse_packet(packet)
        original = json.loads((ASSETS / 'ch3-chunk-breakdown.json').read_text(encoding='utf-8'))
        chunks = json.loads((ASSETS / 'source-chunks.json').read_text(encoding='utf-8'))
        crosswalk = json.loads((ASSETS / 'operation-crosswalk.json').read_text(encoding='utf-8'))
        before = copy.deepcopy((original, chunks, packet, crosswalk))
        imported = import_annotations(original, chunks, packet, crosswalk)
        self.assertEqual([r['original'] for r in imported['chunks']], original)
        self.assertEqual(before, (original, chunks, packet, crosswalk))
        reference = next(r for r in imported['chunks'] if r['original']['chunk_id'] == 'cullen:ch3:chunk:0055')['procedure_reference']
        result = compare_reference(packet, graph, reference, crosswalk)
        self.assertEqual(result['matched_steps'], 7)
        self.assertEqual(reference['steps'][3]['evaluation_expectation']['outputs'], {'quotient': 'quot4', 'remainder': 'rem4'})
        again = import_annotations(original, chunks, packet, crosswalk)
        self.assertEqual(json.dumps(imported, ensure_ascii=False, sort_keys=True), json.dumps(again, ensure_ascii=False, sort_keys=True))

    def test_missing_crosswalk_unknown_schema_and_conceptual_exclusion(self):
        packet = {'primary_documents': [source_document('s', '置甲。')], 'context_documents': []}
        annotations = [{'chunk_id': 'c', 'chunk_type': 'conceptual', 'terms': [],
                        'relations': [{'subject': '甲', 'relation': 'IS', 'object': '乙'}], 'steps': []},
                       {'chunk_id': 'p', 'chunk_type': 'procedure', 'terms': [], 'relations': [],
                        'steps': [{'order': 1, 'phrase': '置甲', 'op': 'new_op', 'input': 'out1+2', 'parameter': '', 'output': 'out1'}]}]
        sources = {'chunks': [{'id': 'c', 'source_text_zh': '置甲。'}, {'id': 'p', 'source_text_zh': '置甲。'}]}
        result = import_annotations(annotations, sources, packet, {'operations': {}})
        self.assertEqual(result['chunks'][0]['relation_reference'][0]['target_status'], 'not_current_parser_target')
        step = result['chunks'][1]['procedure_reference']['steps'][0]
        self.assertIn('crosswalk_missing', step['issues'])
        self.assertIn('manual_schema_unparsed', step['issues'])


if __name__ == '__main__':
    unittest.main()
