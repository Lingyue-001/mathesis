"""Real file-backed review round trips; no live corpus or human records touched."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from source_adapters import corpus_index as index
from source_adapters import corpus_review as review

ROOT = Path(__file__).resolve().parents[1]
ACTOR = {'type': 'scripted_test', 'id': 'segmentation-tests'}


def _review_app(root):
    import streamlit as st
    from tools.parser_inspector.segmentation_review import render, render_full_text
    st.set_page_config(layout='wide')
    if st.session_state.get('inspector_page') == 'Corpus Full Text':
        render_full_text(root)
    else:
        render(root)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'config').mkdir(parents=True)
        for name in ('calendrical-ir-pipeline.json', 'workbench-procedures.json'):
            shutil.copyfile(ROOT / 'config' / name, self.root / 'config' / name)
        shutil.copyfile(ROOT / 'calendars-四分历.md', self.root / 'calendars-四分历.md')
        review.regenerate(self.root)

    def state(self):
        return review.load(self.root)

    @unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit tests run with inspector venv')
    def test_full_text_reads_effective_in_source_order_and_returns_to_selected_review(self):
        from streamlit.testing.v1 import AppTest
        self.act('set_type', self.unit(38), type='discourse')
        self.act('split_unit', self.unit(39), boundaries=[3])
        frozen = [p.read_bytes() for p in review.paths(self.root)]
        app = AppTest.from_function(_review_app, args=(str(self.root),), default_timeout=30).run()
        app.text_input(key='seg_reviewer').set_value('full-text-reader').run()
        app.selectbox(key='seg_actor').select('scripted_test').run()
        position = next(i for i,u in enumerate(self.state()['auto']['units']) if u['sections'] == [40])
        app.selectbox(key='seg_auto:sifen').select(position).run()
        app.button(key='seg_full_text').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['inspector_page'], 'Corpus Full Text')
        html = next(h.value for h in app.get('html') if 'seg-full-text' in h.value)
        from html import escape
        offsets = [html.index(f'data-unit-id="{escape(u["id"], quote=True)}"') for u in self.state()['effective']['units']]
        self.assertEqual(offsets, sorted(offsets))
        for unit in self.state()['effective']['units']:
            self.assertIn(escape(unit['text_original']), html)
        app.button(key='seg_back_review').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key='seg_auto:sifen').value, position)
        self.assertEqual(app.text_input(key='seg_reviewer').value, 'full-text-reader')
        self.assertEqual(app.selectbox(key='seg_actor').value, 'scripted_test')
        self.assertEqual(frozen, [p.read_bytes() for p in review.paths(self.root)])

    def test_registered_calendars_have_isolated_workspaces_and_manifest_hashes(self):
        import hashlib
        for filename in ('calendars-三统历.md', 'calendars-九执历.md'):
            shutil.copyfile(ROOT / filename, self.root / filename)
        (self.root / 'calendars-未登记.md').write_text('1 待登记。', encoding='utf-8')
        self.assertEqual({s['id'] for s in index.list_review_sources(self.root)}, {'sifen', 'santong', 'jiuzhi'})
        frozen = [p.read_bytes() for p in review.paths(self.root)]
        for source_id in ('santong', 'jiuzhi'):
            review.regenerate(self.root, source_id=source_id)
            state = review.load(self.root, source_id=source_id)
            units = state['auto']['units']
            self.assertEqual(len({u['id'] for u in units}), len(units))
            self.assertTrue(all(u['id'].startswith(source_id + ':') for u in units))
            review.apply(self.root, 'accept', index.unit_anchor(units[0]), {},
                         source_id=source_id, revision=state['revision'], actor=ACTOR)
            manifest = json.loads((self.root / 'corpus-review' / source_id / 'manifest.json').read_bytes())
            self.assertEqual(manifest['review_status']['reviewed'], 1)
            for label, path in zip(('auto', 'override', 'effective'), review.paths(self.root, source_id)):
                self.assertEqual(manifest[label + '_sha'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(frozen, [p.read_bytes() for p in review.paths(self.root)])
        # One occurrence can be modified without editing the same numbered section in another volume.
        state = review.load(self.root, 'jiuzhi')
        firsts = [u for u in state['auto']['units'] if u['sections'] == [1]]
        self.assertEqual(len(firsts), 2)
        from source_adapters.corpus import build_source_packet_from_units
        documents = build_source_packet_from_units(
            self.root, 'jiuzhi', [u['id'] for u in firsts], provided_scope='fixture')['primary_documents']
        self.assertEqual(len({d['doc_id'] for d in documents}), 2)
        result = review.apply(self.root, 'split_unit', index.unit_anchor(firsts[1]), {'boundaries': [2]},
                              source_id='jiuzhi', revision=state['revision'], actor=ACTOR)
        self.assertEqual(result['auto']['units'][0]['human_review'][-1]['status'], 'accepted')
        self.assertFalse(result['stale'])
        with self.assertRaises(ValueError):
            review.load(self.root, '../sifen')

    def test_legacy_migration_preserves_review_and_undo(self):
        self.act('accept', self.unit())
        state = self.state()
        legacy = [self.root / 'tmp/corpus-index/sifen-units.auto.json',
                  self.root / 'config/corpus-review/sifen-segmentation-overrides.json',
                  self.root / 'tmp/corpus-index/sifen-units.effective.json']
        for old, new in zip(legacy, review.paths(self.root)):
            old.parent.mkdir(parents=True, exist_ok=True)
            old.write_bytes(new.read_bytes())
            new.unlink()
        (self.root / 'corpus-review/sifen/manifest.json').unlink()
        review.regenerate(self.root)
        self.assertEqual(state['auto'], self.state()['auto'])
        self.assertEqual(state['overrides'], self.state()['overrides'])
        self.assertTrue(all(not p.exists() for p in legacy))
        self.act('undo', self.unit())
        self.assertEqual(self.unit(layer='auto')['human_review'], [])

    def act(self, action, unit, **payload):
        state = self.state()
        return review.apply(self.root, action, index.unit_anchor(unit), payload,
                            revision=state['revision'], actor=ACTOR, note='software acceptance')

    def unit(self, section=38, layer='effective'):
        return next(u for u in self.state()[layer]['units'] if u['sections'] == [section])

    def test_accept_preserves_machine_and_survives_regeneration(self):
        machine = self.state()['auto']
        self.act('accept', self.unit(layer='auto'))
        reviewed = self.unit(layer='auto')['human_review'][-1]
        self.assertEqual(reviewed['status'], 'accepted')
        self.assertEqual(reviewed['actor'], ACTOR)
        self.assertEqual(self.state()['overrides']['operations'], [])
        review.regenerate(self.root)
        after = self.state()['auto']
        self.assertEqual(self.unit(layer='auto')['human_review'][-1], reviewed)
        for unit in after['units']:
            unit['human_review'] = []
        self.assertEqual(after, machine)

    def test_revision_history_survives_undo_and_revision_has_before_after(self):
        self.act('accept', self.unit(layer='auto'))
        self.act('set_type', self.unit(), type='discourse')
        saved = copy.deepcopy(self.state()['overrides']['history'])
        self.act('undo', self.unit())
        history = self.state()['overrides']['history']
        self.assertEqual(len(history), 3)
        self.assertEqual(history[:2], saved)
        self.assertEqual([h['revision'] for h in history], [1, 2, 3])
        self.assertEqual(history[-1]['reverts'], 2)
        self.assertEqual(history[1]['supersedes'], [1])
        self.assertEqual(self.unit()['type'], 'procedure')
        before, after = review.history_states(self.state(), history[1])
        self.assertEqual(next(u for u in before if u['sections'] == [38])['type'], 'procedure')
        self.assertEqual(next(u for u in after if u['sections'] == [38])['type'], 'discourse')
        self.act('undo', self.unit())
        self.assertEqual(self.unit(layer='auto')['human_review'], [])
        self.assertEqual(len(self.state()['overrides']['history']), 4)
        self.act('set_type', self.unit(), type='heading')
        self.assertEqual(self.state()['overrides']['history'][-1]['revision'], 5)

    def test_type_and_relations_are_replayed_and_undo_restores_exact_state(self):
        original = self.state()
        self.act('set_type', self.unit(), type='alternative_procedure')
        self.assertEqual(self.unit()['type'], 'alternative_procedure')
        self.assertEqual(self.unit(layer='auto')['type'], 'procedure')
        record = self.unit(layer='auto')['human_review'][-1]
        self.assertEqual(record['status'], 'modified')
        self.assertTrue(record['override_ids'])
        self.act('set_relations', self.unit(), relations=[{
            'kind': 'alternative_of', 'target_spans': index.unit_anchor(self.unit(15))}])
        state = self.state()
        self.assertEqual(index.effective_from_auto(state['auto'], state['overrides'])['units'], state['effective']['units'])
        self.assertEqual(self.unit()['relations'][0]['target_id'], 'sifen:section:15')
        self.act('undo', self.unit())
        self.act('undo', self.unit())
        self.assertEqual(self.state()['auto'], original['auto'])
        self.assertEqual(self.state()['effective']['units'], original['effective']['units'])

    def test_merge_split_merge_uses_character_anchors_and_preserves_auto(self):
        auto_before = copy.deepcopy(self.state()['auto']['units'])
        unit = self.unit()
        self.act('merge_down', unit)
        merged = next(u for u in self.state()['effective']['units'] if 38 in u['sections'])
        self.assertIn(39, merged['sections'])
        self.act('split_unit', merged, boundaries=[3])
        pieces = [u for u in self.state()['effective']['units'] if 38 in u['sections']]
        self.assertEqual(pieces[0]['text_original'], unit['text_original'][:3])
        self.act('merge_down', pieces[0])
        merged_again = next(u for u in self.state()['effective']['units'] if 38 in u['sections'])
        self.assertEqual(index.unit_anchor(merged_again), index.unit_anchor(merged))
        self.act('split_unit', merged_again, boundaries=[len(unit['text_original'])])
        self.assertEqual(self.unit()['text_original'], unit['text_original'])
        self.act('reset', self.unit())
        for before, after in zip(auto_before, self.state()['auto']['units']):
            self.assertEqual(before, after)
        self.assertEqual(self.state()['overrides']['operations'], [])

    def test_merge_keeps_active_unit_metadata_instead_of_importing_neighbor_alternative(self):
        for sections, action in [([49], 'merge_up'), ([47], 'merge_down')]:
            with self.subTest(sections=sections, action=action):
                before = self.state()
                active = next(u for u in before['effective']['units'] if u['sections'] == sections)
                neighbor = next(u for u in before['effective']['units'] if u['sections'] == [48])
                self.act(action, active)
                merged = next(u for u in self.state()['effective']['units'] if 48 in u['sections'])
                state = self.state()
                self.act('undo', merged)
                self.assertEqual(merged['type'], active['type'])
                self.assertEqual(merged['relations'], active['relations'])
                ordered = sorted([active, neighbor], key=lambda u: u['source_spans'][0]['start'])
                self.assertEqual(merged['text_original'], ''.join(u['text_original'] for u in ordered))
                self.assertEqual(index.effective_from_auto(state['auto'], state['overrides'])['units'], state['effective']['units'])
                self.assertEqual(self.state()['effective']['units'], before['effective']['units'])

    def test_merge_preserves_active_explicit_relation_and_legacy_history(self):
        # Existing snapshots must still replay byte-for-byte; new UI actions pin
        # active metadata explicitly instead of changing legacy merge defaults.
        base = self.state()['auto']['units']
        active = next(u for u in base if u['sections'] == [49])
        neighbor = next(u for u in base if u['sections'] == [48])
        legacy = {'operations': [{'op':'merge_units', 'targets': [index.unit_anchor(neighbor), index.unit_anchor(active)]}]}
        old = next(u for u in index._apply_overrides(base, legacy) if 48 in u['sections'])
        self.assertEqual(old['type'], 'alternative_procedure')
        self.act('set_type', active, type='alternative_procedure')
        active = next(u for u in self.state()['effective']['units'] if u['sections'] == [49])
        self.act('set_relations', active, relations=[{'kind':'alternative_of', 'target_spans':index.unit_anchor(self.unit(38))}])
        active = next(u for u in self.state()['effective']['units'] if u['sections'] == [49])
        relations = index._anchored_relations(active['relations'], self.state()['effective']['units'])
        self.act('merge_up', active)
        merged = next(u for u in self.state()['effective']['units'] if 48 in u['sections'])
        self.assertEqual(index._anchored_relations(merged['relations'], self.state()['effective']['units']), relations)

    def test_stale_browser_and_source_changes_are_blocked_without_losing_review(self):
        old = self.state()
        self.act('accept', self.unit(layer='auto'))
        with self.assertRaisesRegex(ValueError, 'stale_page'):
            review.apply(self.root, 'set_type', index.unit_anchor(self.unit()), {'type': 'heading'},
                         revision=old['revision'], actor=ACTOR)
        before = [path.read_bytes() for path in review.paths(self.root)]
        source = self.root / 'calendars-四分历.md'
        source.write_bytes(source.read_bytes() + b'\r\n')
        self.assertTrue(self.state()['stale'])
        with self.assertRaisesRegex(ValueError, 'source_changed'):
            review.regenerate(self.root)
        with self.assertRaisesRegex(ValueError, 'source_changed'):
            self.act('accept', self.unit(layer='auto'))
        self.assertEqual(before, [path.read_bytes() for path in review.paths(self.root)])

    def test_illegal_spans_type_and_boundaries_never_write(self):
        before = [path.read_bytes() for path in review.paths(self.root)]
        for action, payload in [('set_type', {'type': 'new_ontology'}),
                                ('split_unit', {'boundaries': [0]}),
                                ('split_unit', {'boundaries': [999999]}),
                                ('set_relations', {'relations': [{'kind': 'alternative_of', 'target_spans': [[0, 1]]}]})]:
            with self.subTest(action=action), self.assertRaises(ValueError):
                self.act(action, self.unit(), **payload)
        self.assertEqual(before, [path.read_bytes() for path in review.paths(self.root)])

    def test_unchanged_save_is_not_a_modification_and_accept_cannot_mask_overrides(self):
        before = [path.read_bytes() for path in review.paths(self.root)]
        self.act('set_type', self.unit(), type=self.unit()['type'])
        self.act('set_relations', self.unit(), relations=self.unit()['relations'])
        self.assertEqual(before, [path.read_bytes() for path in review.paths(self.root)])
        self.act('set_type', self.unit(), type='discourse')
        with self.assertRaisesRegex(ValueError, 'reset_modified_unit'):
            self.act('accept', self.unit(layer='auto'))

    def test_relation_target_split_stays_anchored_and_requires_review(self):
        self.act('set_relations', self.unit(40), relations=[{
            'kind': 'alternative_of', 'target_spans': index.unit_anchor(self.unit(15))}])
        self.act('split_unit', self.unit(15), boundaries=[2])
        relation = self.unit(40)['relations'][0]
        self.assertEqual(len(relation['target_ids']), 2)
        self.assertEqual(relation['needs_review'], 'relation_target_split_or_self')
        self.assertTrue(any(q['kind'] == 'relation_target_split_or_self' for q in self.state()['effective']['review_queue']))

    def test_only_corpus_alternative_relations_are_editable(self):
        frozen = [p.read_bytes() for p in review.paths(self.root)]
        for kind in ('free_text', 'followup', 'dependency', 'data_flow', 'context_candidate'):
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'unsupported_corpus_relation'):
                self.act('set_relations', self.unit(40), relations=[{
                    'kind': kind, 'target_spans': index.unit_anchor(self.unit(39))}])
        self.assertEqual(frozen, [p.read_bytes() for p in review.paths(self.root)])
        machine = copy.deepcopy(self.unit(40, layer='auto'))
        self.assertEqual(machine['relations'][0]['kind'], 'alternative_of_candidate')
        self.act('set_relations', self.unit(40), relations=[{
            'kind': 'alternative_of', 'target_spans': index.unit_anchor(self.unit(39)),
            'basis': 'human_relation_review'}])
        self.assertEqual(self.unit(40)['relations'][0]['kind'], 'alternative_of')
        self.act('set_relations', self.unit(40), relations=[{
            'kind': 'alternative_of', 'target_spans': index.unit_anchor(self.unit(38))}])
        self.assertEqual(self.unit(40)['relations'][0]['target_id'], 'sifen:section:38')
        self.act('set_relations', self.unit(40), relations=[])
        self.assertEqual(self.unit(40)['relations'], [])
        self.assertEqual(self.unit(40, layer='auto'), {**machine, 'human_review': self.unit(40, layer='auto')['human_review']})

    def test_independent_procedure_cannot_acquire_alternative_and_retype_clears_it(self):
        before = [p.read_bytes() for p in review.paths(self.root)]
        with self.assertRaisesRegex(ValueError, 'alternative_requires_alternative_procedure'):
            self.act('set_relations', self.unit(38), relations=[{
                'kind':'alternative_of', 'target_spans':index.unit_anchor(self.unit(39))}])
        self.assertEqual(before, [p.read_bytes() for p in review.paths(self.root)])
        self.act('set_type', self.unit(40), type='procedure')
        self.assertEqual(self.unit(40)['relations'], [])
        self.assertEqual(self.unit(40)['type'], 'procedure')
        self.act('undo', self.unit(40))
        self.assertEqual(self.unit(40)['type'], 'alternative_procedure')
        self.assertEqual(len(self.unit(40)['relations']), 1)
        self.act('split_unit', self.unit(40), boundaries=[3])
        self.assertTrue(all(not u['relations'] for u in self.state()['effective']['units'] if 40 in u['sections']))

    def test_history_revert_is_local_restore_is_replayable_and_reset_all_is_undoable(self):
        initial = self.state()
        self.act('set_type', self.unit(38), type='discourse')  # rev 1
        self.act('accept', self.unit(15))  # unrelated rev 2
        self.act('revert_revision', self.unit(38), revision_id=1)
        self.assertEqual(self.unit(38)['type'], 'procedure')
        self.assertEqual(self.unit(15, 'auto')['human_review'][-1]['status'], 'accepted')
        self.assertNotIn(1, [h['revision'] for h in review.active_history(self.state()['overrides'])])
        self.act('undo', self.unit(38))
        self.assertEqual(self.unit(38)['type'], 'discourse')
        self.assertIn(1, [h['revision'] for h in review.active_history(self.state()['overrides'])])
        self.act('set_type', self.unit(38), type='heading')
        frozen = [p.read_bytes() for p in review.paths(self.root)]
        with self.assertRaisesRegex(ValueError, 'history_has_dependent_changes'):
            self.act('revert_revision', self.unit(38), revision_id=1)
        self.assertEqual(frozen, [p.read_bytes() for p in review.paths(self.root)])
        self.act('restore_revision', self.unit(38), revision_id=1, side='after')
        self.assertEqual(self.unit(38)['type'], 'discourse')
        self.assertEqual(self.unit(15, 'auto')['human_review'][-1]['status'], 'accepted')
        before_reset = self.state()
        all_units = {'source_spans':[s for u in before_reset['auto']['units'] for s in u['source_spans']]}
        self.act('reset', all_units)
        self.assertEqual(self.state()['auto']['units'], initial['auto']['units'])
        self.assertEqual(self.state()['effective']['units'], initial['effective']['units'])
        self.act('undo', self.unit(38))
        self.assertEqual(self.state()['effective']['units'], before_reset['effective']['units'])

    @unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit tests run with inspector venv')
    def test_legacy_bad_relation_can_be_deleted_directly_despite_incomplete_new_relation(self):
        # Reproduce the historic bad delta without asking today's action API to create it.
        state = self.state()
        target = next(u for u in state['auto']['units'] if u['sections'] == [49])
        state['overrides']['operations'] = [{'op':'set_relations', 'target_spans':index.unit_anchor(target),
            'relations':[{'kind':'alternative_of_candidate', 'target_spans':index.unit_anchor(self.unit(47)),
                          'basis':'nearest preceding procedure + marker 一術'}]}]
        state['overrides']['source_lock'] = {key: state['auto']['source'][key] for key in ('source_id', 'sha256')}
        review._save(self.root, state['auto'], state['overrides'])
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_function(_review_app, args=(str(self.root),), default_timeout=30).run()
        app.text_input(key='seg_reviewer').set_value('legacy-cleanup-test').run()
        app.selectbox(key='seg_actor').select('scripted_test').run()
        position = next(i for i,u in enumerate(self.state()['auto']['units']) if u['sections'] == [49])
        app.selectbox(key='seg_auto:sifen').select(position).run()
        app.button(key='seg_delete_relation:0:sifen').click().run()
        self.assertFalse(app.exception)
        unit = next(u for u in self.state()['effective']['units'] if u['sections'] == [49])
        self.assertEqual(unit['relations'], [])
        self.assertEqual(unit['type'], 'procedure')

    @unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit tests run with inspector venv')
    def test_ui_explains_types_and_confirms_candidate_with_fixed_choices(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_function(_review_app, args=(str(self.root),), default_timeout=30).run()
        app.text_input(key='seg_reviewer').set_value('UI-contract-test').run()
        app.selectbox(key='seg_actor').select('scripted_test').run()
        position = next(i for i,u in enumerate(self.state()['auto']['units']) if u['sections'] == [40])
        app.selectbox(key='seg_auto:sifen').select(position).run()
        self.assertFalse(any('关系' in item.label and '名称' in item.label for item in app.text_input))
        self.assertTrue(any('分块类型说明' in e.label for e in app.expander))
        kinds = next(s for s in app.selectbox if s.key.startswith('seg_relation_kind:'))
        self.assertEqual(set(kinds.options), {'alternative_of_candidate', 'alternative_of'})
        kinds.select('alternative_of').run()
        app.button(key='seg_save_relations:sifen').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(self.unit(40)['relations'][0]['kind'], 'alternative_of')

    def test_previews_end_at_first_punctuation_and_source_diff_uses_anchors(self):
        from tools.parser_inspector.segmentation_review import _label, _text_runs
        unit = self.unit(38)
        self.assertIn('推天正術 ·', _label(unit))
        self.assertNotIn('推天正術，', _label(unit))
        self.assertNotIn('置入蔀', _label(unit))
        self.act('merge_down', unit)
        merged = next(u for u in self.state()['effective']['units'] if 38 in u['sections'])
        runs = _text_runs(merged, reference=unit)
        self.assertEqual(''.join(r['text'] for r in runs if r['changed']), self.unit(39, 'auto')['text_original'])
        self.assertEqual(''.join(r['text'] for r in runs), merged['text_original'])
        self.act('reset', merged)
        self.act('split_unit', self.unit(38), boundaries=[3])
        pieces = [u for u in self.state()['effective']['units'] if 38 in u['sections']]
        self.assertFalse(any(r['changed'] for r in _text_runs(pieces[0], reference=unit)))
        self.assertTrue(all(r['changed'] for r in _text_runs(pieces[1], reference=unit)))
        auto_runs = _text_runs(unit, compared=pieces)
        self.assertEqual(''.join(r['text'] for r in auto_runs if r['changed']), unit['text_original'][3:])

    @unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit tests run with inspector venv')
    def test_unsaved_type_blocks_next_and_dropdown_until_save_or_discard(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_function(_review_app, args=(str(self.root),), default_timeout=30).run()
        app.text_input(key='seg_reviewer').set_value('draft-test').run()
        app.selectbox(key='seg_actor').select('scripted_test').run()
        start = app.selectbox(key='seg_auto:sifen').value
        original = self.state()['auto']['units'][start]
        new_type = next(t for t in index.UNIT_TYPES if t != original['type'])
        next(s for s in app.selectbox if s.key.startswith('seg_type:')).select(new_type).run()
        self.assertTrue(app.button(key='seg_next:sifen').disabled)
        self.assertEqual(app.selectbox(key='seg_auto:sifen').value, start)
        self.assertTrue(any('未保存' in w.value for w in app.warning))
        app.button(key='seg_save_type:sifen').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(app.button(key='seg_next:sifen').disabled)
        app.button(key='seg_next:sifen').click().run()
        self.assertEqual(app.selectbox(key='seg_auto:sifen').value, start+1)
        self.assertEqual(self.state()['effective']['units'][start]['type'], new_type)
        next(s for s in app.selectbox if s.key.startswith('seg_type:')).select('heading').run()
        self.assertTrue(app.selectbox(key='seg_auto:sifen').disabled)
        self.assertEqual(app.selectbox(key='seg_auto:sifen').value, start+1)
        app.button(key='seg_discard_draft').click().run()
        app.selectbox(key='seg_auto:sifen').select(start+2).run()
        self.assertEqual(app.selectbox(key='seg_auto:sifen').value, start+2)

    @unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit tests run with inspector venv')
    def test_saving_independent_type_discards_incompatible_relation_draft(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_function(_review_app, args=(str(self.root),), default_timeout=30).run()
        app.text_input(key='seg_reviewer').set_value('multi-panel-draft').run()
        app.selectbox(key='seg_actor').select('scripted_test').run()
        position = next(i for i,u in enumerate(self.state()['auto']['units']) if u['sections'] == [40])
        app.selectbox(key='seg_auto:sifen').select(position).run()
        next(s for s in app.selectbox if s.key.startswith('seg_relation_kind:')).select('alternative_of').run()
        next(s for s in app.selectbox if s.key.startswith('seg_type:')).select('procedure').run()
        app.button(key='seg_save_type:sifen').click().run()
        self.assertFalse(app.exception)
        self.assertFalse(any(s.key.startswith('seg_relation_kind:') for s in app.selectbox))
        self.assertEqual(self.unit(40)['relations'], [])
        self.assertFalse(app.button(key='seg_next:sifen').disabled)

    def test_reset_keeps_independent_reviews_and_normalization_is_repeatable(self):
        self.act('accept', self.unit(15))
        self.act('set_type', self.unit(38), type='discourse')
        self.act('merge_down', self.unit(38))
        state = self.state()
        operations = index.normalize_operations(state['auto'], state['effective']['units'])
        self.assertEqual(operations, index.normalize_operations(state['auto'], state['effective']['units']))
        self.assertTrue(all('target_id' not in op and 'target_ids' not in op for op in operations))
        merged = next(u for u in state['effective']['units'] if 38 in u['sections'])
        self.act('reset', merged)
        self.assertEqual(self.unit(15, 'auto')['human_review'][-1]['status'], 'accepted')
        self.assertEqual(self.unit(38, 'auto')['human_review'], [])

    def test_crash_during_write_is_recovered_as_one_transaction(self):
        original_atomic = review._atomic
        def fail_at_override(path, value):
            if path == review.paths(self.root)[1]:
                raise OSError('simulated power loss')
            original_atomic(path, value)
        with patch.object(review, '_atomic', side_effect=fail_at_override):
            with self.assertRaisesRegex(OSError, 'simulated power loss'):
                self.act('accept', self.unit())
        recovered = self.state()
        self.assertFalse(recovered['stale'])
        self.assertEqual(self.unit(layer='auto')['human_review'][-1]['status'], 'accepted')
        self.assertFalse((review.paths(self.root)[0].parent / '.segmentation-transaction.json').exists())

    def test_changed_machine_fields_block_regeneration_and_adapter_blocks_stale_index(self):
        from source_adapters.corpus import build_source_packet
        self.act('accept', self.unit())
        before = [p.read_bytes() for p in review.paths(self.root)]
        changed = index.build_auto_index(self.root)
        next(u for u in changed['units'] if u['sections'] == [38])['type'] = 'discourse'
        with patch.object(index, 'build_auto_index', return_value=changed):
            with self.assertRaisesRegex(ValueError, 'machine_changed'):
                review.regenerate(self.root)
        self.assertEqual(before, [p.read_bytes() for p in review.paths(self.root)])
        override = review.paths(self.root)[1]
        content = json.loads(override.read_bytes())
        content['operations'] = [{'op': 'set_type', 'target_id': 'sifen:section:38', 'type': 'discourse'}]
        override.write_text(json.dumps(content, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'index_out_of_sync'):
            build_source_packet(self.root, 'sifen-3-5')

    def test_unicode_split_offsets_and_repeat_text_are_occurrence_specific(self):
        # Start a separate fresh corpus, preserving CRLF and supplementary chars.
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'config').mkdir()
            (root / 'config/calendrical-ir-pipeline.json').write_text(json.dumps({
                'inputs': {'source_texts': [{'id': 'sifen', 'path': 'source.md'}]}}), encoding='utf-8')
            text = '題\r\n1 推術𠀀é甲。\r\n2 推術𠀀é甲。\r\n'
            (root / 'source.md').write_bytes(text.encode())
            review.regenerate(root)
            state = review.load(root)
            unit = state['effective']['units'][0]
            result = review.apply(root, 'split_unit', index.unit_anchor(unit), {'boundaries': [3, 5]},
                                  revision=state['revision'], actor=ACTOR)
            self.assertEqual([u['text_original'] for u in result['effective']['units']], ['推術𠀀', 'é', '甲。', '推術𠀀é甲。'])
            for u in result['effective']['units']:
                self.assertEqual(u['text_original'], ''.join(text[s['start']:s['end']] for s in u['source_spans']))
            self.assertEqual(result['auto']['units'][1]['human_review'], [])

    @unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit tests run with inspector venv')
    def test_ui_saves_resumes_and_refreshes_external_changes_without_reload_button(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_function(_review_app, args=(str(self.root),), default_timeout=30).run()
        self.assertFalse(app.exception)
        app.text_input(key='seg_reviewer').set_value('UI-test').run()
        app.selectbox(key='seg_actor').select('scripted_test').run()
        position = next(i for i, u in enumerate(self.state()['auto']['units']) if u['sections'] == [38])
        app.selectbox(key='seg_auto:sifen').select(position).run()
        app.button(key='seg_accept:sifen').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(self.unit(layer='auto')['human_review'][-1]['status'], 'accepted')
        self.assertEqual(app.selectbox(key='seg_auto:sifen').value, position)
        self.assertIn('已审·原样接受', app.selectbox(key='seg_auto:sifen').options[position])
        types = next(s for s in app.selectbox if s.key.startswith('seg_type:'))
        types.select('discourse').run()
        app.button(key='seg_save_type:sifen').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(self.unit()['type'], 'discourse')
        self.assertEqual(app.selectbox(key='seg_auto:sifen').value, position)
        self.assertIn('已审·已修改', app.selectbox(key='seg_auto:sifen').options[position])
        self.act('accept', self.unit(15))  # A second tab/process changed the store.
        app.run()
        self.assertFalse(app.button(key='seg_merge_down:sifen').disabled)
        self.assertFalse(any(b.key == 'seg_reload:sifen' for b in app.button))
        reopened = AppTest.from_function(_review_app, args=(str(self.root),), default_timeout=30).run()
        self.assertFalse(reopened.exception)
        first = next(i for i,u in enumerate(self.state()['auto']['units']) if not u['human_review'])
        reopened.button(key='seg_resume:sifen').click().run()
        self.assertEqual(reopened.selectbox(key='seg_auto:sifen').value, first)
        self.assertTrue(any('Revision 3' in c.value for c in reopened.caption))

    @unittest.skipUnless(importlib.util.find_spec('streamlit'), 'Streamlit tests run with inspector venv')
    def test_relation_cards_show_complete_target_text_in_each_layer_including_split_targets(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_function(_review_app, args=(str(self.root),), default_timeout=30).run()
        position = next(i for i,u in enumerate(self.state()['auto']['units']) if u['sections'] == [40])
        app.selectbox(key='seg_auto:sifen').select(position).run()
        target = self.unit(39)['text_original']
        self.assertEqual(sum(t.value == target for t in app.text), 2)
        self.act('split_unit', self.unit(39), boundaries=[3])
        app.run()
        self.assertFalse(app.exception)
        selected = app.selectbox(key='seg_auto:sifen').value
        self.assertEqual(self.state()['effective']['units'][selected]['sections'], [40])
        # Auto retains the full original target; Effective displays both exact pieces.
        for text in (target, target[:3], target[3:]):
            self.assertTrue(any(t.value == text for t in app.text), text)


if __name__ == '__main__':
    unittest.main()
