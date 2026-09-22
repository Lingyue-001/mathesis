"""Deterministic source-bound questions over current compiler and Kernel evidence."""
from collections import defaultdict

from adjudication.anchors import anchor_for, anchor_key, validate_anchor
from adjudication.decision_contracts import normalize_decision_target
from adjudication.term_claims import adopt_term_candidate, reject_term_candidates
from domain_kernel.engine import suggest_packet_semantics
from source_adapters.dependencies import digest
from analysis_parser.rule_trace import condition, rule


# Authored presentation labels for the existing finite Kernel vocabulary.
CONCEPT_LABELS = {
    'body.sun': 'the sun', 'body.moon': 'the moon', 'time.day': 'days',
    'time.month': 'months', 'time.lunation': 'lunations', 'time.civil_month': 'civil months',
    'time.year': 'years', 'time.civil_year': 'civil years', 'time.solar_cycle': 'a solar cycle',
    'measure.du': 'angular du', 'compute.accumulation': 'accumulation',
    'compute.residual': 'a remainder', 'compute.factor': 'a calculation factor',
    'compute.rate': 'a rate', 'compute.part': 'a fractional part', 'compute.number': 'a number',
    'relation.entry': 'entry into a local frame', 'scope.calendar_cycle': 'a calendrical cycle',
    'scope.zhang': 'the 章 cycle', 'scope.bu': 'the 蔀 cycle', 'scope.ji': 'the 紀 cycle',
    'scope.yuan': 'the 元 cycle', 'frame.origin': 'a reference origin',
    'event.conjunction': 'conjunction', 'event.full_moon': 'full moon',
    'event.solstice': 'winter solstice', 'event.qi': 'a solar term',
    'calendar.intercalation': 'intercalation',
}
CONSTRUCTOR_LABELS = {
    'accumulation': 'Accumulated {quantity}', 'residual_of': 'Remainder associated with {associate}',
    'factor_for': 'Calculation factor associated with {associate}',
    'rate_for': 'Rate associated with {associate}', 'part_of_quantity': 'Fractional part of {associate}',
    'localized_quantity': '{quantity} within {scope}', 'scoped_quantity': '{quantity} in {scope}',
    'number_of': 'Number of {associate}',
}


def expression_label(expression):
    if expression['op'] == 'concept':
        return CONCEPT_LABELS[expression['concept_id']]
    if expression['op'] == 'unknown':
        return 'Uninterpreted source component: ' + expression.get('source_text', '')
    return CONSTRUCTOR_LABELS[expression['op']].format(**{
        key: expression_label(value) for key, value in expression['arguments'].items()})


def _option(label, action, payload, assertions=(), **extra):
    return {'id': 'option:' + digest([action, payload])[:20], 'label': label, 'action': action,
            'payload': payload, 'assertions': list(assertions), 'management_facets': [],
            'depends_on': [], **extra}


def _question(kind, title, anchor, options, evidence=None, *, semantic_key=None,
              display_anchor=None, evidence_anchors=(), decision_target=None, machine_context=None):
    """Keep the reviewed object separate from its source presentation location."""
    display_anchor = display_anchor or anchor
    semantic_key = semantic_key or {'issue_family': kind, 'occurrence': anchor_key(display_anchor)}
    evidence_anchors = _unique_anchors([display_anchor, *evidence_anchors])
    deferred = rule('REVIEW-DEFER-01', 'scholar_question', [], _question,
        result={'action': 'defer', 'result_class': 'available_action'})
    unresolved = [_option('Leave unresolved', 'defer', {'unresolved': 'Interpretation left open'},
                         group='source_resolution')] if deferred['matched'] else []
    return {'id': 'annotation:' + digest([kind, semantic_key])[:20], 'kind': kind, 'title': title,
            'anchor': display_anchor, 'display_anchor': display_anchor,
            'evidence_anchors': evidence_anchors, 'decision_target': decision_target or anchor,
            'semantic_key': semantic_key, 'machine_context': machine_context or {
                'reading': 'Machine has marked this source occurrence for review.',
                'source_status': 'unresolved',
                'why_blocked': 'No reviewed decision has resolved this annotation facet.'},
            'options': [*options, *unresolved],
            'rule_trace': [deferred] if semantic_key['issue_family'] == 'source_supply' else [],
            'evidence': evidence or {}}


