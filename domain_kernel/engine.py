"""Source-grounded, typed term suggestions over the existing lexical/syntax APIs.

Only the candidate projection of the review2 registry is consumed. No compiler,
execution, adjudication, scoped facts or evaluation resources are imported.
"""
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unicodedata

from analysis_parser import inputs, lexical, construction_ir, syntax_ir

HERE = Path(__file__).resolve().parent
VIEW_KEYS = ('schema_version', 'sources', 'concepts', 'lexical_cues', 'constructors',
             'composition_rules', 'fixed_expressions', 'relations', 'projection_contracts')
PRECONDITIONS = ('same_reading', 'ordered_adjacent_spans', 'nominal_term_region', 'typed_arguments')


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _json(value):
    # Dictionary order is immaterial. Array order, especially children, is not.
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _digest(value):
    return hashlib.sha256(_json(value).encode('utf-8')).hexdigest()


def _read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def _keyed(rows, name):
    result = {r['id']: r for r in rows}
    _require(len(rows) == len(result), 'duplicate_id:' + name)
    return result


def _sort(expression, concepts, constructors):
    op = expression.get('op')
    if op == 'concept':
        _require(set(expression) == {'op', 'concept_id'}, 'concept_fields')
        _require(expression['concept_id'] in concepts, 'concept_reference:unknown')
        family = concepts[expression['concept_id']]['family']
        return {'quantity_concept': 'quantity_expression', 'scope_concept': 'scope_expression'}.get(family, 'semantic_expression')
    if op == 'unknown':
        _require(set(expression) == {'op', 'source_text', 'sort'} and
                 isinstance(expression['source_text'], str) and expression['source_text'] and
                 expression['sort'] == 'semantic_expression', 'opaque_sort:overclaim')
        return 'semantic_expression'
    _require(op in constructors, 'constructor_reference:unknown')
    _require(set(expression) == {'op', 'arguments'}, 'constructor_fields')
    contract = constructors[op]
    arguments = expression['arguments']
    _require(set(arguments) == set(contract['arguments']), 'constructor_arguments:' + op)
    for name, expected in contract['arguments'].items():
        actual = _sort(arguments[name], concepts, constructors)
        _require(expected == 'semantic_expression' or actual == expected, 'constructor_sort:' + op + ':' + name)
    return contract['result_sort']


def _registry_view(registry):
    view = deepcopy({key: registry[key] for key in VIEW_KEYS})
    _require(view['schema_version'] == '0.1.0-review2', 'registry_version')
    maps = {key: _keyed(view[key], key) for key in VIEW_KEYS[1:-1]}
    concepts, constructors, sources = maps['concepts'], maps['constructors'], maps['sources']
    allowed_ops = {e['properties']['op']['const'] for e in _read('kernel.schema.json')['$defs']['Expression']['oneOf']}
    for c in concepts.values():
        _require(set(c['parent_ids']) <= concepts.keys(), 'concept_parent:unknown')
    def visit(ident, stack):
        _require(ident not in stack, 'concept_hierarchy:cycle')
        for parent in concepts[ident]['parent_ids']:
            visit(parent, stack | {ident})
    for ident in concepts:
        visit(ident, set())
    for cue in maps['lexical_cues'].values():
        _require(bool(cue['form']) and bool(cue['sense_concept_ids']) and
                 set(cue['sense_concept_ids']) <= concepts.keys(), 'cue_sense:unknown')
    sorts = {'semantic_expression', 'quantity_expression', 'scope_expression'}
    for ctor in constructors.values():
        _require(ctor['id'] in allowed_ops and ctor['result_sort'] in sorts and
                 set(ctor['arguments'].values()) <= sorts, 'constructor_contract')
        _require(ctor['relation_kind'] in maps['relations'], 'constructor_relation:unknown')
    for rule in maps['composition_rules'].values():
        _require(rule['effect'] == 'propose_candidate', 'rule:authority_escalation')
        _require(set(rule['preconditions']) == set(PRECONDITIONS), 'rule:unknown_precondition')
        _require(len(rule['pattern']) >= 2, 'rule:non_expanding_pattern')
        variables = {}
        for part in rule['pattern']:
            if part['kind'] == 'cue':
                _require(part['cue_id'] in maps['lexical_cues'], 'rule:unknown_cue')
            else:
                _require(part['kind'] == 'variable' and part['name'] not in variables and part['sort'] in sorts, 'rule:variable')
                variables[part['name']] = part['sort']
        build = rule['build']
        _require(build['op'] in constructors, 'rule:unknown_constructor')
        _require(set(build['arguments_from']) == set(constructors[build['op']]['arguments']), 'rule:constructor_slots')
        for slot, value in build['arguments_from'].items():
            _require(value.startswith('$') and value[1:] in variables, 'rule:unbound_variable')
            required = constructors[build['op']]['arguments'][slot]
            _require(required == 'semantic_expression' or variables[value[1:]] == required, 'rule:variable_sort')
    for key in ('concepts', 'lexical_cues', 'composition_rules', 'fixed_expressions'):
        for row in view[key]:
            _require(set(row.get('evidence_ids', [])) <= sources.keys(), 'provenance_reference:unknown')
    for fixed in view['fixed_expressions']:
        _require(fixed['effect'] == 'propose_candidate' and bool(fixed['form']), 'fixed_expression:contract')
    return view


