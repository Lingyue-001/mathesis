"""Finite, provenance-carrying semantic closure; never a candidate selector.

No parser, Kernel or lexical lookups. The graph and replay-reduced decisions
are inputs only. Quantity facets and occurrence expressions remain distinct.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import json

from analysis_parser.semantic_rules import ordinal_to_elapsed


RULES = {
    'SEM_INPUT_VALUE': 'Exact producer value at this input port',
    'SEM_TERM_SLOT': 'Reviewed interpretation at this exact input',
    'SEM_IDENTITY_LOAD': 'Value-preserving load',
    'SEM_IDENTITY_ALIAS': 'Value-preserving alias',
    'SEM_ORDINAL_TO_ELAPSED': 'One-based ordinal to elapsed coordinate',
    'SEM_NAMES_OUTPUT': 'Exact naming of an interpreted output',
}
FACETS = ('unit', 'scale', 'quantity_kind', 'representation', 'coordinate_kind',
          'index_base', 'step_unit', 'reference_origin', 'counting_boundary')
REQUIRED_COORDINATE = ('coordinate_kind', 'index_base', 'step_unit', 'reference_origin', 'counting_boundary')


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def _id(prefix, value):
    return prefix + sha256(_json(value).encode()).hexdigest()[:24]


def same_anchor(a, b):
    return all(a.get(k) == b.get(k) for k in ('doc_id', 'reading_id', 'start', 'end')) and (
        not a.get('source_sha256') or not b.get('source_sha256') or a['source_sha256'] == b['source_sha256'])


def _value(ident):
    return {'kind': 'quantity', 'value_id': ident}


def _input(event, port):
    return {'kind': 'input_port', 'event_id': event['id'], 'port': port}


def _term(anchor):
    return {'kind': 'term', 'anchor': deepcopy(anchor)}


def _graph_ref(event, port=None):
    return {'kind': 'graph_port' if port else 'graph_event', 'id': event['id'], **({'port': port} if port else {})}


def compute_semantic_closure(graph, effective, *, conflicted_decisions=()):
    """Return SemanticClosure/1 from current active facts, without modifying IR.

    Facts deduplicate by target/facet/value/authority. Positive derivation is
    monotone and finite (identity and one coordinate transformation). Proof
    alternatives are retained; conflicts then quarantine targets and invalidate
    descendants by grounded reachability, so cycles cannot self-support.
    """
    events = sorted(graph.get('events', []), key=lambda r: r['id'])
    by_event = {e['id']: e for e in events}
    values = {v['id']: v for v in graph.get('value_instances', [])}
    candidates = [c for c in graph.get('construction_candidates', []) if c.get('status') == 'selected']
    assertions, diagnostics, rejections = {}, [], []
    effective = deepcopy(effective)
    conflicted_ids = {d['decision_id'] for d in conflicted_decisions}
    for decision in conflicted_decisions:
        row = {**deepcopy(decision['payload']), 'decision_id': decision['decision_id']}
        if decision['action'] == 'set_term_interpretation':
            row['target'] = decision['targets'][0]
            effective.setdefault('term_interpretations', []).append(row)
        elif decision['action'] == 'set_quantity_semantics':
            effective.setdefault('quantity_semantics', {})['conflicted:' + decision['decision_id']] = row

    def diagnostic(reason, target, **extra):
        row = dict(reason=reason, target=deepcopy(target), **deepcopy(extra))
        if row not in diagnostics:
            diagnostics.append(row)

    def add(target, facet, value, authority, rule, dependencies, anchors=()):
        origin = sorted(d['id'] for d in dependencies if d['kind'] == 'review_decision') if authority == 'reviewed' else []
        key = _id('semantic:', [target, facet, value, authority, origin]) if origin else _id('semantic:', [target, facet, value, authority])
        proof = {'rule_id': rule, 'depends_on': sorted(deepcopy(dependencies), key=_json)}
        if rule:
            proof['depends_on'].append({'kind': 'registered_rule', 'id': rule})
        if key not in assertions:
            assertions[key] = dict(schema='SemanticAssertion/1', id=key,
                kind='term' if target['kind'] == 'term' else 'quantity', target=deepcopy(target),
                facet=facet, value=deepcopy(value), authority=authority, status=authority,
                rule_id=rule, depends_on=proof['depends_on'], proofs=[proof],
                source_anchors=deepcopy(list(anchors)), object_refs=[], usable=True)
        elif proof not in assertions[key]['proofs']:
            assertions[key]['proofs'].append(proof)
        if any(d['kind'] == 'review_decision' and d['id'] in conflicted_ids for d in dependencies):
            assertions[key]['status'] = 'conflicted'
            assertions[key]['usable'] = False
        return assertions[key]

    def derive(target, facet, value, rule, premises, event, anchors=()):
        if any(not p['usable'] for p in premises):
            return
        # Disallow circular proof alternatives, even though they cannot seed facts.
        key = _id('semantic:', [target, facet, value, 'derived'])
        if any(p['id'] == key for p in premises):
            return
        return add(target, facet, value, 'derived', rule,
            [{'kind': 'assertion', 'id': p['id']} for p in premises] + [_graph_ref(event)],
            anchors or event.get('source_spans', []))

    def at(target):
        return [a for a in assertions.values() if a['target'] == target and a['usable']]

    # Resolve active quantity reviews from exact syntax and semantic port addresses.
    for row in effective.get('quantity_semantics', {}).values():
        direction = 'input' if row.get('semantic_input') else 'output'
        address = row.get('semantic_' + direction)
        if not address:
            continue  # legacy non-occurrence constraints are not scholarly seeds
        anchor = address.get('construction_anchor', {})
        nodes = {c['node_id'] for c in candidates if any(same_anchor(s, anchor) for s in c.get('source_spans', []))}
        matching = [e for e in events if e.get('syntax_node_id') in nodes
                    and e['kind'] == address.get('semantic_role')]
        port = address.get('input_slot' if direction == 'input' else 'output_port')
        matching = [e for e in matching if port in e.get('reads' if direction == 'input' else 'writes', {})]
        if len(matching) != 1:
            diagnostic('reviewed_quantity_link_not_unique', address, decision_id=row.get('decision_id'))
            continue
        event = matching[0]
        target = _input(event, port) if direction == 'input' else _value(event['writes'][port])
        refs = row.get('decision_refs') or [row.get('decision_id')]
        if not all(refs):
            diagnostic('reviewed_quantity_missing_decision', address)
            continue
        for facet, value in row.get('facets', {}).items():
            if facet in FACETS and value not in (None, 'unknown', 'opaque'):
                add(target, facet, value, 'reviewed', None,
                    [{'kind': 'review_decision', 'id': ref} for ref in refs] + [_graph_ref(event, port)], [anchor])

    # Exact Term occurrence -> an input port, never a shared upstream producer.
    for row in effective.get('term_interpretations', []):
        claim = row['claim']
        anchor = claim['anchor']
        if claim['origin'] == 'machine_rejection':
            for snap in claim.get('candidate_snapshots', []):
                rejections.append((anchor, snap['expression'], row['decision_id']))
            continue
        fact = add(_term(anchor), 'expression', claim['expression'], 'reviewed', None,
                   [{'kind': 'review_decision', 'id': row['decision_id']}], [anchor])
        links = []
        for candidate in candidates:
            for slot, leaf in candidate.get('slots', {}).items():
                if leaf.get('kind') != 'Term' or not any(same_anchor(s, anchor) for s in leaf.get('source_spans', [])):
                    continue
                for event in events:
                    if event.get('syntax_node_id') != candidate['node_id']:
                        continue
                    if candidate['kind'] in ('name', 'remainder_name') and slot == 'label' and event['kind'] == 'alias' and 'result' in event['writes']:
                        links.append((_value(event['writes']['result']), event))
                    elif event['kind'] == candidate['kind'] and slot in event.get('reads', {}):
                        links.append((_input(event, slot), event))
        if len(links) != 1:
            diagnostic('term_graph_link_not_unique', _term(anchor), decision_id=row['decision_id'], match_count=len(links))
        else:
            target, event = links[0]
            derive(target, 'expression', claim['expression'], 'SEM_TERM_SLOT', [fact], event, [anchor])

    def incoming(event, port):
        return at(_input(event, port)) + at(_value(event.get('reads', {}).get(port)))

    # Finite saturation: no new expression constructors or unbounded arithmetic.
    while True:
        size = len(assertions)
        for event in events:
            for port, value_id in event.get('reads', {}).items():
                for fact in list(at(_value(value_id))):
                    derive(_input(event, port), fact['facet'], fact['value'], 'SEM_INPUT_VALUE', [fact], event)
            if event['kind'] in ('load', 'alias') and set(event.get('reads', {})) == {'value'} and set(event.get('writes', {})) == {'result'}:
                rule = 'SEM_IDENTITY_LOAD' if event['kind'] == 'load' else 'SEM_IDENTITY_ALIAS'
                for fact in list(at(_input(event, 'value'))):
                    derive(_value(event['writes']['result']), fact['facet'], fact['value'], rule, [fact], event)
                if event['kind'] == 'alias':
                    names = [c for c in candidates if c['node_id'] == event.get('syntax_node_id') and c['kind'] in ('name', 'remainder_name')]
                    for c in names:
                        anchors = c.get('slots', {}).get('label', {}).get('source_spans', [])
                        if len(anchors) == 1:
                            for fact in list(at(_input(event, 'value'))):
                                if fact['facet'] == 'expression':
                                    derive(_term(anchors[0]), 'expression', fact['value'], 'SEM_NAMES_OUTPUT', [fact], event, anchors)
            if event['kind'] != 'subtract' or set(event.get('reads', {})) != {'left', 'right'} or 'result' not in event.get('writes', {}):
                continue
            right = values.get(event['reads']['right'], {})
            literal = by_event.get(right.get('producer'), {})
            if literal.get('kind') != 'literal' or type(literal.get('attributes', {}).get('value')) is not int:
                continue
            rows = [a for a in at(_input(event, 'left')) if a['facet'] in FACETS]
            grouped = defaultdict(list)
            for fact in rows:
                grouped[fact['facet']].append(fact)
            if not all(k in grouped and len({_json(f['value']) for f in grouped[k]}) == 1 for k in REQUIRED_COORDINATE):
                continue
            coordinate = {k: v[0]['value'] for k, v in grouped.items() if len({_json(f['value']) for f in v}) == 1}
            metadata = values.get(event['reads']['left'], {})
            if metadata.get('unit', 'unknown') not in ('unknown', coordinate['step_unit'], coordinate['step_unit'] + '_ordinal'):
                continue
            if metadata.get('representation', {}).get('kind', 'whole') not in ('whole', 'unknown'):
                continue
            if coordinate.get('unit', coordinate['step_unit']) not in (coordinate['step_unit'], coordinate['step_unit'] + '_ordinal'):
                continue
            if coordinate.get('representation', {}).get('kind', 'whole') != 'whole':
                continue
            transition = ordinal_to_elapsed(coordinate, literal['attributes']['value'])
            if transition:
                for facet, value in transition.items():
                    fact = derive(_value(event['writes']['result']), facet, value, 'SEM_ORDINAL_TO_ELAPSED', rows, event)
                    if fact:
                        # The actual literal port is a proof premise, not prose.
                        ref = _graph_ref(literal, 'result')
                        for proof in fact['proofs']:
                            if ref not in proof['depends_on']:
                                proof['depends_on'].append(ref)
                        fact['depends_on'] = fact['proofs'][0]['depends_on']
        if len(assertions) == size:
            break

    # Contradiction is between positive facts (or an explicit human rejection),
    # never between an incomplete vocabulary and a supported conclusion.
    groups = defaultdict(list)
    for fact in assertions.values():
        groups[(_json(fact['target']), fact['facet'])].append(fact)
    conflicts, blocked = [], set()
    for (target_key, facet), rows in sorted(groups.items()):
        inactive = [r for r in rows if r['status'] == 'conflicted']
        if inactive:
            conflicts.append({'id': _id('conflict:', [target_key, facet, 'replay']), 'target': rows[0]['target'],
                              'facet': facet, 'assertion_ids': sorted(r['id'] for r in inactive), 'reason': 'conflicting_review_decisions'})
        rows = [r for r in rows if r['status'] != 'conflicted']
        distinct = {_json(r['value']) for r in rows}
        if len(distinct) <= 1:
            continue
        if facet == 'expression':
            diagnostic('expression_equivalence_not_registered', rows[0]['target'])
            blocked.add((target_key, facet))
            continue
        conflicts.append({'id': _id('conflict:', [target_key, facet]), 'target': rows[0]['target'],
                          'facet': facet, 'assertion_ids': sorted(r['id'] for r in rows), 'reason': 'incompatible_supported_facets'})
        blocked.add((target_key, facet))
    for anchor, expression, decision in rejections:
        rows = [r for r in assertions.values() if r['kind'] == 'term' and same_anchor(r['target']['anchor'], anchor) and r['value'] == expression]
        if rows:
            blocked.update((_json(r['target']), r['facet']) for r in rows)
            conflicts.append({'id': _id('conflict:', [anchor, decision]), 'target': _term(anchor), 'facet': 'expression',
                              'assertion_ids': [r['id'] for r in rows], 'decision_ids': [decision], 'reason': 'explicit_rejection'})
    depth = {a['id']: 0 for a in assertions.values() if a['authority'] == 'reviewed' and a['status'] != 'conflicted'
             and (_json(a['target']), a['facet']) not in blocked}
    while True:
        before = dict(depth)
        for fact in assertions.values():
            if fact['status'] == 'conflicted' or (_json(fact['target']), fact['facet']) in blocked:
                continue
            for proof in fact['proofs']:
                refs = [d['id'] for d in proof['depends_on'] if d['kind'] == 'assertion']
                if all(ident in depth for ident in refs):
                    candidate_depth = 1 + max((depth[ident] for ident in refs), default=-1)
                    depth[fact['id']] = min(depth.get(fact['id'], candidate_depth), candidate_depth)
        if depth == before:
            break
    for fact in assertions.values():
        fact['usable'] = fact['id'] in depth
        def proof_rank(proof):
            refs = [d['id'] for d in proof['depends_on'] if d['kind'] == 'assertion']
            proof['usable'] = fact['usable'] and all(ident in depth for ident in refs)
            cost = max((depth.get(ident, len(assertions) + 1) for ident in refs), default=-1)
            return (not proof['usable'], cost, _json(proof))
        fact['proofs'].sort(key=proof_rank)
        fact['depends_on'] = fact['proofs'][0]['depends_on']
    # Report unsupported arithmetic semantics using graph identity only.
    for event in events:
        if event['kind'] in ('multiply', 'divide', 'divmod') and any(incoming(event, p) for p in event.get('reads', {})):
            diagnostic('missing_registered_arithmetic_semantic_relation', {'kind': 'graph_event', 'event_id': event['id']}, operation=event['kind'])
    return {'schema': 'SemanticClosure/1', 'assertions': sorted(assertions.values(), key=lambda a: a['id']),
            'conflicts': sorted(conflicts, key=lambda c: c['id']), 'unresolved': sorted(diagnostics, key=_json),
            'rules': deepcopy(RULES)}


def term_resolution(closure, anchor):
    """No candidate inputs: epistemic authority cannot originate in the Kernel."""
    rows = [a for a in closure.get('assertions', []) if a['kind'] == 'term' and same_anchor(a['target']['anchor'], anchor)]
    conflicts = [c for c in closure.get('conflicts', []) if c['target'].get('kind') == 'term' and same_anchor(c['target']['anchor'], anchor)]
    usable = [a for a in rows if a['usable']]
    return {'assertions': rows, 'conflicts': conflicts,
            'resolved': bool(usable) and len({_json(a['value']) for a in usable}) == 1 and not conflicts}
