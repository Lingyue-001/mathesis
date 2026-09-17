"""Deterministic branch reduction with conflicts and stale dependencies visible."""
import copy
import json

from .anchors import overlaps, packet_identity, validate_anchor
from .decision_contracts import semantic_target_key
from .session import branch_ancestors, runtime_identity


def _slot(decision):
    return semantic_target_key(decision['action'], decision['payload'], decision['targets'])


def _normalize(value):
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')))


def replay_session(session, packet, branch_id='main'):
    source = packet_identity(packet)
    if source != session.get('source_packet'):
        return {'status': 'stale_source', 'source_packet': source, 'decision_status': {},
                'effective': _empty_effective(), 'normalized': _normalize({'status': 'stale_source'})}
    if runtime_identity(packet) != session.get('identity_locks'):
        return {'status': 'stale_identity', 'source_packet': source, 'decision_status': {},
                'effective': _empty_effective(), 'normalized': _normalize({'status': 'stale_identity'})}
    visible = branch_ancestors(session, branch_id)
    decisions = [copy.deepcopy(row) for row in session.get('decisions', []) if row['branch_id'] in visible]
    status = {row['decision_id']: {'status': 'active', 'reasons': []} for row in decisions}
    ids = {row['decision_id'] for row in decisions}
    for row in decisions:
        try:
            for target in row['targets']:
                validate_anchor(packet, target)
        except ValueError as error:
            status[row['decision_id']] = {'status': 'needs_revalidation', 'reasons': [str(error)]}
        for dependency in row.get('depends_on', []):
            if dependency not in ids:
                status[row['decision_id']] = {'status': 'needs_revalidation', 'reasons': ['missing_dependency:' + dependency]}
    retracted = set()
    for row in decisions:
        if row['action'] == 'retract' and status[row['decision_id']]['status'] == 'active':
            target_id = row['payload']['decision_id']
            if target_id in status:
                retracted.add(target_id)
                status[target_id] = {'status': 'retracted', 'reasons': ['retracted_by:' + row['decision_id']]}
            else:
                status[row['decision_id']] = {'status': 'needs_revalidation', 'reasons': ['unknown_retraction_target']}
    changed = list(retracted)
    while changed:
        prior = changed.pop()
        for row in decisions:
            if prior in row.get('depends_on', []) and status[row['decision_id']]['status'] == 'active':
                status[row['decision_id']] = {'status': 'needs_revalidation', 'reasons': ['dependency_retracted:' + prior]}
                changed.append(row['decision_id'])
    segmenters = [row for row in decisions if row['action'] == 'resegment' and status[row['decision_id']]['status'] == 'active']
    for row in decisions:
        if row['action'] == 'resegment' or status[row['decision_id']]['status'] != 'active':
            continue
        if any(row.get('revision', 0) < segmenter.get('revision', 0) and any(overlaps(row['targets'][0], segment)
                   for segment in (segmenter['payload'].get('segments') or segmenter['targets']))
               for segmenter in segmenters):
            status[row['decision_id']] = {'status': 'needs_revalidation',
                                          'reasons': ['upstream_segmentation_changed']}
    context_decisions = [row for row in decisions if row['action'] == 'attach_context'
                         and status[row['decision_id']]['status'] == 'active']
    if context_decisions:
        for row in decisions:
            if (row['action'] in ('select_candidate', 'bind_value', 'bind_call')
                    and status[row['decision_id']]['status'] == 'active'
                    and any(row.get('revision', 0) < context.get('revision', 0) for context in context_decisions)):
                status[row['decision_id']] = {'status': 'needs_revalidation',
                                              'reasons': ['context_candidate_set_changed']}
    active = [row for row in decisions if status[row['decision_id']]['status'] == 'active'
              and row['action'] != 'retract']
    by_slot = {}
    for row in active:
        by_slot.setdefault(_slot(row), []).append(row)
    for rows in by_slot.values():
        payloads = {_normalize(row['payload']).__repr__() for row in rows}
        if len(rows) > 1 and len(payloads) > 1:
            for row in rows:
                status[row['decision_id']] = {'status': 'conflicted', 'reasons': ['multiple_active_decisions_for_slot']}
    effective = _empty_effective()
    for row in decisions:
        if status[row['decision_id']]['status'] != 'active' or row['action'] == 'retract':
            continue
        _apply(effective, row)
    normalized = {'branch_id': branch_id, 'effective': effective,
                  'decision_status': {key: status[key] for key in sorted(status)}}
    return {'status': 'ok', 'source_packet': source, 'decision_status': status,
            'effective': effective, 'normalized': _normalize(normalized)}


def _empty_effective():
    return {'selected_candidates': {}, 'candidate_selection_metadata': {}, 'rejected_candidates': [], 'segments': [], 'scopes': {},
            'bindings': {}, 'quantity_semantics': {}, 'profiles': [], 'contexts': [], 'parameters': {},
            'manual_structures': [], 'noncomputational': [], 'deferred': [], 'approved_scopes': [], 'lexical_roles': []}


def _apply(effective, row):
    action, payload = row['action'], row['payload']
    token = semantic_target_key(action, payload, row['targets'])
    if action == 'select_candidate':
        effective['selected_candidates'][token] = payload['selected_candidate_id']
        effective['candidate_selection_metadata'][token] = {
            'decision_id': row['decision_id'], 'target': row['targets'][0],
        }
    elif action == 'reject_candidate':
        if payload['candidate_id'] not in effective['rejected_candidates']:
            effective['rejected_candidates'].append(payload['candidate_id'])
    elif action == 'resegment':
        effective['segments'].append({'decision_id': row['decision_id'], 'target': row['targets'][0],
                                      'segments': payload.get('segments', [])})
    elif action == 'set_scope':
        effective['scopes'][token] = payload
    elif action in ('bind_value', 'bind_call'):
        effective['bindings'][token] = {**payload, 'decision_id': row['decision_id'], 'target': row['targets'][0]}
    elif action == 'set_quantity_semantics':
        effective['quantity_semantics'][token] = {**payload, 'decision_id': row['decision_id']}
    elif action == 'select_profile':
        profile = payload.get('profile_id')
        if profile and profile not in effective['profiles']:
            effective['profiles'].append(profile)
    elif action == 'attach_context':
        effective['contexts'].append({**payload, 'decision_id': row['decision_id']})
    elif action == 'declare_parameter':
        effective['parameters'][payload['name']] = {**payload, 'decision_id': row['decision_id'],
                                                     'target': row['targets'][0]}
    elif action == 'assemble_known_structure':
        effective['manual_structures'].append({**payload, 'decision_id': row['decision_id'],
                                               'target': row['targets'][0]})
    elif action == 'mark_noncomputational':
        effective['noncomputational'].append({**payload, 'decision_id': row['decision_id'],
                                              'target': row['targets'][0]})
    elif action == 'defer':
        effective['deferred'].append({**payload, 'decision_id': row['decision_id'], 'target': row['targets'][0]})
    elif action == 'approve_scope':
        effective['approved_scopes'].append({**payload, 'decision_id': row['decision_id'],
                                             'target': row['targets'][0]})
    elif action == 'set_lexical_role':
        effective['lexical_roles'].append({**payload, 'decision_id': row['decision_id'],
                                           'target': row['targets'][0], 'evidence_refs': row['evidence_refs'],
                                           'reason': row['reason']})