def load_kernel(registry_path=None):
    """Return a fresh, validated candidate-only projection of the registry."""
    path = Path(registry_path) if registry_path is not None else HERE / 'kernel.registry.json'
    try:
        return _registry_view(json.loads(path.read_text(encoding='utf-8')))
    except (KeyError, TypeError) as error:
        raise ValueError('registry_shape:' + str(error)) from error


def _document(doc):
    _require(isinstance(doc['text'], str), 'source_text')
    _require(doc['actual_sha256'] == hashlib.sha256(doc['text'].encode('utf-8')).hexdigest(), 'source_hash:mismatch')
    text, mapping = doc['analysis_text'], doc['analysis_to_source']
    _require(len(text) == len(mapping) and all(type(p) is int for p in mapping), 'analysis_mapping:length')
    _require(all(0 <= p < len(doc['text']) for p in mapping) and
             all(a < b for a, b in zip(mapping, mapping[1:])), 'analysis_mapping:order')
    _require(''.join(doc['text'][p] for p in mapping) == text, 'analysis_mapping:text')


def _anchor(doc, a, b):
    # Reuse the existing span implementation; the shared SourceAnchor has a
    # closed set of fields, so editorial extras remain in the original doc.
    span = inputs.span(doc, a, b)
    return {key: span[key] for key in ('doc_id', 'reading_id', 'start', 'end', 'quote')} | {'source_sha256': doc['actual_sha256']}


def _check_anchor(anchor, doc):
    _require(set(anchor) == {'doc_id', 'reading_id', 'source_sha256', 'start', 'end', 'quote'}, 'source_anchor:fields')
    _require(all(anchor[k] == doc[k] for k in ('doc_id', 'reading_id')) and
             anchor['source_sha256'] == doc['actual_sha256'], 'source_identity:reading_or_hash')
    a, b = anchor['start'], anchor['end']
    _require(type(a) is int and type(b) is int and 0 <= a < b <= len(doc['text']), 'source_range:bounds')
    _require(doc['text'][a:b] == anchor['quote'], 'source_quote:mismatch')


def _continuous(doc, a, b):
    mapping = doc['analysis_to_source']
    return all(not doc['text'][x+1:y] or doc['text'][x+1:y].isspace()
               for x, y in zip(mapping[a:b], mapping[a+1:b]))


def _analysis_range(anchor, doc):
    _check_anchor(anchor, doc)
    indices = [i for i, p in enumerate(doc['analysis_to_source']) if anchor['start'] <= p < anchor['end']]
    _require(bool(indices), 'region:no_analysis_characters')
    return [indices[0], indices[-1] + 1]


def _span_at(doc, a, b):
    mapping = doc['analysis_to_source']
    return _anchor(doc, mapping[a], mapping[b-1] + 1)


def _regions(doc, syntax, explicit):
    regions = {}
    def add(span, analysis_range, basis, origins):
        row = {'span': span, 'analysis_range': analysis_range, 'basis': basis, 'origins': origins}
        row['id'] = 'region:' + _digest(row)
        regions[row['id']] = row
    for source in explicit:
        add(deepcopy(source), _analysis_range(source, doc), 'explicit_selection', [])
    nodes = {n['id']: n for n in syntax['nodes']}
    grouped = defaultdict(list)
    for parent in syntax['nodes']:
        for slot, ident in parent['slots'].items():
            node = nodes[ident]
            if node['kind'] == 'Term' and node['analysis_range'][0] < node['analysis_range'][1]:
                grouped[tuple(node['analysis_range'])].append({'parent_id': parent['id'], 'slot': slot, 'node_id': ident})
    for (a, b), origins in sorted(grouped.items()):
        add(_span_at(doc, a, b), [a, b], 'grammar_candidate', sorted(origins, key=_json))
    return sorted(regions.values(), key=lambda r: (r['analysis_range'], r['basis'], r['id']))


