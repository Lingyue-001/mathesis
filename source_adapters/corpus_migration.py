"""Exact-span rule upgrades with immutable original baselines for historical replay."""
import copy
import hashlib
import json
from pathlib import Path

from . import corpus_index as index


def transfer_reviews(auto, original):
    """Transfer only reviews whose original source region contains the new unit.

    A machine unit crossing reviewed/unreviewed regions needs a human decision.
    Review records themselves remain unchanged, including their original IDs.
    """
    for unit in auto['units']:
        anchor = index.unit_anchor(unit)
        records = []
        for old in original['units']:
            if not old.get('human_review') or not index.overlaps(anchor, index.unit_anchor(old)):
                continue
            if not all(any(c <= a and b <= d for c, d in index.unit_anchor(old)) for a, b in anchor):
                raise ValueError('nonunique_review_migration:' + old['id'] + ' -> ' + unit['id'])
            for record in old['human_review']:
                if record not in records:
                    records.append(copy.deepcopy(record))
        unit['human_review'] = records


def _signature(unit, units):
    return {'source_spans': index.unit_anchor(unit), 'type': unit['type'],
            'text_original': unit['text_original'], 'text_effective': unit['text_effective'],
            'relations': index._anchored_relations(unit['relations'], units),
            'parameters': unit['parameters'], 'member_roles': unit['member_roles']}


def plan(root, state, auto):
    """Pure migration proposal: retained decisions are source intervals, never text similarity."""
    old = state['auto']
    if old['source'] != auto['source']:
        raise ValueError('source_changed: migration requires identical source bytes and offsets')
    if state['stale']:
        raise ValueError('stale_workspace: recover before rule migration')
    changes = []
    for unit in old['units']:
        matches = [u for u in auto['units'] if index.overlaps(index.unit_anchor(unit), index.unit_anchor(u))]
        if len(matches) != 1 or _signature(unit, old['units']) != _signature(matches[0], auto['units']):
            before = _signature(unit, old['units'])
            after = [_signature(u, auto['units']) for u in matches]
            changes.append({'old_id': unit['id'], 'sections': unit['sections'],
                            'source_spans': index.unit_anchor(unit), 'new_ids': [u['id'] for u in matches],
                            'old_type': unit['type'], 'new_types': [u['type'] for u in matches],
                            'reviewed': bool(unit['human_review']),
                            'changed_fields': [key for key in before if len(after) != 1 or before[key] != after[0][key]]})
    reviewed = [u for u in old['units'] if u['human_review']]
    protected = [index.unit_anchor(u) for u in reviewed]
    for op in state['overrides']['operations']:
        protected.extend(op.get('targets', [op.get('target_spans')]) or [])
    # Expand through effective/automatic partitions to retain complete regions.
    region = [interval for anchor in protected if anchor for interval in anchor]
    changed = True
    while changed:
        changed = False
        for unit in old['units'] + state['effective']['units'] + auto['units']:
            if region and index.overlaps(region, index.unit_anchor(unit)):
                for interval in index.unit_anchor(unit):
                    if interval not in region:
                        region.append(interval)
                        changed = True
    transfer_reviews(auto, old)
    final = index._normalize(
        [copy.deepcopy(u) for u in auto['units'] if not index.overlaps(region, index.unit_anchor(u))] +
        [copy.deepcopy(u) for u in state['effective']['units'] if index.overlaps(region, index.unit_anchor(u))])
    # Resolve machine relation targets before mixing partitions.
    for unit in final:
        origin = state['effective']['units'] if index.overlaps(region, index.unit_anchor(unit)) else auto['units']
        unit['relations'] = index._anchored_relations(unit['relations'], origin)
    overrides = copy.deepcopy(state['overrides'])
    operations = index.normalize_operations(auto, final)
    known = {op.get('id'): op for op in overrides['operations']}
    overrides['operations'] = [copy.deepcopy(known.get(op['id'], op)) for op in operations]
    overrides['source_lock'] = {key: auto['source'][key] for key in ('source_id', 'sha256')}
    effective = index.effective_from_auto(auto, overrides)
    from .dependencies import unit_hash
    new_hashes = {u['id']: unit_hash(u) for u in effective['units']}
    affected = [u['id'] for u in state['effective']['units'] if new_hashes.get(u['id']) != unit_hash(u)]
    root = Path(root)
    references = []
    errors = []
    # Inventory local selection/session/artifact stores without modifying them.
    inventory_folders = ('config', 'tmp', 'output', 'outputs', 'workbench', 'corpus-review', 'tools/parser_inspector/output')
    for folder in inventory_folders:
        for path in sorted((root / folder).rglob('*.json')):
            if 'migrations' in path.parts or path.parent == root / 'corpus-review' / auto['source']['source_id']:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except (OSError, UnicodeError) as error:
                errors.append({'path': path.relative_to(root).as_posix(), 'error': str(error)})
                continue
            ids = [ident for ident in affected if ident in text]
            session = 'SourcePacket' in text or 'session_id' in text or 'engine_identity' in text
            if ids or session or path.name == 'workbench-procedures.json' or folder == 'tools/parser_inspector/output':
                references.append({'path': path.relative_to(root).as_posix(), 'affected_unit_ids': ids,
                                   'session_or_model': session,
                                   'action': 'retain; validate selected unit hashes and engine identity on next use'})
    report = {'schema': 'CorpusRuleMigration/1', 'source_id': auto['source']['source_id'],
              'original_revision': state['revision'], 'changes': changes,
              'unit_counts': {'old_auto': len(old['units']), 'new_auto': len(auto['units']),
                              'old_effective': len(state['effective']['units']), 'new_effective': len(effective['units'])},
              'reviewed_original_units': [{'id': u['id'], 'source_spans': index.unit_anchor(u)} for u in reviewed],
              'preserved_history_events': len(overrides.get('history', [])),
              'affected_effective_units': affected, 'references': references, 'inventory_errors': errors,
              'inventory_scope': list(inventory_folders),
              'browser_local_sessions': 'Not enumerable from disk; retained, with source/engine locks checked on reuse.',
              'engine_change': 'Compiler identity changes invalidate old compiled sessions; no automatic relock.',
              'pending_questions': [], 'proposed_operations': overrides['operations']}
    return auto, overrides, report


