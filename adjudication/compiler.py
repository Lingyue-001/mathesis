"""Compile reviewed SourcePacket 3.x input through Program IR and lower_linked."""
import copy
import hashlib
import json

from analysis_parser.context_compiler import compile_documents
from analysis_parser.program_ir import link_entry, static_interface
from analysis_parser.scoped import ScopedParser, lower_linked

from .anchors import overlaps, validate_anchor
from .coverage import build_coverage_ledger
from .registry import validate_manual_structure, validate_profile, validate_quantity_semantics
from .replay import replay_session
from .review_queue import build_review_queue
from .trace import build_reconstruction_trace
from .validation import validate_effective_decisions


def _anchor_matches(candidate, anchor):
    return any(overlaps(span, anchor) for span in candidate.get('source_spans', []))


def _manual_candidate(packet, structure, specification, sequence):
    anchors = specification.get('source_anchors') or [specification.get('source_anchor', structure['target'])]
    anchors = [validate_anchor(packet, anchor) for anchor in anchors]
    anchor = anchors[0]
    node_id = 'review-' + hashlib.sha256(json.dumps({
        'decision': structure['decision_id'], 'sequence': sequence, 'anchor': anchor,
        'kind': specification['kind'], 'slots': specification.get('slots', {}),
    }, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:20]
    slots = {}
    for name, value in specification.get('slots', {}).items():
        slots[name] = dict(value) if isinstance(value, dict) else {'kind': 'Term', 'text': value}
    return {'kind': specification['kind'], 'slots': slots, 'source_spans': anchors,
            'analysis_range': [min(row['start'] for row in anchors), max(row['end'] for row in anchors)], 'text': ''.join(row['quote'] for row in anchors),
            'node_id': node_id, 'production_id': 'ADJUDICATION_MANUAL_V1',
            'attributes': {'decision_id': structure['decision_id'], 'authored_structure': True},
            'status': 'reviewed', 'selection_reason': 'scholar assembled known typed structure'}


def _prepare_packet(packet, effective):
    prepared = copy.deepcopy(packet)
    selected = list(prepared.get('selected_profiles', []))
    for profile in effective['profiles']:
        validate_profile(profile)
        if profile not in selected:
            selected.append(profile)
    if selected:
        prepared['selected_profiles'] = selected
    # Context attachment is deliberately limited to a complete document object;
    # it is parsed by the ordinary context compiler and never inserted as a value.
    for attachment in effective['contexts']:
        document = attachment.get('document')
        if not isinstance(document, dict) or not document.get('doc_id') or not document.get('text'):
            raise ValueError('attach_context_requires_complete_document')
        prepared.setdefault('context_documents', []).append(copy.deepcopy(document))
    return prepared


def _rebuild_program(parser, effective, packet):
    streams = {doc_id: [copy.deepcopy(candidate) for candidate in candidates]
               for doc_id, candidates in parser.all_candidates.items()}
    selected = effective['selected_candidates']
    rejected = effective['rejected_candidates']
    for doc_id, candidates in streams.items():
        retained = []
        for candidate in candidates:
            token = ':'.join((candidate['source_spans'][0]['doc_id'],
                              str(candidate['source_spans'][0]['start']), str(candidate['source_spans'][0]['end'])))
            if candidate['node_id'] in rejected:
                continue
            if token in selected and candidate['node_id'] != selected[token]:
                continue
            retained.append(candidate)
        streams[doc_id] = retained
    for structure in effective['manual_structures']:
        validate_manual_structure(structure)
        target = structure['target']
        document_id = target['doc_id']
        if document_id not in streams:
            raise ValueError('manual_structure_unknown_document')
        if structure.get('replace_automatic'):
            streams[document_id] = [candidate for candidate in streams[document_id]
                                    if not _anchor_matches(candidate, target)]
        for sequence, specification in enumerate(structure['candidates']):
            streams[document_id].append(_manual_candidate(packet, structure, specification, sequence))
        streams[document_id].sort(key=lambda row: (row['analysis_range'][0], row['analysis_range'][1], row['node_id']))
    rebuilt = compile_documents([], {})
    rebuilt.syntaxes = streams
    rebuilt.syntax_results = dict(parser.program.syntax_results)
    rebuilt.diagnostics = list(parser.program.diagnostics)
    docs = {doc['doc_id']: doc for doc in parser.docs}
    from analysis_parser.program_ir import compile_frames
    from analysis_parser.scoped import TASKS
    for doc_id, candidates in streams.items():
        compile_frames(docs[doc_id], candidates, rebuilt, TASKS)
    for definition in rebuilt.definitions:
        body = [candidate for stream in streams.values() for candidate in stream
                if candidate.get('definition_id') == definition['id']]
        names, uses = static_interface(body)
        definition['defined_values'] = names
        definition['free_variables'] = uses
        definition['formal_inputs'] = dict(uses)
    for definition in rebuilt.definitions:
        names = definition['defined_values']
        used = set().union(*(set(row['free_variables']) for row in rebuilt.definitions if row['id'] != definition['id']))
        returned = ({next(reversed(names))} if names else set()) | (set(names) & used)
        definition['return_ports'] = {name: dict(ref) for name, ref in names.items() if name in returned}
    # Scope decisions modify Program IR frames before linking.  They use source
    # anchors, never saved runtime graph ids.
    for payload in effective.get('scopes', {}).values():
        target = payload.get('definition_anchor')
        if not target:
            continue
        definition_id = _definition_for_anchor(rebuilt, target)
        definition = next(row for row in rebuilt.definitions if row['id'] == definition_id)
        parent_anchor = payload.get('parent_definition_anchor')
        if parent_anchor:
            parent = _definition_for_anchor(rebuilt, parent_anchor)
            if parent == definition_id:
                raise ValueError('scope_parent_cycle')
            definition['parent'] = parent
        base_anchor = payload.get('query_base_anchor')
        if base_anchor:
            definition['base_ref'] = _definition_for_anchor(rebuilt, base_anchor) + ':base'
    parents = {definition['id']: definition.get('parent') for definition in rebuilt.definitions}
    for definition_id in parents:
        seen = set()
        cursor = definition_id
        while cursor:
            if cursor in seen:
                raise ValueError('scope_parent_cycle')
            seen.add(cursor)
            cursor = parents.get(cursor)
    for attribute in ('aliases', 'parameter_uses', 'initial_frame', 'interval_parameters', 'preferred_frame_inputs'):
        setattr(rebuilt, attribute, copy.deepcopy(getattr(parser.program, attribute, {} if attribute == 'aliases' else set())))
    parser.program = rebuilt
    parser.all_candidates = streams
    parser.report['construction_candidates'] = [candidate for stream in streams.values() for candidate in stream]
    parser.report['program'] = rebuilt.to_dict()
    return rebuilt


def _definition_for_anchor(program, anchor):
    matches = [definition for definition in program.definitions
               if any(overlaps(span, anchor) for span in definition.get('source_spans', []))]
    if len(matches) != 1:
        raise ValueError('ambiguous_definition_anchor')
    return matches[0]['id']


def _binding_constraints(program, effective):
    constraints = {}
    for payload in effective['bindings'].values():
        consumer = payload.get('consumer_definition_id')
        if not consumer and payload.get('consumer_definition_anchor'):
            consumer = _definition_for_anchor(program, payload['consumer_definition_anchor'])
        producer = payload.get('producer_definition_id')
        if not producer and payload.get('producer_definition_anchor'):
            producer = _definition_for_anchor(program, payload['producer_definition_anchor'])
        if not consumer or not producer:
            raise ValueError('binding_requires_stable_definition_anchor')
        constraints[(consumer, payload.get('formal') or payload.get('input_slot'))] = {
            'producer_definition_id': producer, 'output_port': payload.get('output_port', 'result'),
            'decision_id': payload['decision_id'],
        }
    return constraints


def compile_reviewed(packet, session, branch_id='main'):
    """Return a reviewed compilation without mutating packet, session, or graph post hoc."""
    replay = replay_session(session, packet, branch_id)
    if replay['status'] != 'ok':
        return {'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0', 'replay': replay,
                'graph': None, 'coverage_ledger': None, 'trace': None,
                'review_queue': {'schema': 'ReviewQueue', 'schema_version': '1.0', 'items': []}}
    decision_issues = validate_effective_decisions(replay['effective'])
    extension_issues = [row for row in decision_issues if row['kind'] == 'schema_extension_required']
    fatal_issues = [row for row in decision_issues if row['kind'] != 'schema_extension_required']
    if fatal_issues:
        return {'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0', 'session_id': session['session_id'],
                'branch_id': branch_id, 'replay': replay, 'graph': None, 'coverage_ledger': None, 'trace': None,
                'review_queue': {'schema': 'ReviewQueue', 'schema_version': '1.0', 'items': [
                    {'kind': 'invalid_human_decision', 'severity': 'blocking', 'source_spans': [],
                     'details': row, 'suggested_actions': ['retract']} for row in fatal_issues]}}
    if extension_issues:
        return {'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0', 'session_id': session['session_id'],
                'branch_id': branch_id, 'replay': replay, 'graph': None, 'coverage_ledger': None, 'trace': None,
                'review_queue': {'schema': 'ReviewQueue', 'schema_version': '1.0', 'items': [
                    {'kind': 'schema_extension_required', 'severity': 'blocking', 'source_spans': [],
                     'details': row, 'suggested_actions': ['defer']} for row in extension_issues]}}
    prepared = _prepare_packet(packet, replay['effective'])
    parser = ScopedParser(prepared)
    program = _rebuild_program(parser, replay['effective'], prepared)
    metadata = {}
    for payload in replay['effective']['quantity_semantics'].values():
        validate_quantity_semantics(payload)
        syntax_node_id, port = payload.get('syntax_node_id'), payload.get('output_port', 'result')
        metadata[(syntax_node_id, port)] = {key: value for key, value in payload.items()
                                             if key in ('unit', 'scale', 'role', 'quantity_kind', 'representation', 'resolution_status')}
        metadata[(syntax_node_id, port)]['decision_id'] = payload['decision_id']
    parser.review_output_metadata = metadata
    program.binding_constraints = _binding_constraints(program, replay['effective'])
    allowed = {name: {'unit': payload.get('unit', 'unknown'), 'decision_id': payload['decision_id']}
               for name, payload in replay['effective']['parameters'].items()
               if payload.get('root_input', True)}
    entries = [definition['id'] for definition in program.definitions
               if definition['kind'] == 'ProcedureDef' and definition['source_role'] == 'primary' and not definition.get('parent')]
    graph = lower_linked(link_entry(program, entries, allowed), parser)
    graph['adjudication'] = {'session_id': session['session_id'], 'branch_id': branch_id,
                             'effective_decisions': replay['normalized']['effective']}
    ledger = build_coverage_ledger(prepared, graph, replay['effective'])
    trace = build_reconstruction_trace(graph)
    queue = build_review_queue(graph, replay)
    return {'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0', 'session_id': session['session_id'],
            'branch_id': branch_id, 'replay': replay, 'graph': graph,
            'coverage_ledger': ledger, 'trace': trace, 'review_queue': queue}
