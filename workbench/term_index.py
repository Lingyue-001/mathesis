"""Read-only lexical index derived only from ScholarSourceProjection/1."""
from copy import deepcopy
import json
from pathlib import Path


_SOURCE_IDENTITY_FIELDS = ('source_id', 'unit_id', 'doc_id', 'reading_id')
_OCCURRENCE_IDENTITY_FIELDS = (*_SOURCE_IDENTITY_FIELDS, 'start', 'end')
_ROLES = {'maximal', 'component'}
_OCCURRENCE_LOCAL_FIELDS = (
    'semantic_candidates',
    'reviewed_claims',
    'semantic_assertions',
    'derived_assertions',
    'semantic_conflicts',
    'decision_refs',
    'review_facets',
    'evidence',
)


def _require(mapping, fields, error):
    if not isinstance(mapping, dict) or any(mapping.get(field) is None for field in fields):
        raise ValueError(error)


def _source_identity(source):
    _require(source, _SOURCE_IDENTITY_FIELDS, 'term_index_requires_projection_source_identity')
    return {field: deepcopy(source[field]) for field in _SOURCE_IDENTITY_FIELDS}


def _occurrence(projection_source, source, row):
    anchor = row.get('source_anchor') if isinstance(row, dict) else None
    _require(anchor, ('doc_id', 'reading_id', 'start', 'end', 'offset_unit'),
             'term_index_requires_unicode_source_anchor')
    start, end = anchor['start'], anchor['end']
    text = source.get('text') if isinstance(source, dict) else None
    if (anchor['doc_id'] != projection_source['doc_id']
            or anchor['reading_id'] != projection_source['reading_id']
            or anchor['offset_unit'] != 'unicode_code_point'
            or not isinstance(start, int) or isinstance(start, bool)
            or not isinstance(end, int) or isinstance(end, bool)
            or start < 0 or end <= start
            or not isinstance(text, str) or end > len(text)):
        raise ValueError('term_index_requires_unicode_source_anchor')
    if row.get('display_level') not in _ROLES:
        raise ValueError('term_index_requires_term_display_level')
    if not isinstance(row.get('surface'), str):
        raise ValueError('term_index_requires_term_surface')
    if not isinstance(row.get('id'), str):
        raise ValueError('term_index_requires_projection_term_id')
    identity = {**projection_source, 'start': start, 'end': end}
    occurrence = {
        'identity': identity,
        'surface': row['surface'],
        'display_level': row['display_level'],
        'projection_term_id': row['id'],
        'source_anchor': deepcopy(anchor),
    }
    for field in _OCCURRENCE_LOCAL_FIELDS:
        if field in row:
            occurrence[field] = deepcopy(row[field])
    return occurrence


def _identity_key(identity):
    return tuple(identity[field] for field in _OCCURRENCE_IDENTITY_FIELDS)


def _source_identity_key(identity):
    return tuple(identity[field] for field in _SOURCE_IDENTITY_FIELDS)


def _child_ids(row):
    links = row.get('children', [])
    alternatives = row.get('composition_alternatives', [])
    if not isinstance(links, list) or not isinstance(alternatives, list):
        raise ValueError('term_index_requires_composition_links')
    children = list(links)
    for alternative in alternatives:
        if not isinstance(alternative, list):
            raise ValueError('term_index_requires_composition_links')
        children.extend(alternative)
    if not all(isinstance(child, str) for child in children):
        raise ValueError('term_index_requires_composition_links')
    return set(children)


def build_term_index(projections):
    """Build a deterministic, side-effect-free `TermIndex/1` mapping."""
    admitted = []
    sources = []
    occurrences_by_key = {}
    direct_parents = {}
    seen_sources = set()
    for projection in projections:
        if not isinstance(projection, dict) or projection.get('schema') != 'ScholarSourceProjection/1':
            raise ValueError('term_index_requires_scholar_source_projection_v1')
        source = projection.get('source')
        identity = _source_identity(source)
        source_key = _source_identity_key(identity)
        if source_key in seen_sources:
            raise ValueError('term_index_duplicate_projection_source_identity')
        seen_sources.add(source_key)
        sources.append(deepcopy(source))
        rows = projection.get('terms', [])
        if not isinstance(rows, list):
            raise ValueError('term_index_requires_projection_terms_list')
        terms = {}
        for row in rows:
            occurrence = _occurrence(identity, source, row)
            occurrence_key = _identity_key(occurrence['identity'])
            if row['id'] in terms or occurrence_key in occurrences_by_key:
                raise ValueError('term_index_requires_unique_projection_terms')
            terms[row['id']] = (row, occurrence, occurrence_key)
            occurrences_by_key[occurrence_key] = occurrence
            admitted.append(occurrence)
        for row, parent, parent_key in terms.values():
            for child_id in _child_ids(row):
                if child_id not in terms:
                    raise ValueError('term_index_unresolved_composition_child')
                child_key = terms[child_id][2]
                direct_parents.setdefault(child_key, set()).add(parent_key)

    entries = {}
    for occurrence in admitted:
        entry = entries.setdefault(occurrence['surface'], {
            'surface': occurrence['surface'],
            'occurrences': [],
            'direct_parent_occurrences': [],
            'compound_ancestor_occurrences': [],
        })
        entry['occurrences'].append(occurrence)

    result_entries = []
    for surface in sorted(entries):
        entry = entries[surface]
        entry['occurrences'].sort(key=lambda row: _identity_key(row['identity']))
        direct = set()
        ancestors = set()
        for occurrence in entry['occurrences']:
            occurrence_key = _identity_key(occurrence['identity'])
            immediate = direct_parents.get(occurrence_key, set())
            direct.update(immediate)
            pending = list(immediate)
            while pending:
                parent_key = pending.pop()
                if parent_key in ancestors:
                    continue
                ancestors.add(parent_key)
                pending.extend(direct_parents.get(parent_key, set()))
        entry['direct_parent_occurrences'] = [
            deepcopy(occurrences_by_key[key]['identity']) for key in sorted(direct)
        ]
        entry['compound_ancestor_occurrences'] = [
            deepcopy(occurrences_by_key[key]['identity']) for key in sorted(ancestors)
        ]
        roles = {row['display_level'] for row in entry['occurrences']}
        entry['occurrence_classification'] = 'both' if roles == _ROLES else next(iter(roles), 'maximal')
        entry['counts'] = {
            'maximal_occurrences': sum(row['display_level'] == 'maximal' for row in entry['occurrences']),
            'component_occurrences': sum(row['display_level'] == 'component' for row in entry['occurrences']),
            'appears_in_compounds': len(ancestors),
        }
        result_entries.append(entry)

    sources.sort(key=lambda source: tuple(source[field] for field in _SOURCE_IDENTITY_FIELDS))
    return {'schema': 'TermIndex/1', 'sources': sources, 'entries': result_entries}


def serialize_term_index(index):
    """Return deterministic, readable UTF-8 JSON for an existing index."""
    if not isinstance(index, dict) or index.get('schema') != 'TermIndex/1':
        raise ValueError('term_index_serializer_requires_v1')
    return json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def export_term_index(index, path):
    """Write an already-built index only to the caller-selected destination."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize_term_index(index), encoding='utf-8', newline='\n')
    return target
