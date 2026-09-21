"""Narrow corpus → compiler → executor orchestration shared by HTTP and tests."""
from analysis_parser.pipeline import parse_packet
from analysis_parser.execution import execute
from adjudication import append_decision, compile_reviewed, create_branch, new_session
from adjudication.bundle import make_bundle
from source_adapters.corpus import build_source_packet, build_source_packet_from_units
from workbench.projection import project_graph
from workbench.presentation import build_presentation
from source_adapters.dependencies import artifact


def _artifacts(packet, graph):
    parser = artifact('parser', graph, packet=packet)
    return [parser, artifact('graph', graph, parents=[parser])]


def analyze_procedure(root, procedure_id):
    source = build_source_packet(root, procedure_id)
    graph = parse_packet(source['source_packet'])
    projection = project_graph(graph)
    return {
        **source, 'graph': graph, 'projection': projection,
        'artifacts': _artifacts(source['source_packet'], graph),
        'summary': {
            'graph_status': 'issues' if projection['issues'] else 'compiled',
            'execution_status': 'not_run',
            'event_count': len(graph['events']),
            'value_count': len(graph['value_instances']),
        },
    }


def compile_procedure(root, procedure_id, inputs):
    source = analyze_procedure(root, procedure_id)
    contract = {item['name']: item for item in source['procedure']['inputs']}
    if not isinstance(inputs, dict) or set(inputs) - set(contract):
        raise ValueError('invalid_inputs: use declared input names')
    for name, value in inputs.items():
        spec = contract[name]
        if (spec['type'] != 'integer' or type(value) is not int
                or not spec['minimum'] <= value <= spec['maximum']):
            raise ValueError(f"invalid_input: {name} must be an integer in {spec['minimum']}–{spec['maximum']}")
    graph = source['graph']
    execution = execute(graph, inputs)
    unresolved = {
        'compiler': graph.get('unresolved', []),
        'diagnostics': graph.get('diagnostics', []),
        'unparsed_spans': graph.get('coverage', {}).get('unparsed_spans', []),
        'execution': execution.get('unresolved', []),
    }
    missing = any(row.get('cause') == 'requires_explicit_input' for row in unresolved['execution'])
    graph_issues = bool(source['projection']['issues'])
    return {
        **source,
        'summary': {
            'graph_status': 'issues' if graph_issues else 'compiled',
            'execution_status': 'missing_inputs' if missing else 'unresolved' if unresolved['execution'] else 'executed',
            'event_count': len(graph['events']),
            'value_count': len(graph['value_instances']),
        },
        'unresolved': unresolved,
        'graph': graph,
        'execution': execution,
        'artifacts': [*source['artifacts'], artifact('execution', {'inputs': inputs, 'execution': execution},
                                                   parents=[source['artifacts'][-1]])],
    }


def _stage_records(source, bundle):
    """Describe completed compiler products; this is not a progress simulation."""
    graph = bundle['graph']
    queue = bundle['review_queue']['items']
    coverage = bundle['coverage_ledger']
    status = lambda needed: 'needs_review' if needed else 'completed'
    blocked = coverage['graph_status'] == 'invalid'
    return [
        {'id': 'source_scope', 'label': '来源与范围核验', 'status': 'completed',
         'inputs': ['canonical corpus', 'procedure registry'],
         'artifacts': [{'kind': 'source_packet', 'packet_id': source['source_packet']['packet_id']},
                       {'kind': 'documents', 'count': len(graph.get('documents', []))}],
         'rules': ['source_adapter_hash_and_section_validation'], 'affected_stages': ['lexical_syntax']},
        {'id': 'lexical_syntax', 'label': '词项／构式候选',
         'status': status(bool(graph.get('syntax', {}).get('diagnostics'))),
         'inputs': ['SourcePacket documents'],
         'artifacts': [{'kind': 'tokens', 'count': len(graph.get('tokens', []))},
                       {'kind': 'construction_candidates', 'count': len(graph.get('construction_candidates', []))}],
         'rules': ['analysis_parser.lexical', 'analysis_parser.construction_ir'],
         'affected_stages': ['procedure_control', 'quantity_binding']},
        {'id': 'procedure_control', 'label': '过程与控制结构',
         'status': status(bool(graph.get('program', {}).get('diagnostics'))),
         'inputs': ['syntax candidates'],
         'artifacts': [{'kind': 'definitions', 'count': len(graph.get('program', {}).get('definitions', []))}],
         'rules': ['analysis_parser.program_ir'], 'affected_stages': ['quantity_binding', 'graph_coverage']},
        {'id': 'quantity_binding', 'label': '数量／来源／端口绑定',
         'status': status(any(item['kind'] in ('missing_input', 'producer_or_port_ambiguity', 'quantity_semantics') for item in queue)),
         'inputs': ['program definitions', 'binding constraints'],
         'artifacts': [{'kind': 'values', 'count': len(graph.get('value_instances', []))},
                       {'kind': 'events', 'count': len(graph.get('events', []))}],
         'rules': ['analysis_parser.link_entry', 'adjudication.binding_constraints'],
         'affected_stages': ['graph_coverage', 'review']},
        {'id': 'graph_coverage', 'label': '图与覆盖检查',
         'status': 'blocked' if blocked else status(coverage['graph_status'] != 'closed'),
         'inputs': ['typed graph', 'coverage ledger'],
         'artifacts': [{'kind': 'graph_status', 'value': coverage['graph_status']},
                       {'kind': 'unresolved_required_spans', 'count': len(coverage['unresolved_required_spans'])}],
         'rules': ['SourceStructureCoverageLedger'], 'affected_stages': ['review']},
        {'id': 'review', 'label': '待审定或审定完成', 'status': status(bool(queue)),
         'inputs': ['review queue', 'replay status'],
         'artifacts': [{'kind': 'review_questions', 'count': len(queue)}],
         'rules': ['adjudication.review_queue'], 'affected_stages': []},
    ]


