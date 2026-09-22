"""Shared authored labels for compiled semantic evidence, without inference."""
from collections import defaultdict
import json

from workbench.question_presenter import expression_label


FACET_LABELS = {'unit': 'Unit', 'scale': 'Scale', 'quantity_kind': 'Quantity kind',
    'representation': 'Representation', 'coordinate_kind': 'Coordinate', 'index_base': 'Base',
    'step_unit': 'Step unit', 'reference_origin': 'Origin', 'counting_boundary': 'Counting boundary'}


def assertion_label(assertion):
    value = assertion['value']
    if assertion['facet'] == 'expression':
        try:
            return expression_label(value)
        except (KeyError, TypeError, ValueError):
            return 'Registered interpretation'
    if isinstance(value, dict):
        value = ', '.join(str(v).replace('_', ' ') for v in value.values())
    return FACET_LABELS.get(assertion['facet'], assertion['facet']) + ': ' + str(value).replace('_', ' ')


def semantic_summary(assertions):
    usable = [a for a in assertions if a['usable']]
    if not usable:
        return ''
    preferred = [a for a in usable if a['facet'] in ('expression', 'coordinate_kind', 'unit')]
    labels = list(dict.fromkeys(assertion_label(a) for a in preferred))
    states = list(dict.fromkeys(a['authority'] for a in usable))
    return ' · '.join(labels[:2] + states)


def provenance_blocks(closure, object_ids, objects):
    index = {a['id']: a for a in closure.get('assertions', [])}
    groups = defaultdict(list)
    for a in index.values():
        if a['target'].get('object_id') in object_ids:
            key = (a['kind'], json.dumps(a['target'], sort_keys=True), a['authority'], a['rule_id'], a['usable'])
            groups[key].append(a)
    result = []
    for rows in groups.values():
        order = {'expression': 0, 'coordinate_kind': 1, 'index_base': 2, 'unit': 3, 'step_unit': 4}
        rows.sort(key=lambda a: (order.get(a['facet'], 5), a['facet']))
        first = rows[0]
        state = first['authority'].capitalize()
        title = state + (' interpretation' if first['kind'] == 'term' else ' quantity properties')
        if not first['usable']:
            title += ' · unresolved / conflict'
        dependencies, seen = [], set()
        for row in rows:
            for dep in row['depends_on']:
                ref = index.get(dep.get('id')) if dep['kind'] == 'assertion' else None
                object_id = ref['target'].get('object_id') if ref else dep.get('object_id')
                owner = objects.get(object_id, {})
                if ref:
                    text = ref['authority'].capitalize() + ': ' + assertion_label(ref)
                elif dep['kind'] == 'registered_rule':
                    text = closure.get('rules', {}).get(dep['id'], 'Registered semantic rule')
                elif dep['kind'] == 'review_decision':
                    text = 'Recorded human decision'
                else:
                    text = owner.get('surface') or owner.get('operation') or dep.get('operation', 'Canonical graph fact')
                    if dep.get('port'):
                        text += ' · ' + dep['port'].replace('_', ' ')
                key = (text, object_id)
                if key not in seen:
                    seen.add(key)
                    dependencies.append({'label': text, 'object_id': object_id,
                        'source_anchors': (ref.get('source_anchors', []) if ref else dep.get('source_anchors', []))})
        # Several facets of one upstream quantity are one navigable dependency.
        grouped_dependencies = {}
        for dep in dependencies:
            if dep.get('object_id') and dep['label'].startswith(('Derived:', 'Reviewed:')):
                key = (dep['object_id'], dep['label'].split(':', 1)[0])
                if key in grouped_dependencies:
                    grouped_dependencies[key]['facet_count'] += 1
                else:
                    grouped_dependencies[key] = dict(dep, facet_count=1)
            else:
                grouped_dependencies[(dep['label'], dep.get('object_id'))] = dep
        for dep in grouped_dependencies.values():
            if dep.get('facet_count', 1) > 1:
                dep['label'] += ' (+' + str(dep['facet_count'] - 1) + ' properties)'
        target = first['target']
        target_label = ('Input · ' if target['kind'] == 'input_port' else 'Output · ') + target.get('port', '') if first['kind'] == 'quantity' else ''
        result.append({'title': title, 'target_label': target_label,
                       'label': ' · '.join(dict.fromkeys(assertion_label(a) for a in rows)),
                       'dependencies': list(grouped_dependencies.values()), 'evidence': rows, 'rule_id': first['rule_id']})
    return sorted(result, key=lambda r: (r['evidence'][0]['kind'] != 'term',
        r['evidence'][0]['target']['kind'] == 'input_port', r['title'], r['label']))
