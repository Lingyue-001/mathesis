"""Pure, source-grounded display records for ScholarSourceProjection/1.

This module deliberately has no compiler, parser, Kernel, or review-job calls.
It turns the already canonical projection into small records that the Workbench
source component can draw and select.
"""
from copy import deepcopy

from analysis_parser.construction_ir import RULES
from analysis_parser.ontology import entry as ontology_entry, label_en
from source_adapters.corpus import _load_effective_index
from workbench.question_presenter import expression_label


_FACET_LABELS = {
    'semantic_conflict': 'conflict',
    'term_meaning': 'meaning?',
    'term_boundary': 'meaning?',
    'quantity_meaning': 'count?',
    'source_supply': 'source?',
    'source_context': 'context?',
    'construction_context_requirement': 'context?',
}
_FLOW_STATUS = {
    'unresolved_source': 'unresolved',
    'ambiguous_source': 'unresolved',
    'linked_source': 'linked historical source',
    'runtime_value_permitted': 'runtime value',
}
# Bounded presentation mapping keyed by the *registered* pattern, not raw text.
# Tuple: operation literal-part index; exact canonical slot roles.
_STEP_LAYOUT = {
    ('置{value:a}減{decrement:n}', 'load'): (0, {'value': 'input'}),
    ('置{value:a}減{decrement:n}', 'subtract'): (2, {}),
    ('置{value:a}', 'load'): (0, {'value': 'input'}),
    ('以{left:a}乘{right:a}', 'multiply'): (2, {'left': 'left', 'right': 'right'}),
    ('又以{left:a}乘{right:a}', 'multiply'): (2, {'left': 'left', 'right': 'right'}),
    ('每以{left:a}乘{right:a}', 'multiply'): (2, {'left': 'left', 'right': 'right'}),
    ('餘以{left:a}乘{right:a}', 'multiply'): (2, {'left': 'left', 'right': 'right'}),
    ('{value:o}滿{divisor:a}得一', 'divmod'): (1, {'value': 'dividend', 'divisor': 'divisor'}),
    ('{value:o}盈{divisor:a}得一', 'divmod'): (1, {'value': 'dividend', 'divisor': 'divisor'}),
    ('{value:o}{lower:n}以上', 'threshold'): (2, {'lower': 'lower bound'}),
}


def ontology_hover(category, code):
    """Read authored terminology; missing definitions are explicit, not invented."""
    try:
        record = ontology_entry(category, code)
    except ValueError:
        record = {}
    label = record.get('label_en') or code
    definition = record.get('definition_en') or record.get('definition')
    return category.capitalize() + ' · ' + label + '\n' + (definition or 'No authored description registered')


def pack_lanes(rows):
    """Assign the first non-overlapping source lane, deterministically."""
    ends = []
    packed = []
    for row in sorted(rows, key=lambda item: (item['span'][0], item['span'][1], item['id'])):
        start, end = row['span']
        lane = next((index for index, lane_end in enumerate(ends) if lane_end <= start), len(ends))
        if lane == len(ends):
            ends.append(end)
        else:
            ends[lane] = end
        packed.append({**deepcopy(row), 'lane': lane})
    return packed


def _label_expression(expression):
    if not isinstance(expression, dict):
        return None
    try:
        return expression_label(expression)
    except (KeyError, TypeError):
        # Projection keeps a human-readable expression when the existing
        # finite QuestionPresenter vocabulary does not cover this proposal.
        return None


def _reviewed_expression(term):
    for record in term.get('reviewed_claims', []):
        claim = record.get('claim', record)
        expression = claim.get('expression') if isinstance(claim, dict) else None
        label = _label_expression(expression)
        if label:
            return label
    return None


