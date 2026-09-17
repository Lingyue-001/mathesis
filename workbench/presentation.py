"""Read-only scholar language from confirmed backend fields. No inference engine.

IDs are retained as addresses, not human labels. All code translations use the
single ontology; nearby candidates and suggested actions retain their backend
meaning. This module does not decide legality, blocking, or historical truth.
"""
from copy import deepcopy
from analysis_parser.ontology import REGISTRY, VERSION, entry, label


def ontology_reference():
    return {'version': VERSION, 'entries': [deepcopy(REGISTRY[key]) for key in sorted(REGISTRY)]}


def _label(domain, value):
    return '未记录' if value is None else label(domain, value)


def present_question(question):
    kind = entry('issue', question['kind'])
    reasons = question.get('reason') or []
    if isinstance(reasons, str):
        reasons = [reasons]
    reason_text = [entry('cause', reason.split(':', 1)[0])['definition'] for reason in reasons]
    return {
        'id': question.get('id'), 'label': kind['label'],
        'text': '；'.join(dict.fromkeys([kind['definition'], *reason_text])),
        'severity': label('severity', question['severity']),
        'source_anchors': deepcopy(question.get('source_anchors', [])),
        'actions': [{'code': code, 'label': label('action', code)} for code in question.get('suggested_actions', [])],
        'affected_text': f"后端记录影响 {len(question.get('affected_outputs', []))} 个对象",
        'nearby_evidence': [{'id': row.get('id'), 'label': label('construction', row['kind']),
                             'text': row.get('surface') or ' / '.join(s.get('quote', '') for s in row.get('source_spans', []))}
                            for row in question.get('candidate_options', [])],
        'evidence_note': '附近构式证据；未据此判断为合法替代候选',
        'provenance': {'kind': question['kind'], 'reason': deepcopy(question.get('reason'))},
    }


