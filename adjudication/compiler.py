"""Compile reviewed SourcePacket 3.x input through Program IR and lower_linked."""
import copy
import hashlib
import json

from analysis_parser.context_compiler import compile_documents
from analysis_parser.construction_ir import parse_syntax
from analysis_parser.lexical import tokenize_candidates
from analysis_parser.program_ir import link_entry, static_interface
from analysis_parser.scoped import ScopedParser, lower_linked

from .anchors import anchor_key, overlaps, validate_anchor, validate_semantic_output_address
from .coverage import build_coverage_ledger
from .registry import OPERATION_CONTRACTS, validate_manual_structure, validate_profile, validate_quantity_semantics
from .replay import replay_session
from .review_queue import build_review_queue
from .trace import build_reconstruction_trace
from .validation import validate_effective_decisions, validate_root_parameters


def _anchor_matches(candidate, anchor):
    return any(overlaps(span, anchor) for span in candidate.get('source_spans', []))


def _lowering_slot(packet, reference, known_references):
    kind = reference['ref_kind']
    if kind == 'source_anchor':
        anchor = validate_anchor(packet, reference['anchor'])
        if reference.get('label') not in (None, anchor['quote']):
            raise ValueError('source_anchor_label_must_match_attested_quote')
        return {'kind': 'Term', 'text': reference.get('label', anchor['quote'])}
    if kind == 'literal':
        if not isinstance(reference.get('text'), str):
            raise ValueError('literal_text_required')
        if 'evidence_anchor' not in reference:
            raise ValueError('literal_requires_source_evidence_anchor')
        evidence = validate_anchor(packet, reference['evidence_anchor'])
        if reference['text'] != evidence['quote']:
            raise ValueError('literal_text_must_match_source_evidence')
        result = {'kind': 'Number', 'text': reference['text']}
        if 'value' in reference:
            result['value'] = reference['value']
        return result
    if kind in ('quantity_ref', 'root_input', 'context_declaration'):
        if not isinstance(reference.get('label'), str) or not reference['label']:
            raise ValueError('manual_reference_label_required')
        if reference['label'] not in known_references:
            raise ValueError('manual_reference_not_declared_or_produced')
        return {'kind': 'Term', 'text': reference['label']}
    raise ValueError('unsupported_manual_reference')