def _identity(doc, registry, max_candidates):
    return {'doc_id': doc['doc_id'], 'reading_id': doc['reading_id'], 'source_sha256': doc['actual_sha256'],
            'registry_sha256': _digest(registry),
            'schema_sha256': _digest([_read('kernel.schema.json'), _read('output.schema.json')]),
            'engine_sha256': hashlib.sha256(Path(__file__).read_bytes() + (HERE/'__init__.py').read_bytes()).hexdigest(),
            'dependency_hashes': {module.__name__: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                                  for module in (inputs, lexical, construction_ir, syntax_ir)},
            'options': {'max_candidates': max_candidates}}


def _candidate_id(node, identity):
    return 'term:' + _digest({'identity': identity, 'node': {k: v for k, v in node.items() if k != 'id'}})


def _rule_expression(rule, children, concepts, constructors):
    _require(len(rule['pattern']) == len(children), 'rule_arity:mismatch')
    variables = {}
    for part, child in zip(rule['pattern'], children):
        if part['kind'] == 'cue':
            _require(child['method'] == 'cue' and child['cue_id'] == part['cue_id'], 'rule_cue:mismatch')
        else:
            actual = _sort(child['expression'], concepts, constructors)
            _require(part['sort'] == 'semantic_expression' or actual == part['sort'], 'rule_sort:mismatch')
            variables[part['name']] = child['expression']
    result = {'op': rule['build']['op'], 'arguments': {
        key: deepcopy(variables[value[1:]]) for key, value in rule['build']['arguments_from'].items()}}
    _sort(result, concepts, constructors)
    return result