def _term_gloss(term):
    if term.get('semantic_conflicts'):
        return {'kind': 'conflicted', 'label': 'Conflicting semantic evidence'}
    reviewed = _reviewed_expression(term)
    if reviewed:
        return {'kind': 'reviewed', 'label': reviewed}
    for assertion in term.get('derived_assertions', []):
        if assertion['kind'] == 'term' and assertion['facet'] == 'expression':
            return {'kind': 'derived', 'label': _label_expression(assertion['value']) or 'Registered interpretation'}
    candidates = [row for row in term.get('semantic_candidates', [])
                  if row.get('status') not in ('rejected', 'incompatible')]
    labels = []
    for candidate in candidates:
        label = _label_expression(candidate.get('structured_expression'))
        if label and label not in labels:
            labels.append(label)
    if labels:
        # The source line reports a set, never a ranked recommendation.
        return {'kind': 'suggestions', 'label': labels[0] if len(labels) == 1 else f'{len(labels)} suggestions',
                'labels': labels}
    return {'kind': 'unresolved', 'label': 'unresolved'}


def _term_hover(term):
    gloss = _term_gloss(term)
    if gloss['kind'] in ('reviewed', 'derived', 'conflicted'):
        text = {'reviewed': 'Reviewed interpretation', 'derived': 'Derived interpretation', 'conflicted': 'Conflict'}[gloss['kind']] + '\n' + gloss['label']
    elif len(gloss.get('labels', [])) > 1:
        text = str(len(gloss['labels'])) + ' machine suggestions\n' + '\n'.join('• ' + s for s in gloss['labels'])
    else:
        text = ('Machine suggestion\n' if gloss['kind'] == 'suggestions' else '') + gloss['label']
    return term['surface'] + '\n' + text


def _badges(facets, questions=None):
    rows = []
    for facet in sorted(facets, key=lambda row: (row['facet'], row['facet_key'])):
        label = _FACET_LABELS.get(facet['facet'])
        if not label:
            continue
        if facet['status'] != 'pending':
            label = label.rstrip('?') + (' ✓' if facet['status'] == 'reviewed' else ' · rejected')
        question = (questions or {}).get(facet.get('question_id'), {})
        hover = question.get('title')
        if not hover:
            actions = sorted({r['action'] for r in facet.get('decision_refs', []) if r.get('action')})
            hover = facet['status'].capitalize() + ' · ' + facet['facet'].replace('_', ' ')
            if actions:
                hover += ' · ' + ', '.join(actions)
        rows.append({'object_id': facet['object_id'], 'facet_key': facet['facet_key'], 'facet': facet['facet'], 'status': facet['status'],
                     'hover': hover,
                     'question_id': facet.get('question_id'), 'label': label,
                     'related_object_ids': list(facet.get('related_object_ids', []))})
    return rows


def _registered_rule(production_id):
    if not isinstance(production_id, str):
        return None
    for index, rule in enumerate(RULES):
        kind, _public_kind, _pattern, parts = rule
        if production_id == f'G_{kind.upper()}_{index}':
            return rule
    return None


def _production_parts(step, construction):
    """Return literal spans only when registered grammar plus slot spans prove them.

    The helper intentionally receives neither source text nor parsing utilities:
    it can only place literals that lie exactly between canonical slot spans.
    """
    if not construction or construction.get('id') not in step.get('construction_ids', []):
        return None
    rule = _registered_rule(construction.get('production_id'))
    if rule is None:
        return None
    _lowering, _public_kind, pattern, parts = rule
    mapping = _STEP_LAYOUT.get((pattern, step.get('operation')))
    if mapping is None:
        return None
    slots = {row['name']: row['span'] for row in construction.get('slots', [])
             if isinstance(row.get('span'), list) and len(row['span']) == 2}
    cursor = construction['span'][0]
    grounded = []
    for part in parts:
        if isinstance(part, str):
            end = cursor + len(part)
            if end > construction['span'][1]:
                return None
            grounded.append([cursor, end])
            cursor = end
            continue
        name, slot_type = part
        span = slots.get(name)
        if span is None:
            if slot_type == 'o':
                grounded.append(None)
                continue
            return None
        if span[0] != cursor or span[1] < span[0] or span[1] > construction['span'][1]:
            return None
        grounded.append(span)
        cursor = span[1]
    if cursor != construction['span'][1]:
        return None
    return grounded, mapping


