"""Source-first, exact Unicode occurrence selection for K2 review."""
from adjudication.anchors import anchor_for, validate_anchor


def selection_anchor(packet, doc_id, selection):
    """Turn an inclusive character gesture into a stable source anchor."""
    if not isinstance(selection, (list, tuple)) or len(selection) != 2:
        raise ValueError('select_a_source_span')
    start, end = selection
    if type(start) is not int or type(end) is not int or start >= end:
        raise ValueError('select_a_nonempty_source_span')
    return anchor_for(packet, doc_id, start, end)


def marks_for_document(packet, doc_id, questions, decisions=(), decision_status=None):
    marks = []
    for row in questions:
        if row.get('display_anchor') and row.get('facets') is not None:
            anchor = row['display_anchor']
            if anchor['doc_id'] != doc_id:
                continue
            facets = row['facets']
            statuses = {facet['status'] for facet in facets}
            state = ('pending' if 'pending' in statuses else 'conflicted' if 'conflicted' in statuses else 'reviewed')
            label = '; '.join(facet['facet'].replace('_', ' ') + ': ' + facet['status'] for facet in facets)
            marks.append({'id': row['id'], 'start': anchor['start'], 'end': anchor['end'],
                          'status': state, 'label': label, 'annotation': row})
            continue
        anchor = row.get('anchor')
        if anchor and anchor['doc_id'] == doc_id:
            marks.append({'id': row['id'], 'start': anchor['start'], 'end': anchor['end'],
                          'status': 'pending', 'label': row.get('title', anchor['quote'])})
    status = decision_status or {}
    for decision in decisions:
        if decision.get('action') in ('retract', 'defer'):
            continue
        state = status.get(decision['decision_id'], {}).get('status', 'active')
        if state == 'retracted':
            continue
        for anchor in decision.get('targets', []):
            if anchor['doc_id'] == doc_id:
                validate_anchor(packet, anchor)
                marks.append({'id': decision['decision_id'], 'start': anchor['start'], 'end': anchor['end'],
                              'status': 'reviewed' if state == 'active' else 'conflicted',
                              'label': anchor['quote']})
    return marks


def source_annotation_component():
    """One component with separate source-glyph and annotation layers."""
    from streamlit.components.v2 import component
    return component(
        'k2_source_annotation',
        html='<div class="source" role="group" aria-label="Source annotation"></div>',
        css=scholar_component_asset('source_annotation', 'css'),
        js=scholar_component_asset('source_annotation', 'mjs'))


def scholar_component_asset(name, suffix):
    """Inline the shared UI helper for Streamlit; files remain ES modules for static use."""
    from pathlib import Path
    assets = Path(__file__).parent
    shared = (assets / ('scholar_ui.' + suffix)).read_text(encoding='utf-8')
    source = (assets / (name + '.' + suffix)).read_text(encoding='utf-8')
    return shared + '\n' + source.replace("import {explainScholarObject} from './scholar_ui.mjs';", '')


def procedure_model_component():
    from streamlit.components.v2 import component
    return component('k2_procedure_model', html='<div class="procedure-model"></div>',
                     css=scholar_component_asset('procedure_model', 'css'),
                     js=scholar_component_asset('procedure_model', 'mjs'))