def _reviewed_response(source, session, branch_id):
    compilation = compile_reviewed(source['source_packet'], session, branch_id)
    bundle = make_bundle(compilation, session)
    graph = bundle.get('graph')
    projection = project_graph(graph, bundle) if graph is not None else {
        'projection_version': 2, 'frames': [], 'steps': [], 'nodes': [], 'edges': [], 'quantities': [],
        'issues': [], 'layers': {}, 'coverage': None, 'review_queue': bundle['review_queue'], 'trace': None,
    }
    response = {
        **source, 'session': session, 'branch_id': branch_id, 'bundle': bundle, 'graph': graph,
        'projection': projection,
        'stages': _stage_records(source, bundle) if graph is not None else [
            {'id': 'source_scope', 'label': '来源与范围核验', 'status': 'stale', 'inputs': [],
             'artifacts': [], 'rules': [], 'affected_stages': []}],
        'summary': {
            'graph_status': bundle['coverage_ledger']['graph_status'] if graph is not None else 'invalid',
            'review_status': ('needs_revalidation' if graph is None else
                              'needs_review' if bundle['review_queue']['items'] else 'completed'),
            'execution_status': 'not_run',
            'comparison_status': 'unavailable',
        },
    }
    if graph is None:
        # A blocked replay is not an empty successful analysis. Keep its session
        # and graph=None; provide a separately labelled, decision-free reference
        # through the same compiler so the current source remains inspectable.
        reference = _reviewed_response(source, new_session(source['source_packet'],
                                       f"workbench:{source['procedure']['id']}"), 'main')
        response['reference_analysis'] = {
            'kind': 'current_automatic_reference',
            **{key: reference[key] for key in ('graph', 'projection', 'stages', 'summary')},
        }
    response['presentation'] = build_presentation(response)
    response['artifacts'] = _artifacts(source['source_packet'], graph) if graph is not None else []
    bundle['artifacts'] = response['artifacts']
    return response


def open_adjudication(root, procedure_id, session=None, branch_id='main'):
    """Open a real reviewed compiler session for one registered corpus procedure."""
    source = build_source_packet(root, procedure_id)
    session = session or new_session(source['source_packet'], f'workbench:{procedure_id}')
    return _reviewed_response(source, session, branch_id)


def compile_adjudication(root, procedure_id, session, branch_id='main'):
    """Recompile a supplied session; all graph changes flow through the reviewed compiler."""
    if not isinstance(session, dict) or session.get('schema') != 'AdjudicationSession':
        raise ValueError('invalid_adjudication_session')
    return _reviewed_response(build_source_packet(root, procedure_id), session, branch_id)


def execute_adjudication(root, procedure_id, session, branch_id, inputs):
    """Run the numerical check against the reviewed graph currently on screen."""
    result = compile_adjudication(root, procedure_id, session, branch_id)
    contract = {item['name']: item for item in result['procedure']['inputs']}
    if not isinstance(inputs, dict) or set(inputs) - set(contract):
        raise ValueError('invalid_inputs: use declared input names')
    for name, value in inputs.items():
        spec = contract[name]
        if (spec['type'] != 'integer' or type(value) is not int
                or not spec['minimum'] <= value <= spec['maximum']):
            raise ValueError(f"invalid_input: {name} must be an integer in {spec['minimum']}–{spec['maximum']}")
    if result['graph'] is None:
        raise ValueError('reviewed_graph_unavailable')
    execution = execute(result['graph'], inputs)
    missing = any(row.get('cause') == 'requires_explicit_input' for row in execution.get('unresolved', []))
    result['execution'] = execution
    result['artifacts'] = [*result['artifacts'], artifact('execution', {'inputs': inputs, 'execution': execution},
                                                       parents=[result['artifacts'][-1]])]
    result['bundle']['artifacts'] = result['artifacts']
    result['summary'] = {**result['summary'], 'execution_graph': 'reviewed',
                         'execution_status': 'missing_inputs' if missing else 'unresolved' if execution.get('unresolved') else 'executed'}
    result['presentation'] = build_presentation(result)
    return result


