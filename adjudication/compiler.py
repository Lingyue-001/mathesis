"""Compile reviewed SourcePacket 3.x input through Program IR and lower_linked."""
import copy
import hashlib
import json

from analysis_parser.context_compiler import build_documents_from_candidates
from analysis_parser.construction_ir import parse_syntax
from analysis_parser.inputs import documents
from analysis_parser.lexical import tokenize_candidates
from analysis_parser.program_ir import link_entry
from analysis_parser.scoped import ScopedParser, lower_linked
from analysis_parser.syntax_ir import syntax_from_candidates

from .anchors import anchor_key, anchor_location, overlaps, validate_anchor
from .coverage import build_coverage_ledger
from .registry import validate_manual_structure, validate_profile, validate_quantity_semantics
from .replay import replay_session
from .review_queue import build_review_queue
from .trace import build_reconstruction_trace
from .validation import validate_effective_decisions, validate_root_parameters


def _anchor_matches(candidate, anchor):
    return any(overlaps(span, anchor) for span in candidate.get('source_spans', []))


def _lowering_slot(packet, reference, known_references):
    def exact_grounding(anchor):
        document = next((doc for doc in documents(packet) if doc['doc_id'] == anchor['doc_id']), None)
        positions = ([] if document is None else [index for index, source_index
                     in enumerate(document.get('analysis_to_source', ()))
                     if anchor['start'] <= source_index < anchor['end']])
        if not positions:
            return {'grounding_diagnostic': 'source_anchor_has_no_exact_analysis_grounding'}
        return {'source_spans': [anchor], 'analysis_range': [min(positions), max(positions) + 1]}

    kind = reference['ref_kind']
    if kind == 'source_anchor':
        anchor = validate_anchor(packet, reference['anchor'])
        if reference.get('label') not in (None, anchor['quote']):
            raise ValueError('source_anchor_label_must_match_attested_quote')
        return {'kind': 'Term', 'text': reference.get('label', anchor['quote']), **exact_grounding(anchor)}
    if kind == 'literal':
        if not isinstance(reference.get('text'), str):
            raise ValueError('literal_text_required')
        if 'evidence_anchor' not in reference:
            raise ValueError('literal_requires_source_evidence_anchor')
        evidence = validate_anchor(packet, reference['evidence_anchor'])
        if reference['text'] != evidence['quote']:
            raise ValueError('literal_text_must_match_source_evidence')
        result = {'kind': 'Number', 'text': reference['text'], **exact_grounding(evidence)}
        if 'value' in reference:
            result['value'] = reference['value']
        return result
    if kind in ('quantity_ref', 'root_input', 'context_declaration'):
        if not isinstance(reference.get('label'), str) or not reference['label']:
            raise ValueError('manual_reference_label_required')
        if reference['label'] not in known_references:
            raise ValueError('manual_reference_not_declared_or_produced')
        return {'kind': 'Term', 'text': reference['label'],
                'grounding_diagnostic': 'abstract_reference_has_no_local_source_grounding'}
    raise ValueError('unsupported_manual_reference')