def _anchor(packet, span):
    return anchor_for(packet, span['doc_id'], span['start'], span['end'], span.get('reading_id'))


def _unique_anchors(rows):
    unique = {}
    for row in rows:
        unique.setdefault(anchor_key(row), row)
    return list(unique.values())


def _term_anchor_in_use(packet, use_anchor, formal):
    """Prefer the exact formal occurrence, but never invent one outside the recorded use."""
    document = next((d for group in ('primary_documents', 'context_documents')
                     for d in packet.get(group, []) if d['doc_id'] == use_anchor['doc_id']), None)
    if document is None:
        return use_anchor
    starts = [offset for offset in range(use_anchor['start'], use_anchor['end'])
              if document['text'].startswith(formal, offset)]
    return (_anchor(packet, {'doc_id': use_anchor['doc_id'], 'reading_id': use_anchor.get('reading_id'),
                             'start': starts[0], 'end': starts[0] + len(formal)})
            if len(starts) == 1 else use_anchor)


def _source_supply_target(packet, graph, form, branch_id):
    """Normalize only diagnostics that demonstrably address one linked input."""
    details = form['question'].get('details', {})
    formal = form.get('formal') or (details.get('missing_or_conflicting_inputs') or [None])[0]
    imports = graph.get('program', {}).get('linked', {}).get('imports', [])
    constructions = {row.get('node_id'): row for row in graph.get('construction_candidates', [])}
    diagnostic_nodes = {row.get('node_id') for row in constructions.values()
                        if any(span['doc_id'] == anchor['doc_id'] and span['start'] == anchor['start']
                               and span['end'] == anchor['end'] for span in row.get('source_spans', [])
                               for anchor in form.get('anchors', []))}
    matches = [row for row in imports if row.get('formal') == formal
               and (form.get('consumer_definition_id') is None or row.get('consumer_definition_id') == form['consumer_definition_id'])
               and (not diagnostic_nodes or diagnostic_nodes.intersection(row.get('uses', [])))]
    formation = rule('SOURCE-SUPPLY-01', 'scholar_question', [condition('formal exists', bool(formal)),
        condition('canonical consumer count', len({row['consumer_definition_id'] for row in matches}), 1),
        condition('source supply unresolved', bool(matches) and all(not row.get('selected_definition_id') for row in matches))],
        _source_supply_target, result={'issue_family': 'source_supply', 'result_class': 'unresolved'})
    if not formation['matched']:
        return None
    consumer = matches[0]['consumer_definition_id']
    use_nodes = {node for row in matches for node in row.get('uses', [])}
    canonical_spans = [span for node in use_nodes
                       for slot in constructions.get(node, {}).get('slots', {}).values()
                       if slot.get('kind') == 'Term' and slot.get('text') == formal
                       for span in slot.get('source_spans', [])]
    use_anchors = _unique_anchors([_anchor(packet, span) for span in canonical_spans])
    grounding = 'canonical_slot'
    if use_anchors:
        display = use_anchors[0]
    else:
        # Legacy/external streams may lack slot grounding.  This is an explicit
        # presentation fallback, never a replacement canonical occurrence.
        parent_anchors = [_anchor(packet, span) for node in use_nodes
                          for span in constructions.get(node, {}).get('source_spans', [])]
        if not parent_anchors:
            return None
        use_anchors = _unique_anchors(parent_anchors)
        display = _term_anchor_in_use(packet, use_anchors[0], formal)
        grounding = ('fallback_unique_substring' if display != use_anchors[0]
                     else 'missing_exact_slot_grounding')
    roles = sorted({slot for node in use_nodes for slot, value in constructions.get(node, {}).get('slots', {}).items()
                    if value.get('kind') == 'Term' and value.get('text') == formal})
    decision_target = form.get('consumer_anchor') or form['anchors'][0]
    return {'rule_trace': [formation], 'semantic_key': {'branch_id': branch_id, 'issue_family': 'source_supply',
                             'consumer_definition_id': consumer, 'formal': formal},
            'display_anchor': display, 'evidence_anchors': _unique_anchors([*use_anchors, decision_target]),
            'decision_target': decision_target,
            'machine_context': {'reading': f'“{formal}” is an unresolved input in the current procedure.',
                                'roles': roles, 'source_status': 'unresolved',
                                'why_blocked': 'No linked source producer or declared runtime value is present.',
                                'grounding': grounding}}