def apply_adjudication_decision(root, procedure_id, session, decision, branch_id='main'):
    """Append one validated human decision, then recompile the affected reviewed model."""
    source = build_source_packet(root, procedure_id)
    append_decision(session, decision, packet=source['source_packet'])
    return _reviewed_response(source, session, branch_id)


def branch_adjudication(root, procedure_id, session, branch_id, from_branch='main'):
    """Create an explicit interpretation branch without overwriting its parent."""
    create_branch(session, branch_id, from_branch)
    return _reviewed_response(build_source_packet(root, procedure_id), session, branch_id)


# K2-A uses the same compiler and decision language, with a file-backed envelope.
import copy
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from adjudication.anchors import anchor_for, anchor_key, overlaps, packet_identity, validate_anchor
from adjudication.effective_packet import derive_packet, decision_anchors, validate_context_dependencies
from adjudication.decision_contracts import normalize_decision_target
from adjudication.replay import dependency_cycles, replay_session
from adjudication.session import _hash_files, runtime_identity, validate_decision
from source_adapters.dependencies import digest
from workbench import review_jobs


def _now():
    return datetime.now(timezone.utc).isoformat()


def _packet_for_job(root, selection, job_id):
    fields = {'source_id', 'primary_unit_ids', 'context_unit_ids', 'provided_scope', 'selected_profiles'}
    if not isinstance(selection, dict) or set(selection) != fields:
        raise ValueError('invalid_review_job_source_selection')
    if not isinstance(selection['provided_scope'], dict) or not isinstance(selection['selected_profiles'], list):
        raise ValueError('invalid_review_job_analysis_inputs')
    for key in ('primary_unit_ids', 'context_unit_ids'):
        if not isinstance(selection[key], list) or not all(isinstance(s, str) and s for s in selection[key]):
            raise ValueError('invalid_review_job_units')
        if len(set(selection[key])) != len(selection[key]):
            raise ValueError('duplicate_review_job_units')
    if set(selection['primary_unit_ids']) & set(selection['context_unit_ids']):
        raise ValueError('primary_context_overlap')
    packet = build_source_packet_from_units(root, selection['source_id'], selection['primary_unit_ids'],
        selection['context_unit_ids'], copy.deepcopy(selection['provided_scope']), packet_id='review-job:' + job_id)
    packet['selected_profiles'] = copy.deepcopy(selection['selected_profiles'])
    return packet


def _current_job_packet(root, job):
    packet = _packet_for_job(root, job['source_selection'], job['job_id'])
    if packet_identity(packet) != job['base_packet_identity'] or _analysis_inputs_digest(packet) != job['analysis_inputs_digest']:
        raise ValueError('review_job_source_or_analysis_inputs_changed')
    if runtime_identity(packet) != job['session']['identity_locks']:
        raise ValueError('review_job_runtime_identity_changed')
    return packet


def _analysis_inputs_digest(packet):
    code_root = Path(__file__).resolve().parents[1]
    files = sorted(p.relative_to(code_root).as_posix() for p in (code_root / 'adjudication').glob('*.py'))
    files.extend(['workbench/service.py', 'workbench/review_jobs.py', 'source_adapters/corpus.py'])
    return digest({'packet': packet, 'review_code': _hash_files(files)})


def _context_freshness(root, contexts):
    for row in contexts:
        doc = row['document']; source = doc.get('source', {})
        if source.get('source_id') and source.get('unit_id'):
            current = build_source_packet_from_units(root, source['source_id'], [source['unit_id']])['primary_documents'][0]
            if current != doc:
                raise ValueError('review_job_attached_source_changed:' + doc['doc_id'])


def _management_scope(job, packet, compilation):
    state = compilation['replay']; contexts = state['effective']['contexts']
    catalog = derive_packet(packet, contexts)
    active = [r for r in job['session']['decisions'] if state['decision_status'].get(r['decision_id'], {}).get('status') == 'active']
    result = []
    for event in review_jobs.management_state(job):
        if event['branch_id'] != job['branch_id']:
            continue
        row = {**event, 'status': 'pending' if event['managed'] else 'unmanaged',
               'decision_refs': [], 'consumer_status': 'source_occurrence_only'}
        if not event['managed']:
            result.append(row)
            continue
        try:
            if any(state['decision_status'].get(d, {}).get('status') != 'active' for d in event.get('depends_on', [])):
                raise ValueError('management_dependency_inactive')
            validate_context_dependencies(packet, catalog, {'targets': [event['target']], 'depends_on': event.get('depends_on', [])}, contexts)
        except ValueError:
            row['status'] = 'needs_revalidation'
        else:
            for decision in active:
                if (decision['action'] == 'set_quantity_semantics' and event['facet'] in decision['payload'].get('facets', decision['payload'])
                    or decision['action'] in ('bind_value', 'bind_call') and event['facet'] == 'binding'):
                    payload = copy.deepcopy(decision['payload'])
                    for direction in ('semantic_input', 'semantic_output'):
                        if direction in payload:
                            payload[direction]['branch_id'] = job['branch_id']
                    semantic_anchor = ((payload.get('semantic_input') or payload.get('semantic_output'))['construction_anchor'] if decision['action'] == 'set_quantity_semantics'
                                       else payload['consumer_definition_anchor'])
                    if anchor_key(semantic_anchor) == anchor_key(event['target']):
                        if event.get('semantic_target') is not None and digest(event['semantic_target']) != digest(
                                normalize_decision_target(decision['action'], payload, decision['targets'])):
                            continue
                        row['decision_refs'].append(decision['decision_id'])
            # A bare occurrence may contain several outputs. It stays pending
            # until the manager explicitly identifies the semantic input/output.
            if event.get('semantic_target') and row['decision_refs']:
                row['status'] = 'interpretation_recorded'
            for applied in compilation['graph'].get('managed_scopes', []):
                if applied.get('event_id') == event['event_id']:
                    row['consumer_status'] = 'applied_before_operation' if applied['status'] == 'resolved' else 'unresolved_fallback_suppressed'
                    if applied['status'] == 'needs_revalidation':
                        row['status'] = 'needs_revalidation'
        result.append(row)
    return result


