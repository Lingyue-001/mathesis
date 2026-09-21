"""Deterministic branch reduction with conflicts and stale dependencies visible."""
import copy
import json

from .anchors import overlaps, packet_identity, validate_anchor
from .decision_contracts import semantic_target_key, validate_action_payload
from .effective_packet import derive_packet, validate_context_dependencies
from .session import branch_ancestors, runtime_identity


def _slot(decision):
    return semantic_target_key(decision['action'], decision['payload'], decision['targets'])


def _normalize(value):
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')))


def dependency_cycles(decisions):
    edges = {r['decision_id']: r.get('depends_on', []) for r in decisions}
    done, visiting, cycles = set(), [], set()
    def visit(ident):
        if ident in visiting:
            cycles.update(visiting[visiting.index(ident):]); return
        if ident in done or ident not in edges:
            return
        visiting.append(ident)
        for dep in edges[ident]:
            visit(dep)
        visiting.pop(); done.add(ident)
    for ident in edges:
        visit(ident)
    return cycles


def propagate_inactive(decisions, status):
    changed = True
    while changed:
        changed = False
        for row in decisions:
            ident = row['decision_id']
            if status[ident]['status'] != 'active':
                continue
            unavailable = [d for d in row.get('depends_on', []) if status.get(d, {}).get('status') != 'active']
            if unavailable:
                status[ident] = {'status': 'needs_revalidation', 'reasons': ['dependency_inactive:' + d for d in unavailable]}
                changed = True


def replay_session(session, packet, branch_id='main', *, invalid_decisions=None):
    invalid = dict(invalid_decisions or {})
    for _ in range(len(session.get('decisions', [])) + 1):
        result = _replay_pass(session, packet, branch_id, invalid)
        inactive_effects = result.pop('_inactive_effects', {})
        fresh = {k: v for k, v in inactive_effects.items() if k not in invalid}
        if not fresh:
            return result
        invalid.update(fresh)
    raise RuntimeError('replay_invalidation_did_not_converge')


def _replay_pass(session, packet, branch_id, invalid_decisions):
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
    for ident in dependency_cycles(decisions):
        status[ident] = {'status': 'needs_revalidation', 'reasons': ['decision_dependency_cycle']}
    for ident, issue in (invalid_decisions or {}).items():
        if ident in status:
            status[ident] = {'status': 'needs_revalidation', 'reasons': [issue.get('reason', issue['kind'])]}
    # Validate against a derived catalogue without altering the base source lock.
    contexts = []
    for row in decisions:
        if row['action'] == 'attach_context' and status[row['decision_id']]['status'] == 'active':
            candidate = {**row['payload'], 'decision_id': row['decision_id']}
            try:
                derive_packet(packet, [*contexts, candidate])
                contexts.append(candidate)
            except ValueError as error:
                status[row['decision_id']] = {'status': 'needs_revalidation', 'reasons': [str(error)]}
    catalog = derive_packet(packet, contexts)
    for row in decisions:
        if status[row['decision_id']]['status'] != 'active':
            continue
        try:
            validate_context_dependencies(packet, catalog, row, contexts)
            validate_action_payload(catalog, row['action'], row['payload'], row['targets'])
        except (ValueError, KeyError, TypeError) as error:
            status[row['decision_id']] = {'status': 'needs_revalidation', 'reasons': [str(error)]}
        for dependency in row.get('depends_on', []):
            if dependency not in ids:
                status[row['decision_id']] = {'status': 'needs_revalidation', 'reasons': ['missing_dependency:' + dependency]}
    propagate_inactive(decisions, status)
    retracted = set()
    applied_influencers = set()
    for row in reversed(decisions):
        if row['action'] == 'retract' and status[row['decision_id']]['status'] == 'active':
            target_id = row['payload']['decision_id']
            if target_id in status:
                applied_influencers.add(row['decision_id'])
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
    applied_influencers.update(r['decision_id'] for r in segmenters)
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
    applied_influencers.update(r['decision_id'] for r in context_decisions)
    if context_decisions:
        for row in decisions:
            if (row['action'] in ('select_candidate', 'bind_value', 'bind_call')
                    and status[row['decision_id']]['status'] == 'active'
                    and any(row.get('revision', 0) < context.get('revision', 0) for context in context_decisions)):
                status[row['decision_id']] = {'status': 'needs_revalidation',
                                              'reasons': ['context_candidate_set_changed']}
    active = [row for row in decisions if status[row['decision_id']]['status'] == 'active'
              and row['action'] != 'retract']
    # Inherited assertions address the same semantic object in this branch.
    # Authored records are untouched; copied replay rows acquire current scope.
    for row in active:
        for key in ('semantic_input', 'semantic_output'):
            if key in row['payload']:
                row['payload'][key]['branch_id'] = branch_id
    by_slot = {}
    for row in active:
        by_slot.setdefault(_slot(row), []).append(row)
    for rows in by_slot.values():
        if rows[0]['action'] == 'set_term_interpretation':
            positive = [row for row in rows if row['payload']['claim']['origin'] != 'machine_rejection']
            negative = [row for row in rows if row['payload']['claim']['origin'] == 'machine_rejection']
            expressions = {json.dumps(row['payload']['claim']['expression'], sort_keys=True) for row in positive}
            if len(expressions) > 1:
                for row in positive:
                    status[row['decision_id']] = {'status': 'conflicted', 'reasons': ['contradictory_term_interpretations']}
            for chosen in positive:
                expression = chosen['payload']['claim']['expression']
                for rejected in negative:
                    if any(snapshot['expression'] == expression for snapshot in rejected['payload']['claim']['candidate_snapshots']):
                        for row in (chosen, rejected):
                            status[row['decision_id']] = {'status': 'conflicted', 'reasons': ['adopted_term_interpretation_rejected']}
            continue
        if rows[0]['action'] == 'set_quantity_semantics' and any('facets' in row['payload'] for row in rows):
            from .quantity_targets import QUANTITY_FACETS, quantity_compatibility_issues
            facets, contributors = {}, {}
            for row in rows:
                values = row['payload'].get('facets', {k: v for k, v in row['payload'].items() if k in QUANTITY_FACETS})
                for key, value in values.items():
                    contributors.setdefault(key, []).append((row, value))
            for assignments in contributors.values():
                if len({json.dumps(value, sort_keys=True) for _, value in assignments}) > 1:
                    for row, _ in assignments:
                        status[row['decision_id']] = {'status': 'conflicted', 'reasons': ['conflicting_quantity_facet']}
            compatible_rows = [row for row in rows if status[row['decision_id']]['status'] == 'active']
            for row in compatible_rows:
                facets.update(row['payload'].get('facets', {k: v for k, v in row['payload'].items() if k in QUANTITY_FACETS}))
            incompatible = set().union(*(pair for _, pair in quantity_compatibility_issues(facets)))
            for row in compatible_rows:
                row_facets = row['payload'].get('facets', {k: v for k, v in row['payload'].items() if k in QUANTITY_FACETS})
                if incompatible.intersection(row_facets):
                    status[row['decision_id']] = {'status': 'conflicted', 'reasons': ['incompatible_combined_quantity_assertions']}
            continue
        payloads = {_normalize(row['payload']).__repr__() for row in rows}
        if len(rows) > 1 and len(payloads) > 1:
            for row in rows:
                status[row['decision_id']] = {'status': 'conflicted', 'reasons': ['multiple_active_decisions_for_slot']}
    propagate_inactive(decisions, status)
    effective = _empty_effective()
    for row in decisions:
        if status[row['decision_id']]['status'] != 'active' or row['action'] == 'retract':
            continue
        _apply(effective, row)
    normalized = {'branch_id': branch_id, 'effective': effective,
                  'decision_status': {key: status[key] for key in sorted(status)}}
    return {'status': 'ok', 'source_packet': source, 'decision_status': status,
            'effective': effective, 'normalized': _normalize(normalized),
            '_inactive_effects': {ident: {'kind': 'inactive_review_premise', 'reason': ','.join(status[ident]['reasons'])}
                                 for ident in applied_influencers if status[ident]['status'] != 'active'}}


