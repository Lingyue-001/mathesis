"""Per-source review workspaces; no parser or semantic inference.

AUTO owns current review annotations. Overrides own active deltas and permanent history.
A short-lived journal completes interrupted data + manifest transactions.
"""
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from . import corpus_index as index


def workspace(root, source_id='sifen'):
    root = Path(root).resolve()
    if not re.fullmatch(r'[a-z][a-z0-9_-]*', source_id):
        raise ValueError('invalid_source_id')
    folder = root / 'corpus-review' / source_id
    if not folder.resolve().is_relative_to(root):
        raise ValueError('workspace_outside_repository')
    return folder


def paths(root, source_id='sifen'):
    folder = workspace(root, source_id)
    return tuple(folder / name for name in ('auto.json', 'overrides.json', 'effective.json'))


def _manifest(auto, raw):
    statuses = [u['human_review'][-1]['status'] if u['human_review'] else 'unreviewed' for u in auto['units']]
    return {'schema_version': 'mathesis.corpus_review_workspace/1.0',
            'source_id': auto['source']['source_id'], 'source_path': auto['source']['path'],
            'source_sha': auto['source']['sha256'],
            **{key + '_sha': hashlib.sha256(value).hexdigest() for key, value in zip(('auto', 'override', 'effective'), raw)},
            'review_revision': hashlib.sha256(b'\0'.join(raw)).hexdigest(),
            'review_status': {'total': len(statuses), 'reviewed': len(statuses)-statuses.count('unreviewed'),
                              'accepted': statuses.count('accepted'), 'modified': statuses.count('modified'),
                              'unreviewed': statuses.count('unreviewed')}}


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.' + path.name, suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def _locked(root, source_id='sifen'):
    folder = workspace(root, source_id)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / '.segmentation.lock').open('a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            if lock.tell() == 0:
                lock.write(b'0')
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            journal = folder / '.segmentation-transaction.json'
            if journal.exists():
                values = index._json(journal)
                if not isinstance(values, list) or len(values) != 4:
                    raise ValueError('invalid_review_transaction')
                for path, value in zip((*paths(root, source_id), folder / 'manifest.json'), values):
                    _atomic(path, value)
                journal.unlink()
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def _save(root, auto, overrides, source_id='sifen'):
    effective = index.effective_from_auto(auto, overrides)  # Validate before any write.
    folder = workspace(root, source_id)
    journal = folder / '.segmentation-transaction.json'
    values = [auto, overrides, effective]
    values.append(_manifest(auto, [_bytes(value) for value in values]))
    _atomic(journal, values)
    for path, value in zip((*paths(root, source_id), folder / 'manifest.json'), values):
        _atomic(path, value)
    journal.unlink()


def _load(root, source_id='sifen'):
    files = paths(root, source_id)
    raw = [path.read_bytes() for path in files]
    auto, overrides, effective = [json.loads(value) for value in raw]
    _, _, source, _ = index.read_registered_source(root, source_id)
    manifest = index._json(workspace(root, source_id) / 'manifest.json')
    source_changed = hashlib.sha256(source).hexdigest() != auto['source']['sha256']
    out_of_sync = (manifest != _manifest(auto, raw) or auto['source']['source_id'] != source_id
                   or effective.get('auto_sha256') != index._sha(json.dumps(auto, ensure_ascii=False, sort_keys=True))
                   or effective.get('overrides', {}).get('sha256') != index._sha(json.dumps(overrides, ensure_ascii=False, sort_keys=True)))
    baselines = []
    for migration in overrides.get('rule_migrations', []):
        archive = (Path(root) / migration['archive']).resolve()
        if not archive.is_relative_to(workspace(root, source_id) / 'migrations'):
            raise ValueError('history_archive_outside_workspace')
        saved = {}
        for name, expected in migration['hashes'].items():
            if name not in ('auto.json', 'overrides.json', 'effective.json', 'manifest.json'):
                raise ValueError('invalid_history_archive_file')
            data = (archive / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError('history_archive_changed')
            saved[name.removesuffix('.json')] = json.loads(data)
        baselines.append({'through_revision': migration['through_revision'], **saved})
    return {'auto': auto, 'overrides': overrides, 'effective': effective, 'manifest': manifest,
            'history_baselines': baselines,
            'revision': hashlib.sha256(b'\0'.join(raw)).hexdigest(),
            'stale': source_changed or out_of_sync,
            'stale_reason': 'source_changed' if source_changed else 'index_out_of_sync' if out_of_sync else None}


def load(root, source_id='sifen'):
    with _locked(root, source_id):
        return _load(root, source_id)


def active_history(overrides):
    """Undo is itself an event; its target remains in the scholarly record."""
    history = overrides.get('history', [])
    reverted = set()
    for i in range(len(history)-1, -1, -1):
        entry = history[i]
        if entry.get('revision', i+1) not in reverted and entry.get('reverts'):
            reverted.add(entry['reverts'])
    return [h for i, h in enumerate(history, 1)
            if h['action'] != 'undo' and h.get('revision', i) not in reverted]


def _history_snapshot(state, entry, side):
    state = _history_baseline(state, entry)
    if side == 'before':
        return entry['before']
    if side != 'after':
        raise ValueError('invalid_history_side')
    history = state['overrides'].get('history', [])
    position = history.index(entry)
    return entry.get('after') or (history[position+1]['before'] if position+1 < len(history) else {
        'operations': state['overrides']['operations'],
        'reviews': {u['id']: u['human_review'] for u in state['auto']['units']}})


def _history_baseline(state, entry):
    revision = entry.get('revision', state['overrides'].get('history', []).index(entry) + 1)
    return next((base for base in state.get('history_baselines', [])
                 if revision <= base['through_revision']), state)


def history_states(state, entry):
    """Materialize a historical before/after using the same anchored replayer."""
    result = []
    for snapshot in (_history_snapshot(state, entry, 'before'), _history_snapshot(state, entry, 'after')):
        auto = copy.deepcopy(_history_baseline(state, entry)['auto'])
        for unit in auto['units']:
            unit['human_review'] = snapshot['reviews'].get(unit['id'], [])
        effective = index.effective_from_auto(auto, {'operations': snapshot['operations'],
            'source_lock': {key: auto['source'][key] for key in ('source_id', 'sha256')}})
        result.append(effective['units'])
    return result


def migrate_rules(root, source_id='sifen', *, apply=False):
    from .corpus_migration import migrate
    return migrate(root, source_id, apply=apply)


def regenerate(root, output_dir=None, source_id='sifen'):
    """Re-extract machine fields; retain reviews or fail without replacing them."""
    with _locked(root, source_id):
        auto = index.build_auto_index(root, source_id)
        auto_path, override_path, _ = paths(root, source_id)
        # One-time relocation, never a parallel runtime data source. Finish
        # the new transaction before removing any legacy file.
        legacy = [Path(root) / 'tmp/corpus-index' / f'{source_id}-units.auto.json',
                  Path(root) / 'config/corpus-review' / f'{source_id}-segmentation-overrides.json',
                  Path(root) / 'tmp/corpus-index' / f'{source_id}-units.effective.json']
        migrating = not any(p.exists() for p in paths(root, source_id)) and any(p.exists() for p in legacy)
        if migrating and (legacy[0].parent / '.segmentation-transaction.json').exists():
            raise ValueError('legacy_transaction_pending: recover old transaction before migration')
        old_auto, old_overrides = (legacy[:2] if migrating else (auto_path, override_path))
        overrides = index._json(old_overrides) if old_overrides.exists() else {
            'schema_version': 'mathesis.corpus_overrides/1.1',
            '_notes': ['所有人工修改的统一 delta log；Accept 仅记录在 auto.human_review。'],
            'operations': []}
        old = index._json(old_auto) if old_auto.exists() else None
        if old is None and overrides.get('history'):
            raise ValueError('reviewed_auto_missing: restore auto before regeneration')
        if old and old.get('method', {}).get('segmentation_rules') != auto['method'].get('segmentation_rules'):
            raise ValueError('rule_migration_required: run extraction --migration-report then --migrate-rules; originals retained')
        if old and any(u.get('human_review') for u in old['units']):
            if old['source']['sha256'] != auto['source']['sha256']:
                raise ValueError('source_changed: existing human_review is stale; originals retained')
            for old_unit in old['units']:
                if not old_unit.get('human_review'):
                    continue
                new = next((u for u in auto['units'] if index.unit_anchor(u) == index.unit_anchor(old_unit)), None)
                if new is None or {k: v for k, v in old_unit.items() if k != 'human_review'} != {k: v for k, v in new.items() if k != 'human_review'}:
                    raise ValueError('machine_changed: reviewed unit needs revalidation; originals retained')
                new['human_review'] = copy.deepcopy(old_unit['human_review'])
        effective = index.effective_from_auto(auto, overrides)
        if output_dir and Path(output_dir).resolve() != auto_path.parent.resolve():
            # Explicit export does not replace the authoritative review store.
            for suffix, value in [('auto', auto), ('effective', effective)]:
                _atomic(Path(output_dir) / f'{source_id}-units.{suffix}.json', value)
        else:
            _save(root, auto, overrides, source_id)
            if migrating:
                for path in legacy:
                    if not path.resolve().is_relative_to(Path(root).resolve()):
                        raise ValueError('legacy_path_outside_repository')
                    path.unlink(missing_ok=True)


def _region(auto, effective, anchor, operations):
    """Expand to the connected source region, including prior merge/split deltas."""
    anchors = [index.unit_anchor(u) for u in auto['units'] + effective['units']]
    anchors += [op.get('target_spans') or [s for target in op.get('targets', []) for s in target] for op in operations]
    anchors += [r.get('source_spans', []) for u in auto['units'] for r in u['human_review']]
    region = list(anchor)
    changed = True
    while changed:
        changed = False
        for candidate in anchors:
            if candidate and index.overlaps(region, candidate):
                for interval in candidate:
                    if interval not in region:
                        region.append(interval)
                        changed = True
    merged = []
    for start, end in sorted(region):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(end, merged[-1][1])
        else:
            merged.append([start, end])
    return merged


def apply(root, action, anchor, payload, *, revision, actor, note='', source_id='sifen'):
    """Optimistic-concurrency-checked command; source anchors, never client text."""
    with _locked(root, source_id):
        state = _load(root, source_id)
        if state['stale']:
            raise ValueError(state['stale_reason'])
        if revision != state['revision']:
            raise ValueError('stale_page: reload before saving')
        if not isinstance(actor, dict) or not actor.get('id') or actor.get('type') not in ('human', 'scripted_test', 'automated_browser'):
            raise ValueError('review_actor_required')
        auto, overrides, effective = state['auto'], state['overrides'], state['effective']
        units = effective['units']
        index._slice_spans(auto['units'], anchor)
        previous = {'operations': copy.deepcopy(overrides['operations']),
                    'reviews': {u['id']: copy.deepcopy(u['human_review']) for u in auto['units']}}
        # Older histories have no event IDs. Assign their existing order once;
        # no deleted pre-upgrade Undo event can be reconstructed or invented.
        for i, entry in enumerate(overrides.get('history', []), 1):
            entry.setdefault('revision', i)
        revision_number = max((h['revision'] for h in overrides.get('history', [])), default=0) + 1
        now = datetime.now(timezone.utc).isoformat()
        stamp = {'time': now, 'actor': copy.deepcopy(actor), 'note': note, 'revision': revision_number}
        touched = anchor
        reverts = None
        if action == 'undo':
            candidates = active_history(overrides)
            if not candidates:
                raise ValueError('nothing_to_undo')
            entry = candidates[-1]
            reverts = entry['revision']
            touched = entry['source_spans']
            if _history_baseline(state, entry) is state:
                overrides['operations'] = copy.deepcopy(entry['before']['operations'])
                for unit in auto['units']:
                    unit['human_review'] = copy.deepcopy(entry['before']['reviews'].get(unit['id'], []))
            else:
                from .corpus_migration import transfer_reviews
                restored = history_states(state, entry)[0]
                snapshot = _history_snapshot(state, entry, 'before')
                touched = _region(auto, {'units': units + restored}, entry['source_spans'],
                                  previous['operations'] + snapshot['operations'])
                final = index._normalize(
                    [u for u in units if not index.overlaps(touched, index.unit_anchor(u))] +
                    [u for u in restored if index.overlaps(touched, index.unit_anchor(u))])
                overrides['operations'] = index.normalize_operations(auto, final)
                transfer_reviews({'units': [u for u in auto['units']
                    if index.overlaps(touched, index.unit_anchor(u))]}, {'units': restored})
        elif action in ('restore_revision', 'revert_revision'):
            entry = next((h for h in overrides.get('history', []) if h['revision'] == payload.get('revision_id')), None)
            if entry is None or not index.overlaps(anchor, entry['source_spans']):
                raise ValueError('history_revision_not_in_region')
            side = payload.get('side', 'after') if action == 'restore_revision' else 'before'
            snapshot = _history_snapshot(state, entry, side)
            touched = _region(auto, effective, entry['source_spans'], previous['operations'] + snapshot['operations'])
            if action == 'revert_revision':
                active = active_history(overrides)
                if entry not in active:
                    raise ValueError('history_change_already_reverted')
                if any(h['revision'] > entry['revision'] and index.overlaps(touched, h['source_spans']) for h in active):
                    raise ValueError('history_has_dependent_changes: 请先撤销后续区域修改，或明确恢复该记录之前／之后的区域状态。')
                reverts = entry['revision']
            restored = history_states(state, entry)[0 if side == 'before' else 1]
            final = sorted([u for u in units if not index.overlaps(touched, index.unit_anchor(u))] +
                           [u for u in restored if index.overlaps(touched, index.unit_anchor(u))],
                           key=lambda u: u['source_spans'][0]['start'])
            if any(u['relations'] and u['type'] != 'alternative_procedure' for u in final
                   if index.overlaps(touched, index.unit_anchor(u))):
                raise ValueError('alternative_requires_alternative_procedure: 旧错误状态仅供查看，不能恢复；请选择更早记录或退回最初。')
            overrides['operations'] = index.normalize_operations(auto, final)
            if _history_baseline(state, entry) is not state:
                from .corpus_migration import transfer_reviews
                transfer_reviews({'units': [u for u in auto['units']
                    if index.overlaps(touched, index.unit_anchor(u))]}, {'units': restored})
            else:
                for unit in auto['units']:
                    if index.overlaps(touched, index.unit_anchor(unit)):
                        unit['human_review'] = copy.deepcopy(snapshot['reviews'].get(unit['id'], []))
        else:
            if action == 'accept':
                target = next((u for u in auto['units'] if index.unit_anchor(u) == anchor), None)
                if target is None:
                    raise ValueError('accept_requires_auto_unit')
                current = [u for u in units if index.overlaps(index.unit_anchor(u), anchor)]
                unchanged = (len(current) == 1 and index.unit_anchor(current[0]) == anchor
                             and current[0]['type'] == target['type']
                             and index._anchored_relations(current[0]['relations'], units)
                             == index._anchored_relations(target['relations'], auto['units']))
                if not unchanged:
                    raise ValueError('reset_modified_unit_before_accept')
                if target['human_review'] and target['human_review'][-1]['status'] == 'modified':
                    raise ValueError('reset_modified_unit_before_accept')
                target['human_review'].append({**stamp, 'status': 'accepted', 'override_ids': []})
            elif action == 'reset':
                touched = _region(auto, effective, anchor, overrides['operations'])
                retained = [op for op in overrides['operations'] if not index.overlaps(touched,
                    op.get('target_spans') or [s for target in op.get('targets', []) for s in target])]
                overrides['operations'] = retained
                for unit in auto['units']:
                    if index.overlaps(index.unit_anchor(unit), touched):
                        unit['human_review'] = []
            else:
                target = next((u for u in units if index.unit_anchor(u) == anchor), None)
                if target is None:
                    raise ValueError('effective_unit_not_found')
                command = {'op': action, 'target_spans': anchor}
                if action == 'set_type':
                    command['type'] = payload.get('type')
                elif action == 'set_relations':
                    command['relations'] = payload.get('relations', [])
                    if command['relations'] and target['type'] != 'alternative_procedure':
                        raise ValueError('alternative_requires_alternative_procedure: 独立 procedure 不能保存 alternative 关系；请先明确修改类型。')
                elif action == 'split_unit':
                    command['groups'] = index.split_groups(target, payload.get('boundaries'))
                elif action in ('merge_up', 'merge_down'):
                    position = units.index(target)
                    neighbor = position + (-1 if action == 'merge_up' else 1)
                    if not 0 <= neighbor < len(units):
                        raise ValueError('no_adjacent_unit')
                    selected = units[min(position, neighbor):max(position, neighbor)+1]
                    touched = index.unit_anchor({'source_spans': [s for u in selected for s in u['source_spans']]})
                    # Boundary edit: retain the active block's metadata, never
                    # promote a neighbor's alternative type/relation. Explicit
                    # payloads leave old merge snapshots replayable unchanged.
                    command = {'op': 'merge_units', 'targets': [index.unit_anchor(u) for u in selected],
                               'type': target['type'], 'relations': copy.deepcopy(target['relations'])}
                else:
                    raise ValueError('unsupported_review_action')
                final = index._apply_overrides(units, {'operations': [command]})
                if action == 'set_type' and command['type'] != 'alternative_procedure':
                    # Choosing an independent type also cancels the incompatible
                    # outgoing relation in this same recorded transaction.
                    final = index._apply_overrides(final, {'operations': [
                        {'op':'set_relations', 'target_spans':anchor, 'relations':[]}]})
                if final == units:
                    return state
                operations = index.normalize_operations(auto, final)
                known = {op.get('id'): op for op in overrides['operations']}
                overrides['operations'] = [known.get(op['id'], {**op, **stamp}) for op in operations]
                touched = _region(auto, effective, touched, previous['operations'] + operations)
                for unit in auto['units']:
                    if index.overlaps(index.unit_anchor(unit), touched):
                        ids = [op['id'] for op in operations if index.overlaps(index.unit_anchor(unit),
                            op.get('target_spans') or [s for group in op.get('targets', []) for s in group])]
                        unit['human_review'].append({**stamp, 'status': 'modified', 'override_ids': ids,
                                                     'source_spans': touched})
        supersedes = [h['revision'] for h in active_history(overrides)
                      if index.overlaps(touched, h['source_spans'])]
        overrides.setdefault('history', []).append({**stamp, 'action': action,
            'source_spans': touched, 'supersedes': supersedes, 'reverts': reverts,
            **({'restores':entry['revision'], 'restore_side':side} if action == 'restore_revision' else {}),
            'before': previous, 'after': {'operations': copy.deepcopy(overrides['operations']),
                'reviews': {u['id']: copy.deepcopy(u['human_review']) for u in auto['units']}}})
        overrides['schema_version'] = 'mathesis.corpus_overrides/1.3'
        overrides['source_lock'] = {key: auto['source'][key] for key in ('source_id', 'sha256')}
        _save(root, auto, overrides, source_id)
        return _load(root, source_id)