def _job_response(root, job, packet, compilation=None):
    compilation = compilation if compilation is not None else compile_reviewed(
        packet, job['session'], job['branch_id'], management=review_jobs.management_state(job))
    if compilation.get('graph') is None:
        raise ValueError('review_job_' + compilation['replay']['status'])
    contexts = compilation['replay']['effective']['contexts']
    _context_freshness(root, contexts)
    if any(d.get('kind') == 'parser_exception' for d in compilation['graph'].get('diagnostics', [])):
        raise RuntimeError('review_job_compiler_exception')
    bundle = make_bundle(compilation, job['session'])
    catalog = derive_packet(packet, contexts)
    forms = _review_forms(catalog, compilation)
    from .question_presenter import build_questions
    return {'job': job, 'job_digest': digest(job), 'packet': packet, 'effective_packet': catalog,
            'session': job['session'], 'branch_id': job['branch_id'], 'compilation': compilation, 'bundle': bundle,
            'graph': compilation['graph'], 'freshness': {'status': 'current'},
            'managed_scope': _management_scope(job, packet, compilation),
            'review_forms': forms, 'questions': build_questions(catalog, compilation, forms, job['branch_id']),
            'summary': {'graph_status': compilation['coverage_ledger']['graph_status'], 'execution_status': 'not_run'}}


def create_review_job(root, job_id, source_selection):
    with review_jobs.job_lock(root, job_id):
        if review_jobs.job_path(root, job_id).exists():
            raise ValueError('review_job_already_exists')
        packet = _packet_for_job(root, source_selection, job_id)
        now = _now()
        job = {'schema': 'ReviewJob/1', 'job_id': job_id, 'revision': 1,
               'source_selection': copy.deepcopy(source_selection), 'base_packet_identity': packet_identity(packet),
               'analysis_inputs_digest': _analysis_inputs_digest(packet), 'session': new_session(packet, 'review:' + uuid4().hex),
               'branch_id': 'main', 'management_events': [], 'created_at': now, 'updated_at': now}
        response = _job_response(root, job, packet)
        review_jobs.write_job_atomic(root, job)
        return response


def create_fresh_review_job(root, source_selection):
    """Create a new opaque ReviewJob for an explicit advanced-session action."""
    base = 'session-' + digest(source_selection)[:20]
    suffix = 0
    while True:
        job_id = base if suffix == 0 else base + '-' + str(suffix)
        try:
            return create_review_job(root, job_id, source_selection)
        except ValueError as error:
            if str(error) != 'review_job_already_exists':
                raise
            suffix += 1


def resolve_current_review_job(root, source_selection):
    """Return the newest current job for one exact source selection.

    ReviewJob remains the durable transaction record, but ordinary UI entry
    should neither name nor create it explicitly.  A stale record is retained
    for audit/history and deliberately cannot win this lookup.
    """
    current = []
    for row in review_jobs.list_jobs(root):
        if row['status'] != 'readable':
            continue
        job = review_jobs.load_job(root, row['job_id'])
        if job['source_selection'] != source_selection:
            continue
        response = compile_review_job(root, job['job_id'])
        if response['freshness']['status'] == 'current':
            current.append(response)
    if current:
        return max(current, key=lambda response: (response['job']['updated_at'],
                                                   response['job']['revision'],
                                                   response['job']['job_id']))
    return create_fresh_review_job(root, source_selection)


def compile_review_job(root, job_id):
    job = review_jobs.load_job(root, job_id)
    try:
        packet = _current_job_packet(root, job)
        return _job_response(root, job, packet)
    except (ValueError, OSError) as error:
        return {'job': job, 'job_digest': digest(job), 'freshness': {'status': 'stale', 'reason': str(error)},
                'graph': None, 'review_forms': [], 'managed_scope': []}


def _decision_signature(row):
    return digest({k: row.get(k) for k in ('branch_id', 'action', 'targets', 'payload', 'evidence_refs', 'reason', 'depends_on')})


