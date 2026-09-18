"""Deterministic, evaluation-only import of the complete legacy annotation JSON.

No parser imports, passage-specific rules, authored expectations or fuzzy match.
Original objects are preserved; derived interpretations are explicitly partial.
"""
import copy
import hashlib
import re


PUNCTUATION = '，,．。；;：:'
NUMBER = re.compile(r'[零〇一二三四五六七八九十百千萬万]+|[0-9]+')
LABEL = re.compile(r'[\u3400-\u9fff\U00020000-\U0003134f]+|[A-Za-z_][A-Za-z_0-9]*')


def source_document(ident, text):
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    return {'doc_id': ident, 'reading_id': ident + '.' + digest[:12],
            'text': text, 'text_sha256': digest}


def _anchor(doc, start, end):
    return {'doc_id': doc['doc_id'], 'reading_id': doc['reading_id'], 'start': start, 'end': end,
            'quote': doc['text'][start:end], 'offset_unit': 'unicode_code_point'}


def _occurrences(text, needle):
    if not needle:
        return []
    return [m.start() for m in re.finditer('(?=' + re.escape(needle) + ')', text)]


def recover_mention(term, doc):
    """Exact anchor containment first; a suffix may resolve remaining ambiguity.

    Suffix N denotes the Nth exact text occurrence in this chunk, only when it
    also lies in an exact anchor occurrence. A unique anchor match wins without
    assuming every earlier unannotated occurrence was numbered by the author.
    """
    text, context = term.get('text', ''), term.get('anchor', '')
    candidates = {}
    for start in _occurrences(doc['text'], context):
        for offset in _occurrences(context, text):
            candidates[start + offset] = (start, start + len(context))
    suffix = re.search(r'_(\d{3})$', term.get('mention_id', ''))
    if len(candidates) != 1:
        all_positions = _occurrences(doc['text'], text)
        ordinal = int(suffix[1]) if suffix else 0
        selected = all_positions[ordinal - 1] if 0 < ordinal <= len(all_positions) else None
        if selected not in candidates:
            return {'status': 'needs_review', 'reason': 'missing_or_ambiguous_exact_occurrence', 'anchors': []}
        candidates = {selected: candidates[selected]}
    start, (a, b) = next(iter(candidates.items()))
    return {'status': 'resolved', 'anchors': [_anchor(doc, start, start + len(text))],
            'context_anchor': _anchor(doc, a, b), 'occurrence_suffix': suffix[1] if suffix else None}


def _number(text):
    if text.isascii():
        return int(text)
    digits = dict(zip('零〇一二三四五六七八九', [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]))
    if not any(c in '十百千萬万' for c in text):
        return int(''.join(str(digits[c]) for c in text))
    if re.search('[一二三四五六七八九]{2}', text):
        raise ValueError('manual_schema_unparsed: adjacent digits in unit numeral')
    total = block = digit = 0
    previous_unit = 10000
    for c in text:
        if c in digits:
            digit = digits[c]
        elif c in '萬万':
            total += (block + digit) * 10000
            block = digit = 0
            previous_unit = 10000
        else:
            unit = {'十': 10, '百': 100, '千': 1000}[c]
            if unit >= previous_unit:
                raise ValueError('manual_schema_unparsed: numeral unit order')
            block += (digit or 1) * unit
            digit = 0
            previous_unit = unit
    return total + block + digit


def parse_expression(text):
    """Small grammar, never eval(): atoms, value/presence(), comparisons,
    Chinese-semicolon lists and ASCII-semicolon assignments/conjunctions.
    Brackets, arbitrary functions, arithmetic and unknown punctuation fail.
    """
    text = text.strip()
    if not text:
        return {'kind': 'empty'}
    if ';' in text:
        items = [parse_expression(p) for p in text.split(';')]
        if any(p['kind'] == 'empty' for p in items):
            raise ValueError('manual_schema_unparsed: empty item')
        if all(p['kind'] == 'assignments' for p in items):
            pairs = [(k, v) for p in items for k, v in p['items'].items()]
            if len({k for k, _ in pairs}) != len(pairs):
                raise ValueError('manual_schema_unparsed: duplicate assignment')
            return {'kind': 'assignments', 'items': dict(pairs)}
        return {'kind': 'sequence', 'items': items}
    if '；' in text:
        items = [parse_expression(p) for p in text.split('；')]
        if any(p['kind'] == 'empty' for p in items):
            raise ValueError('manual_schema_unparsed: empty list item')
        return {'kind': 'list', 'items': items}
    comparison = re.fullmatch(r'(.*?)(>=|<=|!=|==|>|<|=)(.+)', text)
    if comparison:
        left, operator, right = comparison.groups()
        if operator == '=' and re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', left):
            return {'kind': 'assignments', 'items': {left: parse_expression(right)}}
        return {'kind': 'comparison', 'left': parse_expression(left),
                'operator': operator, 'right': parse_expression(right)}
    call = re.fullmatch(r'(value|presence)\(([^()]+)\)', text)
    if call:
        return {'kind': 'call', 'name': call[1], 'argument': parse_expression(call[2])}
    if re.fullmatch(r'(out|rem|quot)[1-9][0-9]*', text):
        return {'kind': 'reference', 'name': text}
    if NUMBER.fullmatch(text):
        return {'kind': 'number', 'value': _number(text)}
    if text in ('true', 'false'):
        return {'kind': 'boolean', 'value': text == 'true'}
    if LABEL.fullmatch(text):
        return {'kind': 'label', 'name': text}
    raise ValueError('manual_schema_unparsed: unsupported expression')


