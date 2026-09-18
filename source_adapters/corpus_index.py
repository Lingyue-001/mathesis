"""Deterministic source-level corpus unit indexes, independent of the parser.

Units are evidence-bearing source blocks.  Their type and proximity relations are
reviewable extraction results, never lexical, construction, or graph assertions.
"""
import copy
import hashlib
import json
from pathlib import Path
import re


SCHEMA_VERSION = 'mathesis.corpus_unit_index/1.0'
SECTION_RE = re.compile(r'^(?P<section>\d+)[ \t]+(?P<text>[^\r\n]+)', re.MULTILINE)
TABLE_RE = re.compile(r'^\[TABLE\]$', re.I)
NUMERALS = '零〇一二三四五六七八九十百千萬万億亿兆兩两半'
OPERATION_CUES = ('置', '乘', '除', '減', '加', '滿', '不滿', '餘', '得', '筭', '算', '命', '并', '約', '求')
INCOMPLETE_SUFFIXES = ('以', '各以', '其', '之', '所', '為', '則', '而', '乃', '從', '并', '減', '加', '乘', '除', '置', '滿', '不滿', '夜半')
PLANET_LABELS = {'周率', '日率', '合積月', '月餘', '月法', '大餘', '小餘', '虛分', '入月日', '日餘', '日度法', '積度', '度餘'}


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def list_review_sources(root):
    """Existing registry IDs intersected with allowed root calendar files."""
    root = Path(root).resolve()
    allowed = {p.name for p in root.glob('calendars-*.md') if p.is_file() and p.resolve().is_relative_to(root)}
    sources = _json(root / 'config/calendrical-ir-pipeline.json')['inputs']['source_texts']
    result = [dict(s, label=Path(s['path']).stem.removeprefix('calendars-'))
              for s in sources if s['path'] in allowed]
    if len({s['id'] for s in result}) != len(result) or len({s['path'] for s in result}) != len(result):
        raise ValueError('duplicate_corpus_registration')
    return result