def production_operation_cue(step, construction):
    result = _production_parts(step, construction)
    return ({'status': 'precise', 'spans': [result[0][result[1][0]]]} if result
            else {'status': 'unavailable', 'spans': []})


def step_presentation(step, construction):
    """Compact operation/role tokens; missing grounding stays broad, explicitly."""
    result = _production_parts(step, construction)
    if result is None:
        return [{'label': step['operation'], 'span': span, 'role': 'operation',
                 'alignment': 'broad'} for span in step.get('source_spans', [])]
    grounded, (cue_index, role_slots) = result
    cue_span = list(grounded[cue_index])
    label = step['operation']
    if label == 'divmod':
        label = ontology_entry('operation', 'divmod')['label_en'].lower()
    elif label == 'threshold':
        label = 'test ≥'
    slots = {r['name']: r for r in construction.get('slots', [])}
    if step['operation'] == 'subtract' and 'decrement' in slots:
        cue_span[1] = slots['decrement']['span'][1]
        operand = next((r['literal'] for r in step.get('inputs', []) if r.get('role') == 'right'
                        and 'literal' in r), None)
        label += ' ' + str(operand if operand is not None else slots['decrement'].get('surface', ''))
    rows = [{'label': label, 'span': cue_span, 'role': 'operation', 'alignment': 'precise'}]
    for slot_name, role in role_slots.items():
        slot = slots.get(slot_name)
        if slot and slot.get('span'):
            prior = any(r.get('role') == slot_name and r.get('from_step_id') for r in step.get('inputs', []))
            display = 'previous result' if prior else ('operand' if role in ('left', 'right') else role)
            rows.append({'label': display, 'span': list(slot['span']),
                         'role': role, 'alignment': 'precise'})
    if step['operation'] == 'divmod':
        rows.append({'label': 'quotient cue', 'span': list(grounded[-1]),
                     'role': 'quotient', 'alignment': 'precise'})
    return rows


def corpus_search_hints(root, source_id, formal):
    """Exact effective-corpus occurrences for display only; never create links."""
    if not source_id or not formal:
        return []
    _source, index = _load_effective_index(root, source_id)
    from source_adapters.corpus_index import source_review_evidence
    evidence = source_review_evidence(index, formal)
    return [*evidence['declarations'], *evidence['occurrences']]


def _step_span(step):
    spans = step.get('source_spans', [])
    if not spans:
        return None
    return [min(span[0] for span in spans), max(span[1] for span in spans)]