def review_execution_inputs(graph):
    """Read numeric input requirements from the current graph, not a preset."""
    return sorted({event['attributes']['name'] for event in graph['events']
                   if event['kind'] == 'input' and not event.get('attributes', {}).get('execution_blocked')})


def review_analysis_identity(response):
    return digest({'graph': response['graph'], 'locks': response['session']['identity_locks'],
                   'branch': response['branch_id']})


def review_execution_stale(execution, response):
    return (response['freshness']['status'] != 'current'
            or execution.get('job_id') != response['job']['job_id']
            or execution.get('revision') != response['job']['revision']
            or execution.get('branch_id') != response['job']['branch_id']
            or execution.get('job_digest') != response['job_digest']
            or execution.get('analysis_identity') != review_analysis_identity(response))


def execute_review_job(root, job_id, inputs, *, expected_revision, expected_digest):
    """Execute the locked current reviewed graph using the existing exact executor."""
    with review_jobs.job_lock(root, job_id):
        job = review_jobs.load_job(root, job_id)
        if type(expected_revision) is not int or job['revision'] != expected_revision or digest(job) != expected_digest:
            raise ValueError('stale_job_revision_or_digest')
        packet = _current_job_packet(root, job)
        response = _job_response(root, job, packet)
        if not isinstance(inputs, dict) or set(inputs) - set(review_execution_inputs(response['graph'])):
            raise ValueError('invalid_inputs: use current graph input names')
        if any(type(value) is not int for value in inputs.values()):
            raise ValueError('invalid_inputs: exact integers required')
        parameter_names = {e['attributes']['name'] for e in response['graph']['events']
                           if e['kind'] == 'input' and e['attributes'].get('parameter')}
        execution = execute(response['graph'], inputs, {name: value for name, value in inputs.items() if name in parameter_names})
        output_quantities = {}
        for value in response['graph']['value_instances']:
            if value['id'] not in execution['values'] or value['role'] in ('parameter', 'literal', 'external_input', 'parameter_missing'):
                continue
            for label in value.get('labels', []):
                name = value['scope'].get('query', 'main') + ':' + label
                representation = copy.deepcopy(value.get('representation', {}))
                denominator = representation.get('denominator_id', representation.get('denominator'))
                if isinstance(denominator, str) and denominator in execution['values']:
                    representation['denominator_value'] = execution['values'][denominator]
                output_quantities[name] = {'value': execution['values'][value['id']],
                    'unit': value.get('unit', 'unknown'), 'representation': representation,
                    'coordinate_kind': value.get('coordinate_kind'),
                    'decision_refs': value.get('adjudication_decision_refs', [])}
        return {'schema': 'ReviewExecution/1', 'job_id': job_id, 'revision': job['revision'],
                'branch_id': job['branch_id'], 'job_digest': response['job_digest'],
                'analysis_identity': review_analysis_identity(response), 'inputs': copy.deepcopy(inputs),
                'graph_status': response['summary']['graph_status'],
                'status': 'unresolved' if execution['unresolved'] else 'executed', 'output_quantities': output_quantities,
                **execution}