def _empty_effective():
    return {'selected_candidates': {}, 'candidate_selection_metadata': {}, 'rejected_candidates': [], 'segments': [], 'scopes': {},
            'bindings': {}, 'quantity_semantics': {}, 'profiles': [], 'contexts': [], 'parameters': {},
            'manual_structures': [], 'noncomputational': [], 'deferred': [], 'approved_scopes': [], 'lexical_roles': [],
            'term_boundaries': [], 'term_interpretations': [], 'reviewed_relations': []}


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
        effective['scopes'][token] = {**payload, 'decision_id': row['decision_id']}
    elif action in ('bind_value', 'bind_call'):
        effective['bindings'][token] = {**payload, 'decision_id': row['decision_id'], 'target': row['targets'][0]}
    elif action == 'set_quantity_semantics':
        previous = effective['quantity_semantics'].get(token)
        if previous and ('facets' in payload or 'facets' in previous):
            from .quantity_targets import QUANTITY_FACETS
            values = payload.get('facets', {k: v for k, v in payload.items() if k in QUANTITY_FACETS})
            prior = previous.get('facets', {k: v for k, v in previous.items() if k in QUANTITY_FACETS})
            effective['quantity_semantics'][token] = {**payload, 'facets': {**prior, **values},
                'decision_id': row['decision_id'], 'decision_refs': previous.get('decision_refs', [previous['decision_id']]) + [row['decision_id']]}
        else:
            effective['quantity_semantics'][token] = {**payload, 'decision_id': row['decision_id']}
    elif action == 'set_term_boundary':
        effective['term_boundaries'].append({'decision_id': row['decision_id'], 'target': row['targets'][0], 'branch_id': row['branch_id']})
    elif action == 'set_term_interpretation':
        effective['term_interpretations'].append({**payload, 'decision_id': row['decision_id'], 'target': row['targets'][0]})
    elif action == 'approve_reviewed_relation':
        effective['reviewed_relations'].append({**payload, 'decision_id': row['decision_id']})
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