def build_presentation(response):
    """A view model with object IDs for navigation and authored text for display."""
    reference = response.get('reference_analysis')
    display = reference or response
    projection = display['projection']
    nodes, values = projection['nodes'], projection['quantities']
    def source_name(value):
        return label('symbol', value) if ('symbol', value) in REGISTRY else value
    frame_names = {frame['id']: label('frame', frame['kind']) +
                   ((' · ' + frame['label']) if frame['label'] not in (frame['kind'], 'Context') else '')
                   for frame in projection['frames']}
    names = {node['id']: f"步骤 {i + 1} · {label('operation', node['kind'])}" for i, node in enumerate(nodes)}
    quantities = {}
    for i, value in enumerate(values):
        quantities[value['id']] = {
            'name': ' / '.join(source_name(name) for name in value.get('labels') or []) or f'数量 {i + 1}',
            'kind': _label('quantity_kind', value.get('quantity_kind')),
            'role': _label('role', value.get('role')),
            'unit': _label('unit', value.get('unit')),
            'status': _label('resolution_state', value.get('resolution_status')),
            'representation': _label('representation', (value.get('representation') or {}).get('kind')),
        }
    def quantity_name(ident):
        return quantities[ident]['name'] if ident in quantities else '未找到所引用的量'
    def scale_text(value):
        scale = value.get('scale')
        if isinstance(scale, dict):
            denominator = scale.get('denominator')
            return f'分母：{quantity_name(denominator)}' if denominator else '尺度已记录，详见证据'
        return str(scale) if isinstance(scale, (int, float)) else '未记录'
    by_value = {v['id']: v for v in values}
    edges = []
    for edge in projection['edges']:
        text = f"{names.get(edge['producer'], '来源待定')}（{_label('port', edge['output_port'])}） → {quantity_name(edge['value_id'])} → {names.get(edge['consumer'], '去向待定')}（{_label('port', edge['input_port'])}）"
        edges.append({**edge, 'text': text})
    shown_nodes = {}
    for node in nodes:
        rows = []
        for direction, ports in [('输入', node.get('reads', {})), ('输出', node.get('writes', {}))]:
            for port, ident in ports.items():
                value = by_value.get(ident, {})
                q = quantities.get(ident, {})
                rows.append({'direction': direction + ' · ' + label('port', port),
                             'name': quantity_name(ident), 'role': q.get('role', '未记录') + ' / ' + q.get('kind', '未记录'),
                             'producer_id': value.get('producer'),
                             'producer': names.get(value.get('producer'), '来源待定') + ' · ' + _label('port', value.get('output_port')),
                             'unit_scale': q.get('unit', '未记录') + ' / ' + scale_text(value) + ' / ' + q.get('representation', '未记录'),
                             'status': q.get('status', '未记录')})
        scope = node.get('scope') or {}
        attributes = node.get('attributes') or {}
        control = []
        for key, text in [('lower_inclusive', '下界包含等号'), ('upper_inclusive', '上界包含等号')]:
            if key in attributes:
                control.append(text + ('：是' if attributes[key] else '：否'))
        if 'judgment' in attributes:
            control.append('判断文字：' + attributes['judgment'])
        if 'scope_end' in attributes:
            control.append('范围结束：' + label('control_end', attributes['scope_end']))
        shown_nodes[node['id']] = {
            'label': names[node['id']], 'operation': label('operation', node['kind']),
            'outputs': ' / '.join(quantity_name(ident) for ident in node.get('writes', {}).values()) or '无独立输出',
            'rows': rows, 'source': ' / '.join(s.get('quote', '') for s in node.get('source_spans', [])),
            'evidence': _label('evidence', node.get('evidence_status')),
            'scope': frame_names.get(scope.get('definition_id'), '背景范围' if scope.get('task') == 'context' else '未记录所属定义'),
            'control': '；'.join(control) or '未记录独立控制属性',
            'order': f"原文次序：{node.get('text_order', '未记录')}；依赖次序：{node.get('dependency_order', '未记录')}",
            'dependencies': [e['text'] for e in edges if node['id'] in (e['producer'], e['consumer'])],
        }
    steps = {}
    for step in projection['steps']:
        steps[step['id']] = {'label': label('syntax', step['kind']), 'surface': step['surface'],
                             'events': ' · '.join(names[i] for i in step['event_ids']) or '无独立计算节点',
                             'issues': f"{len(step['issue_ids'])} 项结构提示",
                             'slots': ' · '.join(f"{label('port', port)}：{slot.get('surface') or '尚未记录具体对象'}" for port, slot in step['slots'].items())}
    frames = {frame['id']: {'label': frame_names[frame['id']],
                            'source_role': '背景材料' if frame.get('source_role') == 'context' else '所选正文',
                            'base': '已记录查询基态' if frame.get('base_ref') else '未记录查询基态'} for frame in projection['frames']}
    queue = response['projection']['review_queue']['items'] if reference else []
    questions = [present_question(q) for q in [*queue, *projection['review_queue']['items']]]
    issues = [{'id': q['id'], 'label': label('cause', q['kind']),
               'text': entry('cause', q['kind'])['definition'], 'source_spans': q.get('source_spans', [])} for q in projection['issues']]
    decisions = {row['decision_id']: row for row in response['session']['decisions']}
    candidates = []
    for row in display['graph'].get('construction_candidates', []):
        attrs = row.get('attributes') or {}
        evidence = '已记录构式规则来源' if row.get('production_id') else '未记录构式规则来源'
        if attrs.get('authored_structure'):
            evidence = '由审定决定构造'
            decision = decisions.get(attrs.get('decision_id'))
            if decision:
                evidence += ' · ' + label('evidence', decision['actor']['type'])
        candidates.append({'id': row['node_id'], 'label': label('construction', row['kind']),
                           'surface': row.get('text', ''), 'source_spans': deepcopy(row.get('source_spans', [])),
                           'evidence': evidence + ' · ' + _label('candidate_state', row.get('status')) + '；不据此认定学术含义',
                           'provenance': {'production_id': row.get('production_id'), 'attributes': deepcopy(attrs)}})
    stages = []
    stage_names = {s['id']: s['label'] for s in display['stages']}
    stage_records = [(stage, False) for stage in response['stages']]
    if reference:
        stage_records += [(stage, True) for stage in display['stages']]
    for stage, is_reference in stage_records:
        artifacts = []
        for artifact in stage['artifacts']:
            text = label('artifact', artifact['kind'])
            if 'count' in artifact:
                text += f"：{artifact['count']}"
            if artifact['kind'] == 'graph_status':
                text += '：' + label('graph_state', artifact['value'])
            artifacts.append(text)
        stages.append({'id': ('reference-' if is_reference else '') + stage['id'],
                       'label': ('自动参考：' if is_reference else '') + stage['label'], 'status': label('stage_state', stage['status']),
                       'text': '；'.join(artifacts) or '本次未返回阶段产物',
                       'downstream': '影响后续：' + ('、'.join(stage_names[i] for i in stage['affected_stages']) or '无后续阶段'),
                       'provenance': deepcopy(stage)})
    statuses = {key: label(domain, response['summary'][key]) for key, domain in
                [('review_status', 'review_state'), ('graph_status', 'graph_state'),
                 ('execution_status', 'execution_state'), ('comparison_status', 'comparison_state')]}
    replay = response['bundle']['replay']
    session_status = label('session_state', replay['status'])
    validation_status = label('validation_state', str(response['bundle']['validation']['valid_for_complete_export']).lower())
    history = [{'id': row['decision_id'], 'label': label('action', row['action']),
                'actor': label('evidence', row['actor']['type']), 'quote': row['targets'][0].get('quote', ''),
                'status': _label('session_state', (replay.get('decision_status', {}).get(row['decision_id']) or {}).get('status')),
                'revision': row.get('revision'), 'action': row['action']} for row in response['session']['decisions']]
    controls = {
        'candidate-select': candidates,
        'manual-operation': [{'code': code, 'label': label('construction', code)} for code in ('load', 'name')],
        'lexical-role': [{'code': code, 'label': label('lexical_role', code)} for code in ('term', 'numeral', 'pronoun', 'function_word', 'preposition', 'particle', 'operator_cue')],
        'parameter-unit': [{'code': code, 'label': label('unit', code)} for code in ('integer', 'year', 'month', 'day', 'unknown')],
        'profile-select': [{'code': '', 'label': '请选择已有解释方案'}, *[{'code': code, 'label': label('profile', code)} for code in ('ST_elapsed', 'SF_Liu_inclusive', 'SF_completed_four', 'instant_lunation', 'civil_whole_day')]],
    }
    # Names already present in output signatures; no compatibility filtering or
    # invented candidate. The ordinary decision validator still checks binding.
    output_ports = list(dict.fromkeys([port for node in nodes for port in node.get('writes', {})] +
                                     [name for frame in projection['frames'] for name in frame.get('return_ports', {})]))
    controls['binding-port'] = [{'code': port, 'label': label('port', port) if ('port', port) in REGISTRY else port}
                                for port in output_ports]
    execution_text = '\n'.join(f"{source_name(key.split(':', 1)[-1])}：{value if isinstance(value, (int, float)) else '结构化结果，见原始执行记录'}" for key, value in response.get('execution', {}).get('named_outputs', {}).items())
    return {'version': VERSION, 'nodes': shown_nodes, 'steps': steps, 'frames': frames,
            'quantities': quantities, 'edges': edges, 'questions': questions, 'issues': issues,
            'candidates': candidates, 'stages': stages, 'history': history, 'controls': controls,
            'actions': [{'code': c, 'label': item['label']} for (domain, c), item in REGISTRY.items() if domain in ('action', 'action_variant')],
            'statuses': statuses, 'reference_only': bool(reference), 'execution_text': execution_text,
            'status_text': ('旧会话待重验；以下为只读自动参考，原决定未应用。' if reference else '已载入结构分析。') + f'当前有 {len(questions)} 项待审问题。',
            'session_text': f"审定：{statuses['review_status']} · 图：{statuses['graph_status']} · 核算：{statuses['execution_status']} · 对照：{statuses['comparison_status']} · {session_status} · {validation_status}",
            'graph_text': ('只读自动参考 · ' if reference else '') + f"{len(nodes)} 个操作 · {len(values)} 个数量 · {len(edges)} 条依赖 · {label('graph_state', display['summary']['graph_status'])}"}