def apply_review_job_changes(root, job_id, *, decisions=(), management_events=(), expected_revision, expected_digest):
    with review_jobs.job_lock(root, job_id):
        original = review_jobs.load_job(root, job_id)
        if type(expected_revision) is not int or original['revision'] != expected_revision or digest(original) != expected_digest:
            raise ValueError('stale_job_revision_or_digest')
        packet = _current_job_packet(root, original)
        before = _job_response(root, original, packet)
        if not isinstance(decisions, (list, tuple)) or not isinstance(management_events, (list, tuple)):
            raise ValueError('review_job_changes_must_be_lists')
        job = copy.deepcopy(original)
        if dependency_cycles([*job['session']['decisions'], *decisions]):
            raise ValueError('decision_dependency_cycle')
        # Topological order permits explicitly listed attachment + dependent batches.
        remaining = list(copy.deepcopy(decisions)); added = []
        while remaining:
            pending_ids = {r['decision_id'] for r in remaining}
            ready = [r for r in remaining if not pending_ids.intersection(r.get('depends_on', []))]
            if not ready:
                raise ValueError('decision_dependency_cycle')
            for row in ready:
                remaining.remove(row)
                current = replay_session(job['session'], packet, job['branch_id'])
                if row['branch_id'] != job['branch_id']:
                    raise ValueError('review_job_branch_mismatch')
                if any(_decision_signature(row) == _decision_signature(d)
                       and current['decision_status'].get(d['decision_id'], {}).get('status') == 'active'
                       for d in job['session']['decisions']):
                    continue
                validate_decision(job['session'], packet, row)
                if any(current['decision_status'].get(d, {}).get('status') != 'active' for d in row.get('depends_on', [])):
                    raise ValueError('decision_dependency_not_active')
                append_decision(job['session'], row, packet=packet); added.append(row['decision_id'])
        # Stage the complete ownership ledger before the authoritative trial.
        for event in management_events:
            review_jobs.validate_management_event(event)
            if event['branch_id'] != job['branch_id']:
                raise ValueError('management_branch_mismatch')
            if any(e['event_id'] == event['event_id'] for e in job['management_events']):
                raise ValueError('duplicate_management_event')
            prior = next((s for s in review_jobs.management_state(job)
                          if review_jobs.management_key(s) == review_jobs.management_key(event)), None)
            if event['action'] == 'unmanage':
                if prior is None:
                    raise ValueError('unmanage_requires_recorded_scope')
            if prior and prior['managed'] == (event['action'] == 'manage'):
                continue
            job['management_events'].append(copy.deepcopy(event))
        after = _job_response(root, job, packet)
        state = after['compilation']['replay']
        for ident in added:
            status = state['decision_status'][ident]
            if status['status'] in ('needs_revalidation', 'conflicted'):
                raise ValueError('invalid_submitted_decision:' + ident + ':' + ','.join(status['reasons']))
        for event in management_events:
            if event['action'] == 'manage':
                invalid_scope = next((scope for scope in after['graph'].get('managed_scopes', [])
                    if scope.get('event_id') == event['event_id'] and scope['status'] == 'needs_revalidation'), None)
                if invalid_scope:
                    raise ValueError('invalid_management_target:' + invalid_scope.get('reason', 'unavailable_consumer'))
                if any(state['decision_status'].get(d, {}).get('status') != 'active'
                       for d in event.get('depends_on', [])):
                    raise ValueError('management_dependency_not_active')
                validate_context_dependencies(packet, after['effective_packet'],
                    {'targets': [event['target']], 'depends_on': event.get('depends_on', [])}, state['effective']['contexts'])
            else:
                # An explicit release must not silently discard active reviewed facts.
                prior_scopes = _management_scope({**job, 'management_events': [e for e in job['management_events']
                    if e['event_id'] != event['event_id']]}, packet, after['compilation'])
                prior = next((s for s in prior_scopes if review_jobs.management_key(s) == review_jobs.management_key(event)), None)
                if prior and prior['decision_refs']:
                    raise ValueError('unmanage_has_active_semantic_decisions')
        if job == original:
            return {**before, 'saved': False, 'effects': _review_effects(before, before), 'recorded_decisions': []}
        job['revision'] += 1; job['updated_at'] = _now()
        after = _job_response(root, job, packet, after['compilation'])
        effects = _review_effects(before, after)
        review_jobs.write_job_atomic(root, job)
        return {**after, 'saved': True, 'effects': effects, 'recorded_decisions': added,
                'previous_revision': original['revision']}


def import_review_job(root, text):
    job = review_jobs.parse_job(text)
    with review_jobs.job_lock(root, job['job_id']):
        if review_jobs.job_path(root, job['job_id']).exists():
            raise ValueError('review_job_import_would_overwrite')
        packet = _current_job_packet(root, job)
        if dependency_cycles(job['session']['decisions']):
            raise ValueError('decision_dependency_cycle')
        # Validate historical payloads in authored order, with their then-current context.
        check = copy.deepcopy(job['session']); check['decisions'] = []
        for row in job['session']['decisions']:
            append_decision(check, row, packet=packet)
        if check != job['session']:
            raise ValueError('invalid_review_job_decision_history')
        response = _job_response(root, job, packet)
        recorded_scopes = set()
        for event in job['management_events']:
            # Historical management may reference a now-retracted context; its source
            # evidence must still be valid against the recorded attachment snapshot.
            key = review_jobs.management_key(event)
            if event['action'] == 'unmanage':
                if key not in recorded_scopes:
                    raise ValueError('unmanage_requires_recorded_scope')
                continue
            contexts = [{**r['payload'], 'decision_id': r['decision_id']} for r in job['session']['decisions']
                        if r['action'] == 'attach_context' and r['decision_id'] in event.get('depends_on', [])]
            validate_context_dependencies(packet, derive_packet(packet, contexts),
                {'targets': [event['target']], 'depends_on': event.get('depends_on', [])}, contexts)
            recorded_scopes.add(key)
        review_jobs.write_job_atomic(root, job)
        return response


K2A_RESOLVING_ACTIONS = frozenset(('attach_context', 'bind_value', 'declare_parameter'))
SYSTEM_DIAGNOSTIC_KINDS = frozenset(('invalid_graph_structure',))
DECISION_ISSUE_KINDS = frozenset(('stale_decision', 'decision_conflict', 'invalid_review_binding'))
FUTURE_SEMANTIC_KINDS = frozenset(('quantity_semantics', 'no_legal_candidate',
                                   'ontology_extension_required', 'uncovered_source'))