def _construction_context_target(form, branch_id):
    """A native context/profile requirement is not a source-supply question."""
    question = form['question']
    details = question.get('details', {})
    anchor = form['anchors'][0]
    cause = details.get('cause') or question.get('reason') or question['kind']
    missing = sorted(details.get('missing_or_conflicting_inputs', ()))
    return {'semantic_key': {'branch_id': branch_id, 'issue_family': 'construction_context_requirement',
                             'construction': anchor_key(anchor), 'cause': cause, 'missing_inputs': missing},
            'display_anchor': anchor, 'evidence_anchors': form['anchors'], 'decision_target': anchor,
            'machine_context': {'reading': 'Machine requires contextual material for this construction.',
                                'source_status': 'unresolved', 'native_requirement': question['kind'],
                                'why_blocked': details.get('reason', question.get('reason',
                                    'The current reviewed graph has no resolving context.'))}}


def _offered_action(form, action):
    """Trace the existing native-form presentation gate, including suppressed actions."""
    return rule('SCHOLAR-OPTION-01', 'scholar_option',
        [condition('action in resolving_actions', action in form['resolving_actions'])], _offered_action,
        result={'action': action, 'result_class': 'available_action'},
        subject={'action': action, 'resolving_actions': form['resolving_actions'], 'native_form_id': form['id']})


def _bu_year_ordinal_candidate(bundle, formal):
    """Return the current K evidence that can justify this narrow ordinal option."""
    matches = []
    for candidate in bundle['candidates']:
        expression = candidate['expression']
        arguments = expression.get('arguments', {})
        scope = arguments.get('scope', {})
        quantity = arguments.get('quantity', {})
        if (candidate['span']['quote'] == formal and expression.get('op') == 'localized_quantity'
                and scope == {'op': 'concept', 'concept_id': 'scope.bu'}
                and quantity.get('op') == 'concept'
                and quantity.get('concept_id') in ('time.year', 'time.civil_year')
                and candidate['constraint_status'] == 'compatible'):
            matches.append(candidate)
    return next((row for row in matches
                 if row['expression']['arguments']['quantity']['concept_id'] == 'time.year'),
                matches[0] if matches else None)