def _manual_candidate(packet, structure, specification, sequence, known_references):
    anchors = specification.get('source_anchors') or [specification.get('source_anchor', structure['target'])]
    anchors = [validate_anchor(packet, anchor) for anchor in anchors]
    anchor = anchors[0]
    node_id = 'review-' + hashlib.sha256(json.dumps({
        'sequence': sequence, 'anchor': anchor,
        'kind': specification['kind'], 'slots': specification.get('slots', {}),
    }, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:20]
    slots = {}
    for name, value in specification.get('slots', {}).items():
        slots[name] = _lowering_slot(packet, value, known_references)
    return {'kind': specification['kind'], 'public_kind': None, 'slots': slots, 'source_spans': anchors,
            'analysis_range': [min(row['start'] for row in anchors), max(row['end'] for row in anchors)], 'text': ''.join(row['quote'] for row in anchors),
            'node_id': node_id, 'production_id': 'ADJUDICATION_MANUAL_V1',
            'attributes': {'decision_id': structure['decision_id'], 'authored_structure': True,
                           'authored_sequence': sequence},
            'status': 'reviewed', 'selection_reason': 'scholar assembled known typed structure'}


def _prepare_packet(packet, effective):
    from .effective_packet import derive_packet
    prepared = derive_packet(packet, effective['contexts'])
    selected = list(prepared.get('selected_profiles', []))
    for profile in effective['profiles']:
        validate_profile(profile)
        if profile not in selected:
            selected.append(profile)
    if selected:
        prepared['selected_profiles'] = selected
    # Context attachment is deliberately limited to a complete document object;
    # it is parsed by the ordinary context compiler and never inserted as a value.
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


def _candidate_sort_key(candidate):
    return (candidate['analysis_range'][0], candidate['analysis_range'][1],
            candidate.get('attributes', {}).get('authored_sequence', float('inf')), candidate['node_id'])


def _matches_candidate_target(candidate, target):
    return any(anchor_location(span) == anchor_location(target) for span in candidate.get('source_spans', []))


class _InvalidScope(ValueError):
    def __init__(self, decision_ids, reason):
        super().__init__(reason)
        self.decision_ids = decision_ids


def _rebuild_program(parser, effective, packet, invalid_manual=None):
    streams = {doc_id: [copy.deepcopy(candidate) for candidate in candidates]
               for doc_id, candidates in parser.all_candidates.items()}
    rejected = effective['rejected_candidates']
    selections = effective['candidate_selection_metadata']
    valid_selection_ids = {}
    for token, metadata in selections.items():
        candidate_ids = {candidate['node_id'] for candidates in streams.values() for candidate in candidates
                         if _matches_candidate_target(candidate, metadata['target'])}
        selected_id = effective['selected_candidates'][token]
        if selected_id in candidate_ids:
            valid_selection_ids[token] = selected_id
        elif invalid_manual is not None:
            invalid_manual.append({'kind': 'invalid_candidate_selection', 'decision_id': metadata['decision_id'],
                                   'target': metadata['target'], 'reason': 'candidate_not_in_current_snapshot'})
    for doc_id, candidates in streams.items():
        retained = []
        for candidate in candidates:
            token = next((key for key, metadata in selections.items()
                          if _matches_candidate_target(candidate, metadata['target'])), None)
            if candidate['node_id'] in rejected:
                continue
            if token in valid_selection_ids and candidate['node_id'] != valid_selection_ids[token]:
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
                invalid_manual.append({'kind': 'schema_extension_required', 'decision_id': structure['decision_id'],
                                       'target': structure['target'], 'reason': 'existing_registry_cannot_represent_structure'})
                continue
            raise
        target = structure['target']
        document_id = target['doc_id']
        if document_id not in streams:
            raise ValueError('manual_structure_unknown_document')
        try:
            manual_candidates = [_manual_candidate(packet, structure, specification, sequence, known_references)
                                 for sequence, specification in enumerate(structure['candidates'])]
        except ValueError as error:
            if invalid_manual is not None:
                invalid_manual.append({'kind': 'invalid_human_decision', 'decision_id': structure['decision_id'],
                                       'target': target, 'reason': str(error)})
                continue
            raise
        if structure.get('replace_automatic'):
            streams[document_id] = [candidate for candidate in streams[document_id]
                                     if not _anchor_matches(candidate, target)]
        streams[document_id].extend(manual_candidates)
        for candidate in manual_candidates:
            if candidate['kind'] in ('name', 'remainder_name'):
                known_references.add(candidate['slots']['label']['text'])
        streams[document_id].sort(key=_candidate_sort_key)
    for document_id in streams:
        streams[document_id].sort(key=_candidate_sort_key)
    # Ownership is applied to the source marker before frame generation, so an
    # independent 求 actually starts a new definition rather than relabelling a
    # completed graph. Ordinary automatic compilation never supplies this flag.
    for payload in effective.get('scopes', {}).values():
        if payload.get('procedure_role') != 'independent':
            continue
        target = payload['definition_anchor']
        markers = [candidate for candidate in streams.get(target['doc_id'], [])
                   if candidate['kind'] in ('task_marker', 'query_marker')
                   and _anchor_matches(candidate, target)]
        if len(markers) != 1:
            raise _InvalidScope([payload['decision_id']], 'procedure_choice_requires_unique_marker')
        markers[0].setdefault('attributes', {})['reviewed_procedure_role'] = 'independent'
    changed_documents = {row['target']['doc_id'] for row in effective.get('segments', [])}
    changed_documents.update(row['target']['doc_id'] for row in effective.get('manual_structures', []))
    changed_documents.update(row['target']['doc_id'] for row in effective.get('term_boundaries', []))
    changed_documents.update(row['target']['doc_id'] for row in effective.get('term_interpretations', []))
    syntax_results = {
        doc_id: syntax_from_candidates(candidates) if doc_id in changed_documents
        else copy.deepcopy(parser.program.syntax_results[doc_id])
        for doc_id, candidates in streams.items()
    }
    rebuilt = build_documents_from_candidates(
        parser.docs, streams, syntax_results, {},
        context_tables=packet.get('context_tables', []),
        profile={'tradition': parser.env.scope.get('tradition'), 'selected_profiles': parser.selected},
    )
    # Scope decisions modify Program IR frames before linking.  They use source
    # anchors, never saved runtime graph ids.
    for payload in effective.get('scopes', {}).values():
        try:
            target = payload.get('definition_anchor')
            if not target:
                continue
            definition_id = _definition_for_anchor(rebuilt, target)
            definition = next(row for row in rebuilt.definitions if row['id'] == definition_id)
            parent_anchor = payload.get('parent_definition_anchor')
            if parent_anchor:
                parent = _definition_for_anchor(rebuilt, parent_anchor, owner=True)
                if parent == definition_id:
                    raise ValueError('scope_parent_cycle')
                definition['parent'] = parent
                if payload.get('procedure_role') == 'followup':
                    definition['kind'] = 'QueryDef'
                    for stream in streams.values():
                        for candidate in stream:
                            if candidate.get('definition_id') == definition_id:
                                candidate['procedure_id'] = parent
            base_anchor = payload.get('query_base_anchor')
            if base_anchor:
                base = _definition_for_anchor(rebuilt, base_anchor, owner=True)
                if payload.get('procedure_role') == 'followup':
                    if base != definition.get('parent'):
                        raise ValueError('followup_base_must_match_parent')
                    initial = next((d for d in rebuilt.definitions
                                    if d.get('parent') == base and d.get('is_initial')), None)
                    definition['reviewed_base_definition_id'] = initial['id'] if initial else base
                definition['base_ref'] = base + ':base'
        except ValueError as error:
            raise _InvalidScope([payload['decision_id']], str(error)) from error
    parents = {definition['id']: definition.get('parent') for definition in rebuilt.definitions}
    for definition_id in parents:
        seen = set()
        cursor = definition_id
        while cursor:
            if cursor in seen:
                raise _InvalidScope([p['decision_id'] for p in effective['scopes'].values()], 'scope_parent_cycle')
            seen.add(cursor)
            cursor = parents.get(cursor)
    for attribute in ('aliases', 'parameter_uses', 'initial_frame', 'interval_parameters', 'preferred_frame_inputs'):
        setattr(rebuilt, attribute, copy.deepcopy(getattr(parser.program, attribute, {} if attribute == 'aliases' else set())))
    parser.program = rebuilt
    parser.context_ir = rebuilt.context_ir
    parser.all_candidates = streams
    from analysis_parser.control_ir import resolve_control
    stops = [profile['stop'] for profile in parser.profile.values() if 'stop' in profile]
    parser.loop_controls = {doc_id: resolve_control(candidates, {'stop': stops[0] if len(stops) == 1 else None}, {})
                            for doc_id, candidates in streams.items()}
    parser.report['construction_candidates'] = [candidate for stream in streams.values() for candidate in stream]
    parser.report['program'] = rebuilt.to_dict()
    parser.report['context'] = rebuilt.context_ir
    parser.report['method_library'] = rebuilt.context_ir['method_library']
    parser.report['syntax'] = {key: [item for syntax in rebuilt.syntax_results.values() for item in getattr(syntax, key)]
                               for key in ('nodes', 'roots', 'diagnostics', 'token_coverage')}
    return rebuilt


def _definition_for_anchor(program, anchor, *, owner=False):
    matches = [definition for definition in program.definitions
               if any(overlaps(span, anchor) for span in definition.get('source_spans', []))]
    if owner:
        matches = [d for d in matches if d['kind'] == 'ProcedureDef']
    if anchor.get('definition_kind'):
        matches = [d for d in matches if d['kind'] == anchor['definition_kind']]
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
        port = payload.get('output_port', 'result')
        definition = next(d for d in program.definitions if d['id'] == producer)
        # The automatic linker can demand an intermediate source-defined value.
        # Give an explicit reviewed choice the same existing value/port, without
        # creating another operation or changing the automatic interface.
        if port not in definition.get('return_ports', {}) and port in definition.get('defined_values', {}):
            definition.setdefault('return_ports', {})[port] = copy.deepcopy(definition['defined_values'][port])
        constraints[(consumer, payload.get('formal') or payload.get('input_slot'))] = {
            'producer_definition_id': producer, 'output_port': port,
            'decision_id': payload['decision_id'],
        }
    return constraints


def _without_invalid_decisions(effective, invalid_ids):
    """Keep compiling the known region while excluding invalid review inputs."""
    usable = copy.deepcopy(effective)
    for name in ('candidate_selection_metadata', 'scopes', 'bindings', 'quantity_semantics', 'parameters'):
        usable[name] = {key: value for key, value in usable.get(name, {}).items()
                        if value.get('decision_id') not in invalid_ids}
    usable['selected_candidates'] = {
        key: value for key, value in usable.get('selected_candidates', {}).items()
        if key in usable['candidate_selection_metadata']}
    for name in ('segments', 'contexts', 'manual_structures', 'noncomputational', 'deferred', 'approved_scopes', 'lexical_roles'):
        usable[name] = [value for value in usable.get(name, []) if value.get('decision_id') not in invalid_ids]
    return usable


def _apply_local_lexical_roles(parser, effective):
    """Attach reviewed grammar evidence to matching syntax candidates only.

    This cannot lower a new operation or make source text noncomputational.
    It records a scoped compiler input for researcher inspection and future
    construction review while keeping lexical, construction, and quantity
    semantics distinct.
    """
    roles = effective.get('lexical_roles', [])
    if not roles:
        return
    for candidates in parser.all_candidates.values():
        for candidate in candidates:
            matching = [role for role in roles if _anchor_matches(candidate, role['target'])]
            if matching:
                candidate.setdefault('attributes', {})['reviewed_lexical_roles'] = copy.deepcopy(matching)


def compile_reviewed(packet, session, branch_id='main', *, management=()):
    """Return a reviewed compilation without mutating packet, session, or graph post hoc."""
    invalid = {}
    for _ in range(len(session.get('decisions', [])) + 1):
        result, discovered = _compile_reviewed_pass(packet, session, branch_id, invalid, management)
        fresh = {i['decision_id']: i for i in discovered if i['decision_id'] not in invalid}
        if not fresh:
            return result
        invalid.update(fresh)
    raise RuntimeError('reviewed_invalidation_did_not_converge')


def _compile_reviewed_pass(packet, session, branch_id, invalid, management=(), relation_hooks=None):
    replay = replay_session(session, packet, branch_id, invalid_decisions=invalid)
    if replay['status'] != 'ok':
        return {'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0', 'replay': replay,
                'graph': None, 'coverage_ledger': None, 'trace': None,
                'review_queue': {'schema': 'ReviewQueue', 'schema_version': '1.0', 'items': [
                    {'id': 'session-revalidation', 'kind': 'stale_session', 'severity': 'blocking',
                     'reason': replay['status'], 'source_spans': [], 'source_anchors': [],
                     'affected_outputs': [], 'candidate_options': [], 'suggested_actions': [],
                     'details': {'requires_revalidation': True}}]}}, []
    decision_issues = validate_effective_decisions(replay['effective'])
    fatal_issues = [row for row in decision_issues if row['kind'] != 'schema_extension_required']
    if fatal_issues:
        return None, fatal_issues
    effective = _without_invalid_decisions(replay['effective'], {row['decision_id'] for row in fatal_issues})
    prepared = _prepare_packet(packet, effective)
    parser = ScopedParser(prepared)
    from .term_claims import prepare_term_parser, revalidate_term_interpretation, apply_term_interpretations
    try:
        prepare_term_parser(parser, effective.get('term_boundaries', []))
    except ValueError as error:
        return None, [{'kind': 'invalid_term_boundary', 'decision_id': row['decision_id'], 'reason': str(error)}
                      for row in effective.get('term_boundaries', [])]
    term_issues = []
    for row in effective.get('term_interpretations', []):
        result = revalidate_term_interpretation(row['claim'], prepared,
            term_boundaries=effective.get('term_boundaries', []))
        if result['status'] != 'valid':
            term_issues.append({'kind': 'invalid_term_interpretation', 'decision_id': row['decision_id'], 'reason': result['reason']})
    if term_issues:
        return None, term_issues
    apply_term_interpretations(parser, effective.get('term_interpretations', []))
    invalid_manual = []
    try:
        program = _rebuild_program(parser, effective, prepared, invalid_manual)
    except _InvalidScope as error:
        return None, [{'kind': 'invalid_scope', 'decision_id': ident, 'reason': str(error)} for ident in error.decision_ids]
    _apply_local_lexical_roles(parser, effective)
    root_issues = validate_root_parameters(program, effective)
    if root_issues:
        return None, root_issues
    failed_manual = [row for row in invalid_manual if row['kind'] != 'schema_extension_required']
    if failed_manual:
        return None, failed_manual
    parser.review_output_metadata = {}
    parser.review_relation_output_metadata = relation_hooks or []
    parser.review_relation_operation_metadata = relation_hooks or []
    from .quantity_targets import install_quantity_semantics
    quantity_issues = install_quantity_semantics(parser, prepared, program,
        list(effective['quantity_semantics'].values()), management)
    if quantity_issues:
        return None, quantity_issues
    try:
        program.binding_constraints = _binding_constraints(program, effective)
    except ValueError:
        # Identify the particular invalid address instead of dropping all bindings.
        issues = []
        for key, payload in effective['bindings'].items():
            try:
                _binding_constraints(program, {**effective, 'bindings': {key: payload}})
            except ValueError as error:
                issues.append({'kind': 'invalid_review_binding', 'decision_id': payload['decision_id'], 'reason': str(error)})
        return None, issues
    program.managed_bindings = {}
    for row in management:
        address = row.get('semantic_target') or {}
        if not row.get('managed', row.get('action') == 'manage') or row.get('facet') != 'binding' or not address:
            continue
        evidence = {'event_id': row.get('event_id'), 'target': address, 'facet': 'binding'}
        try:
            target = validate_anchor(prepared, row['target'])
            formal = address.get('formal')
            consumers = {c['definition_id'] for stream in program.syntaxes.values() for c in stream
                         if any(overlaps(span, target) for span in c['source_spans'])
                         and c.get('definition_id')}
            consumers = {d['id'] for d in program.definitions if d['id'] in consumers and formal in d['free_variables']}
            if len(consumers) != 1:
                raise ValueError('ambiguous_managed_binding_target')
            consumer = consumers.pop()
            definition = next(d for d in program.definitions if d['id'] == consumer)
            if address.get('kind') != 'binding' or formal not in definition['free_variables']:
                raise ValueError('invalid_managed_binding_target')
            program.managed_bindings[(consumer, formal)] = row
            evidence['status'] = 'resolved' if (consumer, formal) in program.binding_constraints else 'unresolved'
        except (ValueError, KeyError, StopIteration) as error:
            evidence.update(status='needs_revalidation', reason=str(error))
        parser.report.setdefault('managed_scopes', []).append(evidence)
    allowed = {name: {'unit': payload.get('unit', 'unknown'), 'decision_id': payload['decision_id']}
               for name, payload in effective['parameters'].items()
               if payload.get('root_input', True)}
    entries = [definition['id'] for definition in program.definitions
               if definition['kind'] == 'ProcedureDef' and definition['source_role'] == 'primary' and not definition.get('parent')]
    # A separately selected, explicitly reviewed follow-up remains a primary
    # entry even when its source base is supplied as Context.
    primary_ids = {d['id'] for d in program.definitions if d['source_role'] == 'primary'}
    entries.extend(d['id'] for d in program.definitions if d['source_role'] == 'primary'
                   and d['kind'] == 'QueryDef' and d.get('parent') not in primary_ids)
    graph = lower_linked(link_entry(program, entries, allowed), parser)
    if effective.get('reviewed_relations') and relation_hooks is None:
        from .reviewed_relations import resolve_reviewed_relation
        hooks, relation_issues = [], []
        for claim in effective['reviewed_relations']:
            try:
                proof = resolve_reviewed_relation(prepared, graph, claim)
                for hook in proof['output_hooks']:
                    hook['metadata'].update(decision_id=claim['decision_id'],
                        decision_refs=[claim['decision_id']], evidence_basis=claim['evidence_refs'],
                        decision_origin='human_selection')
                hooks.extend(proof['output_hooks'])
                operation = proof['operation_hook']
                operation['metadata'].update(decision_id=claim['decision_id'],
                    decision_refs=[claim['decision_id']], evidence_basis=claim['evidence_refs'],
                    decision_origin='human_selection')
                for metadata in operation['metadata']['ports'].values():
                    metadata.update(decision_id=claim['decision_id'],
                        decision_refs=[claim['decision_id']], evidence_basis=claim['evidence_refs'],
                        decision_origin='human_selection')
                hooks.append(operation)
            except ValueError as error:
                relation_issues.append({'kind': 'invalid_reviewed_relation', 'decision_id': claim['decision_id'], 'reason': str(error)})
        if relation_issues:
            return None, relation_issues
        # Fresh lowering consumes the validated semantic hooks at emission.
        return _compile_reviewed_pass(packet, session, branch_id, invalid, management, hooks)
    invalid_bindings = [d for d in graph['program'].get('linked', {}).get('diagnostics', [])
                        if d.get('kind') == 'invalid_review_binding']
    if invalid_bindings:
        return None, [{'kind': 'invalid_review_binding', 'decision_id': d['constraint']['decision_id'],
                       'reason': 'producer_or_output_port_unavailable'} for d in invalid_bindings]
    fatal_issues.extend(invalid.values())
    holes = [{'kind': 'ExtensionRequired', 'decision_id': row['decision_id'],
              'source_anchors': [row['target']], 'reason': row['reason']}
             for row in invalid_manual if row['kind'] == 'schema_extension_required']
    extension_requests = [{'kind': 'ExtensionRequired', 'decision_id': row['decision_id'],
                           'source_anchors': [row['target']], 'reason': 'schema_extension_required'}
                          for row in effective.get('deferred', []) if row.get('schema_extension_required')]
    holes.extend(extension_requests)
    fatal_issues.extend({'kind': row['kind'], 'decision_id': row['decision_id'], 'reason': row['reason']}
                         for row in invalid_manual if row['kind'] != 'schema_extension_required')
    graph['unresolved'].extend({'cause': 'schema_extension_required', 'source_spans': hole['source_anchors'],
                                'hole': hole} for hole in holes)
    decision_sources = {row['decision_id']: row['targets'] for row in session.get('decisions', [])}
    graph['unresolved'].extend({'cause': 'invalid_human_decision',
                                'source_spans': decision_sources.get(issue['decision_id'], []), 'issue': issue}
                               for issue in fatal_issues)
    graph['adjudication'] = {'session_id': session['session_id'], 'branch_id': branch_id,
                             'management': copy.deepcopy(list(management)),
                             'effective_decisions': replay['normalized']['effective'], 'holes': holes,
                             'extension_requests': extension_requests,
                             'lexical_roles': copy.deepcopy(effective.get('lexical_roles', []))}
    ledger = build_coverage_ledger(prepared, graph, replay['effective'], replay)
    trace = build_reconstruction_trace(graph)
    queue = build_review_queue(graph, replay, uncovered=ledger['unresolved_required_spans'],
                               structural_diagnostics=ledger['structural_diagnostics'])
    queue['items'].extend({'kind': 'invalid_human_decision', 'severity': 'blocking',
                           'source_spans': decision_sources.get(issue['decision_id'], []),
                           'source_anchors': decision_sources.get(issue['decision_id'], []),
                           'reason': issue['kind'], 'affected_outputs': [], 'details': issue,
                           'suggested_actions': ['retract']} for issue in fatal_issues)
    return {'schema': 'ReviewedProcedureBundle', 'schema_version': '1.0', 'session_id': session['session_id'],
            'branch_id': branch_id, 'replay': replay, 'graph': graph,
            'coverage_ledger': ledger, 'trace': trace, 'review_queue': queue}, []