def _compact(text):
    positions = [i for i, c in enumerate(text) if not c.isspace() and c not in PUNCTUATION]
    return ''.join(text[i] for i in positions), positions


def _layout_matches(text, documents, scope=None):
    needle, old_positions = _compact(text)
    matches = []
    for doc in documents:
        value, positions = _compact(doc['text'])
        for index in _occurrences(value, needle):
            selected = positions[index:index + len(needle)]
            if not selected:
                continue
            if scope and not (doc['doc_id'] == scope['doc_id'] and scope['start'] <= selected[0] and selected[-1] < scope['end']):
                continue
            matches.append((doc, selected, old_positions))
    return matches


def map_anchor(anchor, old_doc, documents, scope=None, context=None):
    context = context or anchor
    matches = _layout_matches(context['quote'], documents, scope)
    if len(matches) != 1:
        return None
    doc, positions, old_positions = matches[0]
    selected = [b for a, b in zip(old_positions, positions)
                if anchor['start'] <= context['start'] + a < anchor['end']]
    if not selected:
        return None
    mapped = _anchor(doc, selected[0], selected[-1] + 1)
    return mapped if _compact(mapped['quote'])[0] == _compact(anchor['quote'])[0] else None


def _step_anchors(step, old, documents, scope):
    if not isinstance(step.get('phrase'), str) or not step['phrase']:
        return [], [], ['manual_schema_unparsed']
    positions = _occurrences(old['text'], step['phrase'])
    if len(positions) != 1:
        return [], [], ['needs_review']
    start = positions[0]
    legacy, mapped = [], []
    # A phrase with multiple clauses retains multiple evidence spans. This
    # segmentation is evaluation evidence only, never compiler segmentation.
    for part in re.finditer('[^' + re.escape(PUNCTUATION) + ']+', step['phrase']):
        quote = part[0].strip()
        if not quote:
            continue
        a = start + part.start() + len(part[0]) - len(part[0].lstrip())
        anchor = _anchor(old, a, a + len(quote))
        legacy.append(anchor)
        source = map_anchor(anchor, old, documents, scope)
        if source:
            mapped.append(source)
    return legacy, mapped, [] if legacy and len(legacy) == len(mapped) else ['needs_review']


def _expectation(parsed, rule, symbols):
    """Serialize the parsed reference using the EXISTING semantic contract.
    No legacy operation name is dispatched here; semantics come from crosswalk.
    """
    def operand(node):
        if node['kind'] == 'number':
            return {'literal': node['value']}
        if node['kind'] in ('reference', 'label'):
            name = node['name']
            return {'reference' if name in symbols or node['kind'] == 'reference' else 'label': name}
        raise ValueError('needs_review: non-scalar operand unsupported by registered crosswalk')
    kinds = {a['event_kind'] for a in rule['alternatives']}
    reads = {'input': operand(parsed['input'])}
    parameter, output = parsed['parameter'], parsed['output']
    attributes = {}
    if kinds == {'threshold'}:
        if parameter['kind'] != 'comparison' or parameter['operator'] != '>=':
            raise ValueError('crosswalk_missing: only inclusive lower threshold registered')
        left = parameter['left']
        if left['kind'] != 'empty' and not (left['kind'] == 'call' and left['name'] == 'value' and left['argument'] == parsed['input']):
            raise ValueError('needs_review: comparison subject differs from input')
        reads['parameter'] = operand(parameter['right'])
        if output['kind'] != 'label':
            raise ValueError('needs_review: judgment label required')
        attributes = {'lower_inclusive': True, 'judgment': output['name']}
    elif parameter['kind'] != 'empty':
        reads['parameter'] = operand(parameter)
    if output['kind'] == 'assignments':
        outputs = {}
        for port, node in output['items'].items():
            if port not in ('quotient', 'remainder', 'result') or node['kind'] not in ('reference', 'label'):
                raise ValueError('manual_schema_unparsed: unknown output port or output expression')
            outputs[port] = node['name']
    elif output['kind'] in ('reference', 'label'):
        if kinds == {'divmod'}:
            raise ValueError('needs_review: unspecified quotient/remainder output')
        outputs = {'result': output['name']}
    else:
        raise ValueError('manual_schema_unparsed: output must be named')
    if kinds == {'alias'}:
        if output['kind'] != 'label':
            raise ValueError('needs_review: alias label required')
        attributes = {'label': output['name']}
    if not any(set(a['read_ports']) == set(reads) for a in rule['alternatives']):
        raise ValueError('needs_review: roles outside registered crosswalk')
    return {'reads': reads, 'outputs': outputs, **({'attributes': attributes} if attributes else {})}


