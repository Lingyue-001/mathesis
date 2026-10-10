"""Baseline corpus collection for the local Term Index view."""
from copy import deepcopy
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from tests.workbench.test_review_jobs import isolated_source
from workbench.term_index_corpus import (baseline_corpus_inputs, collect_baseline_term_index,
                                         fingerprint_effective_units, term_index_producer_files)


def unit(source_id, unit_id, revision='review-a', source_sha='source-a'):
    return {
        'source_id': source_id,
        'unit_id': unit_id,
        'source_spans': [[0, 2]],
        'effective_revision': revision,
        'source_sha256': source_sha,
    }


def projection(source_id, unit_id, doc_id, reading_id, surface):
    return {
        'schema': 'ScholarSourceProjection/1',
        'source': {
            'source_id': source_id, 'unit_id': unit_id, 'doc_id': doc_id,
            'reading_id': reading_id, 'text': surface, 'text_sha256': 'text-' + unit_id,
        },
        'terms': [{
            'id': 'term:' + unit_id + ':0-1', 'surface': surface, 'display_level': 'maximal',
            'source_anchor': {'doc_id': doc_id, 'reading_id': reading_id, 'start': 0, 'end': 1,
                              'quote': surface, 'offset_unit': 'unicode_code_point'},
            'children': [], 'composition_alternatives': [],
        }],
    }


class BaselineCorpusCollectorTests(unittest.TestCase):
    def test_real_current_effective_fixture_builds_a_baseline_index_for_every_admitted_unit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            isolated_source(root)
            inputs = baseline_corpus_inputs(root)
            result = collect_baseline_term_index(root, inputs=inputs)

        expected = [(row['source_id'], row['unit_id']) for row in inputs['units']]
        actual = [(row['source_id'], row['unit_id']) for row in result['included']]
        self.assertEqual(actual, sorted(expected))
        self.assertEqual(result['kind'], 'baseline_corpus')
        self.assertEqual(result['fingerprint'], inputs['fingerprint'])
        self.assertEqual(result['index']['schema'], 'TermIndex/1')

    def test_baseline_inputs_expose_only_actual_units_and_their_fingerprint(self):
        units = [unit('sifen', 'sifen:39', revision='two'), unit('sifen', 'sifen:38', revision='one')]
        unavailable = [{'source_id': 'jiuzhi', 'reason': 'source_changed'}]
        with patch('workbench.term_index_corpus.current_effective_units', return_value=(units, unavailable)):
            inputs = baseline_corpus_inputs('.')

        self.assertEqual(inputs['corpus_fingerprint'], fingerprint_effective_units(units))
        self.assertIn('producer_identity', inputs)
        self.assertNotEqual(inputs['fingerprint'], inputs['corpus_fingerprint'])
        self.assertEqual(inputs['units'], units)
        self.assertEqual(inputs['unavailable'], unavailable)
        self.assertNotIn('source_selection', inputs)

    def test_producer_identity_change_invalidates_the_same_corpus_state(self):
        units = [unit('sifen', 'sifen:38')]
        with patch('workbench.term_index_corpus.current_effective_units', return_value=(units, [])), \
             patch('workbench.term_index_corpus.term_index_producer_identity', side_effect=[{'sha256': 'one'}, {'sha256': 'two'}], create=True):
            first = baseline_corpus_inputs('.')
            second = baseline_corpus_inputs('.')

        self.assertEqual(first['corpus_fingerprint'], second['corpus_fingerprint'])
        self.assertNotEqual(first['fingerprint'], second['fingerprint'])

    def test_producer_identity_covers_the_complete_analysis_projection_chain(self):
        names = set(term_index_producer_files())
        self.assertTrue({
            'analysis_parser/syntax_ir.py',
            'analysis_parser/context_compiler.py',
            'analysis_parser/inputs.py',
            'adjudication/compiler.py',
            'domain_kernel/engine.py',
            'workbench/annotation_projection.py',
            'workbench/semantic_projection.py',
            'workbench/term_index.py',
            'config/workbench-procedures.json',
        }.issubset(names))

    def test_effective_unit_fingerprint_uses_identity_and_version(self):
        first = [unit('sifen', 'sifen:38'), unit('sifen', 'sifen:39')]
        changed = deepcopy(first)
        changed[1]['effective_revision'] = 'review-b'

        self.assertEqual(fingerprint_effective_units(first), fingerprint_effective_units(list(reversed(first))))
        self.assertNotEqual(fingerprint_effective_units(first), fingerprint_effective_units(changed))

    def test_collector_builds_one_multi_projection_baseline_index_without_review_jobs(self):
        units = [unit('sifen', 'sifen:38'), unit('sifen', 'sifen:39')]
        projections = {
            'sifen:38': projection('sifen', 'sifen:38', 'sifen:38', 'r38', '月'),
            'sifen:39': projection('sifen', 'sifen:39', 'sifen:39', 'r39', '月'),
        }
        before = deepcopy(units)
        with patch('workbench.term_index_corpus.current_effective_units', return_value=(units, [])), \
             patch('workbench.term_index_corpus.project_baseline_unit', side_effect=lambda root, item: projections[item['unit_id']]), \
             patch('workbench.service.resolve_current_review_job') as resolve, \
             patch('workbench.service.create_fresh_review_job') as create:
            result = collect_baseline_term_index('.')

        self.assertEqual(units, before)
        self.assertEqual(result['kind'], 'baseline_corpus')
        self.assertEqual(result['index']['schema'], 'TermIndex/1')
        self.assertEqual(len(result['included']), 2)
        self.assertEqual(result['unavailable'], [])
        self.assertEqual(result['index']['entries'][0]['surface'], '月')
        self.assertEqual(len(result['index']['entries'][0]['occurrences']), 2)
        resolve.assert_not_called()
        create.assert_not_called()

    def test_duplicate_projection_source_identity_and_admitted_projection_failure_fail_closed(self):
        units = [unit('sifen', 'sifen:38'), unit('sifen', 'sifen:39')]
        duplicate = projection('sifen', 'same', 'same', 'r', '月')
        with patch('workbench.term_index_corpus.current_effective_units', return_value=(units, [])), \
             patch('workbench.term_index_corpus.project_baseline_unit', return_value=duplicate):
            with self.assertRaisesRegex(ValueError, 'duplicate_projection_source_identity'):
                collect_baseline_term_index('.')
        with patch('workbench.term_index_corpus.current_effective_units', return_value=(units, [])), \
             patch('workbench.term_index_corpus.project_baseline_unit', side_effect=RuntimeError('bad projection')):
            with self.assertRaisesRegex(ValueError, 'baseline_projection_failed'):
                collect_baseline_term_index('.')

    def test_unavailable_sources_are_explicit_and_empty_collection_has_no_index(self):
        unavailable = [{'source_id': 'jiuzhi', 'reason': 'source_changed'}]
        with patch('workbench.term_index_corpus.current_effective_units', return_value=([], unavailable)):
            result = collect_baseline_term_index('.')

        self.assertIsNone(result['index'])
        self.assertEqual(result['included'], [])
        self.assertEqual(result['unavailable'], unavailable)


if __name__ == '__main__':
    unittest.main()