def build_renderer_model(packet, projection, questions, *, root=None):
    """Derive renderer-only records from an existing Scholar projection."""
    if projection.get('schema') != 'ScholarSourceProjection/1':
        raise ValueError('scholar_renderer_requires_projection_v1')
    facets = {}
    question_index = {r['id']: r for r in questions}
    for row in projection.get('review_facets', []):
        facets.setdefault(row['object_id'], []).append(row)
    terms = []
    for row in projection.get('terms', []):
        object_facets = _badges(facets.get(row['id'], []), question_index)
        gloss = _term_gloss(row)
        if gloss['kind'] in ('derived', 'conflicted'):
            object_facets.append({'object_id': row['id'], 'facet_key': None, 'facet': 'term_meaning',
                'status': gloss['kind'], 'hover': _term_hover(row), 'question_id': None,
                'label': 'derived' if gloss['kind'] == 'derived' else 'conflict', 'related_object_ids': []})
        terms.append({**deepcopy(row), 'id': row['id'], 'span': list(row['span']), 'surface': row['surface'],
                      'gloss': _term_gloss(row), 'hover': _term_hover(row), 'badges': object_facets, 'facets': object_facets,
                      'decision_refs': deepcopy(row.get('decision_refs', []))})
    constructions = []
    by_construction = {row['id']: row for row in projection.get('constructions', [])}
    for row in projection.get('constructions', []):
        fixed = row.get('origin') == 'domain_kernel_fixed_expression'
        object_facets = _badges(facets.get(row['id'], []), question_index)
        constructions.append({**deepcopy(row), 'id': row['id'], 'span': list(row['span']), 'surface': row['surface'],
                              'construction_kind': row['construction_kind'], 'public_kind': row.get('public_kind'),
                              'hover': ontology_hover('construction', row['construction_kind']),
                              'slots': deepcopy(row.get('slots', [])), 'badges': object_facets, 'facets': object_facets,
                              'decision_refs': deepcopy(row.get('decision_refs', [])),
                              'adjudication': 'suggested_read_only' if fixed else None,
                              'label': ('suggested · read-only in current adjudication schema' if fixed
                                        else row.get('public_kind') or row['construction_kind'])})
    constructions = pack_lanes(constructions)
    steps = []
    for row in projection.get('steps', []):
        span = _step_span(row)
        if span is None:
            continue
        supporting = [by_construction[item] for item in row.get('construction_ids', []) if item in by_construction]
        precise = [item for item in supporting if _production_parts(row, item) is not None]
        # A Judgment may support the same threshold Step, but cannot displace
        # the one registered threshold cue. Multiple precise cues stay broad.
        construction = precise[0] if len(precise) == 1 else None
        cue = production_operation_cue(row, construction) if construction else {'status': 'unavailable', 'spans': []}
        object_facets = _badges(facets.get(row['id'], []), question_index)
        steps.append({**deepcopy(row), 'id': row['id'], 'span': span, 'operation': row['operation'],
                      'construction_ids': list(row.get('construction_ids', [])), 'inputs': deepcopy(row.get('inputs', [])),
                      'hover': ontology_hover('operation', row['operation']),
                      'outputs': deepcopy(row.get('outputs', [])), 'cue': cue,
                      'badges': object_facets, 'facets': object_facets,
                      'presentation': step_presentation(row, construction),
                      'decision_refs': deepcopy(row.get('decision_refs', []))})
    flows = []
    for row in projection.get('flows', []):
        item = {**deepcopy(row), 'id': row['id'], 'formal': row['formal'], 'status': row['status'],
                'display_status': _FLOW_STATUS.get(row['status'], row['status']),
                'producer_source': deepcopy(row.get('producer_source')), 'badges': _badges(facets.get(row['id'], []), question_index),
                'decision_refs': deepcopy(row.get('decision_refs', [])), 'search_hints': []}
        flows.append(item)
    objects = {row['id']: row for layer in (terms, constructions, steps, flows) for row in layer}
    bridges = deepcopy(projection.get('review_facets', []))
    return {'schema': 'ScholarRendererModel/1', 'source': deepcopy(projection['source']),
            'terms': [r for r in terms if r.get('display_level') != 'component'],
            'constructions': constructions, 'steps': steps, 'flows': flows,
            'objects': objects, 'facets': bridges, 'questions': {r['id']: deepcopy(r) for r in questions},
            'links': deepcopy(projection.get('links', [])), 'semantic_closure': deepcopy(projection.get('semantic_closure', {}))}