def import_annotations(annotations, sources, packet, crosswalk):
    documents = packet['primary_documents'] + packet.get('context_documents', [])
    source_index = {c['id']: c for c in sources['chunks']}
    records = []
    for raw in annotations:
        record = {'original': copy.deepcopy(raw), 'lexical_semantic_reference': [], 'relation_reference': [], 'procedure_reference': None}
        chunk = source_index.get(raw['chunk_id'])
        if chunk is None:
            record.update(status='needs_review', reason='missing_source_chunk')
            records.append(record)
            continue
        old = source_document(raw['chunk_id'], chunk['source_text_zh'])
        matches = _layout_matches(old['text'], documents)
        scope = _anchor(matches[0][0], matches[0][1][0], matches[0][1][-1] + 1) if len(matches) == 1 else None
        record['scope_basis'] = 'exact_full_chunk' if scope else 'unresolved'
        if not scope:
            # Exact leading-clause identity can locate a document containing an
            # editorial variant elsewhere; it never resolves the variant itself.
            leading = re.split('[' + re.escape(PUNCTUATION) + ']', old['text'])[0]
            candidates = [d for d in documents if _compact(leading)[0] and _compact(leading)[0] ==
                          _compact(re.split('[' + re.escape(PUNCTUATION) + ']', d['text'])[0])[0]]
            if len(candidates) == 1:
                scope = _anchor(candidates[0], 0, len(candidates[0]['text']))
                record['scope_basis'] = 'unique_exact_leading_clause'
        record['source_scope'] = scope
        for term in raw.get('terms', []):
            recovered = recover_mention(term, old)
            mapped = [map_anchor(a, old, documents, scope, recovered.get('context_anchor')) for a in recovered['anchors']]
            record['lexical_semantic_reference'].append({
                'original': copy.deepcopy(term), 'legacy_resolution': recovered,
                'source_anchors': [a for a in mapped if a],
                'status': 'resolved' if mapped and all(mapped) else 'needs_review',
                'semantic_type': term.get('type'),
                'target_status': 'lexical_semantic_reference' if term.get('type') in ('ASTRO_TERM', 'PARAMETER', 'QUANTITY', 'CALC_OP') else 'not_current_parser_target'})
        for relation in raw.get('relations', []):
            record['relation_reference'].append({'original': copy.deepcopy(relation), 'target_status': 'not_current_parser_target'})
        if raw.get('chunk_type') == 'procedure' and raw.get('steps'):
            steps, symbols = [], set()
            orders = [s.get('order') for s in raw['steps']]
            valid_orders = all(type(o) is int and o > 0 for o in orders) and len(set(orders)) == len(orders)
            ordered = sorted(raw['steps'], key=lambda s: s['order']) if valid_orders else raw['steps']
            for index, step in enumerate(ordered):
                legacy, mapped, issues = _step_anchors(step, old, documents, scope)
                parsed, errors = {}, []
                if not valid_orders:
                    issues.append('manual_schema_unparsed')
                    errors.append('order must be a unique positive integer')
                for field in ('input', 'parameter', 'output'):
                    try:
                        parsed[field] = parse_expression(step[field])
                    except (ValueError, KeyError, AttributeError) as error:
                        issues.append('manual_schema_unparsed')
                        errors.append(field + ': ' + str(error))
                operation = step.get('op')
                if not isinstance(operation, str):
                    issues.append('manual_schema_unparsed')
                rule = crosswalk['operations'].get(operation) if isinstance(operation, str) else None
                if rule is None:
                    issues.append('crosswalk_missing')
                expected = None
                if rule and len(parsed) == 3:
                    try:
                        expected = _expectation(parsed, rule, symbols)
                    except ValueError as error:
                        issues.append(str(error).split(':')[0])
                        errors.append(str(error))
                output = parsed.get('output', {})
                output_nodes = list(output['items'].values()) if output.get('kind') == 'assignments' else [output]
                symbols.update(n['name'] for n in output_nodes if n.get('kind') in ('reference', 'label'))
                steps.append({'step_id': 'step-' + str(step['order'] if valid_orders else index + 1), 'legacy': copy.deepcopy(step),
                              'legacy_anchors': legacy, 'source_anchors': mapped, 'parsed': parsed,
                              'issues': sorted(set(issues)), 'details': errors, 'evaluation_expectation': expected})
            record['procedure_reference'] = {
                'schema_version': 'PatternStepReference/2', 'usage': 'evaluation_only',
                'reference_id': raw['chunk_id'], 'procedure_ids': chunk.get('procedure_ids', []),
                'legacy_document': old, 'source_documents': copy.deepcopy([d for d in documents if any(
                    a['doc_id'] == d['doc_id'] for s in steps for a in s['source_anchors'])]),
                'alignment_policy': 'exact_codepoints_except_whitespace_and_listed_punctuation',
                'ignored_punctuation': PUNCTUATION, 'steps': steps}
        record['status'] = 'imported'
        records.append(record)
    return {'schema_version': 'PatternAnnotationImport/1', 'usage': 'evaluation_only',
            'actor': 'deterministic_python_importer', 'chunks': records}
