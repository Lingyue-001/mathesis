"""The one read-only scholar-facing projection for source review.

``project_scholar_source`` reads the reviewed compiler graph, Domain Kernel
candidates, questions, and replay state. It does not parse source or repair
semantic data. ``project_annotations`` is a legacy panel-shaped view derived
from this canonical projection.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import json

from adjudication.anchors import anchor_for, anchor_key
from adjudication.decision_contracts import normalize_decision_target
from domain_kernel.engine import suggest_packet_semantics


_NON_CORE_EVENTS = {'literal', 'input', 'alias', 'unsupported'}
_FACET_NAMES = {'term_interpretation': 'term_meaning', 'counting_convention': 'quantity_meaning'}


def _anchor(packet, span):
    return anchor_for(packet, span['doc_id'], span['start'], span['end'], span.get('reading_id'))


def _span(anchor):
    return [anchor['start'], anchor['end']]


def _unique(rows):
    result = {}
    for row in rows:
        result.setdefault(anchor_key(row), row)
    return list(result.values())


def _term_id(anchor):
    return f"term:{anchor['doc_id']}:{anchor['start']}-{anchor['end']}"


def _construction_id(candidate):
    first = min(candidate['source_spans'], key=lambda item: (item['start'], item['end']))
    return f"construction:{first['doc_id']}:{first['start']}-{first['end']}:{candidate['kind']}"


def _expression_text(expression):
    if expression.get('op') == 'concept':
        return expression['concept_id']
    return f"{expression.get('op')}({','.join(_expression_text(value) for value in expression.get('arguments', {}).values())})"


def _candidate_status(candidate):
    if candidate.get('authorization_status') == 'authorized':
        return 'reviewed'
    if candidate.get('support_status') == 'proposed' and candidate.get('constraint_status') == 'compatible':
        return 'suggested'
    return 'unresolved'


def _candidate_slots(candidate, syntax):
    """Resolve lowered slot text back to its canonical syntax-node references."""
    node = syntax.get(candidate.get('node_id'), {})
    children = syntax
    slots = {}
    for name, slot in candidate.get('slots', {}).items():
        child = children.get(node.get('slots', {}).get(name), {})
        spans = child.get('source_spans', [])
        slots[name] = {**slot, **({'source_span': spans[0]} if len(spans) == 1 else {})}
    return slots


def _in_focus(span, document):
    return (span.get('doc_id') == document['doc_id']
            and span.get('reading_id', document.get('reading_id')) == document.get('reading_id'))


def _term_rows(packet, candidates, syntax, effective, document):
    """Admit domain, reviewed and non-Heading operand occurrences, then their children.

    Candidate child IDs describe alternative analyses. Preserve each ordered
    sequence; only expose a shared occurrence tree when alternatives agree.
    """
    slot_anchors = {}
    for candidate in candidates:
        if (candidate.get('status') != 'selected'
                or syntax.get(candidate.get('node_id'), {}).get('kind') == 'Heading'):
            continue
        for slot in _candidate_slots(candidate, syntax).values():
            if (slot.get('kind') == 'Term' and slot.get('source_span')
                    and _in_focus(slot['source_span'], document)):
                anchor = _anchor(packet, slot['source_span'])
                slot_anchors[anchor_key(anchor)] = anchor
    anchors = dict(slot_anchors)
    boundaries = defaultdict(list)
    boundary_keys = set()
    for row in effective.get('term_boundaries', []):
        if not _in_focus(row['target'], document):
            continue
        anchor = _anchor(packet, row['target'])
        anchors[anchor_key(anchor)] = anchor
        boundary_keys.add(anchor_key(anchor))
        boundaries[anchor['doc_id']].append(anchor)
    candidate_by_anchor, by_id, fixed = defaultdict(list), {}, []
    for bundle in suggest_packet_semantics(packet, term_boundaries=dict(boundaries)).values():
        fixed.extend(c for c in bundle.get('fixed_expression_candidates', []) if _in_focus(c['span'], document))
        for candidate in bundle.get('candidates', []):
            if not candidate.get('span') or not _in_focus(candidate['span'], document):
                continue
            by_id[candidate['id']] = candidate
            anchor = _anchor(packet, candidate['span'])
            if candidate['expression'].get('op') != 'unknown':
                anchors[anchor_key(anchor)] = anchor
            candidate_by_anchor[anchor_key(anchor)].append(candidate)
    claims = defaultdict(list)
    for row in effective.get('term_interpretations', []):
        if not _in_focus(row['target'], document):
            continue
        anchor = _anchor(packet, row['target'])
        anchors[anchor_key(anchor)] = anchor
        claims[anchor_key(anchor)].append(deepcopy(row))
    # Unknown children can be needed by an admitted compound. Close over the
    # canonical child IDs, never over surface containment or spelling.
    pending = list(anchors)
    while pending:
        for candidate in candidate_by_anchor.get(pending.pop(), []):
            for child_id in candidate.get('child_ids', []):
                child = by_id.get(child_id)
                if child:
                    anchor = _anchor(packet, child['span'])
                    key = anchor_key(anchor)
                    if key not in anchors:
                        anchors[key] = anchor
                        pending.append(key)
    component_keys = {anchor_key(_anchor(packet, by_id[child]['span']))
                      for candidate in by_id.values() for child in candidate.get('child_ids', []) if child in by_id}
    rows = []
    for key, anchor in sorted(anchors.items(), key=lambda item: (item[1]['doc_id'], item[1]['start'], -item[1]['end'])):
        semantic = sorted(candidate_by_anchor.get(key, []),
                          key=lambda c: (c.get('rule_id') or '', _expression_text(c['expression'])))
        contained = any(other_key != key and other['doc_id'] == anchor['doc_id']
                        and other['reading_id'] == anchor['reading_id']
                        and other['start'] <= anchor['start'] and anchor['end'] <= other['end']
                        for other_key, other in anchors.items())
        alternatives = []
        for candidate in semantic:
            child_terms = [_term_id(by_id[child]['span']) for child in candidate.get('child_ids', []) if child in by_id]
            if child_terms not in alternatives:
                alternatives.append(child_terms)
        if not any(alternatives):
            alternatives = []
        rows.append({
            'id': _term_id(anchor), 'kind': 'term', 'span': _span(anchor), 'surface': anchor['quote'],
            'display_level': 'component' if (key in component_keys or contained) and key not in slot_anchors
                            and key not in boundary_keys else 'maximal',
            'children': alternatives[0] if len(alternatives) == 1 else [],
            'composition_alternatives': alternatives, 'reviewed_claims': claims.get(key, []),
            'semantic_candidates': [{
                'candidate_id': candidate['id'], 'child_ids': list(candidate['child_ids']),
                'expression': _expression_text(candidate['expression']),
                'structured_expression': deepcopy(candidate['expression']),
                'status': _candidate_status(candidate), 'rule_id': candidate.get('rule_id'),
                'cue_id': candidate.get('cue_id'),
                'support_status': candidate.get('support_status'),
                'constraint_status': candidate.get('constraint_status'),
                'authorization_status': candidate.get('authorization_status'),
                'authorization_refs': deepcopy(candidate.get('authorization_refs', [])),
                'provenance_ids': list(candidate.get('provenance_ids', [])),
            } for candidate in semantic],
            'review_facets': [], 'evidence': [{'candidate_id': candidate['id']} for candidate in semantic],
            'source_anchor': anchor, '_anchor': anchor,
        })
    return rows, fixed


def _slot_projection(packet, name, slot, terms):
    row = {'name': name, 'surface': slot.get('text', '')}
    if slot.get('source_span'):
        anchor = _anchor(packet, slot['source_span'])
        row['span'] = _span(anchor)
        term = terms.get(_term_id(anchor))
        if term:
            row['linked_term_id'] = term['id']
            row['link_basis'] = 'structurally_derived'
    return row


def _construction_rows(packet, candidates, terms, syntax, fixed=()):
    rows = []
    for candidate in candidates:
        if not candidate.get('source_spans'):
            continue
        anchors = [_anchor(packet, span) for span in candidate['source_spans']]
        first = min(anchors, key=lambda anchor: (anchor['start'], anchor['end']))
        rows.append({
            'id': _construction_id(candidate), 'kind': 'construction', 'span': _span(first),
            'source_spans': [_span(anchor) for anchor in anchors], 'source_anchors': anchors,
            'surface': candidate.get('text', first['quote']),
            'construction_kind': candidate['kind'],
            # Candidate public_kind is the canonical reviewed-syntax contract.
            # The syntax node may be the internal ReviewedCandidate sentinel when
            # no native public kind exists, which must remain visible as null.
            'public_kind': (candidate['public_kind'] if 'public_kind' in candidate
                            else syntax.get(candidate.get('node_id'), {}).get('public_kind',
                                syntax.get(candidate.get('node_id'), {}).get('kind'))),
            'production_id': candidate.get('production_id'),
            'parse_status': 'machine_selected' if candidate.get('status') == 'selected' else candidate.get('status', 'unresolved'),
            'slots': [_slot_projection(packet, name, slot, terms) for name, slot in _candidate_slots(candidate, syntax).items()
                      if slot.get('text')],
            'review_facets': [], 'evidence': [{'syntax_node_id': candidate.get('node_id')}],
            '_candidate': candidate, '_slots': _candidate_slots(candidate, syntax), '_anchors': anchors,
        })
    for candidate in fixed:
        anchor = _anchor(packet, candidate['span'])
        rows.append({'id': f"construction:{anchor['doc_id']}:{anchor['start']}-{anchor['end']}:fixed_expression:{candidate['rule_id']}",
                     'kind': 'construction', 'span': _span(anchor), 'source_spans': [_span(anchor)],
                     'source_anchors': [anchor], 'surface': anchor['quote'], 'construction_kind': 'fixed_expression',
                     'public_kind': None, 'origin': 'domain_kernel_fixed_expression', 'rule_id': candidate['rule_id'],
                     'proposal': candidate['proposes'], 'parse_status': 'suggested', 'slots': [], 'review_facets': [],
                     'evidence': [{'candidate_id': candidate['id'], 'kernel_candidate': deepcopy(candidate)}],
                     '_candidate': candidate, '_slots': {}, '_anchors': [anchor]})
    return sorted(rows, key=lambda row: (row['_anchors'][0]['doc_id'], row['span'][0], row['span'][1], row['construction_kind'], row['id']))


def _active_decisions(decisions, statuses):
    return [row for row in decisions if row.get('action') not in ('retract', 'defer')
            and statuses.get(row['decision_id'], {}).get('status', 'active') == 'active']


def _decision_facet(action):
    return {'declare_parameter': 'source_supply', 'bind_value': 'source_supply',
            'set_term_interpretation': 'term_meaning', 'set_term_boundary': 'term_boundary',
            'set_quantity_semantics': 'quantity_meaning', 'attach_context': 'source_context',
            'approve_reviewed_relation': 'reviewed_relation'}.get(action, action)


def _question_facet(question):
    return _FACET_NAMES.get(question.get('semantic_key', {}).get('issue_family', question.get('kind')),
                            question.get('semantic_key', {}).get('issue_family', question.get('kind')))


def _step_id(event, ordinal):
    spans = event['source_spans']
    return f"step:{spans[0]['doc_id']}:{min(span['start'] for span in spans)}-{max(span['end'] for span in spans)}:{event['kind']}:{ordinal}"


def _step_rows(packet, graph, constructions, terms, document, diagnostics):
    events, values = graph.get('events', []), {row['id']: row for row in graph.get('value_instances', [])}
    by_node = {row['_candidate'].get('node_id'): row for row in constructions}
    aliases = defaultdict(list)
    for event in events:
        if (event.get('kind') == 'alias' and event.get('source_spans')
                and all(_in_focus(span, document) for span in event['source_spans'])):
            for value_id in event.get('reads', {}).values():
                aliases[value_id].append(event)
    ordinals, steps_by_event, rows = defaultdict(int), {}, []
    for event in events:
        if event.get('kind') in _NON_CORE_EVENTS or not event.get('syntax_node_id') or not event.get('source_spans'):
            continue
        if not all(_in_focus(span, document) for span in event['source_spans']):
            if any(_in_focus(span, document) for span in event['source_spans']):
                diagnostics.append({'kind': 'cross_document_step_not_projectable', 'event_id': event['id'],
                                    'source_spans': deepcopy(event['source_spans']),
                                    'message': 'Operation anchors do not all belong to the focused source.'})
            continue
        key = (event['source_spans'][0]['doc_id'], min(span['start'] for span in event['source_spans']),
               max(span['end'] for span in event['source_spans']), event['kind'])
        step_id, ordinal = _step_id(event, ordinals[key]), ordinals[key]
        ordinals[key] += 1
        steps_by_event[event['id']] = step_id
        construction = by_node.get(event['syntax_node_id'])
        construction_ids = [construction['id']] if construction else []
        if event['kind'] == 'threshold' and event.get('attributes', {}).get('judgment'):
            matches = [row for row in constructions if row['construction_kind'] == 'judgment'
                       and row['surface'] == event['attributes']['judgment']
                       and any(anchor_key(a) == anchor_key(_anchor(packet, b))
                               for a in row['_anchors'] for b in event['source_spans'])]
            if len(matches) == 1:
                construction_ids.append(matches[0]['id'])
        rows.append({'id': step_id, 'kind': 'computational_step', 'operation': event['kind'],
                     'source_spans': [[span['start'], span['end']] for span in event['source_spans']],
                     'source_anchors': [_anchor(packet, span) for span in event['source_spans']],
                     'construction_ids': construction_ids, 'inputs': [], 'outputs': [],
                     'review_facets': [], 'evidence': [{'event_id': event['id'], 'syntax_node_id': event['syntax_node_id']}],
                     '_event': event})
    for row in rows:
        event, construction = row['_event'], by_node.get(row['_event']['syntax_node_id'])
        slots = construction['_slots'] if construction else {}
        for role, value_id in event.get('reads', {}).items():
            value, item = values.get(value_id, {}), {'role': role, 'value_id': value_id}
            producer = value.get('producer')
            if producer in steps_by_event:
                item['from_step_id'] = steps_by_event[producer]
                if value.get('output_port') not in (None, 'result'):
                    item['output_port'] = value['output_port']
            elif value.get('origin_producer') in steps_by_event:
                item['from_step_id'] = steps_by_event[value['origin_producer']]
                if value.get('origin_port'):
                    item['output_port'] = value['origin_port']
                if value.get('labels'):
                    item['label'] = value['labels'][0]
            else:
                producer_event = next((candidate for candidate in events if candidate['id'] == producer), {})
                if producer_event.get('kind') == 'literal':
                    item['literal'] = producer_event.get('attributes', {}).get('value')
                else:
                    slot = slots.get(role, {})
                    if slot.get('source_span'):
                        term_id = _term_id(_anchor(packet, slot['source_span']))
                        if term_id in terms:
                            item['term_id'] = term_id
            slot = slots.get(role, {})
            if slot.get('source_span') and slot.get('kind') == 'Term':
                term_id = _term_id(_anchor(packet, slot['source_span']))
                if term_id in terms:
                    item['term_id'] = term_id
                    item['term_link_basis'] = 'structurally_derived'
            if slot.get('kind') == 'Anaphor' and slot.get('text'):
                item['surface_reference'] = slot['text']
            row['inputs'].append(item)
        for port, value_id in event.get('writes', {}).items():
            output = {'port': port, 'labels': []}
            for alias in aliases.get(value_id, []):
                label = alias.get('attributes', {}).get('label')
                if not label:
                    continue
                output['labels'].append(label)
                naming = by_node.get(alias.get('syntax_node_id'))
                if naming:
                    output.setdefault('naming_construction_ids', []).append(naming['id'])
                    label_slot = naming['_slots'].get('label', {})
                    if label_slot.get('source_span'):
                        term_id = _term_id(_anchor(packet, label_slot['source_span']))
                        if term_id in terms:
                            output.setdefault('label_term_ids', []).append(term_id)
            output['value_id'] = value_id
            if values.get(value_id, {}).get('quantity_kind'):
                output['quantity_kind'] = values[value_id]['quantity_kind']
            row['outputs'].append(output)
        if event.get('attributes', {}).get('judgment'):
            row['judgment'] = event['attributes']['judgment']
        del row['_event']
    return rows, steps_by_event


def _flow_rows(packet, graph, steps_by_event, diagnostics):
    """Project formal supplies from imports AND native invocation value bindings.

    Declarations and permitted roots can bypass linked.imports. The caller's
    formal_bindings still identifies their actual value; never infer a producer
    from a label or from an unrelated same-named formal.
    """
    events = {row['id']: row for row in graph.get('events', [])}
    values = {row['id']: row for row in graph.get('value_instances', [])}
    program = graph.get('program', {})
    definitions = {row['id']: row for row in program.get('definitions', [])}
    imports = {(row['consumer_definition_id'], row['formal']): row
               for row in program.get('linked', {}).get('imports', [])}
    documents = {doc['doc_id']: doc for group in ('primary_documents', 'context_documents')
                 for doc in packet.get(group, [])}
    rows = []
    for definition in definitions.values():
        for formal, native_use in definition.get('formal_inputs', {}).items():
            imported = imports.get((definition['id'], formal))
            calls = [call for call in program.get('calls', []) if call['definition_id'] == definition['id']]
            value_ids = {call['formal_bindings'][formal] for call in calls if formal in call.get('formal_bindings', {})}
            use_nodes = set(native_use.get('uses', []))
            consumers = [(events[event_id], step_id) for event_id, step_id in steps_by_event.items()
                         if events[event_id].get('syntax_node_id') in use_nodes
                         and events[event_id].get('scope', {}).get('definition_id') == definition['id']]
            refs = [{'step_id': step_id, 'role': role, 'value_id': value_id,
                     'syntax_node_id': event.get('syntax_node_id')}
                    for event, step_id in consumers
                    for role, value_id in event.get('reads', {}).items() if value_id in value_ids]
            if not refs:
                if imported and consumers:
                    diagnostics.append({'kind': 'flow_input_unlinked', 'formal': formal,
                                        'consumer_definition_id': definition['id'],
                                        'consumer_step_ids': [step_id for _, step_id in consumers],
                                        'message': 'Focused import has no unique native invocation/read reference.'})
                continue
            selected = imported.get('selected_definition_id') if imported else None
            port = imported.get('selected_port') if imported else None
            producer_source, producer_step = None, None
            reason = imported.get('selection_reason') if imported else None
            basis = 'explicit'
            native_values = [values[ident] for ident in value_ids if ident in values]
            producers = {value.get('origin_producer', value.get('producer')) for value in native_values}
            producer_event = events.get(next(iter(producers))) if len(producers) == 1 else None
            # Native declarations are not Program IR imports. Locate their
            # owning definition by exact source identity, never by surface text.
            if not imported and producer_event and producer_event.get('kind') != 'input':
                selected = producer_event.get('scope', {}).get('definition_id')
                if not selected:
                    matches = [d['id'] for d in definitions.values() if any(
                        anchor_key(_anchor(packet, a)) == anchor_key(_anchor(packet, b))
                        for a in d.get('source_spans', []) for b in producer_event.get('source_spans', []))]
                    selected = matches[0] if len(matches) == 1 else None
                    basis = 'structurally_derived'
                ports = {value.get('origin_port', value.get('output_port')) for value in native_values}
                port = next(iter(ports)) if len(ports) == 1 else None
                reason = 'native formal binding to source declaration/value'
            if selected in definitions:
                spans = definitions[selected].get('source_spans', [])
                if spans:
                    document = documents.get(spans[0]['doc_id'], {})
                    producer_source = {**deepcopy(document.get('source', {})),
                                       'doc_id': document.get('doc_id', spans[0]['doc_id']),
                                       'reading_id': document.get('reading_id'), 'definition_id': selected,
                                       'source_spans': deepcopy(spans), 'basis': basis}
                producer_step = steps_by_event.get(producer_event['id']) if producer_event else None
            compatible = {row['definition_id'] for row in (imported or {}).get('candidate_evidence', [])
                          if row.get('compatible') is True}
            # This exact canonical linker reason is emitted only for >1 viable
            # producers; unrelated prose and raw named candidates prove nothing.
            ambiguous = (imported or {}).get('selection_reason') in (
                'multiple source producers', 'multiple compatible source producers') or len(compatible) > 1
            status = 'linked_source' if selected else 'ambiguous_source' if ambiguous else 'unresolved_source'
            head = {**_anchor(packet, definition['source_spans'][0]), 'definition_kind': definition['kind']}
            rows.append({'id': f"flow:{head['doc_id']}:{formal}", 'formal': formal,
                         'consumer_definition_id': definition['id'], 'consumer_anchor': head,
                         'consumer_step_ids': list(dict.fromkeys(ref['step_id'] for ref in refs)),
                         'input_refs': refs, 'status': status, 'producer_step_id': producer_step,
                         'producer_source': producer_source, 'selected_definition_id': selected,
                         'selected_port': port, 'output_port': port, 'selection_reason': reason,
                         'review_facets': [], 'evidence': [{'import': deepcopy(imported),
                             'call_ids': [call['id'] for call in calls], 'value_ids': sorted(value_ids)}]})
    counts = defaultdict(int)
    for row in rows:
        counts[row['id']] += 1
    for row in rows:
        if counts[row['id']] > 1:
            anchor = row['consumer_anchor']
            row['id'] += f":consumer:{anchor['definition_kind']}:{anchor['start']}-{anchor['end']}"
    return rows


def _object_for_anchor(anchor, terms, constructions):
    term = next((row for row in terms if row['_anchor']['doc_id'] == anchor['doc_id']
                 and row['_anchor']['reading_id'] == anchor.get('reading_id')
                 and row['_anchor']['start'] == anchor['start'] and row['_anchor']['end'] == anchor['end']), None)
    if term:
        return term
    overlaps = [row for row in constructions if row['_anchors'][0]['doc_id'] == anchor['doc_id']
                and row['_anchors'][0]['reading_id'] == anchor.get('reading_id')
                and row['span'][0] <= anchor['start'] and anchor['end'] <= row['span'][1]]
    return min(overlaps, key=lambda row: (row['span'][1] - row['span'][0], row['id'])) if overlaps else None


def _source_decision_matches(decision, flow):
    payload = decision.get('payload', {})
    formal = payload.get('formal') or payload.get('name')
    if formal != flow['formal'] or not decision.get('targets'):
        return False
    consumer = payload.get('consumer_definition_anchor') or decision['targets'][0]
    if anchor_key(consumer) != anchor_key(flow['consumer_anchor']):
        return False
    if consumer.get('definition_kind') and consumer['definition_kind'] != flow['consumer_anchor'].get('definition_kind'):
        return False
    # A scope-specific binding cannot mark an entire consumer-wide supply.
    scope = payload.get('scope_anchor')
    return scope is None or anchor_key(scope) == anchor_key(flow['consumer_anchor'])


def _question_matches(decision, question, flows):
    if _decision_facet(decision.get('action')) != _question_facet(question) or not decision.get('targets'):
        return False
    question_branch = question.get('semantic_key', {}).get('branch_id')
    if question_branch is not None and question_branch != decision.get('branch_id', 'main'):
        return False
    if _question_facet(question) == 'source_supply':
        key = question.get('semantic_key', {})
        return any(flow['consumer_definition_id'] == key.get('consumer_definition_id')
                   and flow['formal'] == key.get('formal') and _source_decision_matches(decision, flow)
                   for flow in flows)
    actual = normalize_decision_target(decision['action'], decision.get('payload', {}), decision['targets'])
    if decision['action'] in ('set_term_interpretation', 'set_term_boundary'):
        expected = normalize_decision_target(decision['action'], {}, [question.get('decision_target', question['anchor'])])
        return actual == expected
    return any(option['action'] == decision['action'] and actual == normalize_decision_target(
        option['action'], option.get('payload', {}), [question.get('decision_target', question['anchor'])])
        for option in question.get('options', []))


def _decision_facet_status(decision):
    return ('rejected' if decision.get('payload', {}).get('claim', {}).get('origin') == 'machine_rejection'
            else 'reviewed')


def _semantic_identity(value):
    """Normalize source addresses without hashes, display text or cache identity."""
    if isinstance(value, list):
        return [_semantic_identity(item) for item in value]
    if isinstance(value, dict):
        if all(key in value for key in ('doc_id', 'start', 'end')):
            return {key: value[key] for key in ('doc_id', 'reading_id', 'start', 'end', 'definition_kind') if key in value}
        return {key: _semantic_identity(item) for key, item in value.items()
                if key not in ('source_sha256', 'corpus_sha256', 'unit_index_sha256')}
    return value


def _supply_target(flow, branch):
    return {'kind': 'source_supply', 'consumer': _semantic_identity(flow['consumer_anchor']),
            'formal': flow['formal'], 'branch_id': branch}


def _supply_terms(flow, steps):
    return {item['term_id'] for step in steps for item in step['inputs']
            if item.get('flow_id') == flow['id'] and item.get('term_id')}


def _review_facets(questions, decisions, statuses, terms, constructions, steps, flows, branch='main'):
    facets, active = [], _active_decisions(decisions, statuses)
    active_by_id = {row['decision_id']: row for row in active}
    represented_context_ids = set()
    for question in questions:
        facet = _question_facet(question)
        target = _object_for_anchor(question.get('display_anchor', question['anchor']), terms, constructions)
        key = question.get('semantic_key', {})
        if key.get('branch_id', branch) != branch:
            continue
        related = [flow for flow in flows if facet == 'source_supply'
                   and flow['consumer_definition_id'] == key.get('consumer_definition_id')
                   and flow['formal'] == key.get('formal')]
        if facet == 'source_supply' and related and (not target or target['kind'] != 'term'):
            target = related[0] if len(related) == 1 else None
        if not target:
            continue
        matched = [decision for decision in active if _question_matches(decision, question, flows)]
        decision = matched[-1] if matched else None
        recorded = question.get('recorded_decision')
        if related and all(flow['status'] == 'linked_source' for flow in related) and not decision and not recorded:
            continue
        semantic_target = next((normalize_decision_target(option['action'], option.get('payload', {}),
                                [question.get('decision_target', question['anchor'])])
                               for option in question.get('options', [])
                               if option['action'] in ('set_quantity_semantics', 'set_term_interpretation',
                                                       'set_term_boundary', 'approve_reviewed_relation')), None)
        if len(related) == 1:
            semantic_target = _supply_target(related[0], branch)
        elif facet == 'source_supply' and key.get('formal') and question.get('decision_target'):
            semantic_target = {'kind': 'source_supply', 'consumer': _semantic_identity(question['decision_target']),
                               'formal': key['formal'], 'branch_id': branch}
        facets.append({'object_id': target['id'], 'facet': facet, 'semantic_target': semantic_target,
                       'related_object_ids': [flow['id'] for flow in related if flow['id'] != target['id']],
                       'status': _decision_facet_status(decision) if decision else 'pending',
                       'decision_id': decision['decision_id'] if decision else None,
                       'action': decision['action'] if decision else None,
                       'question_id': question['id'], 'semantic_key': question.get('semantic_key', {}),
                       'evidence': question.get('evidence_anchors', [])})
        if recorded and recorded['decision_id'] in active_by_id:
            context = active_by_id[recorded['decision_id']]
            represented_context_ids.add(context['decision_id'])
            facets.append({'object_id': target['id'], 'facet': 'source_context', 'status': 'reviewed',
                           'related_object_ids': [], 'question_id': question['id'],
                           'decision_id': context['decision_id'], 'action': 'attach_context',
                           'semantic_key': normalize_decision_target(context['action'], context['payload'], context['targets']),
                           'semantic_target': normalize_decision_target(context['action'], context['payload'], context['targets']),
                           'evidence': question.get('evidence_anchors', [])})
        if len(related) == 1:
            # Several exact occurrences can consume one formal supply. Each
            # occurrence must expose the existing question without UI traversal.
            primary = facets[-1]
            for term_id in sorted(_supply_terms(related[0], steps) - {target['id']}):
                facets.append({**primary, 'object_id': term_id, 'related_object_ids': [related[0]['id']]})
    for flow in flows:
        for decision in active:
            if _decision_facet(decision['action']) != 'source_supply' or not _source_decision_matches(decision, flow):
                continue
            if decision['action'] == 'declare_parameter' and flow['status'] != 'linked_source':
                flow['status'] = 'runtime_value_permitted'
            targets = _supply_terms(flow, steps)
            if not targets:
                targets.add(flow['id'])
            for object_id in sorted(targets):
                facets.append({'object_id': object_id, 'facet': 'source_supply', 'status': 'reviewed',
                               'related_object_ids': [flow['id']] if object_id != flow['id'] else [],
                               'semantic_target': _supply_target(flow, branch), 'question_id': None,
                               'decision_id': decision['decision_id'], 'action': decision['action'],
                               'semantic_key': {'issue_family': 'source_supply', 'formal': flow['formal'],
                                                'consumer_definition_id': flow['consumer_definition_id'],
                                                'branch_id': decision.get('branch_id', 'main')},
                               'evidence': flow['evidence']})
    # Resolved occurrence-local questions disappear from the queue; replayed
    # decisions retain their exact source target and must remain visible.
    for decision in active:
        family = _decision_facet(decision['action'])
        if family == 'source_supply' or decision['decision_id'] in represented_context_ids or not decision.get('targets'):
            continue
        payload = decision.get('payload', {})
        address = payload.get('semantic_input') or payload.get('semantic_output') or {}
        anchor = address.get('construction_anchor') or payload.get('division_anchor') or decision['targets'][0]
        target = _object_for_anchor(anchor, terms, constructions)
        if target:
            facets.append({'object_id': target['id'], 'facet': family, 'status': _decision_facet_status(decision),
                           'related_object_ids': [], 'question_id': None,
                           'decision_id': decision['decision_id'], 'action': decision['action'],
                           'semantic_key': normalize_decision_target(decision['action'], payload, decision['targets']),
                           'semantic_target': normalize_decision_target(decision['action'], payload, decision['targets']),
                           'evidence': deepcopy(decision['targets'])})
    unique = {}
    for facet in facets:
        identity = [facet['object_id'], facet['facet'], branch,
                    _semantic_identity(facet.get('semantic_target') or facet.get('semantic_key', {}))]
        key = 'facet:' + sha256(json.dumps(identity, ensure_ascii=False, sort_keys=True,
                                         separators=(',', ':')).encode('utf-8')).hexdigest()[:24]
        facet['facet_key'] = key
        priority = {'pending': 0, 'rejected': 1, 'reviewed': 2}
        if key not in unique or priority[facet['status']] > priority[unique[key]['status']]:
            unique[key] = facet
    return sorted(unique.values(), key=lambda row: (row['object_id'], row['facet'], row['facet_key']))


def _explicit_decision_refs(records, actions, statuses):
    """Read named reference fields only on supplied native objects, never nearby objects."""
    refs = {}
    def add(ident, action=None):
        if isinstance(ident, str) and ident and statuses.get(ident, {}).get('status', 'active') == 'active':
            refs[ident] = {'decision_id': ident, 'action': actions.get(ident, action), 'basis': 'explicit'}
    def visit(record):
        if not isinstance(record, dict):
            return
        add(record.get('decision_id'), record.get('action'))
        add(record.get('resegmentation_decision_id'), 'resegment')
        for field in ('decision_refs', 'adjudication_decision_refs', 'authorization_refs'):
            for ref in record.get(field, []):
                ident = ref.get('decision_id') if isinstance(ref, dict) else ref
                if field != 'authorization_refs' or ident in actions or ident in statuses:
                    add(ident, ref.get('action') if isinstance(ref, dict) else None)
        for field in ('attributes', 'metadata', 'quantity_transition', 'reviewed_quantity', 'reviewed_term_interpretations'):
            nested = record.get(field)
            for child in nested if isinstance(nested, list) else [nested]:
                visit(child)
    for record in records:
        visit(record)
    return [refs[key] for key in sorted(refs)]


def _project_decision_refs(terms, constructions, steps, flows, graph, effective, decisions, statuses):
    actions = {row['decision_id']: row['action'] for row in decisions}
    for group, action in (('term_boundaries', 'set_term_boundary'), ('term_interpretations', 'set_term_interpretation')):
        for row in effective.get(group, []):
            actions.setdefault(row['decision_id'], action)
    for term in terms:
        owned = [row for group in ('term_boundaries', 'term_interpretations') for row in effective.get(group, [])
                 if anchor_key(row['target']) == anchor_key(term['_anchor'])]
        term['decision_refs'] = _explicit_decision_refs([*owned, *term['semantic_candidates']], actions, statuses)
    for construction in constructions:
        construction['decision_refs'] = _explicit_decision_refs([construction['_candidate']], actions, statuses)
    events = {row['id']: row for row in graph.get('events', [])}
    values = {row['id']: row for row in graph.get('value_instances', [])}
    for step in steps:
        event = events[step['evidence'][0]['event_id']]
        owned = [values.get(ident, {}) for direction in ('reads', 'writes') for ident in event.get(direction, {}).values()]
        step['decision_refs'] = _explicit_decision_refs([event, *owned], actions, statuses)
    for flow in flows:
        owned = [row.get('import') or {} for row in flow['evidence']]
        # Replayed bindings carry an exact consumer/formal target and real ID,
        # even when Program IR serialization omits its binding_constraints map.
        for group, action in (('bindings', 'bind_value'), ('parameters', 'declare_parameter')):
            for binding in effective.get(group, {}).values():
                native = {'targets': [binding['target']], 'payload': binding}
                if _source_decision_matches(native, flow):
                    owned.append(binding)
                    actions.setdefault(binding['decision_id'], action)
        flow['decision_refs'] = _explicit_decision_refs(owned, actions, statuses)


def _links(constructions, steps, terms):
    links = []
    for construction in constructions:
        for slot in construction['slots']:
            if slot.get('linked_term_id'):
                links.append({'relation': 'fills_slot', 'from_id': slot['linked_term_id'],
                              'to_id': construction['id'], 'role': slot['name'],
                              'basis': slot['link_basis']})
    for step in steps:
        event_node = step['evidence'][0]['syntax_node_id']
        for construction_id in step['construction_ids']:
            construction = next(row for row in constructions if row['id'] == construction_id)
            basis = 'explicit' if construction['_candidate'].get('node_id') == event_node else 'structurally_derived'
            links.append({'relation': 'realizes', 'from_id': construction_id, 'to_id': step['id'], 'basis': basis})
        for output in step['outputs']:
            for naming in output.get('naming_construction_ids', []):
                links.append({'relation': 'names_output', 'from_id': naming, 'to_id': step['id'],
                              'role': output['port'], 'basis': 'explicit'})
    candidate_terms = {candidate['candidate_id']: term['id'] for term in terms
                       for candidate in term['semantic_candidates']}
    for term in terms:
        for candidate in term['semantic_candidates']:
            for ordinal, child in enumerate(candidate['child_ids']):
                if child in candidate_terms:
                    links.append({'relation': 'has_component', 'from_id': term['id'], 'to_id': candidate_terms[child],
                                  'basis': 'explicit', 'ordinal': ordinal,
                                  'evidence': [{'candidate_id': candidate['candidate_id'], 'child_id': child}]})
    return _canonical_links(links)


def _canonical_links(links):
    """Merge support paths at the canonical boundary, keeping the strongest basis."""
    unique = {}
    for link in links:
        key = tuple(link.get(field) for field in ('relation', 'from_id', 'to_id', 'role', 'ordinal'))
        if key not in unique:
            unique[key] = deepcopy({field: value for field, value in link.items() if field != 'evidence'})
        merged = unique[key]
        if link['basis'] == 'explicit':
            merged['basis'] = 'explicit'
        for evidence in link.get('evidence', []):
            if evidence not in merged.setdefault('evidence', []):
                merged['evidence'].append(deepcopy(evidence))
    return list(unique.values())


def _projection_diagnostics(constructions, steps, flows):
    """Record an omitted cross-layer assertion instead of filling it by guesswork."""
    diagnostics = []
    for construction in constructions:
        if construction['public_kind'] is None and construction.get('origin') != 'domain_kernel_fixed_expression':
            diagnostics.append({'kind': 'missing_public_syntax_kind', 'construction_id': construction['id'],
                                'message': 'No canonical syntax node; public kind remains unresolved.'})
        for name, slot in construction['_slots'].items():
            if (construction['construction_kind'] != 'task_marker' and slot.get('kind') == 'Term'
                    and slot.get('text') and not slot.get('source_span')):
                diagnostics.append({'kind': 'slot_source_span_not_unique', 'construction_id': construction['id'],
                                    'slot': name, 'message': 'No unique canonical source span for this Term slot.'})
    for step in steps:
        if not step['construction_ids']:
            diagnostics.append({'kind': 'event_construction_unlinked', 'step_id': step['id'],
                                'message': 'No selected construction has this event syntax-node identity.'})
    for flow in flows:
        if flow['selected_definition_id'] and flow['producer_source'] is None:
            diagnostics.append({'kind': 'selected_source_missing', 'flow_id': flow['id'],
                                'message': 'Selected definition has no source identity in the effective packet.'})
    return diagnostics


def project_scholar_source(packet, compilation, questions=(), decisions=(), decision_status=None, *, focus_doc_id=None):
    """Return the sole ScholarSourceProjection/1 truth without changing review state."""
    documents = [doc for group in ('primary_documents', 'context_documents') for doc in packet.get(group, [])]
    document = (next((doc for doc in documents if doc['doc_id'] == focus_doc_id), None)
                if focus_doc_id is not None else next(iter(packet.get('primary_documents', [])), None))
    if document is None:
        raise ValueError('Focused source document is not present in the effective packet.')
    graph = compilation['graph']
    candidates = [row for row in graph.get('construction_candidates', []) if row.get('source_spans')
                  and all(_in_focus(span, document) for span in row['source_spans'])]
    syntax = {row['id']: row for row in graph.get('syntax', {}).get('nodes', [])}
    effective = compilation.get('replay', {}).get('effective', {})
    terms, fixed = _term_rows(packet, candidates, syntax, effective, document)
    term_map = {row['id']: row for row in terms}
    constructions = _construction_rows(packet, candidates, term_map, syntax, fixed)
    diagnostics = []
    steps, step_ids = _step_rows(packet, graph, constructions, term_map, document, diagnostics)
    flows = _flow_rows(packet, graph, step_ids, diagnostics)
    for flow in flows:
        for ref in flow['input_refs']:
            step = next(row for row in steps if row['id'] == ref['step_id'])
            for item in step['inputs']:
                if item['role'] == ref['role'] and item['value_id'] == ref['value_id']:
                    item['flow_id'] = flow['id']
    branch = compilation.get('branch_id', 'main')
    decisions = [row for row in decisions if row.get('branch_id', branch) == branch]
    facets = _review_facets(questions, decisions, decision_status or {}, terms, constructions, steps, flows, branch)
    _project_decision_refs(terms, constructions, steps, flows, graph, effective, decisions, decision_status or {})
    for row in [*terms, *constructions, *steps, *flows]:
        row['review_facets'] = sorted({facet['facet'] for facet in facets
                                     if facet['object_id'] == row['id'] or row['id'] in facet['related_object_ids']})
    source = {'source_id': document.get('source', {}).get('source_id'),
               'unit_id': document.get('source', {}).get('unit_id'), 'doc_id': document['doc_id'],
               'reading_id': document.get('reading_id'), 'text': document['text'],
               'text_sha256': sha256(document['text'].encode('utf-8')).hexdigest()}
    projection = {'schema': 'ScholarSourceProjection/1', 'source': source, 'terms': terms,
            'constructions': constructions, 'steps': steps, 'flows': flows, 'review_facets': facets,
            'links': _links(constructions, steps, terms),
            'projection_diagnostics': diagnostics + _projection_diagnostics(constructions, steps, flows)}
    from .semantic_projection import attach_semantic_closure
    attach_semantic_closure(projection, compilation)
    # Private indexes are implementation details, not a second copy of native IR.
    for row in [*terms, *constructions]:
        for key in list(row):
            if key.startswith('_'):
                del row[key]
    return projection


def stable_golden_view(projection):
    """Stable semantic view. Never suppress objects/facets to fit a fixture."""
    def term(row):
        return {'id': row['id'], 'span': row['span'], 'surface': row['surface'], 'display_level': row['display_level'],
                'children': row['children'], 'composition_alternatives': row['composition_alternatives'],
                'semantic_candidates': sorted(
                    [{'expression': item['expression'], 'status': item['status'], 'rule_id': item['rule_id']}
                     for item in row['semantic_candidates']], key=lambda c: (c['rule_id'] or '', c['expression']))}
    def construction(row):
        return {'id': row['id'], 'span': row['span'], 'surface': row['surface'],
                'construction_kind': row['construction_kind'], 'public_kind': row['public_kind'],
                'parse_status': row['parse_status'],
                **{key: row[key] for key in ('origin', 'rule_id', 'proposal') if key in row},
                'slots': [{key: slot[key] for key in ('name', 'surface', 'span')
                           if key in slot}
                          for slot in row['slots']]}
    def step(row):
        result = {key: row[key] for key in ('id', 'source_spans', 'operation', 'construction_ids', 'judgment') if key in row}
        result['inputs'] = [{key: value for key, value in item.items() if key != 'value_id'} for item in row['inputs']]
        result['outputs'] = [{key: value for key, value in output.items()
                              if key != 'value_id'} for output in row['outputs']]
        return result
    def flow(row):
        result = {key: row.get(key) for key in ('id', 'formal', 'consumer_step_ids', 'status', 'producer_step_id',
                                               'producer_source', 'selected_port', 'output_port')}
        if result['producer_source'] is not None:
            result['producer_source'] = {key: result['producer_source'][key] for key in (
                'source_id', 'unit_id', 'doc_id', 'reading_id', 'sections', 'source_spans', 'basis')
                if key in result['producer_source']}
        return result
    facets = [{'object_id': row['object_id'], 'facet': row['facet'], 'status': row['status']}
              for row in projection['review_facets']]
    # Sorting may normalize serialization, but must never hide canonical duplicates.
    stable_links = [{key: value for key, value in link.items() if key != 'evidence'} for link in projection['links']]
    relation_order = {'has_component': 0, 'fills_slot': 1, 'realizes': 2, 'names_output': 3}
    stable_links.sort(key=lambda row: (relation_order.get(row['relation'], 4), row['relation'],
                                      row['from_id'], row['to_id'], row.get('role', ''), row.get('ordinal', -1)))
    step_positions = {row['id']: min(span[0] for span in row['source_spans']) for row in projection['steps']}
    flow_positions = {row['id']: min((step_positions[ident] for ident in row['consumer_step_ids']), default=float('inf'))
                      for row in projection['flows']}
    positions = {row['id']: row['span'][0] for layer in ('terms', 'constructions') for row in projection[layer]}
    positions.update(step_positions)
    positions.update(flow_positions)
    layers = {row['id']: i for i, layer in enumerate(('terms', 'constructions', 'steps', 'flows'))
              for row in projection[layer]}
    facets.sort(key=lambda row: (positions[row['object_id']], layers[row['object_id']], row['facet'],
                                 row['object_id'], row['status']))
    return {'source': {key: projection['source'][key] for key in ('source_id', 'unit_id', 'doc_id', 'reading_id', 'text')},
            'terms': [term(row) for row in sorted(projection['terms'], key=lambda r: (r['span'][0], -r['span'][1], r['id']))],
            'constructions': [construction(row) for row in sorted(projection['constructions'], key=lambda r: (*r['span'], r['id']))],
            'steps': [step(row) for row in sorted(projection['steps'], key=lambda r: (
                step_positions[r['id']], max(span[1] for span in r['source_spans']), r['id']))],
            'flows': [flow(row) for row in sorted(projection['flows'], key=lambda r: (flow_positions[r['id']], r['id']))],
            'review_facets': facets, 'links': stable_links}


def _diff_view(projection):
    """Extend the existing semantic view with interaction facts, not native IR."""
    view = stable_golden_view(projection)
    for layer in ('terms', 'constructions', 'steps', 'flows'):
        native = {row['id']: row for row in projection[layer]}
        for row in view[layer]:
            raw = native[row['id']]
            row['decision_refs'] = sorted(deepcopy(raw.get('decision_refs', [])),
                                          key=lambda ref: (ref['decision_id'], ref.get('action') or ''))
            if layer == 'terms':
                claims = []
                for record in raw.get('reviewed_claims', []):
                    claim = record.get('claim', {})
                    item = {key: deepcopy(claim[key]) for key in ('schema', 'origin', 'branch_id', 'expression') if key in claim}
                    item['decision_id'] = record.get('decision_id')
                    item['target'] = _semantic_identity(record.get('target', claim.get('anchor')))
                    # Rejection snapshots expose the rejected meaning. Opaque
                    # candidate IDs and bundle hashes do not identify a meaning.
                    if claim.get('candidate_snapshots'):
                        item['rejected_candidates'] = sorted(
                            [{'expression': snapshot['expression'], 'rule_id': snapshot.get('rule_id')}
                             for snapshot in claim['candidate_snapshots']], key=lambda r: json.dumps(r, sort_keys=True))
                    claims.append(item)
                row['reviewed_claims'] = sorted(claims, key=lambda r: json.dumps(r, sort_keys=True))
                row['composition_alternatives'] = sorted(row['composition_alternatives'])
            elif layer == 'constructions':
                row['slots'] = sorted(row['slots'], key=lambda slot: slot['name'])
            elif layer == 'steps':
                row['inputs'] = sorted(row['inputs'], key=lambda item: item['role'])
                row['outputs'] = sorted(row['outputs'], key=lambda item: item['port'])
            elif layer == 'flows':
                row['consumer_step_ids'] = sorted(row['consumer_step_ids'])
    view['review_facets'] = [{
        'facet_key': row['facet_key'], 'object_id': row['object_id'], 'facet': row['facet'],
        'related_object_ids': sorted(row.get('related_object_ids', [])), 'status': row['status'],
        'has_question': row.get('question_id') is not None,
        'decision_id': row.get('decision_id'), 'action': row.get('action'),
    } for row in projection['review_facets']]
    return view


def diff_scholar_source(before, after, *, trigger=None):
    """Pure comparison of two scholar snapshots; trigger never becomes provenance."""
    source_fields = ('source_id', 'unit_id', 'doc_id', 'reading_id', 'text')
    if any(before['source'].get(key) != after['source'].get(key) for key in source_fields):
        raise ValueError('scholar_diff_source_changed')
    if trigger is not None and (not isinstance(trigger, dict) or trigger.get('mode') not in (
            'trial', 'saved', 'retracted', 'management', 'context')):
        raise ValueError('scholar_diff_invalid_trigger')
    old, new = _diff_view(before), _diff_view(after)

    def identity(layer, row):
        if layer == 'review_facets':
            return row['facet_key']
        if layer == 'links':
            return 'link:' + json.dumps([row.get(key) for key in (
                'relation', 'from_id', 'to_id', 'role', 'ordinal')], ensure_ascii=False, separators=(',', ':'))
        return row['id']

    def index(layer, rows):
        result = {}
        for row in rows:
            key = identity(layer, row)
            if key in result:
                raise ValueError('scholar_diff_duplicate_identity:' + key)
            result[key] = row
        return result

    def fields(left, right, path=''):
        if left == right:
            return []
        if isinstance(left, dict) and isinstance(right, dict):
            changes = []
            for key in sorted(left.keys() | right.keys()):
                child = path + '.' + key if path else key
                if key not in left or key not in right:
                    changes.append({'path': child, 'before': deepcopy(left.get(key)), 'after': deepcopy(right.get(key))})
                else:
                    changes.extend(fields(left[key], right[key], child))
            return changes
        return [{'path': path, 'before': deepcopy(left), 'after': deepcopy(right)}]

    layers, count = {}, 0
    for layer in ('terms', 'constructions', 'steps', 'flows', 'review_facets', 'links'):
        left, right = index(layer, old[layer]), index(layer, new[layer])
        added = [deepcopy(right[key]) for key in sorted(right.keys() - left.keys())]
        removed = [deepcopy(left[key]) for key in sorted(left.keys() - right.keys())]
        changed = []
        for key in sorted(left.keys() & right.keys()):
            changes = fields(left[key], right[key])
            if changes:
                changed.append({'key' if layer in ('review_facets', 'links') else 'id': key,
                                'changed_fields': changes})
        layers[layer] = {'added': added, 'removed': removed, 'changed': changed}
        count += len(added) + len(removed) + len(changed)
    old_derived = {a['id']: a for a in before.get('derived_assertions', [])}
    new_derived = {a['id']: a for a in after.get('derived_assertions', [])}
    resolved_terms = {a['target'].get('object_id') for a in new_derived.values() if a['kind'] == 'term'}
    automatic = {f['question_id'] for f in before['review_facets'] if f.get('question_id')
                 and f['facet'] == 'term_meaning' and f['object_id'] in resolved_terms
                 and not any(n.get('question_id') == f['question_id'] for n in after['review_facets'])}
    return {'schema': 'ScholarSourceDiff/1',
            'source': {key: after['source'].get(key) for key in source_fields if key != 'text'},
            'trigger': deepcopy(trigger), 'layers': layers, 'summary': {'semantic_change_count': count,
                'derived_assertions_added': len(new_derived.keys() - old_derived.keys()),
                'derived_assertions_removed': len(old_derived.keys() - new_derived.keys()),
                'derived_interpretations_added': sum(new_derived[i]['kind'] == 'term' for i in new_derived.keys() - old_derived.keys()),
                'questions_resolved_automatically': len(automatic)}}


def project_annotations(packet, compilation, questions, decisions=(), decision_status=None):
    """Compatibility view for the current Inspector, derived from ScholarSourceProjection/1."""
    projection = project_scholar_source(packet, compilation, questions, decisions, decision_status)
    objects = {row['id']: row for row in [*projection['terms'], *projection['constructions']]}
    contexts = {question['id']: question.get('machine_context', {}) for question in questions}
    rows = {}
    for facet in projection['review_facets']:
        object_row = objects.get(facet['object_id'])
        if not object_row:
            continue
        anchor = object_row.get('source_anchor') or object_row['source_anchors'][0]
        key = anchor_key(anchor)
        row = rows.setdefault(key, {'id': 'annotation:' + str(key), 'display_anchor': anchor,
                                    'evidence_anchors': [anchor], 'facets': [], 'machine_context': {}})
        reviewed_runtime = facet.get('action') == 'declare_parameter' and facet['status'] == 'reviewed'
        row['facets'].append({'id': facet.get('question_id') or facet['facet_key'],
                              'facet': facet['facet'], 'status': facet['status'],
                              'label': ('Runtime value permitted for standalone numerical check.'
                                        if reviewed_runtime else facet['facet'].replace('_', ' ')),
                              'question_id': facet.get('question_id')})
        context = contexts.get(facet.get('question_id'), {})
        if row['machine_context'].get('source_status') == 'runtime value permitted':
            context = {key: value for key, value in context.items() if key != 'source_status'}
        row['machine_context'].update(context)
        if reviewed_runtime:
            row['machine_context']['source_status'] = 'runtime value permitted'
    for row in rows.values():
        row['facets'].sort(key=lambda facet: (facet['facet'], facet['status'], facet['id']))
        row['evidence_anchors'] = _unique(row['evidence_anchors'])
    return sorted(rows.values(), key=lambda row: (row['display_anchor']['doc_id'], row['display_anchor']['start']))