def suggest_term_semantics(doc, *, registry=None, term_regions=(), max_candidates=1024):
    """Generate suggestions without mutating documents, registry or native IR."""
    _document(doc)
    _require(type(max_candidates) is int and max_candidates > 0, 'max_candidates:positive_integer')
    registry = load_kernel() if registry is None else _registry_view(registry)
    concepts = _keyed(registry['concepts'], 'concepts')
    constructors = _keyed(registry['constructors'], 'constructors')
    cues = sorted(registry['lexical_cues'], key=lambda r: r['id'])
    tokens = lexical.tokenize_candidates(doc, [cue['form'] for cue in cues])
    syntax = construction_ir.parse_syntax(tokens, doc).to_dict()
    regions = _regions(doc, syntax, term_regions)
    identity = _identity(doc, registry, max_candidates)
    identity['options']['term_regions'] = sorted((deepcopy(r) for r in term_regions), key=_json)
    out = {'schema': 'TermSemanticCandidates/1', 'identity': identity, 'candidates': [],
           'fixed_expression_candidates': [], 'regions': regions, 'diagnostics': [],
           'truncated': False, 'syntax_preview': syntax}
    if not regions:
        out['diagnostics'].append({'kind': 'missing_term_region', 'reason': 'No nominal syntax slot or explicit term selection.'})
    text = doc['analysis_text']
    seen, by_start = {}, defaultdict(list)
    cue_chars = set(''.join(c['form'] for c in cues))
    blocking = lexical.BOUNDARY - cue_chars
    def safe(a, b):
        return _continuous(doc, a, b) and all(ch not in blocking and not unicodedata.category(ch).startswith('P') for ch in text[a:b])
    def owners(a, b):
        return [r['id'] for r in regions if r['analysis_range'][0] <= a < b <= r['analysis_range'][1]]
    def room():
        if len(out['candidates']) + len(out['fixed_expression_candidates']) < max_candidates:
            return True
        out['truncated'] = True
        return False
    def add(a, b, method, expression, *, cue=None, rule=None, children=()):
        owned = owners(a, b)
        evidence = set((cue or rule or {}).get('evidence_ids', []))
        for child in children:
            evidence.update(child['provenance_ids'])
        checks = {p: 'compatible' for p in PRECONDITIONS}
        if not owned:
            checks['nominal_term_region'] = 'underdetermined'
        node = {'span': _span_at(doc, a, b), 'method': method, 'cue_id': cue['id'] if cue else None,
                'rule_id': rule['id'] if rule else None, 'child_ids': [c['id'] for c in children],
                'expression': expression, 'claim_authority': 'S', 'provenance_ids': sorted(evidence),
                'support_status': 'proposed', 'constraint_status': 'compatible' if owned else 'underdetermined',
                'authorization_status': 'not_authorized', 'authorization_refs': [], 'analysis_range': [a, b],
                'region_ids': owned, 'generated_by': 'domain_kernel:' + identity['engine_sha256'], 'precondition_checks': checks}
        node['id'] = _candidate_id(node, identity)
        if node['id'] in seen:
            return
        if room():
            seen[node['id']] = node
            by_start[a].append(node)
            out['candidates'].append(node)
    edges = {(t['start'], t['end'], t['text']) for t in tokens if t['kind'] == 'Term'}
    covered = set()
    for a, b, surface in sorted(edges):
        if not safe(a, b):
            continue
        for cue in cues:
            if surface == cue['form']:
                covered.update(range(a, b))
                for sense in cue['sense_concept_ids']:
                    add(a, b, 'cue', {'op': 'concept', 'concept_id': sense}, cue=cue)
    # Opaque components are unrecognised runs inside existing term regions,
    # not a free-standing sentence tokenizer and not invented quantity types.
    opaque_ranges = set()
    for region in regions:
        a, end = region['analysis_range']
        while a < end:
            if a in covered or not safe(a, a+1):
                a += 1
                continue
            b = a + 1
            while b < end and b not in covered and safe(a, b+1):
                b += 1
            opaque_ranges.add((a, b)); a = b
    for a, b in sorted(opaque_ranges):
        add(a, b, 'opaque_component', {'op': 'unknown', 'source_text': _span_at(doc, a, b)['quote'], 'sort': 'semantic_expression'})
    # Bottom-up chart: each child is strictly shorter than its parent. The
    # same matcher interprets every rule, including recursive combinations.
    def intervals():
        # Do not materialize a quadratic set, especially after leaf truncation.
        # Region overlap is harmless: add() deduplicates the actual derivation.
        if out['truncated']:
            return
        bounds = sorted({tuple(r['analysis_range']) for r in regions})
        for width in range(2, max((b-a for a, b in bounds), default=0)+1):
            for start, end in bounds:
                for a in range(start, end-width+1):
                    yield a, a+width
    for a, b in intervals():
        if out['truncated']:
            break
        if not safe(a, b):
            continue
        for rule in sorted(registry['composition_rules'], key=lambda r: r['id']):
            def paths(index, position, children):
                if index == len(rule['pattern']):
                    if position == b:
                        yield children
                    return
                part = rule['pattern'][index]
                for child in list(by_start[position]):
                    end = child['analysis_range'][1]
                    if end > b or end - position >= b - a:
                        continue
                    if part['kind'] == 'cue':
                        good = child['method'] == 'cue' and child['cue_id'] == part['cue_id']
                    else:
                        good = part['sort'] == 'semantic_expression' or _sort(child['expression'], concepts, constructors) == part['sort']
                    if good:
                        yield from paths(index+1, end, children+[child])
            for children in paths(0, a, []):
                expression = _rule_expression(rule, children, concepts, constructors)
                add(a, b, 'composition', expression, rule=rule, children=children)
                if out['truncated']:
                    break
    for fixed in sorted(registry['fixed_expressions'], key=lambda r: r['id']):
        for a in range(len(text)):
            b = a + len(fixed['form'])
            if not text.startswith(fixed['form'], a) or not _continuous(doc, a, b):
                continue
            node = {'span': _span_at(doc, a, b), 'analysis_range': [a, b], 'rule_id': fixed['id'],
                    'proposes': fixed['proposes'], 'alternative_group': 'alternative:' + _digest(_span_at(doc, a, b)),
                    'claim_authority': 'S', 'support_status': 'proposed', 'constraint_status': 'underdetermined',
                    'authorization_status': 'not_authorized', 'authorization_refs': [],
                    'provenance_ids': fixed['evidence_ids'], 'precondition_checks': {fixed['required_context']: 'underdetermined'},
                    'generated_by': 'domain_kernel:' + identity['engine_sha256']}
            node['id'] = _candidate_id(node, identity)
            if room():
                out['fixed_expression_candidates'].append(node)
    if out['truncated']:
        out['diagnostics'].append({'kind': 'candidate_limit', 'reason': 'Candidate limit reached; alternatives may be missing.', 'limit': max_candidates})
    out['candidates'].sort(key=lambda n: (n['analysis_range'], n['method'], n['id']))
    # This syntax was just computed from the source, so generation can validate
    # its region references without running the grammar a second time.
    _validate_term_bundle(out, doc, registry, trusted_syntax=syntax)
    return out