def classify_review_item(question, form):
    """Classify a queue item for K2-A presentation without changing its compiler meaning."""
    kind = question.get('kind')
    if kind in SYSTEM_DIAGNOSTIC_KINDS:
        return {'category': 'system_diagnostic', 'resolving_actions': []}
    if kind in DECISION_ISSUE_KINDS:
        return {'category': 'decision_issue', 'resolving_actions': []}
    if kind in FUTURE_SEMANTIC_KINDS:
        return {'category': 'future_semantic_question', 'resolving_actions': []}
    resolving = sorted(set(question.get('suggested_actions', []))
                       & set(form.get('actions', [])) & K2A_RESOLVING_ACTIONS)
    return {'category': 'scholar_actionable' if resolving else 'future_semantic_question',
            'resolving_actions': resolving}


def _review_forms(packet, compilation):
    """Available actions come from current compiler products, never a resource catalogue."""
    forms = []
    graph = compilation['graph']
    questions = list(compilation['review_queue']['items'])
    for binding in graph['program'].get('linked', {}).get('imports', []):
        if binding.get('selected_definition_id'):
            definition = next(d for d in graph['program']['definitions'] if d['id'] == binding['consumer_definition_id'])
            questions.append({'kind': 'source_binding_review', 'reason': '主动复核已有输入来源（不是新增缺口）',
                'source_spans': definition['source_spans'], 'suggested_actions': ['bind_value'],
                'optional_recheck': True, 'details': binding})
    for question in questions:
        anchors = []
        for span in question.get('source_anchors') or question.get('source_spans', []):
            try:
                candidate = anchor_for(packet, span['doc_id'], span['start'], span['end'], span.get('reading_id'))
                if candidate['quote'] != span.get('quote'):
                    continue
                anchors.append(candidate)
            except (ValueError, KeyError):
                pass
        actions = ['attach_context', 'defer'] if anchors else []
        details = question.get('details', {})
        consumer = details.get('definition_id') or details.get('consumer_definition_id')
        formal = details.get('formal')
        definitions = graph['program']['definitions']
        consumer_anchor = _review_definition_anchor(packet, definitions, consumer)
        producers = []
        for definition in definitions:
            evidence = details.get('candidate_evidence')
            candidates = ({c['definition_id'] for c in evidence if c.get('compatible')} if evidence is not None
                          else set(details.get('candidates', [])))
            if definition['id'] not in candidates:
                continue
            producer_anchor = _review_definition_anchor(packet, definitions, definition['id'])
            if producer_anchor and definition['id'] != consumer:
                for port in dict.fromkeys([*definition.get('return_ports', {}), *definition.get('defined_values', {})]):
                    producers.append({'anchor': producer_anchor, 'output_port': port,
                        'label': f"{producer_anchor['doc_id']} · {definition['kind']} · {producer_anchor['quote']} → {port}"})
        produced_names = {name for definition in definitions for name in definition.get('defined_values', {})}
        required_formals = {name for definition in definitions for name in definition.get('formal_inputs', {})}
        if formal and consumer and formal not in produced_names and formal in required_formals:
            actions.append('declare_parameter')
        if consumer_anchor and producers and formal:
            actions.append('bind_value')
        item = {'question': question, 'anchors': anchors, 'actions': actions,
                'consumer_definition_id': consumer, 'formal': formal,
                'consumer_anchor': consumer_anchor, 'producers': producers,
                'fields': {'reason': 'required', 'evidence': 'source_anchor'},
                'unavailable': [a for a in question.get('suggested_actions', []) if a not in actions]}
        item.update(classify_review_item(question, item))
        item['id'] = 'question:' + digest([question['kind'], question.get('reason'), anchors, consumer, formal])[:20]
        if not any(f['id'] == item['id'] for f in forms):
            forms.append(item)
    return forms


def _review_definition_anchor(packet, definitions, ident):
    definition = next((d for d in definitions if d['id'] == ident), None)
    if definition is None:
        return None
    for span in definition.get('source_spans', []):
        if sum(d['kind'] == definition['kind'] and any(overlaps(s, span) for s in d['source_spans'])
               for d in definitions) == 1:
            return {**anchor_for(packet, span['doc_id'], span['start'], span['end'], span.get('reading_id')),
                    'definition_kind': definition['kind']}
    return None


def review_context_document(root, source_id, unit_id):
    """Explicit material selection through the existing Context A adapter."""
    return build_source_packet_from_units(root, source_id, [unit_id])['primary_documents'][0]


def review_decision(response, action, target, payload, actor, reason, depends_on=()):
    """Build the existing decision contract; attachment prerequisites are visible to the caller."""
    if not reason.strip() or not actor.get('id', '').strip():
        raise ValueError('actor_and_reason_required')
    row = {'decision_id': 'decision:' + uuid4().hex, 'actor': actor, 'created_at': _now(),
           'branch_id': response['branch_id'], 'action': action, 'targets': [target],
           'payload': payload, 'evidence_refs': [target], 'reason': reason, 'depends_on': list(depends_on)}
    base_docs = {d['doc_id'] for group in ('primary_documents', 'context_documents') for d in response['packet'].get(group, [])}
    contexts = response['compilation']['replay']['effective']['contexts']
    for anchor in decision_anchors(row):
        if anchor['doc_id'] not in base_docs:
            provider = next((c['decision_id'] for c in contexts if c['document']['doc_id'] == anchor['doc_id']), None)
            if provider and provider not in row['depends_on']:
                row['depends_on'].append(provider)
    return row