def procedure_context(model, object_id):
    """Local construction/step cluster, joined only by recorded projection IDs.

    Close construction-realization edges only. Input producers are displayed as
    references, not recursively expanded into the entire upstream procedure.
    """
    objects, links = model['objects'], model['links']
    terms = {ident for ident, row in objects.items() if row.get('kind') == 'term' or 'gloss' in row}
    constructions = {row['id'] for row in model['constructions']}
    steps = {row['id'] for row in model['steps']}
    flows = {row['id'] for row in model['flows']}
    tids, cids, sids, fids = ({object_id} & pool for pool in (terms, constructions, steps, flows))
    # Selecting a component follows its recorded parent, never its source span.
    tids.update(link['from_id'] for link in links
                if link['relation'] == 'has_component' and link['to_id'] == object_id)
    cids.update(link['to_id'] for link in links
                if link['relation'] == 'fills_slot' and link['from_id'] in tids)
    cids.update(c['id'] for c in model['constructions']
                if any(slot.get('linked_term_id') in tids for slot in c.get('slots', [])))
    for step in model['steps']:
        if (any(i.get('term_id') in tids or i.get('flow_id') in fids for i in step.get('inputs', []))
                or any(tids.intersection(o.get('label_term_ids', [])) for o in step.get('outputs', []))):
            sids.add(step['id'])
    for flow in model['flows']:
        if flow['id'] in fids:
            sids.update(flow.get('consumer_step_ids', []))
            if flow.get('producer_step_id') in steps:
                sids.add(flow['producer_step_id'])
    edges = {(link['from_id'], link['to_id']) for link in links if link['relation'] == 'realizes'}
    edges.update((cid, step['id']) for step in model['steps'] for cid in step.get('construction_ids', []))
    while True:
        before = (set(cids), set(sids))
        for cid, sid in edges:
            if cid in cids or sid in sids:
                cids.add(cid); sids.add(sid)
        if before == (cids, sids):
            break
    for step in model['steps']:
        if step['id'] in sids:
            tids.update(i.get('term_id') for i in step.get('inputs', []))
            fids.update(i.get('flow_id') for i in step.get('inputs', []))
            for output in step.get('outputs', []):
                tids.update(output.get('label_term_ids', []))
    # Naming constructions belong to these output Terms, without following
    # other uses of those Terms to unrelated operations.
    cids.update(link['to_id'] for link in links if link['relation'] == 'fills_slot'
                and link.get('role') == 'label' and link['from_id'] in tids)
    for construction in model['constructions']:
        if construction['id'] in cids:
            tids.update(slot.get('linked_term_id') for slot in construction.get('slots', []))
    fids.update(f['id'] for f in model['flows'] if sids.intersection(f.get('consumer_step_ids', []))
                or f.get('producer_step_id') in sids)
    return {'terms': [row for ident, row in objects.items() if ident in tids & terms],
            'constructions': [c for c in model['constructions'] if c['id'] in cids],
            'steps': [s for s in model['steps'] if s['id'] in sids],
            'flows': [f for f in model['flows'] if f['id'] in fids]}


_SELECTED_SOURCE_SECTIONS = (
    ('terms', 'Term', 'What technical expression is identified here, and what might it mean?',
     'No technical term is directly associated with this selection.'),
    ('constructions', 'Construction', 'How is the source expression structured, and what roles do its parts play?',
     'No textual construction is directly associated with this selection.'),
    ('steps', 'Computational step', 'What operation does this construction represent, with which inputs and outputs?',
     'No computational step is directly associated with this selection.'),
    ('flows', 'Quantity flow', 'Where do the quantities come from, and how do they depend on other steps?',
     'No quantity dependency is directly associated with this selection.'),
)


def _display_label(category, identity):
    """Use only an authored ontology label; otherwise expose the display gap."""
    try:
        return {'label': label_en(category, identity), 'identity': identity}
    except (KeyError, ValueError):
        return {'label': 'Display gap for review', 'identity': identity}


def _object_reference(objects, ident):
    row = objects.get(ident)
    if row is None:
        return {'label': 'Display gap for review', 'identity': ident}
    if row.get('surface'):
        return {'label': row['surface'], 'identity': ident}
    if row.get('formal'):
        return {'label': row['formal'], 'identity': ident}
    if row.get('operation'):
        return _display_label('operation', row['operation'])
    return {'label': 'Display gap for review', 'identity': ident}


