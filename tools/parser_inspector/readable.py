"""Read-only R1–R4 view over the two existing compiler paths."""
from html import escape
from collections import defaultdict, deque
import json
import hashlib

from adjudication import compile_reviewed, new_session
from analysis_parser.ontology import REGISTRY, label, label_en
from analysis_parser.construction_ir import GRAMMAR
from analysis_parser.pipeline import parse_packet
from evaluation.semantic_regression import diff_projection, project_report
from source_adapters.corpus import build_source_packet_from_units


PRIMARY = 'sifen:section:39'
LAYERS = {
    'R1': (('Lexical candidates', '词法候选'), 'lexical.tokenize_candidates',
           ('Which candidate edges were found in the source text?', '原文被切成了哪些可能的词项？同一位置可以保留多个候选。')),
    'R2': (('Local calculation meaning', '局部表达的计算含义'), 'construction_ir.parse_syntax → scoped.ScopedParser',
           ('What calculation does the machine assign to each expression? Read quantities, operation roles, results, and later uses in source order.',
            '这一句机器认为在做什么？看参与的量、运算角色、结果与后续使用。按原文顺序排列，不代表执行已经成功。')),
    'R3': (('Organisation of the calculation', '计算过程的组织'), 'program_ir → scoped call and return records',
           ('Which calculation stages are formed? See required, formed, and provided quantities; indentation is recorded containment.',
            '这些表达组成哪些计算段？看每段需要接入、形成和向后提供的量。缩进表示所属关系，承接只引用已记录的连接。')),
    'R4': (('Quantity sources and current gaps', '量的来源与当前缺口'), 'program_ir.link_entry → pipeline unresolved',
           ('Which quantities have a source and which remain unresolved? Uses and diagnostics for one quantity are grouped together.',
            '哪些量已有来源，哪些仍缺来源？同一量的使用与相关诊断合并查看；只展示当前 Primary 的分析。')),
}


def compile_view(packet, *, include_term_semantics=False, term_regions=None):
    """One automatic compile and one empty-session compile; no persisted state."""
    automatic_report = parse_packet(packet)
    session = new_session(packet, 'inspector:read-only')
    compilation = compile_reviewed(packet, session)
    automatic = project_report(automatic_report)
    graph = compilation['graph']
    # The bundle itself is not a report. Its graph has the native report schema.
    if graph is not None:
        for field in ('tokens', 'construction_candidates', 'program', 'unresolved'):
            if field not in graph:
                raise ValueError('reviewed_report_field_missing: ' + field)
    reviewed = project_report(graph) if graph is not None else None
    view = {'packet': packet, 'session': session, 'automatic_report': automatic_report,
            'compilation': compilation, 'automatic': automatic, 'reviewed': reviewed,
            'diff': diff_projection(automatic, reviewed) if reviewed is not None else None}
    if include_term_semantics:
        try:
            from domain_kernel.engine import suggest_packet_semantics
            view['term_semantics'] = suggest_packet_semantics(packet, term_regions=term_regions)
            view['term_semantics_status'] = {'status': 'complete'}
        except Exception as error:
            view['term_semantics'] = None
            view['term_semantics_status'] = {'status': 'error', 'error': type(error).__name__ + ': ' + str(error)}
    return view


def _text(value):
    return escape(str(value)) if value is not None else '未记录'


def _ui(en, zh):
    """A chrome-only bilingual string; data labels and source text stay untouched."""
    return (f'<span class="ui" data-ui-en="{escape(en)}" data-ui-zh="{escape(zh)}">'
            f'{escape(en)}</span>')


def _label(category, code):
    return _text(label(category, code) if (category, code) in REGISTRY else code)


def _label_en(category, code):
    """Use only the authored short English label in the reading layer."""
    return _text(label_en(category, code))


def _has_label_en(category, code):
    return (category, code) in REGISTRY and bool(REGISTRY[category, code].get('label_en'))


def _ontology(category, code):
    entry = REGISTRY.get((category, code))
    if not entry:
        return _text(code)
    return (f'<details class="ontology"><summary>{_text(entry["label"])} · {_text(code)}</summary>'
            f'<p>definition：{_text(entry["definition"])}</p>'
            f'<p>methodology：{_text(entry["methodology"])}</p>'
            f'<p>不可据此推断：{_text("；".join(entry.get("must_not_infer", [])))}</p></details>')


def _spans(item):
    return ([item['source_span']] if 'source_span' in item else
            item.get('use_source_spans', item.get('source_spans', [])))


def source_position(item):
    return min(((s.get('doc_id', ''), s.get('start', 10**12), s.get('end', 10**12))
                for s in _spans(item)), default=('\uffff', 10**12, 10**12))


def source_order(rows):
    """Presentation order only; never mutate canonical records or snapshots."""
    return sorted(rows, key=source_position)


