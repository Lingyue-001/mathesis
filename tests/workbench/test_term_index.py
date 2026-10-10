"""TermIndex/1 consumes only ScholarSourceProjection/1 records."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from source_adapters.corpus import build_source_packet_from_units
from tests.workbench.test_scholar_source_projection import ScholarSourceProjectionTests
from workbench.term_index import build_term_index, export_term_index, serialize_term_index


def projection(source_id, unit_id, doc_id, reading_id, text, terms):
    for row in terms:
        row['source_anchor']['doc_id'] = doc_id
        row['source_anchor']['reading_id'] = reading_id
    return {
        'schema': 'ScholarSourceProjection/1',
        'source': {
            'source_id': source_id,
            'unit_id': unit_id,
            'doc_id': doc_id,
            'reading_id': reading_id,
            'text': text,
            'text_sha256': 'sha-' + doc_id,
        },
        'terms': terms,
    }


def term(ident, surface, start, end, level):
    return {
        'id': ident,
        'surface': surface,
        'display_level': level,
        'source_anchor': {
            'doc_id': 'unused-by-builder',
            'reading_id': 'unused-by-builder',
            'start': start,
            'end': end,
            'quote': surface,
            'offset_unit': 'unicode_code_point',
        },
        'children': [],
        'composition_alternatives': [],
    }


class TermIndexTests(unittest.TestCase):
    def test_exact_surface_groups_distinct_occurrences_and_derives_both(self):
        first = projection('source-a', 'unit-a', 'doc-a', 'reading-a', '月法', [
            term('term:a:0-1', '月', 0, 1, 'maximal'),
            term('term:a:1-2', '法', 1, 2, 'maximal'),
        ])
        second = projection('source-b', 'unit-b', 'doc-b', 'reading-b', '月', [
            term('term:b:0-1', '月', 0, 1, 'component'),
        ])

        index = build_term_index([first, second])

        self.assertEqual(index['schema'], 'TermIndex/1')
        self.assertEqual([entry['surface'] for entry in index['entries']], ['月', '法'])
        moon = index['entries'][0]
        self.assertEqual(moon['occurrence_classification'], 'both')
        self.assertEqual(moon['counts'], {
            'maximal_occurrences': 1,
            'component_occurrences': 1,
            'appears_in_compounds': 0,
        })
        self.assertEqual(len(moon['occurrences']), 2)
        self.assertEqual(
            {tuple(record['identity'][key] for key in ('source_id', 'unit_id', 'doc_id', 'reading_id', 'start', 'end'))
             for record in moon['occurrences']},
            {
                ('source-a', 'unit-a', 'doc-a', 'reading-a', 0, 1),
                ('source-b', 'unit-b', 'doc-b', 'reading-b', 0, 1),
            },
        )
        self.assertEqual(moon['direct_parent_occurrences'], [])
        self.assertEqual(moon['compound_ancestor_occurrences'], [])

    def test_builder_does_not_mutate_projection_inputs_and_sorts_occurrences(self):
        item = projection('source-b', 'unit-b', 'doc-b', 'reading-b', '甲乙', [
            term('term:b:1-2', '乙', 1, 2, 'maximal'),
            term('term:b:0-1', '乙', 0, 1, 'maximal'),
        ])
        before = deepcopy(item)

        index = build_term_index([item])

        self.assertEqual(item, before)
        records = index['entries'][0]['occurrences']
        self.assertEqual([record['identity']['start'] for record in records], [0, 1])

    def test_recorded_composition_tracks_direct_and_recursive_parents(self):
        root = term('term:root', '入蔀積月', 0, 4, 'maximal')
        root['children'] = ['term:compound']
        root['composition_alternatives'] = [['term:compound'], ['term:compound']]
        compound = term('term:compound', '積月', 2, 4, 'component')
        compound['children'] = ['term:moon']
        compound['composition_alternatives'] = [['term:moon']]
        moon = term('term:moon', '月', 3, 4, 'component')
        index = build_term_index([projection('source-a', 'unit-a', 'doc-a', 'reading-a', '入蔀積月',
                                             [root, compound, moon])])

        entry = next(item for item in index['entries'] if item['surface'] == '月')
        self.assertEqual(
            [(identity['start'], identity['end']) for identity in entry['direct_parent_occurrences']],
            [(2, 4)],
        )
        self.assertEqual(
            [(identity['start'], identity['end']) for identity in entry['compound_ancestor_occurrences']],
            [(0, 4), (2, 4)],
        )
        self.assertEqual(entry['counts']['appears_in_compounds'], 2)

    def test_composition_never_uses_surface_containment(self):
        root = term('term:root', '積月', 0, 2, 'maximal')
        moon = term('term:moon', '月', 1, 2, 'component')
        index = build_term_index([projection('source-a', 'unit-a', 'doc-a', 'reading-a', '積月', [root, moon])])

        entry = next(item for item in index['entries'] if item['surface'] == '月')
        self.assertEqual(entry['direct_parent_occurrences'], [])
        self.assertEqual(entry['compound_ancestor_occurrences'], [])
        self.assertEqual(entry['counts']['appears_in_compounds'], 0)

    def test_rejects_duplicate_projection_source_identity(self):
        first = projection('source-a', 'unit-a', 'doc-a', 'reading-a', '月', [
            term('term:a:0-1', '月', 0, 1, 'maximal'),
        ])
        second = deepcopy(first)
        second['terms'] = [term('term:a:0-1', '法', 0, 1, 'maximal')]

        with self.assertRaisesRegex(ValueError, 'duplicate_projection_source_identity'):
            build_term_index([first, second])

    def test_rejects_unresolved_recorded_composition_child(self):
        root = term('term:root', '積月', 0, 2, 'maximal')
        root['children'] = ['term:missing']

        with self.assertRaisesRegex(ValueError, 'unresolved_composition_child'):
            build_term_index([projection('source-a', 'unit-a', 'doc-a', 'reading-a', '積月', [root])])

    def test_rejects_non_list_projection_terms(self):
        invalid = projection('source-a', 'unit-a', 'doc-a', 'reading-a', '月', [
            term('term:a:0-1', '月', 0, 1, 'maximal'),
        ])
        invalid['terms'] = {'term:a:0-1': invalid['terms'][0]}

        with self.assertRaisesRegex(ValueError, 'requires_projection_terms_list'):
            build_term_index([invalid])

    def test_rejects_invalid_unicode_source_anchor(self):
        for patch in (
            {'start': 1, 'end': 1},
            {'start': -1, 'end': 1},
            {'offset_unit': 'byte'},
            {'doc_id': 'other-doc'},
            {'reading_id': 'other-reading'},
        ):
            with self.subTest(patch=patch):
                invalid = projection('source-a', 'unit-a', 'doc-a', 'reading-a', '月', [
                    term('term:a:0-1', '月', 0, 1, 'maximal'),
                ])
                invalid['terms'][0]['source_anchor'].update(patch)

                with self.assertRaisesRegex(ValueError, 'requires_unicode_source_anchor'):
                    build_term_index([invalid])

    def test_occurrence_local_semantic_material_is_copied_without_entry_status(self):
        first_term = term('term:a:0-1', '月', 0, 1, 'maximal')
        first_term.update({
            'semantic_candidates': [{
                'candidate_id': 'candidate-a',
                'status': 'reviewed',
                'support_status': 'supported',
                'constraint_status': 'satisfied',
                'authorization_status': 'authorized',
            }],
            'reviewed_claims': [{'claim_id': 'claim-a'}],
            'semantic_assertions': [{'assertion_id': 'assertion-a'}],
            'derived_assertions': [{'assertion_id': 'derived-a'}],
            'semantic_conflicts': [{'conflict_id': 'conflict-a'}],
            'decision_refs': [{'decision_id': 'decision-a'}],
            'review_facets': ['term_interpretation'],
            'evidence': [{'candidate_id': 'candidate-a'}],
        })
        index = build_term_index([
            projection('source-a', 'unit-a', 'doc-a', 'reading-a', '月', [first_term]),
            projection('source-b', 'unit-b', 'doc-b', 'reading-b', '月', [
                term('term:b:0-1', '月', 0, 1, 'component'),
            ]),
        ])

        entry = index['entries'][0]
        first = next(record for record in entry['occurrences'] if record['identity']['doc_id'] == 'doc-a')
        second = next(record for record in entry['occurrences'] if record['identity']['doc_id'] == 'doc-b')
        self.assertEqual(first['semantic_candidates'], first_term['semantic_candidates'])
        self.assertEqual(first['reviewed_claims'], first_term['reviewed_claims'])
        self.assertEqual(first['semantic_assertions'], first_term['semantic_assertions'])
        self.assertEqual(first['derived_assertions'], first_term['derived_assertions'])
        self.assertEqual(first['semantic_conflicts'], first_term['semantic_conflicts'])
        self.assertEqual(first['decision_refs'], first_term['decision_refs'])
        self.assertEqual(first['review_facets'], first_term['review_facets'])
        self.assertEqual(first['evidence'], first_term['evidence'])
        self.assertFalse(any(key in entry for key in ('status', 'authorization_status', 'epistemic_status')))
        self.assertEqual(second.get('semantic_candidates', []), [])

    def test_serializer_and_explicit_export_are_deterministic(self):
        index = build_term_index([projection('source-a', 'unit-a', 'doc-a', 'reading-a', '月', [
            term('term:a:0-1', '月', 0, 1, 'maximal'),
        ])])

        serialized = serialize_term_index(index)
        self.assertTrue(serialized.endswith('\n'))
        self.assertEqual(serialized, serialize_term_index(index))
        self.assertEqual(json.loads(serialized), index)
        with tempfile.TemporaryDirectory() as temp:
            target = export_term_index(index, Path(temp) / 'term-index.json')
            self.assertEqual(target.read_text(encoding='utf-8'), serialized)
        with self.assertRaisesRegex(ValueError, 'serializer_requires_v1'):
            serialize_term_index({'schema': 'Other/1'})


if __name__ == '__main__':
    unittest.main()


class TermIndexIntegrationTests(unittest.TestCase):
    @staticmethod
    def _projection(primary, context=()):
        packet = build_source_packet_from_units('.', 'sifen', [primary], list(context), {})
        return ScholarSourceProjectionTests().project(packet)[0]

    @staticmethod
    def _identity(source, row):
        return (source['source_id'], source['unit_id'], source['doc_id'], source['reading_id'],
                row['source_anchor']['start'], row['source_anchor']['end'])

    def _assert_cross_source_case(self, section38):
        section39 = self._projection('sifen:section:39')
        index = build_term_index([section38, section39])

        self.assertEqual(index['schema'], 'TermIndex/1')
        self.assertEqual(
            {(source['source_id'], source['unit_id'], source['doc_id'], source['reading_id'])
             for source in index['sources']},
            {
                (section38['source']['source_id'], section38['source']['unit_id'],
                 section38['source']['doc_id'], section38['source']['reading_id']),
                (section39['source']['source_id'], section39['source']['unit_id'],
                 section39['source']['doc_id'], section39['source']['reading_id']),
            },
        )
        expected_counts = {}
        for projected in (section38, section39):
            for row in projected['terms']:
                expected_counts[row['surface']] = expected_counts.get(row['surface'], 0) + 1
        self.assertEqual(
            {entry['surface']: len(entry['occurrences']) for entry in index['entries']},
            expected_counts,
        )
        self.assertEqual(next(entry for entry in index['entries'] if entry['surface'] == '積月')
                         ['occurrence_classification'], 'both')
        self.assertTrue(any(len(entry['compound_ancestor_occurrences']) > len(entry['direct_parent_occurrences'])
                            for entry in index['entries']))

        actual = {
            (record['identity']['source_id'], record['identity']['unit_id'],
             record['identity']['doc_id'], record['identity']['reading_id'],
             record['identity']['start'], record['identity']['end']): record
            for entry in index['entries'] for record in entry['occurrences']
        }
        for projected in (section38, section39):
            for row in projected['terms']:
                record = actual[self._identity(projected['source'], row)]
                self.assertEqual(record['projection_term_id'], row['id'])
                self.assertEqual(record['source_anchor'], row['source_anchor'])
                for field in ('semantic_candidates', 'reviewed_claims', 'semantic_assertions',
                              'derived_assertions', 'semantic_conflicts', 'decision_refs', 'review_facets', 'evidence'):
                    self.assertEqual(record.get(field), row.get(field))

    def test_real_case_a_combines_proc38_no_context_and_proc39(self):
        self._assert_cross_source_case(self._projection('sifen:section:38'))

    def test_real_case_b_combines_proc38_section15_context_and_proc39(self):
        self._assert_cross_source_case(self._projection('sifen:section:38', ['sifen:section:15']))

    def test_real_contextual_proc38_snapshots_are_rejected_as_duplicate_sources(self):
        no_context = self._projection('sifen:section:38')
        with_context = self._projection('sifen:section:38', ['sifen:section:15'])

        with self.assertRaisesRegex(ValueError, 'duplicate_projection_source_identity'):
            build_term_index([no_context, with_context])
