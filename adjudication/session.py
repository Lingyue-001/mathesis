"""Append-only AdjudicationSession 1.x documents, independent of SourcePacket."""
import copy
import hashlib
import json
from pathlib import Path

from .anchors import packet_identity, validate_anchor
from .decision_contracts import validate_action_payload
from .registry import registry_identity
from analysis_parser.ontology import codes


ACTIONS = codes('action')

# A scholar may correct one attested occurrence's grammatical function.  These
# labels are deliberately textual evidence, not operation kinds or global
# dictionary entries; computational effect remains the construction compiler's
# separate judgement.
LEXICAL_ROLE_CONTRACT = {
    'version': '1.0',
    'roles': frozenset(codes('lexical_role')),
}


def new_session(packet, session_id):
    if not session_id:
        raise ValueError('session_id_required')
    return {
        'schema': 'AdjudicationSession', 'schema_version': '1.0',
        'session_id': session_id, 'source_packet': packet_identity(packet),
        'identity_locks': runtime_identity(packet),
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
        if branch_id in result or branch_id not in rows:
            raise ValueError('invalid_branch_ancestry')
        result.append(branch_id)
        branch_id = rows[branch_id]
    return set(result)


def validate_decision(session, packet, decision):
    required = {'decision_id', 'actor', 'created_at', 'branch_id', 'action', 'targets', 'payload',
                'evidence_refs', 'reason', 'depends_on'}
    if not isinstance(decision, dict):
        raise ValueError('invalid_decision_shape')
    missing = required - set(decision)
    if missing:
        raise ValueError('missing_decision_fields:' + ','.join(sorted(missing)))
    if decision['action'] not in ACTIONS:
        raise ValueError('unsupported_decision_action')
    if not isinstance(decision['actor'], dict) or decision['actor'].get('type') not in ('human', 'agent', 'scripted_fixture') or not decision['actor'].get('id'):
        raise ValueError('invalid_actor')
    if not any(row['id'] == decision['branch_id'] for row in session.get('branches', [])):
        raise ValueError('unknown_branch')
    if not isinstance(decision['targets'], list) or not decision['targets']:
        raise ValueError('decision_requires_target')
    if not isinstance(decision['payload'], dict) or not isinstance(decision['depends_on'], list):
        raise ValueError('invalid_decision_payload')
    for key in ('semantic_input', 'semantic_output', 'claim'):
        address = decision['payload'].get(key)
        if isinstance(address, dict) and address.get('branch_id') != decision['branch_id']:
            raise ValueError('decision_semantic_branch_mismatch')
    if decision['action'] == 'set_term_boundary' and decision['payload'].get('branch_id', decision['branch_id']) != decision['branch_id']:
        raise ValueError('decision_semantic_branch_mismatch')
    if not all(isinstance(d, str) and d for d in decision['depends_on']):
        raise ValueError('invalid_decision_dependency')
    from .effective_packet import derive_packet, validate_context_dependencies
    from .replay import replay_session
    state = replay_session(session, packet, decision['branch_id'])
    if state['status'] != 'ok':
        raise ValueError(state['status'])
    contexts = state['effective']['contexts']
    catalog = derive_packet(packet, contexts)
    validate_context_dependencies(packet, catalog, decision, contexts)
    validate_action_payload(catalog, decision['action'], decision['payload'], decision['targets'])
    if decision['action'] == 'retract' and decision['payload']['decision_id'] not in state['decision_status']:
        raise ValueError('unknown_retraction_target')
    if decision['action'] == 'attach_context':
        derive_packet(catalog, [decision['payload']])
    if decision['action'] == 'mark_noncomputational' and (not decision['reason'] or not decision['evidence_refs']):
        raise ValueError('noncomputational_reason_and_evidence_required')
    if decision['action'] == 'set_lexical_role':
        payload = decision['payload']
        if payload.get('contract_version') != LEXICAL_ROLE_CONTRACT['version']:
            raise ValueError('unsupported_lexical_role_contract')
        if payload.get('grammatical_role') not in LEXICAL_ROLE_CONTRACT['roles']:
            raise ValueError('invalid_lexical_role')
    return copy.deepcopy(decision)


def append_decision(session, decision, *, packet):
    if any(row['decision_id'] == decision.get('decision_id') for row in session.get('decisions', [])):
        raise ValueError('duplicate_decision_id')
    decision = validate_decision(session, packet, decision)
    from .replay import dependency_cycles
    if dependency_cycles([*session.get('decisions', []), decision]):
        raise ValueError('decision_dependency_cycle')
    decision['revision'] = len(session.get('decisions', [])) + 1
    session.setdefault('decisions', []).append(decision)
    return session


def branch_ancestors(session, branch_id):
    return _branch_ids(session, branch_id)


def _hash_files(names):
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for name in names:
        digest.update(name.encode('utf-8'))
        digest.update((root / name).read_bytes())
    return digest.hexdigest()


def runtime_identity(packet):
    from analysis_parser.resources import PROFILES
    selected = {name: PROFILES[name] for name in packet.get('selected_profiles', []) if name in PROFILES}
    profile_bytes = json.dumps(selected, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {
        'engine': {'sha256': _hash_files(('analysis_parser/pipeline.py', 'analysis_parser/scoped.py', 'analysis_parser/program_ir.py',
                                        'analysis_parser/semantic_rules.py', 'adjudication/semantic_closure.py'))},
        'grammar': {'sha256': _hash_files(('analysis_parser/lexical.py', 'analysis_parser/construction_ir.py'))},
        'registry': registry_identity(),
        'profiles': {'sha256': hashlib.sha256(profile_bytes).hexdigest()},
    }