def selected_source_object_sections(model, object_id):
    """Frozen four-layer display records from canonical projection relations only."""
    objects = model['objects']
    context = procedure_context(model, object_id)
    links = model['links']
    construction_by_id = {row['id']: row for row in context['constructions']}

    terms = []
    for row in context['terms']:
        parts = [_object_reference(objects, link['to_id']) for link in links
                 if link['relation'] == 'has_component' and link['from_id'] == row['id']]
        suggestions = []
        for candidate in row.get('semantic_candidates', []):
            label = _label_expression(candidate.get('structured_expression'))
            suggestions.append({'label': label or 'Display gap for review',
                                'identity': candidate.get('candidate_id')})
        gloss = row.get('gloss', {})
        terms.append({'id': row['id'], 'selected': row['id'] == object_id, 'surface_form': row.get('surface'),
                      'composition': parts, 'machine_suggestions': suggestions,
                      'reviewed_interpretation': gloss.get('label') if gloss.get('kind') == 'reviewed' else None})

    constructions = []
    for row in context['constructions']:
        roles = []
        for link in links:
            if link['relation'] == 'fills_slot' and link['to_id'] == row['id']:
                roles.append({'role': _display_label('port', link.get('role')),
                              'value': _object_reference(objects, link['from_id'])})
        slots = [{'role': _display_label('port', slot.get('name')), 'surface': slot.get('surface')}
                 for slot in row.get('slots', [])]
        linked_steps = [_object_reference(objects, link['to_id']) for link in links
                        if link['relation'] == 'realizes' and link['from_id'] == row['id']]
        constructions.append({'id': row['id'], 'selected': row['id'] == object_id,
                              'source_expression': row.get('surface'),
                              'construction_type': _display_label('construction', row.get('construction_kind')),
                              'roles': roles, 'slots': slots, 'linked_steps': linked_steps})

    steps = []
    for row in context['steps']:
        inputs = []
        associated = [construction_by_id[ident] for ident in row.get('construction_ids', [])
                      if ident in construction_by_id]
        for item in row.get('inputs', []):
            source_slots = [slot['surface'] for construction in associated
                            for slot in construction.get('slots', [])
                            if slot.get('name') == item.get('role') and slot.get('surface')]
            source_form = source_slots[0] if len(source_slots) == 1 else None
            input_row = {'role': _display_label('port', item.get('role')),
                         'normalized_value': item.get('literal'), 'source_form': source_form,
                         'source_form_gap': bool(item.get('literal') is not None and source_form is None)}
            if item.get('term_id'):
                input_row['value'] = _object_reference(objects, item['term_id'])
            elif item.get('from_step_id'):
                input_row['value'] = _object_reference(objects, item['from_step_id'])
                input_row['from'] = _object_reference(objects, item['from_step_id'])
            elif item.get('surface_reference'):
                input_row['value'] = {'label': item['surface_reference'], 'identity': None}
            inputs.append(input_row)
        outputs = []
        for output in row.get('outputs', []):
            labels = [_object_reference(objects, ident) for ident in output.get('label_term_ids', [])]
            outputs.append({'role': _display_label('port', output.get('port')), 'labels': labels,
                            'identity': output.get('value_id')})
        steps.append({'id': row['id'], 'selected': row['id'] == object_id,
                      'operation': _display_label('operation', row.get('operation')),
                      'inputs': inputs, 'outputs': outputs})

    flows = []
    for row in context['flows']:
        producer = (_object_reference(objects, row['producer_step_id'])
                    if row.get('producer_step_id') else None)
        consumers = [_object_reference(objects, ident) for ident in row.get('consumer_step_ids', [])]
        source = row.get('producer_source') or {}
        historical = ('§' + ', §'.join(map(str, source['sections'])) if source.get('sections') else None)
        flows.append({'id': row['id'], 'selected': row['id'] == object_id, 'identity': row.get('formal'),
                      'status': row.get('display_status'), 'producer': producer, 'consumers': consumers,
                      'historical_source': historical})

    items = {'terms': terms, 'constructions': constructions, 'steps': steps, 'flows': flows}
    return [{'key': key, 'title': title, 'description': description, 'empty': empty, 'items': items[key]}
            for key, title, description, empty in _SELECTED_SOURCE_SECTIONS]


