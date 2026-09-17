"""Append-only AdjudicationSession 1.x documents, independent of SourcePacket."""
import copy

from .anchors import packet_identity, validate_anchor


ACTIONS = {
    'select_candidate', 'reject_candidate', 'resegment', 'set_scope',
    'bind_value', 'bind_call', 'set_quantity_semantics', 'select_profile',
    'attach_context', 'declare_parameter', 'assemble_known_structure',
    'mark_noncomputational', 'defer', 'approve_scope', 'retract',
}


def new_session(packet, session_id):
    if not session_id:
        raise ValueError('session_id_required')
    return {
        'schema': 'AdjudicationSession', 'schema_version': '1.0',
        'session_id': session_id, 'source_packet': packet_identity(packet),
        'branches': [{'id': 'main', 'parent_id': None}], 'decisions': [],
    }


def create_branch(session, branch_id, from_branch='main'):
    if not branch_id or any(row['id'] == branch_id for row in session.get('branches', [])):
        raise ValueError('invalid_or_duplicate_branch')
    if not any(row['id'] == from_branch for row in session.get('branches', [])):
        raise ValueError('unknown_parent_branch')
    session['branches'].append({'id': branch_id, 'parent_id': from_branch})
    return session


def _branch_ids(session, branch_id):
    rows = {row['id']: row.get('parent_id') for row in session.get('branches', [])}
    if branch_id not in rows:
        raise ValueError('unknown_branch')
    result = []
    while branch_id is not None:
        result.append(branch_id)
        branch_id = rows[branch_id]
    return set(result)


def validate_decision(session, packet, decision):
    required = {'decision_id', 'actor', 'created_at', 'branch_id', 'action', 'targets', 'payload',
                'evidence_refs', 'reason', 'depends_on'}
    missing = required - set(decision or {})
    if missing:
        raise ValueError('missing_decision_fields:' + ','.join(sorted(missing)))
    if decision['action'] not in ACTIONS:
        raise ValueError('unsupported_decision_action')
    if decision['actor'].get('type') not in ('human', 'agent', 'scripted_fixture') or not decision['actor'].get('id'):
        raise ValueError('invalid_actor')
    if not any(row['id'] == decision['branch_id'] for row in session.get('branches', [])):
        raise ValueError('unknown_branch')
    if not isinstance(decision['targets'], list) or not decision['targets']:
        raise ValueError('decision_requires_target')
    for target in decision['targets']:
        validate_anchor(packet, target)
    if not isinstance(decision['payload'], dict) or not isinstance(decision['depends_on'], list):
        raise ValueError('invalid_decision_payload')
    if decision['action'] == 'retract' and not decision['payload'].get('decision_id'):
        raise ValueError('retract_requires_decision_id')
    return copy.deepcopy(decision)


def append_decision(session, decision, packet=None):
    if any(row['decision_id'] == decision.get('decision_id') for row in session.get('decisions', [])):
        raise ValueError('duplicate_decision_id')
    if packet is not None:
        decision = validate_decision(session, packet, decision)
    else:
        decision = copy.deepcopy(decision)
    session.setdefault('decisions', []).append(decision)
    return session


def branch_ancestors(session, branch_id):
    return _branch_ids(session, branch_id)