def migrate(root, source_id='sifen', *, apply=False):
    from . import corpus_review as store
    with store._locked(root, source_id):
        state = store._load(root, source_id)
        auto = index.build_auto_index(root, source_id)
        original_machine = copy.deepcopy(state['auto'])
        for unit in original_machine['units']:
            unit['human_review'] = []
        if original_machine == auto:
            return {'source_id': source_id, 'changes': [], 'already_current': True}
        folder = store.workspace(root, source_id)
        try:
            auto, overrides, report = plan(root, state, auto)
        except ValueError as error:
            if not str(error).startswith('nonunique_review_migration:'):
                raise
            report = {'schema': 'CorpusRuleMigration/1', 'source_id': source_id,
                      'original_revision': state['revision'], 'applied': False,
                      'pending_questions': [{'conflict': str(error),
                          'question': '新机器单元跨越已审与未审区域。请确定保留哪些原始边界及对应审阅范围；当前文件保持原样。'}]}
            store._atomic(folder / 'migration-report.json', report)
            return report
        archive = folder / 'migrations' / state['revision']
        report['archive'] = archive.relative_to(Path(root).resolve()).as_posix()
        # Report is persisted before any authoritative data is replaced.
        store._atomic(folder / 'migration-report.json', report)
        if not apply:
            return report
        archive.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for path in (*store.paths(root, source_id), folder / 'manifest.json'):
            raw = path.read_bytes()
            target = archive / path.name
            if target.exists():
                if target.read_bytes() != raw:
                    raise ValueError('archive_conflict:' + str(target))
            else:
                with target.open('xb') as stream:
                    stream.write(raw)
            hashes[path.name] = hashlib.sha256(raw).hexdigest()
        archived_report = archive / 'migration-report.json'
        report_bytes = store._bytes(report)
        if archived_report.exists():
            if archived_report.read_bytes() != report_bytes:
                raise ValueError('archive_conflict:' + str(archived_report))
        else:
            with archived_report.open('xb') as stream:
                stream.write(report_bytes)
        migrations = overrides.setdefault('rule_migrations', [])
        migrations.append({'archive': report['archive'], 'hashes': hashes,
                           'through_revision': max((h.get('revision', i) for i, h in enumerate(overrides.get('history', []), 1)), default=0)})
        store._save(root, auto, overrides, source_id)
        return report
