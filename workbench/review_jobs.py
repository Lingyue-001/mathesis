"""ReviewJob/1 storage only; decisions still belong to AdjudicationSession."""
import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import threading

from source_adapters.corpus_review import _atomic
from source_adapters.dependencies import digest

MAX_JOB_BYTES = 8 * 1024 * 1024
FIELDS = {'schema', 'job_id', 'revision', 'source_selection', 'base_packet_identity',
          'analysis_inputs_digest', 'session', 'branch_id', 'management_events', 'created_at', 'updated_at'}
FACETS = ('unit', 'quantity_kind', 'representation', 'coordinate_kind', 'index_base', 'reference_origin',
          'counting_boundary', 'step_unit', 'scale', 'term_boundary', 'term_interpretation', 'binding')
_locks = set()
_mutex = threading.Lock()


def job_path(root, job_id):
    if not isinstance(job_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', job_id):
        raise ValueError('invalid_review_job_id')
    folder = Path(root).resolve() / '.local' / 'review-jobs'
    path = folder / (job_id + '.json')
    if not path.resolve().is_relative_to(Path(root).resolve()) or path.is_symlink():
        raise ValueError('invalid_review_job_path')
    return path


def validate_job(job):
    if not isinstance(job, dict) or set(job) != FIELDS or job.get('schema') != 'ReviewJob/1':
        raise ValueError('invalid_review_job_contract')
    job_path('.', job['job_id'])
    if type(job['revision']) is not int or job['revision'] < 1:
        raise ValueError('invalid_review_job_revision')
    session = job['session']
    if not isinstance(session, dict) or session.get('schema') != 'AdjudicationSession' or session.get('schema_version') != '1.0':
        raise ValueError('invalid_review_job_session')
    if not isinstance(session.get('decisions'), list) or not isinstance(session.get('branches'), list):
        raise ValueError('invalid_review_job_session')
    if not all(isinstance(b, dict) and isinstance(b.get('id'), str) and 'parent_id' in b for b in session['branches']):
        raise ValueError('invalid_review_job_branches')
    if len({b['id'] for b in session['branches']}) != len(session['branches']):
        raise ValueError('duplicate_review_job_branch')
    from adjudication.session import branch_ancestors
    for branch in session['branches']:
        branch_ancestors(session, branch['id'])
    if not all(isinstance(d, dict) and isinstance(d.get('decision_id'), str) and d['decision_id']
               and isinstance(d.get('depends_on'), list) and all(isinstance(dep, str) for dep in d['depends_on'])
               for d in session['decisions']):
        raise ValueError('invalid_review_job_decisions')
    if len({d['decision_id'] for d in session['decisions']}) != len(session['decisions']):
        raise ValueError('duplicate_decision_id')
    if session.get('source_packet') != job['base_packet_identity']:
        raise ValueError('review_job_base_identity_mismatch')
    if not any(b.get('id') == job['branch_id'] for b in session['branches']):
        raise ValueError('invalid_review_job_branch')
    if not isinstance(job['management_events'], list) or not isinstance(job['source_selection'], dict):
        raise ValueError('invalid_review_job_fields')
    ids = set()
    for event in job['management_events']:
        validate_management_event(event)
        if event['event_id'] in ids:
            raise ValueError('duplicate_management_event')
        ids.add(event['event_id'])
    return job


def validate_management_event(event):
    required = {'event_id', 'action', 'target', 'facet', 'branch_id', 'actor', 'created_at', 'reason'}
    if not isinstance(event, dict) or not required.issubset(event) or set(event) - required - {'depends_on', 'semantic_target'}:
        raise ValueError('invalid_management_event')
    if event['action'] not in ('manage', 'unmanage') or event['facet'] not in FACETS:
        raise ValueError('unsupported_management_action_or_facet')
    if not all(isinstance(event[k], str) and event[k].strip() for k in ('event_id', 'branch_id', 'created_at', 'reason')):
        raise ValueError('management_event_metadata_required')
    actor = event['actor']
    if not isinstance(actor, dict) or actor.get('type') not in ('human', 'agent', 'scripted_fixture') or not actor.get('id'):
        raise ValueError('management_actor_required')
    if not isinstance(event['target'], dict) or not {'doc_id', 'reading_id', 'source_sha256', 'start', 'end', 'quote'}.issubset(event['target']):
        raise ValueError('management_source_anchor_required')
    if not isinstance(event.get('depends_on', []), list) or not all(isinstance(d, str) for d in event.get('depends_on', [])):
        raise ValueError('invalid_management_dependencies')
    semantic = event.get('semantic_target')
    if semantic is not None:
        if not isinstance(semantic, dict) or semantic.get('kind') not in ('semantic_input', 'semantic_output', 'binding', 'term_boundary', 'term_interpretation'):
            raise ValueError('invalid_management_semantic_target')
        location = semantic.get('construction') or semantic.get('consumer') or semantic.get('source')
        from adjudication.anchors import anchor_location
        if not isinstance(location, (list, tuple)) or tuple(location[:4]) != anchor_location(event['target']):
            raise ValueError('management_semantic_target_location_mismatch')


def management_key(event):
    return digest([event['branch_id'], event['target'], event['facet'], event.get('semantic_target')])


def management_state(job):
    """Reduce ancestry parent-first; child ownership overrides never change parent."""
    parents = {b['id']: b['parent_id'] for b in job['session']['branches']}
    lineage = []
    branch = job['branch_id']
    while branch is not None:
        if branch in lineage or branch not in parents:
            raise ValueError('invalid_branch_ancestry')
        lineage.append(branch)
        branch = parents[branch]
    rows = {}
    for branch in reversed(lineage):
        for event in job['management_events']:
            if event['branch_id'] != branch:
                continue
            row = {**copy.deepcopy(event), 'branch_id': job['branch_id'],
                   'authored_branch_id': branch, 'managed': event['action'] == 'manage'}
            if row.get('semantic_target') and 'branch_id' in row['semantic_target']:
                row['semantic_target']['branch_id'] = job['branch_id']
            rows[management_key(row)] = row
    return list(rows.values())


def export_job(job):
    validate_job(job)
    encoded = json.dumps(job, ensure_ascii=False, indent=2) + '\n'
    if len(encoded.encode('utf-8')) > MAX_JOB_BYTES:
        raise ValueError('review_job_too_large')
    return encoded


def parse_job(text):
    if not isinstance(text, (str, bytes)) or len(text if isinstance(text, bytes) else text.encode('utf-8')) > MAX_JOB_BYTES:
        raise ValueError('review_job_too_large_or_invalid')
    try:
        return validate_job(json.loads(text))
    except (KeyError, TypeError, RecursionError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid_review_job_file') from error


def load_job(root, job_id):
    path = job_path(root, job_id)
    if path.stat().st_size > MAX_JOB_BYTES:
        raise ValueError('review_job_too_large')
    job = parse_job(path.read_bytes())
    if job['job_id'] != job_id:
        raise ValueError('review_job_filename_mismatch')
    return job


def list_jobs(root):
    folder = job_path(root, 'inventory').parent
    if not folder.exists():
        return []
    result = []
    for path in sorted(folder.glob('*.json')):
        try:
            job = load_job(root, path.stem)
            result.append({'job_id': job['job_id'], 'revision': job['revision'], 'status': 'readable'})
        except (ValueError, OSError):
            result.append({'job_id': path.stem, 'status': 'invalid_file'})
    return result


@contextmanager
def job_lock(root, job_id):
    path = job_path(root, job_id).with_suffix('.lock')
    if path.is_symlink() or not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('invalid_review_job_lock_path')
    token = str(path.resolve())
    with _mutex:
        if token in _locks:
            raise ValueError('review_job_locked')
        _locks.add(token)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a+b') as handle:
            try:
                if os.name == 'nt':
                    import msvcrt
                    if handle.tell() == 0:
                        handle.write(b'0'); handle.flush()
                    handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise ValueError('review_job_locked') from error
            try:
                yield
            finally:
                if os.name == 'nt':
                    handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)
    finally:
        with _mutex:
            _locks.discard(token)


def write_job_atomic(root, job):
    export_job(job)  # size and schema validation precede atomic replace
    _atomic(job_path(root, job['job_id']), job)