def build_questions(packet, compilation, native_forms, branch_id='main'):
    """Every offered assertion has a current consumer; diagnostics stay outside."""
    graph = compilation['graph']
    effective = compilation['replay']['effective']
    questions = []
    boundaries = defaultdict(list)
    for row in effective.get('term_boundaries', []):
        boundaries[row['target']['doc_id']].append(row['target'])
    bundles = suggest_packet_semantics(packet, term_boundaries=dict(boundaries))
    candidates = graph.get('construction_candidates', [])
    interpreted = defaultdict(list)
    for row in effective.get('term_interpretations', []):
        interpreted[anchor_key(row['target'])].append(row)
    for doc_id, bundle in bundles.items():
        occurrences = defaultdict(list)
        for candidate in bundle['candidates']:
            span = candidate['span']
            # The existing term-interpretation contract attaches to exact Term
            # leaves, including output labels. Parent containment or a matching
            # surface elsewhere cannot establish this occurrence's eligibility.
            nominal = any(c['kind'] not in ('task_marker', 'query_marker')
                and any(v.get('kind') == 'Term'
                        and any(all(s.get(key) == span.get(key)
                                    for key in ('doc_id', 'reading_id', 'start', 'end', 'quote'))
                                for s in v.get('source_spans', []))
                        for v in c.get('slots', {}).values())
                for c in candidates)
            if (nominal and candidate['constraint_status'] == 'compatible'
                    and candidate['expression']['op'] != 'unknown'):
                occurrences[anchor_key(span)].append(candidate)
        for key, choices in occurrences.items():
            prior = interpreted.get(key, [])
            from adjudication.semantic_closure import term_resolution
            resolution = term_resolution(compilation.get('semantic_closure', {}), choices[0]['span'])
            if resolution['conflicts']:
                continue  # explicit conflict question below, not ordinary adoption
            if resolution['resolved']:
                continue
            if any(row['claim']['origin'] != 'machine_rejection' for row in prior) and not resolution['conflicts']:
                continue
            anchor = _anchor(packet, choices[0]['span'])
            rejected = sorted({ident for row in prior for ident in row['claim'].get('candidate_ids', [])})
            options = [_option(expression_label(c['expression']), 'set_term_interpretation',
                {'claim': adopt_term_candidate(anchor, branch_id, c, bundle)},
                ['Interpret only this occurrence.', 'No value, producer or conversion is supplied.'])
                for c in choices if c['id'] not in rejected]
            available = [c['id'] for c in choices if c['id'] not in rejected]
            for candidate in choices:
                if candidate['id'] in available:
                    options.append(_option('Reject: ' + expression_label(candidate['expression']), 'set_term_interpretation',
                        {'claim': reject_term_candidates(anchor, branch_id, [candidate['id']], bundle)},
                        ['Exclude this candidate only; retain other supported interpretations.']))
            if available:
                options.append(_option('Reject these suggestions', 'set_term_interpretation',
                    {'claim': reject_term_candidates(anchor, branch_id, available, bundle)},
                    ['Exclude these interpretations; keep the meaning unresolved.']))
            question = _question('term_interpretation', f'How should “{anchor["quote"]}” be interpreted here?',
                anchor, options, {'bundle': bundle, 'candidates': choices, 'rejected': rejected},
                machine_context={'reading': f'Machine found {len(choices)} compatible registered reading(s) for this occurrence.',
                                 'source_status': 'suggested',
                                 'why_blocked': 'No reviewed term interpretation has selected or excluded these candidates.'})
            questions.append(question)
    for candidate in candidates:
        if candidate['kind'] != 'load' or candidate.get('slots', {}).get('decrement', {}).get('value') != 1:
            continue
        construction = _anchor(packet, candidate['source_spans'][0])
        formal = candidate['slots']['value']['text']
        # The exact construction anchor is also a stable definition discriminator.
        address = {'definition_anchor': construction, 'construction_anchor': construction,
                   'construction_role': 'load', 'semantic_role': 'load', 'input_slot': 'value',
                   'formal': formal, 'branch_id': branch_id, 'invocation_path': [construction]}
        normalized = normalize_decision_target('set_quantity_semantics', {'semantic_input': address}, [construction])
        existing = {}
        for row in effective['quantity_semantics'].values():
            if row.get('semantic_input') and normalize_decision_target('set_quantity_semantics', row, [construction]) == normalized:
                existing.update(row.get('facets', row))
        required = {'coordinate_kind', 'index_base', 'reference_origin', 'counting_boundary', 'step_unit'}
        if required.issubset(existing) and existing['coordinate_kind'] == 'ordinal':
            continue
        options = []
        bundle = bundles.get(construction['doc_id'])
        kernel_candidate = _bu_year_ordinal_candidate(bundle, formal) if bundle else None
        if kernel_candidate:
            unit = 'year'
            facets = {'coordinate_kind': 'ordinal', 'index_base': 1, 'reference_origin': 'current_bu_start',
                      'counting_boundary': 'start_of_current_' + unit, 'step_unit': unit}
            from adjudication.quantity_targets import quantity_compatibility_issues
            if not (any(key in existing and existing[key] != value for key, value in facets.items())
                    or quantity_compatibility_issues({**existing, **facets})):
                options.append(_option('One-based ordinal ' + unit + ' count within the current 蔀',
                    'set_quantity_semantics', {'contract_version': '2.0', 'semantic_input': address, 'facets': facets},
                    ['Ordinal count', 'Starts at 1', 'Counted in ' + unit + 's',
                     'Relative to the beginning of the current 蔀', 'At the beginning of the current ' + unit],
                    management_facets=list(facets), semantic_target=normalized))
        questions.append(_question('counting_convention', f'How is “{formal}” counted here?', construction, options,
            {'construction': candidate,
             'basis': ('Source subtract-one operation; K candidate supports a current-蔀 year coordinate.'
                       if kernel_candidate else 'Source subtract-one operation; no scoped ordinal evidence.'),
             **({'kernel_candidate': kernel_candidate} if kernel_candidate else {})},
            machine_context={'reading': f'Machine reads “{formal}” in a subtract-one operation.',
                             'source_status': 'suggested' if kernel_candidate else 'unresolved',
                             'why_blocked': 'No reviewed counting coordinate has been recorded.'}))
    source_supply = {}
    for form in native_forms:
        if form['question'].get('optional_recheck') or form['category'] in ('system_diagnostic', 'decision_issue'):
            continue
        if not form.get('anchors'):
            continue
        kind = form['question']['kind']
        if kind in ('no_legal_candidate', 'uncovered_source'):
            anchor = form['anchors'][0]
            if any(c['kind'] not in ('task_marker', 'query_marker') and any(
                    s['doc_id'] == anchor['doc_id'] and s['start'] <= anchor['start']
                    and s['end'] >= anchor['end'] for s in c['source_spans']) for c in candidates):
                continue
            questions.append(_question('term_boundary',
                'Which spans should be treated as complete terms here?', anchor, [],
                {'native_question': form['question'], 'adjust_span': True},
                machine_context={'reading': 'Machine cannot form a supported term boundary at this source location.',
                                 'source_status': 'unresolved',
                                 'why_blocked': 'The current parse has no legal candidate for this span.'}))
            continue
        target = _source_supply_target(packet, graph, form, branch_id)
        if target is None:
            if form['category'] != 'scholar_actionable':
                continue
            target = _construction_context_target(form, branch_id)
        group = source_supply.setdefault(digest(target['semantic_key']), {'target': target, 'forms': []})
        group['forms'].append(form)
    for group in source_supply.values():
        target = group['target']
        options = []
        traces = list(target.get('rule_trace', []))
        for form in group['forms']:
            traces.extend(form.get('rule_trace', []))
            offered_binding = _offered_action(form, 'bind_value')
            offered_runtime = _offered_action(form, 'declare_parameter')
            traces.extend([offered_binding, offered_runtime])
            if offered_binding['matched']:
                for producer in form['producers']:
                    options.append(_option('Use “' + producer['output_port'] + '” from “' + producer['anchor']['quote'] + '”',
                        'bind_value', {'consumer_definition_anchor': form['consumer_anchor'], 'formal': form['formal'],
                            'producer_definition_anchor': producer['anchor'], 'output_port': producer['output_port']},
                        ['Use this source-derived output for the current input.'], group='source_resolution'))
            if offered_runtime['matched']:
                options.append(_option('Supply a runtime test value for “' + form['formal'] + '”', 'declare_parameter',
                    {'name': form['formal'], 'unit': 'unknown', 'role': 'root_input', 'root_input': True,
                     'evidence_basis': 'Standalone runtime value permitted; historical source remains unjudged'},
                    ['Permit a value for execution or testing.',
                     'This does not establish a historical source.', 'The quantity meaning remains unresolved.'], group='runtime_fallback'))
            if target['semantic_key']['issue_family'] != 'source_supply' and 'attach_context' in form['resolving_actions']:
                options.append(_option('Read additional source material', 'attach_context', {},
                    ['Include the selected source as context; do not approve a binding or interpretation.'],
                    requires_context_picker=True))
        try:
            validate_anchor(packet, target['decision_target'])
            valid_context_anchor = True
        except (ValueError, KeyError, TypeError):
            valid_context_anchor = False
        context = rule('SOURCE-CONTEXT-01', 'scholar_question', [
            condition('issue_family', target['semantic_key']['issue_family'], 'source_supply'),
            condition('valid source anchor exists', valid_context_anchor)], build_questions,
            result={'action': 'attach_context', 'result_class': 'available_action'})
        traces.append(context)
        if context['matched']:
            options.append(_option('Read additional source material', 'attach_context', {},
                ['Include the selected source as context; do not approve a binding or interpretation.'],
                requires_context_picker=True, group='source_resolution'))
        options = list({option['id']: option for option in options}.values())
        if options:
            formal = target['semantic_key'].get('formal')
            title = (f'Which source supplies “{formal}” here?' if formal
                     else 'What contextual material is required for this construction?')
            questions.append(_question('quantity_source', title, target['display_anchor'], options,
                {'native_questions': [form['question'] for form in group['forms']]},
                semantic_key=target['semantic_key'], display_anchor=target['display_anchor'],
                evidence_anchors=target['evidence_anchors'], decision_target=target['decision_target'],
                machine_context=target['machine_context']))
            key = target['semantic_key']
            upstream = [r for r in compilation.get('rule_trace', [])
                        if r['subject'].get('formal') == key.get('formal')
                        and r['subject'].get('consumer_definition_id') == key.get('consumer_definition_id')]
            questions[-1]['rule_trace'] = list({digest(r): r for r in [*upstream, *traces, *questions[-1]['rule_trace']]}.values())
    from adjudication.reviewed_relations import propose_reviewed_relations
    if not effective.get('reviewed_relations'):
        for payload in propose_reviewed_relations(packet, graph):
            questions.append(_question('reviewed_relation',
                'Use the attested Han Si-fen month-to-day relation for this calculation?', payload['division_anchor'],
                [_option('Use this evidenced month-to-day relation', 'approve_reviewed_relation', payload,
                    ['Interpret the real quotient as whole days.',
                     'Interpret the real remainder as a fractional-day numerator over 蔀月.',
                     'Retain the existing multiplication and division.'])], {'relation': payload}))
    closure = compilation.get('semantic_closure', {})
    facts = {a['id']: a for a in closure.get('assertions', [])}
    events = {e['id']: e for e in graph.get('events', [])}
    values = {v['id']: v for v in graph.get('value_instances', [])}
    for conflict in closure.get('conflicts', []):
        target = conflict['target']
        event = events.get(target.get('event_id') or values.get(target.get('value_id'), {}).get('producer'), {})
        spans = [target['anchor']] if target.get('anchor') else event.get('source_spans', [])
        if not spans:
            continue
        anchor = _anchor(packet, spans[0])
        decision_ids = set(conflict.get('decision_ids', []))
        pending, visited = list(conflict.get('assertion_ids', [])), set()
        while pending:
            ident = pending.pop()
            if ident in visited or ident not in facts:
                continue
            visited.add(ident)
            for proof in facts[ident]['proofs']:
                for dep in proof['depends_on']:
                    if dep['kind'] == 'review_decision':
                        decision_ids.add(dep['id'])
                    elif dep['kind'] == 'assertion':
                        pending.append(dep['id'])
        from .semantic_presentation import assertion_label
        def premise_label(ident):
            labels = [assertion_label(a) for a in facts.values() if a['authority'] == 'reviewed'
                      and any(d['kind'] == 'review_decision' and d['id'] == ident for d in a['depends_on'])]
            return '; '.join(dict.fromkeys(labels)) or 'explicit rejection'
        options = [_option('Retract review: ' + premise_label(ident), 'retract', {'decision_id': ident},
                   ['Remove this human premise and recompile; no replacement interpretation is chosen automatically.'])
                   for i, ident in enumerate(sorted(decision_ids))]
        questions.append(_question('semantic_conflict', 'Review conflicting semantic evidence', anchor, options,
            {'conflict': conflict, 'assertions': [facts[i] for i in sorted(visited)]},
            semantic_key={'issue_family': 'semantic_conflict', 'occurrence': anchor_key(anchor), 'facet': conflict['facet']},
            machine_context={'reading': 'Independently supported facts disagree.', 'source_status': 'conflicted',
                             'why_blocked': 'Conflicting premises cannot support downstream conclusions.'}))
    unique = {q['id']: q for q in questions}
    order = {d['doc_id']: i for i, d in enumerate(packet.get('primary_documents', []) + packet.get('context_documents', []))}
    return sorted(unique.values(), key=lambda q: (order.get(q['anchor']['doc_id'], 999), q['anchor']['start'],
                                                 q['kind'] != 'term_boundary', q['kind']))
