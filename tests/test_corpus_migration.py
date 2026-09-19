"""Rule migration preserves exact source-backed decisions and old baseline replay."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from source_adapters import corpus_index as index, corpus_review as review
from source_adapters.dependencies import unit_hash

ROOT = Path(__file__).resolve().parents[1]
ACTOR = {'type': 'scripted_test', 'id': 'migration-test'}


class MigrationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / 'config').mkdir()
        shutil.copyfile(ROOT / 'config/calendrical-ir-pipeline.json', self.root / 'config/calendrical-ir-pipeline.json')
        for p in ROOT.glob('calendars-*.md'):
            shutil.copyfile(p, self.root / p.name)
        auto = index.build_auto_index(self.root)
        auto['units'] = index._resolve_relations(auto['units'])
        auto['method']['segmentation_rules'] = 'old-test-baseline'
        members = [u for u in auto['units'] if u['sections'] in ([49], [50])]
        merged = index._new_unit([s for u in members for s in u['source_spans']], 'procedure', 'medium', 'old-forced-query')
        auto['units'] = index._normalize([u for u in auto['units'] if u not in members] + [merged])
        unreviewed = [u for u in auto['units'] if u['sections'] in ([55], [56])]
        old_group = index._new_unit([s for u in unreviewed for s in u['source_spans']], 'procedure', 'medium', 'old-forced-query')
        auto['units'] = index._normalize([u for u in auto['units'] if u not in unreviewed] + [old_group])
        review._save(self.root, auto, {'operations': []})
        state = review.load(self.root)
        review.apply(self.root, 'accept', index.unit_anchor(merged), {}, revision=state['revision'], actor=ACTOR)
        state = review.load(self.root)
        target = next(u for u in state['effective']['units'] if u['sections'] == [23])
        review.apply(self.root, 'set_type', index.unit_anchor(target), {'type': 'discourse'}, revision=state['revision'], actor=ACTOR)
        self.old = review.load(self.root)
        self.raw = {p.name: p.read_bytes() for p in (*review.paths(self.root), review.workspace(self.root) / 'manifest.json')}

    def migrate(self):
        self.assertTrue(callable(getattr(review, 'migrate_rules', None)), 'rule migration entry point is required')
        report = review.migrate_rules(self.root, apply=False)
        self.assertTrue(report['changes'])
        self.assertEqual(self.raw, {p.name: p.read_bytes() for p in (*review.paths(self.root), review.workspace(self.root) / 'manifest.json')})
        return review.migrate_rules(self.root, apply=True)

    def test_archive_report_and_current_reviewed_grouping_are_preserved(self):
        report = self.migrate()
        archive = self.root / report['archive']
        self.assertEqual(self.raw, {name: (archive / name).read_bytes() for name in self.raw})
        self.assertTrue((archive / 'migration-report.json').exists())
        state = review.load(self.root)
        self.assertFalse(state['stale'])
        self.assertEqual(state['overrides']['history'], self.old['overrides']['history'])
        self.assertTrue(any(u['sections'] == [49] for u in state['auto']['units']))
        actual = next(u for u in state['effective']['units'] if u['sections'] == [49, 50])
        original = next(u for u in self.old['effective']['units'] if u['sections'] == [49, 50])
        for field in ('id', 'type', 'text_original', 'human_review'):
            self.assertEqual(actual[field], original[field])

    def test_every_historical_side_and_undo_use_original_baseline(self):
        expected = [review.history_states(self.old, h) for h in self.old['overrides']['history']]
        self.migrate()
        state = review.load(self.root)
        self.assertEqual([review.history_states(state, h) for h in state['overrides']['history']], expected)
        entry = state['overrides']['history'][-1]
        untouched = {u['id']: (unit_hash(u), u['human_review']) for u in state['effective']['units']
                     if not index.overlaps(entry['source_spans'], index.unit_anchor(u))}
        result = review.apply(self.root, 'undo', entry['source_spans'], {}, revision=state['revision'], actor=ACTOR)
        self.assertEqual({u['id']: (unit_hash(u), u['human_review']) for u in result['effective']['units']
                          if not index.overlaps(entry['source_spans'], index.unit_anchor(u))}, untouched)
        self.assertEqual([(index.unit_anchor(u), u['type']) for u in result['effective']['units']
                          if index.overlaps(entry['source_spans'], index.unit_anchor(u))],
                         [(index.unit_anchor(u), u['type']) for u in expected[-1][0]
                          if index.overlaps(entry['source_spans'], index.unit_anchor(u))])
        review.regenerate(self.root)
        self.assertFalse(review.load(self.root)['stale'])

    def test_actual_archived_event15_undo_preserves_all_unaffected_unit_hashes(self):
        # Read-only live source; all actions take place in a disposable copy.
        fixture = self.root / 'actual-workspace'
        shutil.copytree(ROOT / 'config', fixture / 'config')
        for path in ROOT.glob('calendars-*.md'):
            shutil.copyfile(path, fixture / path.name)
        # Use the immutable pre-migration fixture, not today's mutable review state.
        current = json.loads((ROOT / 'corpus-review/sifen/overrides.json').read_bytes())
        archive = ROOT / next(m['archive'] for m in current['rule_migrations'] if m['through_revision'] == 15)
        target = fixture / 'corpus-review/sifen'
        target.mkdir(parents=True)
        for name in ('auto.json', 'overrides.json', 'effective.json', 'manifest.json'):
            shutil.copyfile(archive / name, target / name)
        review.migrate_rules(fixture, apply=True)
        state = review.load(fixture)
        entry = next(h for h in state['overrides']['history'] if h['revision'] == 15)
        self.assertEqual(review.active_history(state['overrides'])[-1]['revision'], 15)
        untouched = {u['id']: (unit_hash(u), u['human_review']) for u in state['effective']['units']
                     if not index.overlaps(entry['source_spans'], index.unit_anchor(u))}
        result = review.apply(fixture, 'undo', entry['source_spans'], {}, revision=state['revision'], actor=ACTOR)
        self.assertEqual({u['id']: (unit_hash(u), u['human_review']) for u in result['effective']['units']
                          if not index.overlaps(entry['source_spans'], index.unit_anchor(u))}, untouched)
        self.assertEqual(result['overrides']['history'][-1]['reverts'], 15)

    def test_restore_old_grouping_preserves_unrelated_new_work(self):
        self.migrate()
        state = review.load(self.root)
        target = next(u for u in state['effective']['units'] if u['sections'] == [38])
        state = review.apply(self.root, 'set_type', index.unit_anchor(target), {'type': 'discourse'}, revision=state['revision'], actor=ACTOR)
        event = self.old['overrides']['history'][0]
        untouched = {u['id']: (unit_hash(u), u['human_review']) for u in state['effective']['units']
                     if not index.overlaps(event['source_spans'], index.unit_anchor(u))}
        state = review.apply(self.root, 'restore_revision', event['source_spans'], {'revision_id': 1, 'side': 'after'}, revision=state['revision'], actor=ACTOR)
        self.assertEqual(next(u for u in state['effective']['units'] if u['sections'] == [38])['type'], 'discourse')
        self.assertTrue(next(u for u in state['effective']['units'] if u['sections'] == [49, 50])['human_review'])
        self.assertEqual({u['id']: (unit_hash(u), u['human_review']) for u in state['effective']['units']
                          if not index.overlaps(event['source_spans'], index.unit_anchor(u))}, untouched)
        # Reset splits the historical group; an incoming relation must then
        # resolve to its two current targets. Truly unrelated units stay exact.
        independent = {u['id'] for u in state['effective']['units'] if u['id'] in untouched
                       and not any(index.overlaps(event['source_spans'], r.get('target_spans', []))
                                   for r in u['relations'])}
        state = review.apply(self.root, 'reset', event['source_spans'], {}, revision=state['revision'], actor=ACTOR)
        self.assertEqual({u['id']: (unit_hash(u), u['human_review']) for u in state['effective']['units']
                          if u['id'] in independent}, {key: untouched[key] for key in independent})

    def test_repeat_migration_is_noop_and_archive_tampering_blocks_replay(self):
        report = self.migrate()
        frozen = [p.read_bytes() for p in review.paths(self.root)]
        self.assertTrue(review.migrate_rules(self.root, apply=True)['already_current'])
        self.assertEqual(frozen, [p.read_bytes() for p in review.paths(self.root)])
        archive = self.root / report['archive'] / 'auto.json'
        archive.write_bytes(archive.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'history_archive_changed'):
            review.load(self.root)

    def test_nonunique_reviewed_to_mixed_region_reports_question_without_write(self):
        from unittest.mock import patch
        candidate = index.build_auto_index(self.root)
        affected = [u for u in candidate['units'] if u['sections'] in ([48], [49], [50])]
        candidate['units'] = index._resolve_relations(candidate['units'])
        merged = index._new_unit([s for u in affected for s in u['source_spans']], 'procedure', 'medium', 'test')
        candidate['units'] = index._normalize([u for u in candidate['units'] if u not in affected] + [merged])
        self.assertTrue(callable(getattr(review, 'migrate_rules', None)))
        with patch.object(index, 'build_auto_index', return_value=candidate):
            report = review.migrate_rules(self.root, apply=True)
        self.assertTrue(report['pending_questions'])
        self.assertEqual(self.raw, {p.name: p.read_bytes() for p in (*review.paths(self.root), review.workspace(self.root) / 'manifest.json')})


if __name__ == '__main__':
    unittest.main()