def _manual_candidate(packet, structure, specification, sequence, known_references):
    anchors = specification.get('source_anchors') or [specification.get('source_anchor', structure['target'])]
    anchors = [validate_anchor(packet, anchor) for anchor in anchors]
    anchor = anchors[0]
    node_id = 'review-' + hashlib.sha256(json.dumps({
        'decision': structure['decision_id'], 'sequence': sequence, 'anchor': anchor,
        'kind': specification['kind'], 'slots': specification.get('slots', {}),
    }, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:20]
    slots = {}
    for name, value in specification.get('slots', {}).items():
        slots[name] = _lowering_slot(packet, value, known_references)
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


def _segment_candidates(doc, decision):
    """Re-tokenize/re-parse only scholar-selected source regions."""
    output = []
    for sequence, anchor in enumerate(decision.get('segments', ())):
        a = validate_anchor({'primary_documents': [doc], 'context_documents': []}, anchor)
        derived = dict(doc, analysis_text=doc['text'][a['start']:a['end']],
                       analysis_to_source=list(range(a['start'], a['end'])))
        syntax = parse_syntax(tokenize_candidates(derived, {}), derived)
        for candidate_index, candidate in enumerate(syntax.candidates()):
            candidate['node_id'] = 'segment-' + hashlib.sha256(
                (anchor_key(a) + ':' + candidate['kind'] + ':' + str(candidate_index)).encode('utf-8')).hexdigest()[:20]
            candidate['analysis_range'] = [span['start'] for span in candidate['source_spans']] + [span['end'] for span in candidate['source_spans']]
            candidate['analysis_range'] = [min(candidate['analysis_range']), max(candidate['analysis_range'])]
            candidate['production_id'] = 'ADJUDICATION_RESEGMENT_' + candidate['production_id']
            candidate['attributes']['resegmentation_decision_id'] = decision['decision_id']
            output.append(candidate)
    return output


def _rebuild_program(parser, effective, packet, invalid_manual=None):
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
    docs = {doc['doc_id']: doc for doc in parser.docs}
    known_references = set(effective.get('parameters', {}))
    known_references.update(name for definition in parser.program.definitions
                            for name in definition.get('defined_values', {}))
    for segmentation in effective.get('segments', []):
        target = segmentation['target']
        document_id = target['doc_id']
        streams[document_id] = [candidate for candidate in streams[document_id]
                                if not _anchor_matches(candidate, target)]
        streams[document_id].extend(_segment_candidates(docs[document_id], segmentation))
    for structure in effective['manual_structures']:
        try:
            validate_manual_structure(structure)
        except ValueError:
            if invalid_manual is not None:
                invalid_manual.append({'kind': 'schema_extension_required', 'structure': structure,
                                       'reason': 'existing_registry_cannot_represent_structure'})
                continue
            raise
        target = structure['target']
        document_id = target['doc_id']
        if document_id not in streams:
            raise ValueError('manual_structure_unknown_document')
        if structure.get('replace_automatic'):
            streams[document_id] = [candidate for candidate in streams[document_id]
                                    if not _anchor_matches(candidate, target)]
        try:
            manual_candidates = [_manual_candidate(packet, structure, specification, sequence, known_references)
                                 for sequence, specification in enumerate(structure['candidates'])]
        except ValueError as error:
            if invalid_manual is not None:
                invalid_manual.append({'kind': 'invalid_human_decision', 'structure': structure, 'reason': str(error)})
                continue
            raise
        streams[document_id].extend(manual_candidates)
        for candidate in manual_candidates:
            if candidate['kind'] in ('name', 'remainder_name'):
                known_references.add(candidate['slots']['label']['text'])
        streams[document_id].sort(key=lambda row: (row['analysis_range'][0], row['analysis_range'][1], row['node_id']))
    for document_id in streams:
        streams[document_id].sort(key=lambda row: (row['analysis_range'][0], row['analysis_range'][1], row['node_id']))
    rebuilt = compile_documents([], {})
    rebuilt.syntaxes = streams
    rebuilt.syntax_results = dict(parser.program.syntax_results)
    rebuilt.diagnostics = list(parser.program.diagnostics)
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
        consumer = _definition_for_anchor(program, payload['consumer_definition_anchor']) if payload.get('consumer_definition_anchor') else None
        producer = _definition_for_anchor(program, payload['producer_definition_anchor']) if payload.get('producer_definition_anchor') else None
        if not consumer or not producer:
            raise ValueError('binding_requires_stable_definition_anchor')
        constraints[(consumer, payload.get('formal') or payload.get('input_slot'))] = {
            'producer_definition_id': producer, 'output_port': payload.get('output_port', 'result'),
            'decision_id': payload['decision_id'],
        }
    return constraints


def _metadata_for_semantic_address(packet, program, payload):
    address = validate_semantic_output_address(packet, payload['semantic_output'])
    definition_id = _definition_for_anchor(program, address['definition_anchor'])
    candidates = [candidate for stream in program.syntaxes.values() for candidate in stream
                  if candidate.get('definition_id') == definition_id
                  and candidate['kind'] == address['construction_role']
                  and any(overlaps(span, address['construction_anchor']) for span in candidate['source_spans'])]
    if len(candidates) != 1:
        raise ValueError('ambiguous_semantic_output_address')
    contract = OPERATION_CONTRACTS.get(candidates[0]['kind'])
    if not contract or address['output_port'] not in contract['outputs']:
        raise ValueError('semantic_output_port_not_supported')
    metadata = {key: value for key, value in payload.items()
                if key in ('unit', 'scale', 'role', 'quantity_kind', 'representation')}
    metadata['resolution_status'] = 'unknown' if payload['unit'] in ('unknown', 'opaque', 'product') else 'resolved'
    metadata['decision_id'] = payload['decision_id']
    metadata['evidence_basis'] = payload.get('evidence_basis', 'scholarship')
    metadata['decision_origin'] = 'human_selection' if payload.get('selection', True) else 'human_construction'
    return (candidates[0]['node_id'], address['output_port'], address['semantic_role']), metadata


def _without_invalid_decisions(effective, invalid_ids):
    """Keep compiling the known region while excluding invalid review inputs."""
    usable = copy.deepcopy(effective)
    for name in ('candidate_selection_metadata', 'scopes', 'bindings', 'quantity_semantics', 'parameters'):
        usable[name] = {key: value for key, value in usable.get(name, {}).items()
                        if value.get('decision_id') not in invalid_ids}
    usable['selected_candidates'] = {
        key: value for key, value in usable.get('selected_candidates', {}).items()
        if key in usable['candidate_selection_metadata']}
    for name in ('segments', 'contexts', 'manual_structures', 'noncomputational', 'deferred', 'approved_scopes'):
        usable[name] = [value for value in usable.get(name, []) if value.get('decision_id') not in invalid_ids]
    return usable


def compile_reviewed(packet, session, branch_id='main'):
    """Return a reviewed compilation without mutating packet, session, or graph post hoc."""
    replay = replay_session(session, packet, branch_id)
    if replay['status'] != 'ok':
        return {'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0', 'replay': replay,
                'graph': None, 'coverage_ledger': None, 'trace': None,
                'review_queue': {'schema': 'ReviewQueue', 'schema_version': '1.0', 'items': []}}
    decision_issues = validate_effective_decisions(replay['effective'])
    fatal_issues = [row for row in decision_issues if row['kind'] != 'schema_extension_required']
    effective = _without_invalid_decisions(replay['effective'], {row['decision_id'] for row in fatal_issues})
    prepared = _prepare_packet(packet, effective)
    parser = ScopedParser(prepared)
    invalid_manual = []
    program = _rebuild_program(parser, effective, prepared, invalid_manual)
    root_issues = validate_root_parameters(program, effective)
    if root_issues:
        fatal_issues.extend(root_issues)
        invalid_ids = {row['decision_id'] for row in root_issues}
        effective = _without_invalid_decisions(effective, invalid_ids)
    metadata = {}
    for payload in effective['quantity_semantics'].values():
        validate_quantity_semantics(payload)
        key, value = _metadata_for_semantic_address(prepared, program, payload)
        metadata[key] = value
    parser.review_output_metadata = metadata
    program.binding_constraints = _binding_constraints(program, effective)
    allowed = {name: {'unit': payload.get('unit', 'unknown'), 'decision_id': payload['decision_id']}
               for name, payload in effective['parameters'].items()
               if payload.get('root_input', True)}
    entries = [definition['id'] for definition in program.definitions
               if definition['kind'] == 'ProcedureDef' and definition['source_role'] == 'primary' and not definition.get('parent')]
    graph = lower_linked(link_entry(program, entries, allowed), parser)
    holes = [{'kind': 'ExtensionRequired', 'decision_id': row['structure']['decision_id'],
              'source_anchors': [row['structure']['target']], 'reason': row['reason']}
             for row in invalid_manual if row['kind'] == 'schema_extension_required']
    fatal_issues.extend({'kind': row['kind'], 'decision_id': row['structure']['decision_id'], 'reason': row['reason']}
                        for row in invalid_manual if row['kind'] != 'schema_extension_required')
    graph['unresolved'].extend({'cause': 'schema_extension_required', 'source_spans': hole['source_anchors'],
                                'hole': hole} for hole in holes)
    decision_sources = {row['decision_id']: row['targets'] for row in session.get('decisions', [])}
    graph['unresolved'].extend({'cause': 'invalid_human_decision',
                                'source_spans': decision_sources.get(issue['decision_id'], []), 'issue': issue}
                               for issue in fatal_issues)
    graph['adjudication'] = {'session_id': session['session_id'], 'branch_id': branch_id,
                             'effective_decisions': replay['normalized']['effective'], 'holes': holes}
    ledger = build_coverage_ledger(prepared, graph, replay['effective'], replay)
    trace = build_reconstruction_trace(graph)
    queue = build_review_queue(graph, replay, uncovered=ledger['unresolved_required_spans'])
    queue['items'].extend({'kind': 'invalid_human_decision', 'severity': 'blocking',
                           'source_spans': decision_sources.get(issue['decision_id'], []),
                           'source_anchors': decision_sources.get(issue['decision_id'], []),
                           'reason': issue['kind'], 'affected_outputs': [], 'details': issue,
                           'suggested_actions': ['retract']} for issue in fatal_issues)
    return {'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0', 'session_id': session['session_id'],
            'branch_id': branch_id, 'replay': replay, 'graph': graph,
            'coverage_ledger': ledger, 'trace': trace, 'review_queue': queue}