def _review_effects(before, after):
    def changed(left, right):
        a = {digest(v): v for v in left}; b = {digest(v): v for v in right}
        return {'added': [b[k] for k in b.keys() - a.keys()], 'removed': [a[k] for k in a.keys() - b.keys()]}
    def structure(response):
        graph = response['graph']; program = graph.get('program', {}); syntax = graph.get('syntax', {})
        # Preserve native order, operand roles and invocation identity. Only
        # generated IDs are renamed; lists are deliberately never sorted.
        families = {'event': graph.get('events', []), 'value': graph.get('value_instances', []),
                    'definition': program.get('definitions', []), 'call': program.get('calls', []),
                    'syntax': syntax.get('nodes', [])}
        identities = {r['id']: f'{kind}:{i}' for kind, rows in families.items() for i, r in enumerate(rows) if 'id' in r}
        for i, row in enumerate(graph.get('construction_candidates', [])):
            if row.get('node_id') not in identities:
                identities[row['node_id']] = f'construction:{i}'
        evidence_fields = {'adjudication_decision_refs', 'decision_id', 'decision_origin', 'evidence_basis',
                           'evidence', 'evidence_refs', 'reason', 'selection_reason', 'diagnostics'}
        literal_fields = {'quote', 'text', 'surface', 'labels', 'source_label', 'formal', 'name', 'goal_surface'}
        def normalized(value, field=None):
            if field in literal_fields:
                return value
            if isinstance(value, dict):
                return {identities.get(k, k): normalized(v, k) for k, v in value.items() if k not in evidence_fields}
            if isinstance(value, list):
                return [normalized(v, field) for v in value]
            return identities.get(value, value) if isinstance(value, str) else value
        return normalized({'events': families['event'], 'values': families['value'],
            'definitions': families['definition'], 'calls': families['call'],
            'syntax': {'nodes': families['syntax'], 'roots': syntax.get('roots', [])},
            'linked': program.get('linked', {})})
    def docs(r):
        return [{'doc_id': d['doc_id'], 'reading_id': d.get('reading_id'), 'text': d['text']}
                for group in ('primary_documents', 'context_documents') for d in r['effective_packet'].get(group, [])]
    same = structure(before) == structure(after)
    bindings = changed(list(before['compilation']['replay']['effective']['bindings'].values()),
                       list(after['compilation']['replay']['effective']['bindings'].values()))
    def grammar(r):
        return [{'kind': c['kind'], 'source': c['source_spans'], 'slots': c['slots']}
                for c in r['graph'].get('construction_candidates', [])]
    def quantities(r):
        return [{'source': v.get('source_spans', []), 'labels': v.get('labels', []),
                 **{k: v[k] for k in ('unit', 'quantity_kind', 'representation', 'coordinate_kind',
                     'index_base', 'reference_origin', 'counting_boundary', 'step_unit') if k in v}}
                for v in r['graph'].get('value_instances', [])]
    grammar_changes = changed(grammar(before), grammar(after))
    quantity_changes = changed(quantities(before), quantities(after))
    message_en = ('Saved. The reviewed model changed.' if not same
                  else 'Saved. No graph structure changed; interpretation evidence was updated.')
    if any(c['kind'] == 'multiply' for c in grammar_changes['added']):
        message_en = 'Saved. This expression is now parsed as multiplication with two operands. Quantity meanings and sources remain separate judgments.'
    elapsed = sorted({q['unit'] for q in quantity_changes['added']
                      if q.get('coordinate_kind') == 'elapsed' and q.get('unit') in ('year', 'month', 'day')})
    if elapsed:
        message_en += ' Subtracting one now produces elapsed ' + ', '.join(unit + 's' for unit in elapsed) + '.'
    blocked = {e['id'] for e in after['graph']['events'] if e.get('attributes', {}).get('execution_blocked') == 'unresolved_managed_quantity'}
    prior_blocked = {e['id'] for e in before['graph']['events'] if e.get('attributes', {}).get('execution_blocked') == 'unresolved_managed_quantity'}
    if blocked - prior_blocked:
        message_en += ' A managed interpretation is unresolved; dependent execution is blocked.'
    return {'baseline': 'reviewed_before_to_reviewed_after', 'structure_changed': not same,
            'message': '已记录，编译结构未变' if same else '已记录，编译结构已变化',
            'message_en': message_en, 'grammar': grammar_changes, 'quantity_semantics': quantity_changes,
            'documents': changed(docs(before), docs(after)), 'bindings': bindings,
            'questions': changed([{'id': f['id'], 'reason': f['question'].get('reason')} for f in before['review_forms'] if not f['question'].get('optional_recheck')],
                                 [{'id': f['id'], 'reason': f['question'].get('reason')} for f in after['review_forms'] if not f['question'].get('optional_recheck')]),
            'evidence_changed': before['session'] != after['session']}