def _signature(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _paired(layer, rows, report):
    """Join canonical rows back to native evidence via the ONE existing projector.

    Queues retain duplicate records; absent evidence stays absent (no text search).
    """
    buckets = defaultdict(deque)
    if layer == 'R2':
        for raw in report.get('construction_candidates', []):
            row = project_report({'construction_candidates': [raw]})[layer][0]
            buckets[_signature(row)].append(raw)
    elif layer == 'R3':
        for raw in report.get('program', {}).get('definitions', []):
            row = project_report({'program': {'definitions': [raw]}})[layer][0]
            buckets[_signature(row)].append(raw)
    return [(row, buckets[_signature(row)].popleft() if buckets[_signature(row)] else {})
            for row in source_order(rows)]


def _pattern(production):
    # Exact IDs are emitted from this existing grammar table; no matching/reparse.
    for index, (kind, public, pattern) in enumerate(GRAMMAR):
        if production == f'G_{kind.upper()}_{index}':
            return pattern
    return 'pattern currently unavailable'


def _value_name(ident, report):
    value = next((v for v in report.get('value_instances', []) if v['id'] == ident), {})
    names = value.get('labels') or ([value['source_label']] if value.get('source_label') else [])
    if names:
        return _text(' / '.join(names))
    event = next((e for e in report.get('events', []) if e['id'] == value.get('producer')), {})
    operation = (_label_en('operation', event['kind'])
                 if _has_label_en('operation', event.get('kind')) else '已记录操作')
    return ('未命名的' + _label_en('port', value.get('output_port')) + '（'
            + operation + '）') if value else '量的记录不可用'


def _program_roles(ident, report):
    roles = []
    definitions = {d['id']: d for d in report.get('program', {}).get('definitions', [])}
    for call in report.get('program', {}).get('calls', []):
        owner = _definition_name(definitions.get(call.get('definition_id')))
        for name, value_id in call.get('formal_bindings', {}).items():
            if value_id == ident:
                roles.append(f'input · {_text(name)}（{owner}；formal_bindings）')
        for name, port in call.get('return_ports', {}).items():
            if port.get('value_id') == ident:
                roles.append(f'output · {_text(name)}（{owner}；return_ports）')
    value = next((v for v in report.get('value_instances', []) if v['id'] == ident), {})
    if value.get('role') in ('input', 'parameter', 'intermediate', 'output'):
        roles.append(_text(value['role']) + '（value.role）')
    return '；'.join(dict.fromkeys(roles)) or 'lowered role unresolved / not currently represented'


def _construction_evidence(item, raw, report, document):
    ast = {n['id']: n for n in report.get('syntax', {}).get('nodes', [])}
    node = ast.get(raw.get('node_id'), {})
    status = ('机器编译采用；未经人工确认' if item.get('status') == 'selected'
              else _label('candidate_state', item.get('status')))
    production = raw.get('production_id')
    parts = [f'<strong>{_text(item["surface"])}</strong>', _ontology('construction', item['kind']),
             f'<p>machine status：{status} · {_text(item.get("status"))}</p>',
             f'<p>grammar production：{_text(production)} · {_text(_pattern(production))}</p>',
             '<h4>Grammar slots · 语法槽位</h4>']
    for name, slot in item['slots'].items():
        leaf = ast.get(node.get('slots', {}).get(name), {})
        parts.append(f'<p>{_text(name)} = {_text(slot.get("text"))}（syntax {_text(slot.get("kind"))}）</p>')
        if leaf.get('source_spans'):
            parts.append('<div data-slot-evidence="syntax">syntax slot 原文：'
                         + _evidence(leaf['source_spans'], document) + '</div>')
    if item['slots']:
        parts.append('<small>slot lexical provenance currently unavailable：report 保留 syntax slot 跨度，'
                     '未保留构造该 slot 时采用的 R1 edge 路径。</small>')
    parts.append('<h4>Lowered operation · 操作端口</h4>')
    events = [e for e in report.get('events', [])
              if raw.get('node_id') and e.get('syntax_node_id') == raw['node_id']]
    if not events:
        parts.append('<p>lowered role unresolved / not currently represented</p>')
    for event in events:
        parts.append(_ontology('operation', event['kind']))
        parts.append('<p>关联依据：event.syntax_node_id → 当前构式；未记录逐 slot → port 映射。</p>')
        for direction in ('reads', 'writes'):
            for port, ident in event.get(direction, {}).items():
                parts.append(f'<p>{direction} · {_text(port)} = {_value_name(ident, report)}</p>')
        for key in ('receiver', 'receiver_label'):
            if key in event.get('attributes', {}):
                parts.append(f'<p>attributes.{key} = {_text(event["attributes"][key])}</p>')
    parts.append('<h4>Program quantity role · 程序中的量角色</h4>')
    quantities = dict.fromkeys(ident for e in events for direction in ('reads', 'writes')
                               for ident in e.get(direction, {}).values())
    for ident in quantities:
        parts.append(f'<p>{_value_name(ident, report)}：{_program_roles(ident, report)}</p>')
    if not quantities:
        parts.append('<p>lowered role unresolved / not currently represented</p>')
    return ''.join(parts)


def _technical(value):
    """Native evidence is available on demand, never the default reading layer."""
    return '<details><summary>原始记录 / internal provenance</summary><pre>' + _text(
        json.dumps(value, ensure_ascii=False, indent=2)) + '</pre></details>'


def _events(raw, report):
    return [e for e in report.get('events', [])
            if raw.get('node_id') and e.get('syntax_node_id') == raw['node_id']]


def _role(port):
    # A port not in the authored vocabulary may remain in technical details,
    # but its backend code must not leak into the normal reading layer.
    return _label_en('port', port) if _has_label_en('port', port) else 'Unlabelled operation role'


def _quantity(ident, report, document):
    if ident is None:
        return '尚未确定'
    value = next((v for v in report.get('value_instances', []) if v['id'] == ident), {})
    result = _value_name(ident, report)
    if value.get('role') in ('missing_upstream', 'parameter_missing', 'external_input'):
        result += '（参数来源尚未确定）' if value['role'] == 'parameter_missing' else '（来源尚未确定）'
    if not value.get('labels') and value.get('producer'):
        producer = next((e for e in report.get('events', []) if e['id'] == value['producer']), {})
        if producer.get('source_spans'):
            result += ' · 来自「' + _evidence(producer['source_spans'], document) + '」'
    return result


def _uses(ident, report, document):
    """Read actual value references, including explicit alias events; no label joins."""
    uses = []
    for event in report.get('events', []):
        ports = [p for p, value_id in event.get('reads', {}).items() if value_id == ident]
        if not ports:
            continue
        if event['kind'] == 'alias' and event.get('attributes', {}).get('label'):
            uses.append('命名为「' + _text(event['attributes']['label']) + '」')
        else:
            operation = (_label_en('operation', event['kind'])
                         if _has_label_en('operation', event.get('kind')) else '后续已记录操作')
            uses.append(operation + '的' + ' / '.join(_role(p) for p in ports))
        if event.get('source_spans'):
            uses[-1] += '：' + _evidence(event['source_spans'], document)
    for definition in report.get('program', {}).get('definitions', []):
        for name, port in definition.get('return_ports', {}).items():
            if port.get('value_id') == ident:
                uses.append('由' + _definition_name(definition) + '向后提供「' + _text(name) + '」')
    return '；'.join(dict.fromkeys(uses)) or '尚未记录后续使用'


def _construction(item, raw, report, document):
    events = _events(raw, report)
    operations = [e for e in events if e['kind'] not in ('input', 'literal', 'alias')
                  and _has_label_en('operation', e.get('kind'))]
    parts = ['<div class="reading">']
    if operations:
        for event in operations:
            method = event['kind'] == 'method_call'
            parts.append('<p><strong>' + _ui('Machine interpretation', '机器理解') + '：'
                         + _label_en('operation', event['kind']) + '</strong></p>')
            if method and event.get('method_binding', {}).get('definition_spans'):
                parts.append('<p>复用计算片段：' + _evidence(event['method_binding']['definition_spans'], document) + '</p>')
            # Divmod roles remain explicit even if an output reference is absent.
            reads = event.get('reads', {})
            writes = event.get('writes', {})
            if event['kind'] in ('divmod', 'cycle_reduce'):
                reads = {**{'dividend': None, 'divisor': None}, **reads}
                writes = {**{'quotient': None, 'remainder': None}, **writes}
            parts.append('<p>' + (_ui('Inputs', '传入') if method else _ui('Uses', '使用')) + '：'
                         + '；'.join(_role(port) + ' = ' + _quantity(ident, report, document)
                                    for port, ident in reads.items()) + '</p>')
            parts.append('<p>' + (_ui('Returns', '返回') if method else _ui('Produces', '得到')) + '：'
                         + ('；'.join(_role(port) + ' = ' + _value_name(ident, report)
                                     if ident is not None else _role(port) + ' = 尚未确定'
                                     for port, ident in writes.items()) or '未记录独立结果') + '</p>')
            for port, ident in writes.items():
                if ident is not None:
                    parts.append('<p>' + _ui('Later use', '后续') + ' · ' + _role(port) + '：'
                                 + _uses(ident, report, document) + '</p>')
            attributes = event.get('attributes', {})
            receiver = attributes.get('receiver', attributes.get('receiver_label'))
            if receiver:
                parts.append('<p>接收量 receiver：' + _text(receiver) + '</p>')
            if attributes.get('execution_blocked') or attributes.get('quantity_transition', {}).get('status') == 'unknown':
                parts.append('<p class="gap">' + _ui('Current gap', '当前缺口')
                             + '：' + _ui('The relation or conversion between quantities is unresolved; recorded ports do not establish execution.',
                                              '量之间的关系或换算尚未确定；已有运算端口不表示计算已解决。') + '</p>')
    else:
        parts.append('<p><strong>' + _ui('Machine interpretation', '机器理解') + '：'
                     + _label_en('construction', item['kind']) + '</strong></p>')
        aliases = [e for e in events if e['kind'] == 'alias']
        for event in aliases:
            parts.append('<p>将 ' + '、'.join(_quantity(v, report, document) for v in event['reads'].values())
                         + ' 命名为 ' + '、'.join(_value_name(v, report) for v in event['writes'].values()) + '</p>')
        if item.get('status') == 'unresolved' or not raw:
            parts.append('<p class="gap">计算含义尚未确定。</p>')
        elif not aliases:
            parts.append('<p>未记录独立运算结果。</p>')
    parts.append('</div><details class="machine-evidence"><summary>'
                 + _ui('View machine evidence', '查看机器依据') + '</summary>')
    parts.append(_construction_evidence(item, raw, report, document))
    values = {v for e in events for side in ('reads', 'writes') for v in e.get(side, {}).values()}
    parts.append(_technical({'candidate': raw, 'events': events,
                             'values': [v for v in report.get('value_instances', []) if v['id'] in values]}))
    return ''.join(parts) + '</details>'


def dependency_groups(value, report):
    """Group by formal; diagnostics require explicit name/value AND exact use span.

    Scope stays visible per import. No fuzzy aliases or span-only attribution.
    """
    groups = {}
    definitions = report.get('program', {}).get('definitions', [])
    candidates = report.get('construction_candidates', [])
    values = {v['id']: v for v in report.get('value_instances', [])}
    for raw in report.get('program', {}).get('imports', []):
        canonical = project_report({'program': {'definitions': definitions, 'imports': [raw]},
                                    'construction_candidates': candidates})['R4']['imports'][0]
        group = groups.setdefault(raw['formal'], {'formal': raw['formal'], 'imports': [],
                                                 'diagnostics': [], 'source_spans': []})
        group['imports'].append((canonical, raw))
        group['source_spans'].extend(canonical['use_source_spans'])
    # Preserve standalone/synthetic canonical records even without native evidence.
    if not groups:
        for item in value['imports']:
            group = groups.setdefault(item['formal'], {'formal': item['formal'], 'imports': [],
                                                      'diagnostics': [], 'source_spans': []})
            group['imports'].append((item, {}))
            group['source_spans'].extend(item['use_source_spans'])
    other = []
    raw_diagnostics = report.get('unresolved', [])
    diagnostics = [(project_report({'unresolved': [d]})['R4']['missing_dependencies'][0], d)
                   for d in raw_diagnostics] if raw_diagnostics else [(d, {}) for d in value['missing_dependencies']]
    for diagnostic, raw_diagnostic in diagnostics:
        assigned = False
        for group in groups.values():
            for item, raw in group['imports']:
                bound = [ident for call in report.get('program', {}).get('calls', [])
                         if call.get('definition_id') == raw.get('consumer_definition_id')
                         for name, ident in call.get('formal_bindings', {}).items() if name == group['formal']]
                names = {group['formal'], *bound}
                for ident in bound:
                    names.update(values.get(ident, {}).get('labels', []))
                missing = raw_diagnostic.get('missing_or_conflicting_inputs', diagnostic['missing_inputs'])
                same_use = any((a.get('doc_id'), a.get('start'), a.get('end')) ==
                               (b.get('doc_id'), b.get('start'), b.get('end'))
                               for a in item['use_source_spans'] for b in diagnostic['source_spans'])
                scope_matches = (not raw_diagnostic.get('definition_id') or
                                 raw_diagnostic['definition_id'] == raw.get('consumer_definition_id'))
                if names.intersection(missing) and same_use and scope_matches:
                    group['diagnostics'].append(diagnostic)
                    assigned = True
                    break
        if not assigned:
            other.append(diagnostic)
    return source_order(list(groups.values())), source_order(other)


def _evidence(spans, document):
    links = []
    for span in sorted(spans, key=lambda row: (row.get('start', 0), row.get('end', 0))):
        start, end = span.get('start'), span.get('end')
        valid = (span.get('doc_id') == document['doc_id'] and type(start) is int and type(end) is int
                 and 0 <= start < end <= len(document['text'])
                 and document['text'][start:end] == span.get('quote'))
        quote = _text(span.get('quote'))
        if valid:
            links.append(f'<a href="#source-{start}" data-start="{start}" data-end="{end}">'
                         f'{quote} <small>[{start}, {end})</small></a>')
        else:
            links.append(f'<span>{quote} · 无可定位的原文跨度</span>')
    return '<br>'.join(links) or '未记录原文跨度'


def _fields(values, category):
    return '；'.join(f'{_text(name)} → {_label(category, item.get("port"))}'
                    if 'port' in item else
                    f'{_text(name)}（grammar roles：{", ".join(_text(role) for role in item.get("roles", [])) or "未记录"}）'
                    for name, item in values.items()) or '无'


def _definition_name(value):
    if value is None:
        return '无'
    name = _label_en('frame', value.get('kind'))
    return name + (
        ' · ' + _text(value['goal_surface']) if value.get('goal_surface') else '')


def _description(layer, item):
    if layer == 'R1':
        return f'<strong>{_text(item["surface"])}</strong> · {_label_en("syntax", item["kind"])}'
    if layer == 'R3':
        return (f'<strong>{_definition_name(item)}</strong>' + _ontology('frame', item.get('kind'))
                + f'<p>领域：{_text(item.get("domain_label"))}</p>'
                f'<p>inputs · 形式输入：{_text("、".join(item["formal_inputs"]) or "无")}</p>'
                f'<p>free variables · 自由变量：{_text("、".join(item["free_variables"]) or "无")}</p>'
                f'<p>已定义量：{_fields(item["defined_values"], "port")}</p>'
                f'<p>outputs · 返回端口：{_fields(item["return_ports"], "port")}</p>')
    if 'formal' in item:
        candidates = '；'.join(_definition_name(value) for value in item['candidates']) or '无'
        return (f'<strong>依赖量：{_text(item["formal"])}</strong>'
                f'<p>使用它的定义：{_definition_name(item["consumer"])}</p>'
                f'<p>当前候选定义：{candidates}</p>'
                f'<p>已连接定义：{_definition_name(item["selected_definition"])}</p>'
                f'<p>端口：{_text(item["selected_port"])}</p><p>{_text(item["selection_reason"])}</p>')
    return (f'<strong>{_label_en("cause", item["cause"])}</strong>'
            f'<p>相关量：{"、".join(_text(name) for name in item["missing_inputs"]) or "未记录名称"}</p>'
            f'<p>{_text(item["reason"])}</p>')


def _table(layer, rows, document, report=None):
    body = []
    for item, raw in _paired(layer, rows, report or {}):
        low = ' class="low-edge"' if layer == 'R1' and item['kind'] == 'Syntax' else ''
        description = (_construction(item, raw, report or {}, document) if layer == 'R2'
                       else _description(layer, item))
        body.append(f'<tr data-record="{layer}"{low}><td>{description}</td>'
                    f'<td>{_evidence(_spans(item), document)}</td></tr>')
    return ('<table><thead><tr><th>' + _ui('Machine record', '机器记录') + '</th><th>'
            + _ui('Source evidence', '原文证据') + '</th></tr></thead><tbody>'
            + ''.join(body) + '</tbody></table>') if body else '<p>' + _ui('No records in this layer.', '此层无记录。') + '</p>'


def _program_tree(rows, report, document):
    pairs = _paired('R3', rows, report)
    by_id = {raw['id']: (item, raw) for item, raw in pairs if 'id' in raw}
    seen = set()

    def node(item, raw):
        ident = raw.get('id')
        if ident in seen:
            return ''
        if ident is not None:
            seen.add(ident)
        children = [(i, r) for i, r in pairs if ident is not None and r.get('parent') == ident]
        methods = []
        calls = report.get('program', {}).get('calls', [])
        call_ids = {c['id'] for c in calls if c.get('definition_id') == ident}
        for call in calls:
            if call.get('parent_call_id') in call_ids:
                target = by_id.get(call.get('definition_id'))
                if target:
                    methods.append(_definition_name(target[0]))
        required = list(dict.fromkeys([*item['formal_inputs'], *item['free_variables']]))
        inherited = []
        for dependency in report.get('program', {}).get('imports', []):
            if dependency.get('consumer_definition_id') == ident and dependency.get('selected_definition_id') in by_id:
                inherited.append(_text(dependency['formal']) + ' ← '
                                 + _definition_name(by_id[dependency['selected_definition_id']][0]))
        return (f'<article data-record="R3"><h3>{_definition_name(item)}</h3>'
                + ('<p>初始计算段</p>' if raw.get('is_initial') else '')
                + '<p>' + _ui('Required quantities', '需要接入的量') + '：' + _text('、'.join(required) or '无') + '</p>'
                + '<p>' + _ui('Quantities formed or named here', '本段形成／命名的量') + '：'
                + _text('、'.join(item['defined_values']) or '未记录') + '</p>'
                + '<p>' + _ui('Quantities provided later', '向后提供的量') + '：'
                + _text('、'.join(item['return_ports']) or '未记录') + '</p>'
                + ('<p>承接已有结果：' + '；'.join(inherited) + '</p>' if inherited else '')
                + '<p>' + _evidence(sorted(item['source_spans'], key=lambda s: (s.get('start', 0), s.get('end', 0)))[:1], document) + '</p>'
                + ('<p>调用方法：' + '；'.join(methods) + '</p>' if methods else '')
                + ('<p class="gap">结构问题：parent 引用无法解析。</p>'
                   if raw.get('parent') and raw['parent'] not in by_id else '')
                + '<details class="machine-evidence"><summary>' + _ui('View machine evidence', '查看机器依据')
                + '</summary>'
                + _description('R3', item) + _evidence(item['source_spans'], document)
                + '<p>input / output 依据 formal_inputs / return_ports；intermediate / parameter：'
                  'lowered role unresolved / not currently represented；不按未返回量推断 intermediate。</p>'
                + _technical(raw) + '</details>'
                + ('<div class="children">' + ''.join(node(i, r) for i, r in children) + '</div>' if children else '')
                + '</article>')

    roots = [(i, r) for i, r in pairs if r.get('parent') not in by_id]
    result = ''.join(node(i, r) for i, r in roots)
    # Do not lose malformed/cyclic hierarchy records; do not invent a parent.
    remaining = [(i, r) for i, r in pairs if r.get('id') is not None and r['id'] not in seen]
    if remaining:
        result += '<p>parent 关系无法完整展开；以下保留原记录。</p>'
        result += ''.join(node(i, r) for i, r in remaining)
    return result or '<p>此层无定义。</p>'


def _dependencies(value, report, document):
    groups, other = dependency_groups(value, report)
    parts = []
    for group in groups:
        parts.append(f'<article data-record="R4" data-formal="{_text(group["formal"])}">'
                     f'<h3>需要的量：{_text(group["formal"])}</h3>')
        technical = []
        for item, raw in sorted(group['imports'], key=lambda pair: source_position(pair[0])):
            definition = next((d for d in report.get('program', {}).get('definitions', [])
                               if d['id'] == raw.get('consumer_definition_id')), {})
            roles = definition.get('formal_inputs', {}).get(item['formal'], {}).get('roles', [])
            bound = {ident for call in report.get('program', {}).get('calls', [])
                     if call.get('definition_id') == raw.get('consumer_definition_id')
                     for name, ident in call.get('formal_bindings', {}).items() if name == item['formal']}
            operation_roles = list(dict.fromkeys(port for event in report.get('events', [])
                                                if event.get('syntax_node_id') in raw.get('uses', [])
                                                for port, ident in event.get('reads', {}).items() if ident in bound))
            parts.append('<div class="use"><p>' + _ui('Used in', '使用位置') + '：' + _definition_name(item['consumer'])
                        + '</p>' + _evidence(item['use_source_spans'], document)
                         + '<p>' + _ui('Role here', '该处角色') + '：' + (' / '.join(_role(p) for p in operation_roles)
                                                or '本段输入；运算角色尚未确定') + '</p>'
                         + '<p>' + _ui('Current source', '当前来源') + '：' + (_definition_name(item['selected_definition'])
                                              if item['selected_definition'] else '未绑定') + '</p>'
                         + '<p>' + (_ui('Source port', '来源端口') if item['selected_definition']
                                     else _ui('Expected port', '预期端口')) + '：'
                         + _text(item['selected_port']) + '</p>'
                         + ('<p class="gap">' + _ui('Current gap', '当前缺口') + '：' + _dependency_reason(item) + '</p>'
                            if not item['selected_definition'] else '') + '</div>')
            technical.append('<p>grammar use：' + _text(' / '.join(roles) or '未记录') + '</p>'
                             + _description('R4', item) + _technical(raw))
        if group['diagnostics'] and all(item['selected_definition'] for item, raw in group['imports']):
            parts.append('<p class="gap">来源已连接，但相关数量关系仍有未解决项，见机器依据。</p>')
        parts.append('<details class="machine-evidence"><summary>'
                     + _ui('View machine evidence', '查看机器依据') + '</summary>' + ''.join(technical))
        if group['diagnostics']:
            parts.append('<p>相关诊断（显式量名或绑定 value，加精确使用跨度；不凭同段文字推测）：</p>')
            parts.append(_table('R4', source_order(group['diagnostics']), document))
        else:
            parts.append('<p>无可精确归属此 formal 的诊断；不据此宣称完全解决。</p>')
        parts.append('</details></article>')
    if other:
        parts.append('<h3>其他尚未解决的表达</h3>')
        for diagnostic in other:
            parts.append('<article><p>' + _evidence(diagnostic['source_spans'], document)
                         + '：' + _label_en('cause', diagnostic['cause']) + '</p>'
                         + '<details class="machine-evidence"><summary>技术详情</summary>'
                         + '<p>尚不能精确归属到某个 dependency formal。</p>'
                         + _description('R4', diagnostic) + _technical(diagnostic) + '</details></article>')
    return ''.join(parts) or '<p>此层无依赖记录。</p>'


def _dependency_reason(item):
    reason = item.get('selection_reason')
    if reason == 'no declared root or source producer':
        return '缺少可接入的已声明输入，或原文中可连接的产出。'
    return _text(reason) if reason else '来源尚未确定；未记录更具体的原因。'


def _layer_content(layer, projection, report, document):
    if layer == 'R1':
        return ('<p>' + _ui('Term, Number, Anaphor, and Syntax are parser-edge types, not confirmed parts of speech. '
                            'Several candidates may share one span; Syntax edges are collapsed by default.',
                            'Term / Number / Anaphor / Syntax 都是 parser edge 类型，不等于已确认词性。'
                            '同一跨度可有多个候选；默认折叠 Syntax edges，其他候选按原文位置显示。') + '</p>'
                '<details class="edge-toggle"><summary>' + _ui('View all parser edges', '查看全部 parser edges') + '</summary>'
                '<p>' + _ui('Syntax edges are expanded; close this item to restore the default view。',
                              '已展开 Syntax edges；折叠此项恢复默认视图。') + '</p></details>'
                '<div class="records lexical">' + _table(layer, projection[layer], document) + '</div>')
    if layer == 'R3':
        return _program_tree(projection[layer], report, document)
    if layer == 'R4':
        return _dependencies(projection[layer], report, document)
    return ''.join('<article data-record="R2" data-kind="' + _text(item['kind']) + '"><h3>'
                   + _evidence(item['source_spans'], document) + '</h3>'
                   + _construction(item, raw, report, document) + '</article>'
                   for item, raw in _paired('R2', projection[layer], report))


def _term_tree(node, nodes, ancestors=()):
    """Only child_ids define the ordered term tree; expression is never traversed."""
    if node['id'] in ancestors:
        raise ValueError('cyclic term child_ids')
    parts = ['<li data-term-node="' + _text(node['id']) + '">' + _text(node['span']['quote'])]
    parts.append(' <small>cue_id: ' + _text(node.get('cue_id')) + ' · rule_id: '
                 + _text(node.get('rule_id')) + '</small>')
    rules = []
    if node.get('child_ids'):
        parts.append('<ol class="children">')
        for child_id in node['child_ids']:
            child_html, child_rules = _term_tree(nodes[child_id], nodes, (*ancestors, node['id']))
            parts.append(child_html)
            rules.extend(child_rules)
        parts.append('</ol>')
    if node.get('rule_id'):
        rules.append(node['rule_id'])
    return ''.join(parts) + '</li>', rules


def _term_candidate(node, nodes, regions, metadata, document):
    tree, rules = _term_tree(node, nodes)
    parts = ['<div class="use" data-term-candidate="' + _text(node['id']) + '">',
             '<h4>' + _ui('Meaning', '候选解释') + '</h4><pre>' + _text(json.dumps(
                 node.get('expression', {'proposes': node.get('proposes')}), ensure_ascii=False, indent=2)) + '</pre>',
             '<h4>' + _ui('How derived', '如何得到') + '</h4>',
             '<p>cue_id: ' + _text(node.get('cue_id')) + ' · rule_id: ' + _text(node.get('rule_id')) + '</p>',
             '<details><summary>' + _ui('Ordered term composition', '有序构词过程') + ' · '
             + _text(' → '.join(rules) or node.get('method')) + '</summary>',
             '<div data-term-tree="' + _text(node['id']) + '"><ol>' + tree + '</ol></div>',
             _technical({key: node[key] for key in ('id', 'method', 'child_ids', 'alternative_group') if key in node}),
             '</details><h4>' + _ui('Evidence', '依据') + '</h4>',
             '<p>' + _ui('Source span', '原文跨度') + ': ' + _evidence([node['span']], document) + '</p>',
             '<details><summary>' + _ui('Lexical / composition rule and provenance', '词素／组合规则及解释来源')
             + '</summary>']
    for category, ident in (('lexical_cues', node.get('cue_id')),
                            ('composition_rules', node.get('rule_id'))):
        if ident:
            record = metadata.get(category, {}).get(ident) or metadata.get('fixed_expressions', {}).get(ident)
            parts.append('<p>' + _text(ident) + '</p>' + (_technical(record) if record else ''))
    parts.append('<p>provenance_ids · ' + _ui('Interpretive evidence; not computational producers.',
                                            '解释依据；不是计算 producer。') + '</p>')
    for ident in node['provenance_ids']:
        source = metadata.get('sources', {}).get(ident)
        parts.append('<p>' + _text(ident) + '</p>' + (_technical(source) if source else ''))
    if node.get('region_ids'):
        parts.append(_technical([regions[ident] for ident in node['region_ids']]))
    parts.extend(['</details><h4>' + _ui('Current status / Why still suggestion-only', '当前状态／为何仍只是建议') + '</h4>',
                  '<p>' + _ui('Support', '支持状态') + ': ' + _text(node['support_status']) + '</p>',
                  '<p>' + _ui('Local composition constraints', '局部组合约束') + ': ' + _text(node['constraint_status']) + '</p>',
                  '<p>' + _ui('Authorization', '授权状态') + ': ' + _text(node['authorization_status']) + '</p>'])
    pending = {key: value for key, value in node['precondition_checks'].items() if value == 'underdetermined'}
    if pending:
        parts.append('<p class="gap">' + _ui('Undetermined preconditions', '未决前提') + ': '
                     + _text(json.dumps(pending, ensure_ascii=False)) + '</p>')
    parts.append('<p>' + _ui('Still suggestion-only: K1 has no authority to set runtime semantics or enter lowering.',
                            '仍仅为建议：K1 无权设定运行时语义或进入 lowering。') + '</p></div>')
    return ''.join(parts)


def _term_bundle(bundle, doc, metadata, registry_hash, document):
    identity = bundle['identity']
    if (bundle['schema'] != 'TermSemanticCandidates/1' or
            any(identity[key] != doc[field] for key, field in (
                ('doc_id', 'doc_id'), ('reading_id', 'reading_id'), ('source_sha256', 'actual_sha256')))):
        raise ValueError('term bundle source identity mismatch')
    parts = ['<h3>' + _text(identity['doc_id']) + '</h3>']
    if registry_hash != identity['registry_sha256']:
        metadata = {}
        parts.append('<p class="notice">' + _ui('Registry metadata unavailable; original evidence IDs retained.',
                                                'Registry 来源信息不可用；保留原始依据 ID。') + '</p>')
    if bundle['truncated']:
        parts.append('<p class="notice">' + _ui('Candidate set truncated; displayed alternatives are not exhaustive.',
                                                '候选集已截断；当前展示的替代解释并不穷尽。') + '</p>')
    candidates = bundle['candidates'] + bundle['fixed_expression_candidates']
    nodes = {node['id']: node for node in candidates}
    if len(nodes) != len(candidates):
        raise ValueError('duplicate term candidate ID')
    regions = {region['id']: region for region in bundle['regions']}
    groups = defaultdict(list)
    for node in candidates:
        span = node['span']
        if (any(span[key] != identity[key] for key in ('doc_id', 'reading_id', 'source_sha256'))
                or not (0 <= span['start'] < span['end'] <= len(doc['text']))
                or doc['text'][span['start']:span['end']] != span['quote']):
            raise ValueError('term candidate source span mismatch')
        groups[(span['start'], span['end'])].append(node)
    composed = {span for span, rows in groups.items()
                if any(n.get('method') == 'composition' or 'proposes' in n for n in rows)}
    maximal = {span for span in composed if not any(
        other != span and other[0] <= span[0] and span[1] <= other[1] for other in composed)}
    if not candidates:
        parts.append('<p>' + _ui('No term semantic candidates in this bundle.', '此候选包未生成术语语义候选。') + '</p>')
    elif not composed:
        parts.append('<p>' + _ui('No composition candidates; lexical cues / opaque components remain available below.',
                                '尚无组合候选；下方仍可查看词素提示／未解释成分。') + '</p>')
    secondary = []
    for span, rows in sorted(groups.items()):
        # Source order between occurrences; original bundle order within an occurrence.
        bases = []
        for node in rows:
            for region_id in node.get('region_ids', []):
                basis = regions[region_id]['basis']
                if basis not in bases:
                    bases.append(basis)
        content = '<article><h3>' + _evidence([rows[0]['span']], document) + '</h3>'
        content += '<p>' + _ui('Region basis', '区域依据') + ': ' + _text(', '.join(bases) or 'unrecorded') + '</p>'
        content += ''.join(_term_candidate(n, nodes, regions, metadata, document) for n in rows) + '</article>'
        (parts if span in maximal else secondary).append(content)
    if secondary:
        parts.append('<details><summary>' + _ui('Contained compositions, lexical cues and opaque components',
                                                '内部组合、词素提示及未解释成分') + '</summary>'
                     + ''.join(secondary) + '</details>')
    return ''.join(parts)


def _term_semantics_section(view, document):
    """Read existing bundles only. Failure here cannot take R1–R4 down with it."""
    if 'term_semantics' not in view and 'term_semantics_status' not in view:
        return ''
    heading = '<section id="term-semantics"><h2>' + _ui('Term semantic candidates', '术语语义候选') + '</h2>'
    try:
        if view['term_semantics_status']['status'] != 'complete':
            raise ValueError(view['term_semantics_status'].get('error', 'candidate generation incomplete'))
        # Metadata is read from the same runtime registry projection used in bundle identity.
        # Never call the generator or its grammar-preview validator from presentation.
        from analysis_parser.inputs import documents
        from domain_kernel.engine import load_kernel
        metadata, registry_hash = {}, None
        try:
            registry = load_kernel()
            registry_hash = hashlib.sha256(json.dumps(registry, ensure_ascii=False, sort_keys=True,
                                                       separators=(',', ':')).encode('utf-8')).hexdigest()
            metadata = {key: {row['id']: row for row in registry[key]}
                        for key in ('sources', 'lexical_cues', 'composition_rules', 'fixed_expressions')}
        except Exception:
            pass  # A missing/mismatched registry hides metadata, never the original IDs.
        docs = {doc['doc_id']: doc for doc in documents(view['packet'])}
        content = '<p>' + _ui('Alternatives are unranked. grammar_candidate denotes a Domain Kernel grammar preview, not parser adoption.',
                             '替代解释不排名。grammar_candidate 来自 Domain Kernel 语法预览，不表示 parser 已采用。') + '</p>'
        content += ''.join(_term_bundle(bundle, docs[doc_id], metadata, registry_hash, document)
                           for doc_id, bundle in view['term_semantics'].items())
        return heading + content + '</section>'
    except Exception as error:
        return (heading + '<p class="notice">' + _ui('Term semantic candidates unavailable', '术语语义候选区块不可用')
                + ': ' + _text(type(error).__name__ + ': ' + str(error)) + '</p></section>')


_STYLE = '''
body {font: 15px/1.6 system-ui, sans-serif; color:#222; background:white; margin:0 12px}
* {box-sizing:border-box} a {color:#175d9b} small {color:#555} p {margin:4px 0}
header {position:sticky; top:0; z-index:20; background:white; border-bottom:1px solid #aaa; padding:12px 0}
#header-meta {display:flex; align-items:center; gap:8px; flex-wrap:wrap}
#source {white-space:pre-wrap; font-size:18px; line-height:1.9; max-height:190px; overflow:auto; margin:6px 0}
#source .selected {background:#ffe28a; color:#111} nav {display:flex; gap:24px}
section {padding:12px 0; border-bottom:1px solid #ccc}
.comparison {display:grid; grid-template-columns:1fr 1fr; gap:16px}
.records {border:1px solid #ddd} .lexical {max-height:360px; overflow:auto}
.low-edge {display:none} .edge-toggle[open] ~ .lexical .low-edge {display:table-row}
.children {margin-left:24px; padding-left:16px; border-left:2px solid #bbb}
article {padding:12px; margin:12px 0; border:1px solid #ddd}
.ontology {margin:4px 0} summary {cursor:pointer} h4 {margin:12px 0 4px}
.use {padding:8px 0; border-bottom:1px solid #ddd}
.machine-evidence {margin-top:10px; border-top:1px solid #ddd; padding-top:6px}
.machine-evidence > summary {color:#555} pre {white-space:pre-wrap; overflow-wrap:anywhere; font-size:12px}
.gap {color:#805500}
table {border-collapse:collapse; width:100%} th,td {padding:8px; border-bottom:1px solid #ddd; text-align:left; vertical-align:top}
td {overflow-wrap:anywhere} th {background:#f4f4f4} td:first-child {width:62%}
h2 {font-size:20px} h3 {font-size:16px} .notice {padding:8px; border-left:3px solid #916000}
@media(max-width:700px) {.comparison {grid-template-columns:1fr} #source {font-size:16px}}
'''

_SCRIPT = '''
function updateEvidenceStatus(start, end) {
  const source = document.getElementById('source');
  const status = document.getElementById('evidence-status');
  const prefix = document.documentElement.lang === 'zh' ? '原文高亮' : 'Source highlight';
  status.dataset.start = String(start);
  status.dataset.end = String(end);
  status.textContent = prefix + ' [' + start + ', ' + end + ')：' +
    Array.from(source.textContent).slice(start, end).join('');
}

document.addEventListener('click', event => {
  const link = event.target.closest('a[data-start]');
  if (!link) return;
  event.preventDefault();
  const start = Number(link.dataset.start), end = Number(link.dataset.end);
  document.querySelectorAll('#source span').forEach(span => {
    const offset = Number(span.dataset.offset);
    span.classList.toggle('selected', start <= offset && offset < end);
  });
  const source = document.getElementById('source');
  const target = document.getElementById('source-' + start);
  source.scrollTop += target.getBoundingClientRect().top - source.getBoundingClientRect().top;
  updateEvidenceStatus(start, end);
});

function applyLanguage(active) {
  document.documentElement.lang = active;
  document.querySelectorAll('[data-ui-en]').forEach(node => {
    node.textContent = node.dataset['ui' + active[0].toUpperCase() + active.slice(1)];
  });
  const status = document.getElementById('evidence-status');
  if (status.dataset.start) updateEvidenceStatus(Number(status.dataset.start), Number(status.dataset.end));
}
'''


def render_html(view, language='en'):
    if language not in ('en', 'zh'):
        raise ValueError('unsupported_inspector_language: ' + language)
    document = view['packet']['primary_documents'][0]
    source = ''.join(f'<span id="source-{i}" data-offset="{i}">{escape(char)}</span>'
                     for i, char in enumerate(document['text']))
    parts = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{_STYLE}</style></head><body>',
             '<header><div id="header-meta">'
             + '<strong>' + _ui('Primary', '主文本') + f' · {_text(document["source"]["unit_id"])}</strong>'
             + '<span> · ' + _ui('No context', '无上下文') + ' · Han_Si_fen_li</span>'
             + '</div>',
             f'<div id="source">{source}</div><nav>' + ''.join(f'<a href="#{key}">{key}</a>' for key in LAYERS)
             + '</nav><small id="evidence-status" aria-live="polite">'
             + _ui('Select source evidence to locate and highlight it; coordinates use Unicode characters in this Primary.',
                   '点原文证据可定位并高亮；坐标以当前 Primary 的 Unicode 字符计。')
             + '</small></header>',
             ]
    has_decisions = bool(view.get('session', {}).get('decisions'))
    different = view['diff'] is not None and any(
        row[key] for row in view['diff'].values() for key in ('added', 'removed', 'changed'))
    if view['reviewed'] is None:
        parts.append('<p class="notice">' + _ui('Reviewed compilation unavailable', 'Reviewed 编译不可用')
                     + f'：{_text(view["compilation"]["replay"]["status"])}。'
                     + _ui('No comparable result was generated.', '未生成可比较结果。') + '</p>')
        if not has_decisions:
            parts.append('<p>no human decisions · ' + _ui('No human decisions.', '无人工决定。') + '</p>')
    elif not has_decisions and different:
        parts.append('<p class="notice">no human decisions · 检测到编译路径差异；reviewed ≠ automatic。'
                     '这些差异不能归因于人工决定。正文只显示 machine result。</p>')
    elif not has_decisions:
        parts.append('<p class="notice">' + _ui('reviewed = automatic / no human decisions',
                                                   'reviewed = automatic / 无人工决定') + ' · '
                     + _ui('R1–R4 projections agree, so one machine result is shown; it has not been confirmed by a human.',
                           '本次实测 R1–R4 projection 一致，仅显示一份 machine result；尚未人工确认。') + '</p>')
    else:
        parts.append('<p class="notice">存在人工决定：automatic / reviewed 对照。</p>')
    for layer, (title, module, note) in LAYERS.items():
        parts.extend([f'<section id="{layer}"><h2>{layer} · {_ui(*title)}</h2>',
                      '<p>' + _ui(*note) + '</p><small>' + _ui('Result source', '结果来源')
                      + f'：{module} · ' + _ui('review only', '仅供审阅') + '</small>'])
        fields = [('automatic', _ui('Machine result', '机器结果'))]
        if has_decisions and view['reviewed'] is not None:
            parts.append('<div class="comparison">')
            fields.append(('reviewed', _ui('Reviewed result', '审阅后结果')))
        for field, heading in fields:
            report = (view.get('automatic_report', {}) if field == 'automatic'
                      else view['compilation']['graph'])
            parts.append(f'<div><h3>{heading}</h3>'
                         + _layer_content(layer, view[field], report, document) + '</div>')
        if len(fields) == 2:
            parts.append('</div>')
        if different and not has_decisions:
            delta = view['diff'][layer]
            if any(delta[key] for key in ('added', 'removed', 'changed')):
                parts.append('<details><summary>编译路径差异详情（无人工决定）</summary>')
                for key, heading in (('added', '空 session 路径新增'), ('removed', '仅自动路径存在')):
                    if delta[key]:
                        parts.append(f'<h3>{heading}</h3>' + _table(layer, delta[key], document))
                for change in delta['changed']:
                    parts.append('<h3>自动路径</h3>' + _table(layer, [change['before']], document)
                                 + '<h3>空 session 路径</h3>' + _table(layer, [change['after']], document))
                parts.append('</details>')
        parts.append('</section>')
        if layer == 'R2':
            parts.append(_term_semantics_section(view, document))
    parts.append('<p>R1–R4 是同一 report 的阅读层次；不表示人工确认或阶段通过。</p>')
    return ''.join(parts) + f'<script>{_SCRIPT}</script><script>applyLanguage({json.dumps(language)});</script></body></html>'


def render(root, language='en'):
    import streamlit as st

    st.caption('Read-only research view · fixed Primary §39 · source and R1–R4'
               if language == 'en' else '只读研究视图 · 固定 Primary §39 · 原文与 R1–R4')
    try:
        packet = build_source_packet_from_units(root, 'sifen', [PRIMARY], context_unit_ids=[],
                                                provided_scope={'tradition': 'Han_Si_fen_li'})
        view = compile_view(packet, include_term_semantics=True)
        st.iframe(render_html(view, language), height=850)
    except (ValueError, OSError, KeyError) as error:
        st.error(f'读取或编译未完成：{error}')