def read_registered_source(root, source_id):
    """Read bytes without newline conversion and return the registered source."""
    root = Path(root).resolve()
    sources = _json(root / 'config/calendrical-ir-pipeline.json')['inputs']['source_texts']
    source = next((item for item in sources if item['id'] == source_id), None)
    if source is None:
        raise ValueError(f'unknown_source: {source_id}')
    path = (root / source['path']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('source_outside_repository')
    raw = path.read_bytes()
    return source, path, raw, raw.decode('utf-8')


def numbered_sections(text):
    """Return numbered source sections with offsets in decoded-byte code points."""
    sections = []
    for match in SECTION_RE.finditer(text):
        sections.append({
            'section': int(match['section']), 'text': match['text'],
            'start': match.start('text'), 'end': match.end('text'),
            'line': text.count('\n', 0, match.start()) + 1,
        })
    if not sections:
        raise ValueError('no_numbered_sections')
    duplicates = {item['section'] for item in sections if sum(row['section'] == item['section'] for row in sections) > 1}
    occurrences = {}
    for item in sections:
        if item['section'] in duplicates:
            occurrences[item['section']] = occurrences.get(item['section'], 0) + 1
            item['occurrence'] = occurrences[item['section']]
    return sections


def _sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _parameter_fields(text):
    """Mechanical name/value candidates kept outside the parser input."""
    value = text.strip()
    match = re.match(rf'^([^，。；：]{{1,12}})，\s*([{NUMERALS}]+)(.*)$', value)
    if match:
        name, numeral, tail = (part.strip() for part in match.groups())
        if len(name) <= 8 and not any(cue in name for cue in OPERATION_CUES):
            return [{'name': name, 'value_text': numeral, 'note': tail.lstrip('，。；:：').strip() or None}]
    match = re.match(rf'^([^零〇一二三四五六七八九十百千萬万億亿兆兩两半，。；：]{{1,8}})([{NUMERALS}]+)[。.]?$', value)
    if match and not any(cue in match.group(1) for cue in OPERATION_CUES):
        return [{'name': match.group(1).strip(), 'value_text': match.group(2).strip(), 'note': None}]
    if value[:1] not in '木火土金水' or sum(label in value for label in PLANET_LABELS) < 3:
        return []
    fields = []
    for sentence in (part.strip() for part in re.split(r'[。；]', value) if part.strip()):
        parts = [part.strip() for part in sentence.split('，') if part.strip()]
        if len(parts) >= 2 and parts[0] in PLANET_LABELS and re.search(rf'[{NUMERALS}]', parts[1]):
            fields.append({'scope': value[0], 'name': parts[0], 'value_text': parts[1]})
    return fields


def _parameter_index(units):
    index = {}
    for unit in units:
        for field in unit['parameters']:
            entry = {'unit_id': unit['id'], 'sections': unit['sections'], 'value_text': field['value_text']}
            if field.get('scope'):
                entry['scope'] = field['scope']
                index.setdefault(f"{field['scope']}::{field['name']}", []).append(dict(entry))
            if field.get('note'):
                entry['note'] = field['note']
            index.setdefault(field['name'], []).append(entry)
    return index


def _classify(text):
    value = text.strip()
    if TABLE_RE.fullmatch(value):
        return 'table', 'high', 'marker:[TABLE]'
    if re.match(r'^一術(?:[，,:：]|$)', value):
        return 'alternative_procedure', 'high', 'marker:一術'
    if re.match(r'^(推|步術)', value):
        return 'procedure_root', 'high' if '術' in value[:24] else 'medium', 'marker:推/步術'
    if value.startswith('求'):
        return 'procedure_followup', 'medium', 'marker:求'
    if re.match(rf'^([^，。；：]{{1,8}})，([{NUMERALS}]+)', value) and not any(cue in value.split('，', 1)[0] for cue in OPERATION_CUES):
        return 'parameter', 'high', 'compact_name_value_declaration'
    if value[:1] in '木火土金水' and sum(label in value for label in PLANET_LABELS) >= 3:
        return 'parameter_block', 'high', 'five_planet_repeated_name_value_fields'
    if value[:1] in '木火土金水' and ('晨伏' in value or '夕伏' in value):
        return 'reference_data', 'medium', 'planet_motion_record'
    count = sum(value.count(cue) for cue in OPERATION_CUES)
    if count >= 4:
        return 'computational_exposition', 'low', 'operation_cue_density_without_procedure_marker'
    if len(value) <= 8 and not re.search(r'[，。；：]', value) and not re.search(rf'[{NUMERALS}]', value):
        return 'heading', 'medium', 'short_heading'
    return 'discourse', 'medium', 'fallback'


def _new_unit(members, kind, confidence, rule, source_id='sifen'):
    sections = [member['section'] for member in members]
    return {
        'id': _unit_id(sections, source_id, members), 'type': kind, 'sections': sections,
        'text_original': ''.join(member['text'] for member in members),
        'text_effective': ''.join(member['text'] for member in members),
        'source_spans': [dict(member) for member in members],
        'detection': {'rule': rule, 'confidence': confidence},
        'parameters': _parameter_fields(''.join(member['text'] for member in members)),
        'relations': [], 'member_roles': [], 'human_review': [],
    }


def _unit_id(sections, source_id, members):
    base = f'{source_id}:section:{sections[0]}' if len(sections) == 1 else f'{source_id}:sections:{sections[0]}-{sections[-1]}'
    return base + (f"@{members[0]['start']}" if any('occurrence' in s for s in members) else '')


def _is_continuation(previous, following):
    text = previous['text'].strip()
    next_text = following['text'].strip()
    next_kind, _, _ = _classify(next_text)
    if re.search(r'[。！？；]$', text) or next_kind in {'table', 'alternative_procedure', 'procedure_root', 'procedure_followup', 'parameter', 'parameter_block', 'heading'}:
        return False
    return text.endswith(INCOMPLETE_SUFFIXES) or (_classify(text)[0] in {'procedure_root', 'computational_exposition'} and next_text.startswith(('之', '其', '以', '不', '所')))


def _physical_spans(sections):
    spans, boundary_events = [], []
    position = 0
    while position < len(sections):
        members = [sections[position]]
        while position + 1 < len(sections) and _is_continuation(members[-1], sections[position + 1]):
            following = sections[position + 1]
            boundary_events.append({'kind': 'physical_continuation_join', 'left_section': members[-1]['section'],
                                    'right_section': following['section'], 'confidence': 'medium',
                                    'reason': 'nonterminal/incomplete ending + no strong new-unit marker'})
            members.append(following)
            position += 1
        spans.append(members)
        position += 1
    return spans, boundary_events


def _build_units(sections, source_id='sifen'):
    units, review = [], []
    active = None
    last_procedure = None
    for members in _physical_spans(sections)[0]:
        text = ''.join(member['text'] for member in members)
        kind, confidence, rule = _classify(text)
        if kind == 'procedure_followup' and active is not None:
            target = units[active]
            old_id = target['id']
            target['sections'].extend(member['section'] for member in members)
            target['source_spans'].extend(dict(member) for member in members)
            target['text_original'] += text
            target['text_effective'] += text
            target['id'] = _unit_id(target['sections'], source_id, target['source_spans'])
            target['member_roles'].append({'sections': [member['section'] for member in members], 'role': 'followup', 'rule': rule})
            for unit in units:
                for relation in unit['relations']:
                    if relation.get('target_id') == old_id:
                        relation['target_id'] = target['id']
            last_procedure = target['id']
            continue
        unit = _new_unit(members, 'procedure' if kind == 'procedure_root' else kind, confidence, rule, source_id)
        if kind == 'procedure_root':
            unit['member_roles'].append({'sections': unit['sections'], 'role': 'procedure_root', 'rule': rule})
            active = len(units)
            last_procedure = unit['id']
        elif kind == 'procedure_followup':
            unit['type'] = 'procedure'
            unit['member_roles'].append({'sections': unit['sections'], 'role': 'unattached_followup', 'rule': rule})
            review.append({'kind': 'unattached_followup', 'unit_id': unit['id'], 'sections': unit['sections']})
            active = len(units)
            last_procedure = unit['id']
        elif kind == 'alternative_procedure':
            if last_procedure:
                unit['relations'].append({'kind': 'alternative_of_candidate', 'target_id': last_procedure,
                                          'confidence': 'low', 'basis': 'nearest preceding procedure + marker 一術'})
                review.append({'kind': 'confirm_alternative_relation', 'unit_id': unit['id'], 'candidate_target': last_procedure})
            else:
                review.append({'kind': 'alternative_without_predecessor', 'unit_id': unit['id']})
            active = len(units)
            last_procedure = unit['id']
        else:
            active = None
            if kind == 'computational_exposition':
                review.append({'kind': 'computational_text_without_explicit_procedure_marker', 'unit_id': unit['id'], 'sections': unit['sections']})
        units.append(unit)
    return units, review


def _normalize(units):
    for unit in units:
        unit['sections'] = sorted(set(unit['sections']))
        unit['source_spans'].sort(key=lambda item: (item['start'], item['end']))
    return sorted(units, key=lambda unit: (unit['source_spans'][0]['start'], unit['id']))


def _check_override_lock(overrides, source_id, source_sha):
    lock = overrides.get('source_lock')
    if overrides.get('operations') and not lock:
        raise ValueError('override_source_lock_required')
    if lock and (lock.get('source_id') != source_id or lock.get('sha256') != source_sha):
        raise ValueError('override_source_lock_mismatch')


UNIT_TYPE_DESCRIPTIONS = {
    'procedure': '术文：有操作目标或步骤的过程，可包含后续子段；不表示 parser 已识别完整或可以执行。',
    'alternative_procedure': '另一术法：作为另一种做法呈现的过程；替代哪一块须另审 relation，仅改类型不确认该关系。',
    'parameter': '单个参数项：一个明确的名称—数值声明；不把完整计算步骤归入此类。',
    'parameter_block': '参数组：多个相关名称—数值项组成的块；区别于单项参数及叙述性数据记录。',
    'reference_data': '参考数据：供参照的记录或数据性描述；不是操作步骤，也不自动成为 parser 的背景输入。',
    'computational_exposition': '计算性说明：讨论计算、含操作表达，但独立术文的目标或边界尚不明确；不是非计算内容。',
    'heading': '标题：标示篇章或主题的短标签；不包含其统领的正文。',
    'discourse': '论述／说明：历史、原理、解释等叙述，亦为机器兜底分类；不等于其中所有词句都无计算意义。',
    'table': '表格：表格块或原文的表格占位；不自动恢复表内数据或推断查表运算。',
}
UNIT_TYPES = tuple(UNIT_TYPE_DESCRIPTIONS)
RELATION_DESCRIPTIONS = {
    'alternative_of_candidate': '待确认替代关系：当前块可能是目标块的另一术法；机器按邻接和“一術”等标记提出，不证明算法等价。',
    'alternative_of': '已确认替代关系：审阅者确认当前块是目标块的另一术法；仅表示文献结构，不表示数据依赖或数值等价。',
}


def unit_anchor(unit):
    """Canonical half-open code-point intervals; never a text search."""
    result = []
    for span in sorted(unit['source_spans'], key=lambda s: s['start']):
        start, end = span['start'], span['end']
        if result and result[-1][1] == start:
            result[-1][1] = end
        else:
            result.append([start, end])
    return result


def overlaps(left, right):
    return any(a < d and c < b for a, b in left for c, d in right)


def _slice_spans(units, anchor):
    spans = []
    if not isinstance(anchor, list) or not anchor:
        raise ValueError('invalid_source_anchor')
    previous = -1
    for interval in anchor:
        if (not isinstance(interval, list) or len(interval) != 2
                or any(type(x) is not int for x in interval)):
            raise ValueError('invalid_source_anchor')
        start, end = interval
        if start < previous or start >= end:
            raise ValueError('invalid_source_anchor')
        previous = end
        count = 0
        for unit in units:
            for span in unit['source_spans']:
                lo, hi = max(start, span['start']), min(end, span['end'])
                if lo < hi:
                    part = dict(span, start=lo, end=hi,
                                text=span['text'][lo-span['start']:hi-span['start']])
                    spans.append(part)
                    count += hi - lo
        if count != end - start:
            raise ValueError('source_anchor_outside_units')
    return spans


def _anchored_relations(relations, units):
    result = copy.deepcopy(relations)
    if not isinstance(result, list):
        raise ValueError('invalid_relations')
    for relation in result:
        if not isinstance(relation, dict) or not isinstance(relation.get('kind'), str) or not relation['kind'].strip():
            raise ValueError('invalid_relation_kind')
        if relation['kind'] not in RELATION_DESCRIPTIONS:
            raise ValueError('unsupported_corpus_relation:' + relation['kind'])
        if 'target_spans' not in relation:
            target = next((u for u in units if u['id'] == relation.get('target_id')), None)
            if target is None:
                raise ValueError('dangling_unit_relation')
            relation['target_spans'] = unit_anchor(target)
        _slice_spans(units, relation['target_spans'])
        for key in ('target_id', 'target_ids', 'needs_review'):
            relation.pop(key, None)
    return result


def _resolve_relations(units):
    for unit in units:
        unit['relations'] = _anchored_relations(unit['relations'], units)
        for relation in unit['relations']:
            targets = [u['id'] for u in units if overlaps(unit_anchor(u), relation['target_spans'])]
            if len(targets) == 1 and targets[0] != unit['id']:
                relation['target_id'] = targets[0]
            else:
                relation['target_ids'] = targets
                relation['needs_review'] = 'relation_target_split_or_self'
    return units


def _review_unit(base, anchor, kind, relations):
    if kind not in UNIT_TYPES:
        raise ValueError('invalid_unit_type')
    spans = _slice_spans(base, anchor)
    original = next((u for u in base if unit_anchor(u) == anchor), None)
    if original:
        unit = copy.deepcopy(original)
    else:
        # No new recognition: inherit the human-selected type, retain exact text.
        unit = {'id': base[0]['id'].split(':', 1)[0] + ':span:' + _sha(json.dumps(anchor))[:16], 'type': kind,
                'sections': sorted({s['section'] for s in spans}), 'source_spans': spans,
                'text_original': ''.join(s['text'] for s in spans),
                'text_effective': ''.join(s['text'] for s in spans),
                'detection': {'rule': 'human_segmentation', 'confidence': 'reviewed'},
                'parameters': [], 'member_roles': [],
                'human_review': [r for u in base if overlaps(unit_anchor(u), anchor) for r in u['human_review']]}
    unit['type'] = kind
    unit['relations'] = copy.deepcopy(relations)
    return unit


def split_groups(unit, boundaries):
    """UI text offsets -> original-source intervals (including physical gaps)."""
    length = len(unit['text_original'])
    if (not isinstance(boundaries, list) or not boundaries
            or any(type(x) is not int or not 0 < x < length for x in boundaries)
            or len(set(boundaries)) != len(boundaries)):
        raise ValueError('invalid_split_boundaries')
    groups = []
    points = [0, *sorted(boundaries), length]
    for lo, hi in zip(points, points[1:]):
        anchor, position = [], 0
        for span in unit['source_spans']:
            size = span['end'] - span['start']
            a, b = max(lo, position), min(hi, position + size)
            if a < b:
                anchor.append([span['start'] + a-position, span['start'] + b-position])
            position += size
        # A relation asserted for the whole block is not evidence for every part.
        # Old split payloads already contain their relations and replay unchanged.
        groups.append({'source_spans': anchor, 'type': unit['type'], 'relations': []})
    return groups


def _apply_overrides(base, overrides):
    """Replay source-anchored deltas, with legacy whole-section payload support."""
    units = copy.deepcopy(base)
    for unit in units:
        unit['relations'] = _anchored_relations(unit['relations'], base)
    for op in overrides.get('operations', []):
        kind = op.get('op')
        if kind == 'replace_text':
            raise ValueError('replace_text_requires_versioned_reading_mapping')
        if kind not in ('set_type', 'set_relations', 'merge_units', 'split_unit'):
            raise ValueError(f'unsupported_override_op: {kind}')
        anchors = op.get('targets') if kind == 'merge_units' else [op.get('target_spans')]
        if not anchors or anchors == [None]:
            ids = op.get('target_ids', []) if kind == 'merge_units' else [op.get('target_id')]
            anchors = [unit_anchor(next((u for u in units if u['id'] == ident), {'source_spans': []})) for ident in ids]
        selected = []
        for anchor in anchors:
            target = next((u for u in units if unit_anchor(u) == anchor), None)
            if target is None:
                raise ValueError('override_target_not_found')
            selected.append(target)
        if kind == 'set_type':
            if op.get('type') not in UNIT_TYPES:
                raise ValueError('invalid_unit_type')
            selected[0]['type'] = op['type']
        elif kind == 'set_relations':
            selected[0]['relations'] = _anchored_relations(op.get('relations', []), units)
        elif kind == 'merge_units':
            positions = sorted(units.index(u) for u in selected)
            if len(positions) < 2 or positions != list(range(positions[0], positions[-1]+1)):
                raise ValueError('merge_requires_adjacent_units')
            anchor = unit_anchor({'source_spans': [s for u in selected for s in u['source_spans']]})
            relations = op.get('relations', [r for u in selected for r in u['relations']])
            replacement = _review_unit(base, anchor, op.get('type', selected[0]['type']), _anchored_relations(relations, units))
            replacement['id'] = op.get('new_id', replacement['id'])
            units = _normalize([u for u in units if u not in selected] + [replacement])
        else:
            target = selected[0]
            groups = op['groups']
            replacements = []
            for group in groups:
                anchor = group.get('source_spans')
                if anchor is None:
                    anchor = unit_anchor({'source_spans': [s for s in target['source_spans'] if s['section'] in group['sections']]})
                replacements.append(_review_unit(base, anchor, group.get('type', target['type']),
                    _anchored_relations(group.get('relations', target['relations']), units)))
            flattened = [s for u in replacements for s in u['source_spans']]
            if (len(replacements) < 2 or unit_anchor({'source_spans': flattened}) != unit_anchor(target)
                    or sum(s['end']-s['start'] for s in flattened) != len(target['text_original'])):
                raise ValueError('split_groups_must_partition_target')
            units = _normalize([u for u in units if u is not target] + replacements)
    return _resolve_relations(_normalize(units))


def normalize_operations(auto, final):
    """Canonical final partitions, not a growing chain of derived unit IDs."""
    base = auto['units']
    # Common cumulative text boundaries delimit independent edited regions.
    def ends(units):
        result, position = {}, 0
        for i, u in enumerate(units):
            position += len(u['text_original'])
            result[position] = i + 1
        return result
    left, right = ends(base), ends(final)
    operations, a, b = [], 0, 0
    for boundary in sorted(left.keys() & right.keys()):
        originals, reviewed = base[a:left[boundary]], final[b:right[boundary]]
        a, b = left[boundary], right[boundary]
        if [unit_anchor(u) for u in originals] == [unit_anchor(u) for u in reviewed]:
            continue
        anchor = unit_anchor({'source_spans': [s for u in originals for s in u['source_spans']]})
        if len(originals) > 1:
            operations.append({'op': 'merge_units', 'targets': [unit_anchor(u) for u in originals]})
        if len(reviewed) > 1:
            operations.append({'op': 'split_unit', 'target_spans': anchor, 'groups': [
                {'source_spans': unit_anchor(u), 'type': u['type'],
                 'relations': _anchored_relations(u['relations'], final)} for u in reviewed]})
    structural = _apply_overrides(base, {'operations': operations})
    for current, desired in zip(structural, final):
        if unit_anchor(current) != unit_anchor(desired):
            raise ValueError('segmentation_partition_mismatch')
        if current['type'] != desired['type']:
            operations.append({'op': 'set_type', 'target_spans': unit_anchor(desired), 'type': desired['type']})
        relations = _anchored_relations(desired['relations'], final)
        if _anchored_relations(current['relations'], structural) != relations:
            operations.append({'op': 'set_relations', 'target_spans': unit_anchor(desired), 'relations': relations})
    for op in operations:
        op['id'] = 'override:' + _sha(json.dumps(op, ensure_ascii=False, sort_keys=True))[:20]
    return operations


def build_auto_index(root, source_id='sifen'):
    source, path, raw, text = read_registered_source(root, source_id)
    sections = numbered_sections(text)
    units, review = _build_units(sections, source_id)
    _, boundary_events = _physical_spans(sections)
    review.extend({**event, 'kind': 'confirm_physical_continuation_join'} for event in boundary_events)
    return {
        'schema_version': SCHEMA_VERSION,
        'source': {'source_id': source_id, 'path': path.relative_to(Path(root).resolve()).as_posix(),
                   'sha256': hashlib.sha256(raw).hexdigest(), 'offset_unit': 'unicode_code_point_in_utf8_decoded_bytes',
                   'numbered_section_count': len(sections)},
        'method': {'mode': 'automatic', 'uses_cullen_segmentation': False,
                   'manual_policy': 'Overrides are explicit review metadata; source text is not overwritten.'},
        'units': _normalize(units), 'parameter_index': _parameter_index(units),
        'review_queue': review, 'boundary_events': boundary_events,
    }


def build_effective_index(root, source_id='sifen'):
    auto = build_auto_index(root, source_id)
    override_path = Path(root) / 'corpus-review' / source_id / 'overrides.json'
    overrides = _json(override_path) if override_path.is_file() else {'operations': []}
    return effective_from_auto(auto, overrides)


def effective_from_auto(auto, overrides):
    source_id = auto['source']['source_id']
    _check_override_lock(overrides, source_id, auto['source']['sha256'])
    effective = copy.deepcopy(auto)
    effective['units'] = _apply_overrides(auto['units'], overrides)
    effective['parameter_index'] = _parameter_index(effective['units'])
    effective['method']['mode'] = 'automatic_plus_human_overrides'
    effective['overrides'] = {'path': f'corpus-review/{source_id}/overrides.json',
                              'sha256': _sha(json.dumps(overrides, ensure_ascii=False, sort_keys=True))}
    effective['auto_sha256'] = _sha(json.dumps(auto, ensure_ascii=False, sort_keys=True))
    effective['review_queue'].extend({'kind': r['needs_review'], 'unit_id': u['id'],
                                     'target_spans': r['target_spans']}
                                    for u in effective['units'] for r in u['relations'] if r.get('needs_review'))
    return effective