def validate_term_bundle(bundle, doc, *, registry=None):
    """Validate runtime contracts; custom registries are supplied explicitly.

    Full JSON Schema validation is a separate offline development check. This
    stdlib validator checks source identity, rule derivation and permissions.
    """
    try:
        _validate_term_bundle(bundle, doc, load_kernel() if registry is None else _registry_view(registry))
    except (KeyError, TypeError, IndexError, AttributeError, RecursionError) as error:
        raise ValueError('bundle_shape:' + str(error)) from error


def _validate_term_bundle(bundle, doc, registry, trusted_syntax=None):
    _document(doc)
    _require(set(bundle) == {'schema', 'identity', 'candidates', 'fixed_expression_candidates', 'regions', 'diagnostics', 'truncated', 'syntax_preview'}, 'bundle_fields')
    _require(bundle['schema'] == 'TermSemanticCandidates/1', 'bundle_schema')
    ident = bundle['identity']
    expected = _identity(doc, registry, ident['options']['max_candidates'])
    _require(set(ident) == set(expected) and all(ident[k] == v for k, v in expected.items() if k != 'options'), 'bundle_identity:mismatch')
    _require(set(ident['options']) == {'max_candidates', 'term_regions'}, 'options_fields')
    _require(type(ident['options']['max_candidates']) is int and ident['options']['max_candidates'] > 0, 'max_candidates:positive_integer')
    for region in ident['options']['term_regions']:
        _check_anchor(region, doc)
    if trusted_syntax is None:
        tokens = lexical.tokenize_candidates(doc, [cue['form'] for cue in registry['lexical_cues']])
        trusted_syntax = construction_ir.parse_syntax(tokens, doc).to_dict()
    _require(bundle['syntax_preview'] == trusted_syntax, 'region_syntax_preview:mismatch')
    expected_regions = _regions(doc, trusted_syntax, ident['options']['term_regions'])
    _require(bundle['regions'] == expected_regions, 'region_provenance:mismatch')
    regions = _keyed(bundle['regions'], 'regions')
    for region in regions.values():
        _check_anchor(region['span'], doc)
        _require(region['analysis_range'] == _analysis_range(region['span'], doc), 'region_analysis_range')
        _require(region['basis'] in ('explicit_selection', 'grammar_candidate'), 'region_basis')
        _require(region['id'] == 'region:' + _digest({k: v for k, v in region.items() if k != 'id'}), 'region_identity')
    maps = {key: _keyed(registry[key], key) for key in ('concepts', 'constructors', 'lexical_cues', 'composition_rules', 'fixed_expressions', 'sources')}
    nodes = _keyed(bundle['candidates'], 'candidates')
    fields = set(_read('kernel.schema.json')['$defs']['SemanticCandidate']['properties'])
    def common(node):
        _check_anchor(node['span'], doc)
        a, b = node['analysis_range']
        _require(type(a) is int and type(b) is int and 0 <= a < b <= len(doc['analysis_text']), 'analysis_range:bounds')
        _require(node['span'] == _span_at(doc, a, b) and _continuous(doc, a, b), 'candidate_source_mapping')
        _require((node['support_status'], node['claim_authority'], node['authorization_status'], node['authorization_refs']) ==
                 ('proposed', 'S', 'not_authorized', []), 'candidate:authority_escalation')
        _require(node['generated_by'] == 'domain_kernel:' + ident['engine_sha256'], 'candidate_generator')
        _require(set(node['provenance_ids']) <= maps['sources'].keys(), 'candidate_provenance:unknown')
        _require(node['id'] == _candidate_id(node, ident), 'candidate_identity:mismatch')
    for node in nodes.values():
        _require(set(node) == fields, 'candidate_fields')
        common(node)
        _sort(node['expression'], maps['concepts'], maps['constructors'])
        a, b = node['analysis_range']
        expected_regions = [r['id'] for r in bundle['regions'] if r['analysis_range'][0] <= a < b <= r['analysis_range'][1]]
        _require(node['region_ids'] == expected_regions, 'candidate_regions')
        checks = {p: 'compatible' for p in PRECONDITIONS}
        if not expected_regions:
            checks['nominal_term_region'] = 'underdetermined'
        _require(node['precondition_checks'] == checks and node['constraint_status'] ==
                 ('compatible' if expected_regions else 'underdetermined'), 'candidate_constraints')
        children = [nodes[c] for c in node['child_ids']]
        _require(len(set(node['child_ids'])) == len(children), 'child_duplicate')
        if node['method'] == 'cue':
            cue = maps['lexical_cues'][node['cue_id']]
            _require(not children and node['rule_id'] is None and doc['analysis_text'][a:b] == cue['form'] and
                     node['expression'].get('concept_id') in cue['sense_concept_ids'], 'cue_sense:mismatch')
            evidence = set(cue.get('evidence_ids', []))
        elif node['method'] == 'opaque_component':
            _require(expected_regions and not children and node['cue_id'] is None and node['rule_id'] is None and
                     node['expression'] == {'op': 'unknown', 'source_text': node['span']['quote'], 'sort': 'semantic_expression'}, 'opaque_contract')
            evidence = set()
        else:
            _require(node['method'] == 'composition' and expected_regions and node['cue_id'] is None, 'composition_contract')
            rule = maps['composition_rules'][node['rule_id']]
            positions = [c['analysis_range'] for c in children]
            _require(positions and positions[0][0] == a and positions[-1][1] == b and
                     all(x[1] == y[0] for x, y in zip(positions, positions[1:])) and
                     all(a <= x < y <= b and y-x < b-a for x, y in positions), 'child_order_or_coverage')
            _require(node['expression'] == _rule_expression(rule, children, maps['concepts'], maps['constructors']), 'rule_build_mismatch')
            evidence = set(rule['evidence_ids']) | {p for c in children for p in c['provenance_ids']}
        _require(node['provenance_ids'] == sorted(evidence), 'candidate_provenance:mismatch')
    fixed_fields = set(_read('output.schema.json')['properties']['fixed_expression_candidates']['items']['properties'])
    fixed_nodes = _keyed(bundle['fixed_expression_candidates'], 'fixed_expression_candidates')
    _require(not nodes.keys() & fixed_nodes.keys(), 'candidate_id_collision')
    for node in fixed_nodes.values():
        _require(set(node) == fixed_fields, 'fixed_expression:fields')
        common(node)
        fixed = maps['fixed_expressions'][node['rule_id']]
        a, b = node['analysis_range']
        _require(doc['analysis_text'][a:b] == fixed['form'] and node['proposes'] == fixed['proposes'], 'fixed_expression:mismatch')
        _require(node['constraint_status'] == 'underdetermined' and node['precondition_checks'] ==
                 {fixed['required_context']: 'underdetermined'}, 'fixed_expression:context')
        _require(node['provenance_ids'] == fixed['evidence_ids'], 'fixed_expression:provenance')
        _require(node['alternative_group'] == 'alternative:' + _digest(node['span']), 'fixed_expression:alternative_group')
    total = len(nodes) + len(bundle['fixed_expression_candidates'])
    _require(total <= ident['options']['max_candidates'], 'candidate_limit:exceeded')
    _require(type(bundle['truncated']) is bool and (not bundle['truncated'] or
                 any(d['kind'] == 'candidate_limit' for d in bundle['diagnostics'])), 'truncation_diagnostic')


def suggest_packet_semantics(packet, *, term_regions=None, registry=None, max_candidates=1024):
    """One independent bundle per reading; duplicate document IDs are errors."""
    docs = inputs.documents(packet)
    _require(len({d['doc_id'] for d in docs}) == len(docs), 'duplicate_doc_id')
    regions = {} if term_regions is None else term_regions
    _require(isinstance(regions, dict) and set(regions) <= {d['doc_id'] for d in docs}, 'term_regions:unknown_doc_id')
    knowledge = load_kernel() if registry is None else _registry_view(registry)
    return {d['doc_id']: suggest_term_semantics(d, registry=knowledge,
             term_regions=regions.get(d['doc_id'], ()), max_candidates=max_candidates) for d in docs}