def selection_details(model, object_id, facet_key=None, *, root=None):
    """One-hop canonical relations and explicit inputs/outputs, scoped to selection."""
    objects = model['objects']
    selected = objects.get(object_id)
    own_facets = [f for f in model['facets'] if f['object_id'] == object_id]
    facet = next((f for f in own_facets if f['facet_key'] == facet_key), None)
    result = {'selected': selected, 'facet': facet, 'facets': _badges(own_facets),
              'composition': [], 'uses': [], 'naming': [], 'named_outputs': [],
              'steps': [], 'flows': [], 'source_assistance': None, 'context_requirement': None,
              'procedure_context': procedure_context(model, object_id)}
    if selected is None:
        return result
    result['facets'] = _badges(own_facets, model['questions'])
    step_ids = set()
    for link in model['links']:
        relation, origin, target = link['relation'], link['from_id'], link['to_id']
        if origin == object_id and relation == 'has_component' and target in objects:
            result['composition'].append(objects[target])
        if origin == object_id and relation == 'fills_slot' and target in objects:
            entry = {'construction': objects[target], 'role': link.get('role')}
            if link.get('role') == 'label':
                result['naming'].append(objects[target])
            else:
                result['uses'].append(entry)
        if origin == object_id and relation == 'realizes':
            step_ids.add(target)
    if 'operation' in selected:
        step_ids.add(object_id)
    for step in model['steps']:
        if any(r.get('term_id') == object_id for r in step.get('inputs', [])):
            step_ids.add(step['id'])
        for output in step.get('outputs', []):
            if object_id in output.get('label_term_ids', []):
                result['named_outputs'].append({'step': step, 'port': output['port']})
    result['steps'] = [r for r in model['steps'] if r['id'] in step_ids]
    from .semantic_presentation import provenance_blocks
    # Quantity evidence is explicitly separate from the selected Term's meaning.
    result['semantic_provenance'] = provenance_blocks(model.get('semantic_closure', {}),
        {object_id, *step_ids}, objects)
    result['semantic_diagnostics'] = [deepcopy(d) for d in model.get('semantic_closure', {}).get('unresolved', [])
                                     if d['target'].get('object_id') in {object_id, *step_ids}]
    # Only immediate supply dependencies of the selected term/step/construction.
    flow_ids = {r['flow_id'] for step in result['steps'] for r in step.get('inputs', [])
                if r.get('flow_id') and (selected.get('kind') != 'term' or r.get('term_id') == object_id)}
    if facet and facet['facet'] == 'source_supply':
        flow_ids.update(facet.get('related_object_ids', []))
        if object_id in {r['id'] for r in model['flows']}:
            flow_ids.add(object_id)
    result['flows'] = [r for r in model['flows'] if r['id'] in flow_ids]
    if facet and facet['facet'] == 'construction_context_requirement':
        key = facet.get('semantic_key', {})
        result['context_requirement'] = {'cause': key.get('cause'), 'missing_inputs': key.get('missing_inputs', [])}
    if facet and facet['facet'] == 'source_supply':
        question = model['questions'].get(facet.get('question_id'), {})
        candidates = [{'label': option['label'], 'evidence': deepcopy(option.get('payload', {}))}
                      for option in question.get('options', []) if option.get('action') == 'bind_value']
        evidence = question.get('source_review')
        hints = [*evidence['declarations'], *evidence['occurrences']] if evidence else []
        if evidence is None and root is not None:
            for flow in result['flows']:
                hints.extend(corpus_search_hints(root, model['source'].get('source_id'), flow['formal']))
        result['source_assistance'] = {'candidates': deepcopy(candidates),
            'registered': [r for r in hints if r['strength'] == 'registered'],
            'other': [r for r in hints if r['strength'] == 'hint']}
    return result
