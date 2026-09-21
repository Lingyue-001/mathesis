"""Source-first K2 review controls; the service owns compilation and persistence."""
import hashlib
from html import escape
from uuid import uuid4

from adjudication.anchors import anchor_for, document_for, validate_anchor
from analysis_parser.ontology import label_en
from adjudication.term_claims import compose_term_interpretation
from domain_kernel.engine import load_kernel
from source_adapters.corpus import _load_effective_index
from source_adapters.corpus_index import list_review_sources
from tools.parser_inspector.source_annotation import selection_anchor, source_annotation_component, procedure_model_component
from workbench import review_jobs, service
from workbench.annotation_projection import diff_scholar_source, project_scholar_source
from workbench.question_presenter import CONCEPT_LABELS, CONSTRUCTOR_LABELS, expression_label
from workbench.scholar_renderer import build_renderer_model, selection_details
from workbench.procedure_model import build_procedure_model, serialize_procedure_model


_UI_ZH = {
    'Parser Inspector': '解析检查器', 'Source': '来源', 'Section': '章节',
    'Source document': '原文文档', 'Session / Advanced': '会话／高级',
    'Current question': '当前问题', 'Interpretation': '解释',
    'Procedure view': '过程视图', 'Current reviewed procedure model': '当前审阅过程模型',
    'Proof of concept · current reviewed procedure': '概念验证 · 当前审阅过程',
    'Source context': '原文上下文', 'Download Procedure Model JSON': '下载过程模型 JSON',
    'Confirm and re-run': '确认并重新运行', 'Why these options?': '为何有这些选项？',
    'Decision history and retract': '决策历史与撤回', 'Management': '管理',
    'Run current reviewed model': '运行当前审阅模型', 'Execution evidence': '执行证据',
    'Saved history': '已保存历史', 'What changed': '发生了什么变化',
    'Review': '审阅', 'Researcher': '研究者', 'Evidence note': '证据备注',
    'Export session': '导出会话', 'Import saved session': '导入已保存会话',
    'Import session': '导入会话', 'Open saved session': '打开已保存会话',
    'Create fresh session for this source': '为当前来源新建会话',
    'Current review session': '当前审阅会话', 'Internal session ID: ': '内部会话 ID：',
    'Selected source object': '选中的原文对象', 'Adjust term span': '调整术语跨度',
    'Queue selected term': '加入待确认术语', 'Confirm term spans and re-run': '确认术语跨度并重新运行',
    'Local computational context': '局部计算上下文', 'Term composition': '术语构成',
    'Construction slots': '构式槽位', 'Textual naming': '原文命名',
    'Computational role': '计算角色', 'Cause': '原因', 'Missing inputs': '缺失输入',
    'Search hints — not yet linked': '检索提示——尚未连接', 'Add as context & re-run': '添加为上下文并重新运行',
    'Last change': '最近变更', 'Composition ': '构成：', 'Preview: ': '预览：',
    'Additional source': '附加来源', 'Source section': '来源章节',
    'Decision to retract': '要撤回的决策', 'Reason for retracting': '撤回理由',
    'Retract and re-run': '撤回并重新运行', 'Scope action': '范围操作',
    'Managed interpretation': '受管理的解释', 'Reviewed aspect': '已审阅方面',
    'Management note': '管理备注', 'Technical details': '技术详情',
    'No reviewed corpus source is available.': '没有可用的已审阅语料来源。',
    'This source has no effective sections yet.': '该来源尚未生成有效文本块。',
    'Not saved: ': '未保存：', 'Not imported: ': '未导入：', 'Not created: ': '未创建：',
    'Researcher and evidence note are used only when recording a decision.': '研究者和证据备注仅在记录决策时使用。',
    'Dotted underline · Term     Bracket · Construction     Lower lane · Step': '点状下划线 · 术语　括号 · 构式　下方轨道 · 步骤',
    'Selected span: ': '选中跨度：', 'Terms to confirm: ': '待确认术语：',
    'Select a term, construction, or step in the source.': '请在原文中选择术语、构式或步骤。',
    'Current interpretation · reviewed': '当前解释 · 已审阅', 'Machine suggestions · unranked': '机器建议 · 未排序',
    'suggested · read-only in current adjudication schema': '建议 · 在当前 adjudication schema 中只读',
    'No canonical producer candidate is currently recorded.': '目前没有记录 canonical producer candidate。',
    'No exact hit.': '没有精确命中。',
    'Read-only here: already included, or this question offers no supported context attachment.': '此处只读：该上下文已包含，或此问题不支持附加上下文。',
    'No supported interpretation is available for this source location yet.': '该原文位置目前没有受支持的解释。',
    'This selection is not saved. Only Confirm and re-run records a decision.': '当前选择尚未保存；只有“确认并重新运行”会记录决策。',
    'This combination is outside the current registry or source. Choose another.': '此组合不在当前 registry 或来源范围内；请选择其他项。',
    'This choice will assert:': '此选择将声明：', 'No saved decisions yet.': '尚无已保存决策。',
    'A managed facet stays under review after its interpretation is retracted.': '解释被撤回后，受管理的 facet 仍保持审阅状态。',
    'STALE — re-run required': '已过期——需要重新运行', 'Analysis identity: ': '分析标识：',
    'Value for ': '为以下量提供值：', 'Use an exact integer for ': '请输入精确整数：',
    'Run reviewed model': '运行审阅模型', 'Execution did not run: ': '执行未运行：',
    'Future semantic work · ': '后续语义工作 · ',
}


def _ui_text(value, language):
    if language != 'zh' or not isinstance(value, str):
        return value
    if value in _UI_ZH:
        return _UI_ZH[value]
    for english, chinese in _UI_ZH.items():
        if value.startswith(english):
            return chinese + value[len(english):]
    return value


class _LocalizedStreamlit:
    """Translate Streamlit chrome at the display boundary; never touch data values."""
    def __init__(self, target, language):
        self._target, self._language = target, language

    def __enter__(self):
        self._target.__enter__()
        return self

    def __exit__(self, *args):
        return self._target.__exit__(*args)

    def __getattr__(self, name):
        value = getattr(self._target, name)
        if not callable(value):
            return value
        def invoke(*args, **kwargs):
            localized_args = tuple(_ui_text(arg, self._language) if isinstance(arg, str) else arg for arg in args)
            localized_kwargs = {key: _ui_text(value, self._language) if key in ('help', 'placeholder', 'label') else value
                                for key, value in kwargs.items()}
            return _wrap_localized(value(*localized_args, **localized_kwargs), self._language)
        return invoke


def _wrap_localized(value, language):
    if isinstance(value, (tuple, list)):
        return type(value)(_wrap_localized(item, language) for item in value)
    return _LocalizedStreamlit(value, language) if hasattr(value, '__enter__') or hasattr(value, 'button') else value


def _data_flow_status(graph_status):
    """Scholar-facing display label for the existing graph-status enum."""
    return {'partial': 'incomplete'}.get(graph_status, graph_status)


def evidence_html(packet, target):
    anchor = validate_anchor(packet, target)
    doc = document_for(packet, anchor['doc_id'], anchor['reading_id'])
    role = 'Primary' if doc in packet.get('primary_documents', []) else 'Context'
    return ('<section class="k2-evidence"><strong>' + escape(role + ' · ' + anchor['doc_id'])
            + '</strong><p>' + escape(anchor['reading_id']) + '</p><pre style="white-space:pre-wrap">'
            + escape(doc['text'][:anchor['start']]) + '<mark>' + escape(anchor['quote'])
            + '</mark>' + escape(doc['text'][anchor['end']:]) + '</pre></section>')


def _units(root, source_id):
    return [unit['id'] for unit in _load_effective_index(root, source_id)[1]['units']]


def _submit(st, root, response, **changes):
    try:
        displayed = st.session_state.get('k2_displayed', {})
        if displayed.get('job_id') != response['job']['job_id']:
            raise ValueError('reload_review_job_before_submission')
        result = service.apply_review_job_changes(root, response['job']['job_id'],
            expected_revision=displayed['revision'], expected_digest=displayed['digest'], **changes)
        st.session_state['k2_last_effects'] = (result['job']['job_id'], result['job']['revision'], result['effects'])
        before = st.session_state.get('k2_scholar_projection')
        focus_doc_id = st.session_state.get('k2_scholar_focus_doc')
        if before:
            try:
                after = project_scholar_source(
                    result['effective_packet'], result['compilation'], result.get('questions', []),
                    result['session']['decisions'], result['compilation']['replay']['decision_status'],
                    focus_doc_id=focus_doc_id)
                trigger_ids = list(result.get('recorded_decisions', []))
                st.session_state['k2_last_scholar_diff'] = {
                    'job_id': result['job']['job_id'], 'revision': result['job']['revision'],
                    'diff': diff_scholar_source(before, after, trigger={
                        'mode': 'saved', 'decision_ids': trigger_ids,
                        'change_kind': 'decision' if trigger_ids else 'management'}),
                }
            except (KeyError, ValueError):
                # A source switch or unavailable focus document has no honest
                # before/after comparison. The saved review transaction remains valid.
                st.session_state.pop('k2_last_scholar_diff', None)
        st.session_state.pop('k2_queued_boundaries', None)
        st.rerun()
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        st.error('Not saved: ' + str(error))


def release_interpretation_events(scopes, branch_id, actor, reason, created_at):
    """Release every managed facet for one selected semantic interpretation."""
    events = []
    for scope in scopes:
        if not scope.get('managed'):
            continue
        event = {'event_id': 'management:' + uuid4().hex, 'action': 'unmanage',
                 'target': scope['target'], 'facet': scope['facet'], 'branch_id': branch_id,
                 'actor': actor, 'created_at': created_at, 'reason': reason}
        if scope.get('semantic_target') is not None:
            event['semantic_target'] = scope['semantic_target']
        events.append(event)
    return events


def _managed_interpretation_groups(scopes):
    groups = {}
    for scope in scopes:
        semantic = scope.get('semantic_target')
        # Facets without a semantic address remain independently managed.
        key = str((scope['target'], semantic)) if semantic is not None else str((scope['target'], scope['facet']))
        groups.setdefault(key, []).append(scope)
    return list(groups.values())


def _selection_picker(st, root):
    """Visible entry is source + one effective section, never a job id."""
    sources = list_review_sources(root)
    if not sources:
        st.info('No reviewed corpus source is available.')
        return None
    labels = {row['id']: row['label'] for row in sources}
    source_id = st.selectbox('Source', list(labels), format_func=labels.__getitem__, key='k2_source')
    units = _units(root, source_id)
    if not units:
        st.info('This source has no effective sections yet.')
        return None
    if st.session_state.get('k2_section') not in units:
        st.session_state['k2_section'] = units[0]
    section = st.selectbox('Section', units, key='k2_section',
                           format_func=lambda unit: '§' + unit.rsplit(':', 1)[-1])
    return {'source_id': source_id, 'primary_unit_ids': [section],
            'context_unit_ids': [], 'provided_scope': {}, 'selected_profiles': []}


def _set_selection_from_job(st, root, job_id):
    """Make an explicitly opened saved session legible through the normal picker."""
    job = review_jobs.load_job(root, job_id)
    selection = job['source_selection']
    units = selection.get('primary_unit_ids', [])
    if len(units) != 1:
        return
    st.session_state['k2_source'] = selection['source_id']
    st.session_state['k2_section'] = units[0]


def _session_advanced(st, root, response, selection):
    """Optional persistence controls; annotation never requires them."""
    job = response['job']
    with st.expander('Session / Advanced'):
        st.caption('Current review session · revision ' + str(job['revision']))
        st.caption('Internal session ID: ' + job['job_id'])
        st.download_button('Export session', review_jobs.export_job(job), job['job_id'] + '.json',
                           'application/json', key='k2_export')
        uploaded = st.file_uploader('Import saved session', type=['json'], key='k2_import')
        if st.button('Import session', key='k2_import_submit', disabled=uploaded is None):
            try:
                imported = service.import_review_job(root, uploaded.getvalue())
                st.session_state['k2_requested_job'] = imported['job']['job_id']
                st.rerun()
            except (ValueError, OSError, RuntimeError) as error:
                st.error('Not imported: ' + str(error))
        saved = [row['job_id'] for row in review_jobs.list_jobs(root) if row['status'] == 'readable']
        if saved:
            saved_id = st.selectbox('Open saved session', saved, key='k2_saved_session')
            if st.button('Open saved session', key='k2_open_saved'):
                st.session_state['k2_requested_job'] = saved_id
                st.rerun()
        if st.button('Create fresh session for this source', key='k2_create_fresh'):
            try:
                # A source selection is intentionally the only visible identity.
                fresh = service.create_fresh_review_job(root, selection)
                st.session_state['k2_requested_job'] = fresh['job']['job_id']
                if 'review_job' in st.query_params:
                    del st.query_params['review_job']
                st.rerun()
            except (ValueError, OSError, RuntimeError) as error:
                st.error('Not created: ' + str(error))
        st.caption('Researcher and evidence note are used only when recording a decision.')
        st.session_state.setdefault('k2_actor_id', 'researcher')
        actor_id = st.text_input('Researcher', key='k2_actor_id')
        reason = st.text_input('Evidence note', value='Source-based review', key='k2_reason')
    return {'type': 'human', 'id': actor_id.strip()}, reason.strip()


def _source_view(st, root, response, question, questions):
    packet = response['effective_packet']
    docs = {d['doc_id']: d for group in ('primary_documents', 'context_documents') for d in packet.get(group, [])}
    if not docs:
        return None
    initial = question['anchor']['doc_id'] if question else next(iter(docs))
    if st.session_state.get('k2_source_job') != response['job']['job_id']:
        st.session_state['k2_source_job'] = response['job']['job_id']
        st.session_state['k2_document'] = initial
        for key in ('k2_queued_boundaries', 'k2_scholar_selected', 'k2_scholar_facet', 'k2_consumed_click',
                    'k2_shown_question', 'k2_consumed_model_click'):
            st.session_state.pop(key, None)
    if st.session_state.get('k2_document') not in docs:
        st.session_state['k2_document'] = initial
    # Existing question navigation also moves its canonical object/facet selection.
    if question and question['id'] != st.session_state.get('k2_shown_question'):
        st.session_state['k2_document'] = initial
    doc_id = st.selectbox('Source document', list(docs), key='k2_document')
    doc = docs[doc_id]
    projection = project_scholar_source(packet, response['compilation'], questions, response['session']['decisions'],
        response['compilation']['replay']['decision_status'], focus_doc_id=doc_id)
    model = build_renderer_model(packet, projection, questions)
    if question and question['id'] != st.session_state.get('k2_shown_question'):
        facet = next((f for f in model['facets'] if f.get('question_id') == question['id']), None)
        if facet:
            st.session_state['k2_scholar_selected'] = facet['object_id']
            st.session_state['k2_scholar_facet'] = facet['facet_key']
    st.session_state['k2_shown_question'] = question['id'] if question else None
    st.session_state['k2_scholar_projection'] = projection
    st.session_state['k2_scholar_model'] = model
    st.session_state['k2_scholar_focus_doc'] = doc_id
    view = st.radio('Procedure view', ['Annotated Source', 'Procedure Model'],
                    key='k2_procedure_view', horizontal=True, label_visibility='collapsed')
    if view == 'Procedure Model':
        procedure = build_procedure_model(projection)
        st.session_state['k2_procedure_model'] = procedure
        st.subheader('Current reviewed procedure model')
        st.caption('Proof of concept · current reviewed procedure')
        st.caption('Data-flow status: ' + procedure['status'])
        st.caption('This representation preserves not only operation order, but also quantity identities, '
                   'input/output roles, dependencies, source links, and unresolved gaps. These features provide '
                   'a richer basis for comparing computational procedures than wording or primitive operation sequences alone.')
        st.download_button('Download Procedure Model JSON', serialize_procedure_model(procedure),
                           file_name=doc_id.replace(':', '-') + '.procedure-model.json', mime='application/json',
                           key='k2_export_procedure')
        result = procedure_model_component()(
            data={'model': procedure, 'focus': st.session_state.get('k2_scholar_selected')},
            default={'clicked': None}, key='k2_procedure_graph:' + response['job']['job_id'] + ':' + doc_id,
            on_clicked_change=lambda: None)
        _consume_scholar_click(st, model, getattr(result, 'clicked', None), 'k2_consumed_model_click')
        return None
    st.caption('Dotted underline · Term     Bracket · Construction     Lower lane · Step')
    adjust = st.toggle('Adjust term boundary', key='k2_adjust')
    last = st.session_state.get('k2_last_scholar_diff')
    changed = set()
    if last and (last['job_id'], last['revision']) == (response['job']['job_id'], response['job']['revision']):
        for layer, change in last['diff']['layers'].items():
            for row in [*change['added'], *change['changed']]:
                if row.get('id'):
                    changed.add(row['id'])
                if row.get('object_id'):
                    changed.add(row['object_id'])
                if layer == 'review_facets':
                    changed.update(f['object_id'] for f in model['facets'] if f['facet_key'] == row.get('key'))
    result = source_annotation_component()(
        data={'text': doc['text'], 'render': {key: model[key] for key in ('terms', 'constructions', 'steps')},
              'focus': st.session_state.get('k2_scholar_selected'), 'facet_key': st.session_state.get('k2_scholar_facet'),
              'changed_ids': sorted(changed), 'adjust': adjust, 'language': st._language},
        default={'clicked': None, 'selection': []},
        key='k2_source_view:' + response['job']['job_id'] + ':' + doc_id + ':' + hashlib.sha256(
            doc['text'].encode('utf-8')).hexdigest()[:12],
        on_clicked_change=lambda: None, on_selection_change=lambda: None)
    _consume_scholar_click(st, model, getattr(result, 'clicked', None), 'k2_consumed_click')
    focused = model['objects'].get(st.session_state.get('k2_scholar_selected'))
    if adjust:
        try:
            selected = selection_anchor(packet, doc_id, result.selection)
            st.caption('Selected span: ' + selected['quote'])
        except ValueError:
            selected = None
        queued = st.session_state.setdefault('k2_queued_boundaries', [])
        if st.button('Queue selected term', key='k2_queue_boundary', disabled=selected is None):
            if selected not in queued:
                queued.append(selected)
            st.rerun()
        if queued:
            st.write('Terms to confirm: ' + ', '.join(row['quote'] for row in queued))
        return selected
    if focused and focused.get('span'):
        return anchor_for(packet, doc_id, *focused['span'])
    return None


def _consume_scholar_click(st, model, click, consumed_key):
    """Both read-only renderers select the same Scholar object/facet state."""
    if click and click.get('nonce') != st.session_state.get(consumed_key):
        st.session_state[consumed_key] = click.get('nonce')
        selected = model['objects'].get(click.get('object_id'))
        if selected:
            facet = next((f for f in model['facets'] if f['facet_key'] == click.get('facet_key')
                          and f['object_id'] == selected['id']), None)
            st.session_state['k2_scholar_selected'] = selected['id']
            st.session_state['k2_scholar_facet'] = facet['facet_key'] if facet else None
            st.session_state['k2_question'] = facet.get('question_id') if facet else None
            st.rerun()


def _procedure_details(st, response):
    model = st.session_state.get('k2_procedure_model', {})
    selected = st.session_state.get('k2_scholar_selected')
    nodes = [n for n in model.get('nodes', []) if selected in n['scholar_object_ids']]
    st.subheader('Source context')
    if not nodes:
        st.caption('Select a node to inspect its source and recorded dependencies.')
        return
    # Selection remains a Scholar ID. Prefer that object over contextual literal
    # representations which also reference its supporting Step.
    node = next((n for n in nodes if n['id'] == selected), nodes[0])
    st.write(node['label'])
    if node.get('definition'):
        st.caption(node['definition'])
    if node.get('status_label'):
        st.caption(node['status_label'])
    if node.get('producer_source'):
        source = node['producer_source']
        st.caption('Source · ' + str(source.get('unit_id') or source.get('doc_id')))
    if node['anchor_scope'] == 'supporting_step':
        st.caption('Supporting Step source; no separate exact anchor is recorded for this node.')
    if not node['source_anchors']:
        st.caption('No exact source anchor is recorded for this object.')
    for anchor in node['source_anchors']:
        st.html(evidence_html(response['effective_packet'], anchor))
    with st.expander('Why / Evidence'):
        st.json({'nodes': nodes, 'edges': [e for e in model['edges']
                 if e['from'] in {n['id'] for n in nodes} or e['to'] in {n['id'] for n in nodes}]})


def _boundary_save(st, root, response, actor, reason):
    queued = st.session_state.get('k2_queued_boundaries', [])
    if queued and st.button('Confirm term spans and re-run', key='k2_save_boundaries',
                            disabled=not actor['id'] or not reason):
        decisions = [service.review_decision(response, 'set_term_boundary', anchor,
                     {'contract_version': '1.0', 'branch_id': response['branch_id']}, actor, reason)
                     for anchor in queued]
        _submit(st, root, response, decisions=decisions)


def context_hint_attachment(root, response, question, source_id, hit):
    """Offer only the current question's existing action and adapter document."""
    option = next((o for o in (question or {}).get('options', []) if o['action'] == 'attach_context'), None)
    if option is None:
        return None
    try:
        document = service.review_context_document(root, source_id, hit['unit_id'])
    except (ValueError, KeyError, OSError):
        return None
    existing = response.get('effective_packet', response['packet'])
    if any(d['doc_id'] == document['doc_id'] for group in ('primary_documents', 'context_documents')
           for d in existing.get(group, [])):
        return None
    return option, document


def _scholar_review_details(st, root, response, question, actor=None, reason=''):
    """Present only the selected object's canonical relations and selected facet."""
    model = st.session_state.get('k2_scholar_model')
    st.subheader('Selected source object')
    if not model:
        return
    details = selection_details(model, st.session_state.get('k2_scholar_selected'),
                                st.session_state.get('k2_scholar_facet'), root=root)
    selected = details['selected']
    if selected is None:
        st.caption('Select a term, construction, or step in the source.')
        return
    objects = model['objects']

    def name(row):
        if row.get('surface') or row.get('formal'):
            return row.get('surface') or row['formal']
        try:
            return label_en('operation', row['operation'])
        except (ValueError, KeyError):
            return row.get('operation', 'Source object')

    def role_name(code):
        try:
            return label_en('port', code)
        except ValueError:
            return code

    st.write(name(selected))
    if selected.get('gloss', {}).get('kind') == 'reviewed':
        st.caption('Current interpretation · reviewed')
        st.write(selected['gloss']['label'])
    if selected.get('semantic_candidates'):
        st.caption('Machine suggestions · unranked')
        for candidate in selected['semantic_candidates']:
            label = expression_label(candidate['structured_expression']) if candidate.get('structured_expression') else candidate.get('expression', '')
            st.write('• ' + label + ' · ' + candidate.get('status', 'suggested'))
    if selected.get('adjudication'):
        st.caption('suggested · read-only in current adjudication schema')
    if details['facets'] and not details['facet']:
        st.write('Review overview')
        for facet in details['facets']:
            st.caption(facet['label'].rstrip('?') + ' · ' + facet['status'])
            st.write(facet['hover'])
            if facet['facet'] == 'source_supply':
                for flow in details['flows']:
                    st.caption(flow['formal'] + ' · ' + flow['display_status'])
            if facet['question_id'] and st.button('Review', key='k2_facet_select:' + facet['facet_key']):
                st.session_state['k2_scholar_facet'] = facet['facet_key']
                st.session_state['k2_question'] = facet['question_id']
                st.rerun()
    if details['uses'] or details['steps'] or details['named_outputs']:
        st.caption('Local computational context')
    if details['composition']:
        st.caption('Term composition')
        for part in details['composition']:
            labels = part['gloss'].get('labels', [part['gloss']['label']])
            st.write(part['surface'] + ' · ' + ' / '.join(labels))
    for use in details['uses']:
        st.caption('Used in · ' + role_name(use['role']))
        st.write(use['construction']['surface'])
    if selected.get('slots'):
        st.caption('Construction slots')
        for slot in selected['slots']:
            st.write(role_name(slot['name']) + ' → ' + slot.get('surface', ''))
    for naming in details['naming']:
        st.caption('Textual naming')
        st.write(naming['surface'])
    for output in details['named_outputs']:
        st.caption('Computational role')
        st.write(name(output['step']) + ' → ' + role_name(output['port']))
    for step in details['steps']:
        st.caption('Computational step · ' + name(step))
        for item in step.get('inputs', []):
            if item.get('term_id') in objects:
                value = name(objects[item['term_id']])
            elif item.get('from_step_id') in objects:
                value = 'from ' + name(objects[item['from_step_id']])
            elif 'literal' in item:
                value = str(item['literal'])
            else:
                value = item.get('surface_reference', 'local source grounding unavailable')
            st.write(role_name(item['role']) + ' → ' + value)
        for output in step.get('outputs', []):
            st.write(role_name(output['port']) + ' → ' + (' / '.join(output.get('labels', [])) or 'unnamed result'))
    for flow in details['flows']:
        st.caption(flow['formal'] + ' · ' + flow['display_status'])
        producer = flow.get('producer_source') or {}
        if producer.get('sections'):
            st.caption('Historical source · §' + ', §'.join(map(str, producer['sections'])))
    if details['context_requirement']:
        context = details['context_requirement']
        st.write('Construction context requirement')
        st.caption('Cause')
        st.write(context['cause'])
        st.caption('Missing inputs')
        st.write(', '.join(context['missing_inputs']))
    assistance = details['source_assistance']
    if assistance is not None:
        st.write('Canonical producer candidates')
        if not assistance['candidates']:
            st.caption('No canonical producer candidate is currently recorded.')
        for candidate in assistance['candidates']:
            st.write(candidate['label'])
        st.caption('Search hints — not yet linked')
        for heading, key in (('Registered parameter/declaration hits', 'registered'),
                             ('Other exact source occurrences', 'other')):
            st.write(heading)
            if not assistance[key]:
                st.caption('No exact hit.')
            for hit in assistance[key]:
                caption = '§' + ', §'.join(map(str, hit['sections'])) + ' · ' + hit['quote']
                st.caption(caption + ' · ' + (hit.get('unit_type') or 'source'))
                with st.expander('Inspect · ' + caption):
                    text = hit['text']; start, end = hit['span']
                    st.html('<div style="white-space:pre-wrap">' + escape(text[:start]) + '<mark>'
                            + escape(text[start:end]) + '</mark>' + escape(text[end:]) + '</div>')
                    attachment = context_hint_attachment(root, response, question, model['source'].get('source_id'), hit)
                    if attachment:
                        option, document = attachment
                        if st.button('Add as context & re-run',
                                     key='k2_hint_attach:' + details['facet']['facet_key'] + ':' + hit['unit_id'] + ':' + str(start),
                                     disabled=not actor or not actor.get('id') or not reason):
                            try:
                                decisions, events = _option_submission(response, question, option, actor, reason,
                                                                         context_document=document)
                                _submit(st, root, response, decisions=decisions, management_events=events)
                            except (ValueError, KeyError, TypeError) as error:
                                st.error('Not saved: ' + str(error))
                    else:
                        st.caption('Read-only here: already included, or this question offers no supported context attachment.')
    last = st.session_state.get('k2_last_scholar_diff')
    if last and (last['job_id'], last['revision']) == (response['job']['job_id'], response['job']['revision']):
        delta = last['diff']
        st.subheader('Last change')
        st.caption(str(delta['summary']['semantic_change_count']) + ' source annotation changes')
        for layer, changes in delta['layers'].items():
            counts = [(key, len(changes[key])) for key in ('added', 'removed', 'changed') if changes[key]]
            if counts:
                st.write(layer.replace('_', ' ') + ' · ' + ', '.join(str(n) + ' ' + key for key, n in counts))
    with st.expander('Why / Evidence'):
        st.json({'object': selected, 'facet': details['facet'],
                 'question_id': question.get('id') if question else None,
                 'explicit_decision_refs': selected.get('decision_refs', [])})


def _compose_controls(st, response, question):
    """Build a source-grounded registry expression, bounded to three levels."""
    registry = load_kernel()
    quote = question['anchor']['quote']
    applicable = [concept for concept in registry['concepts']
                  if any(cue['form'] in quote and concept['id'] in cue['sense_concept_ids']
                         for cue in registry['lexical_cues'])]
    if not applicable:
        st.caption('The current registry cannot express a local composition here.')
        return None
    rules = {row['build']['op'] for row in registry['composition_rules']}
    constructors = [row for row in registry['constructors'] if row['id'] in rules]

    def label(row):
        return CONCEPT_LABELS.get(row['id'], row.get('label_en') or row.get('label_zh') or row['id'])

    def concept_sort(concept):
        return {'quantity_concept': 'quantity_expression',
                'scope_concept': 'scope_expression'}.get(concept['family'], 'semantic_expression')

    def accepts(expected, actual):
        return expected == 'semantic_expression' or expected == actual

    def available_sorts(depth):
        sorts = {concept_sort(concept) for concept in applicable}
        for _ in range(depth - 1):
            for constructor in constructors:
                if all(any(accepts(expected, actual) for actual in sorts)
                       for expected in constructor['arguments'].values()):
                    sorts.add(constructor['result_sort'])
        return sorts

    def build(expected, depth, path):
        concepts = [concept for concept in applicable if accepts(expected, concept_sort(concept))]
        nested = [constructor for constructor in constructors if depth > 1 and accepts(expected, constructor['result_sort'])
                  and all(any(accepts(slot_sort, actual) for actual in available_sorts(depth - 1))
                          for slot_sort in constructor['arguments'].values())]
        choices = [('concept', concept['id']) for concept in concepts] + [('constructor', row['id']) for row in nested]
        if not choices:
            return None
        selected = st.selectbox('Composition ' + path, choices, key='k2_compose:' + question['id'] + ':' + path,
            format_func=lambda choice: (label(next(row for row in concepts if row['id'] == choice[1]))
                if choice[0] == 'concept' else CONSTRUCTOR_LABELS.get(choice[1], choice[1]).split('{')[0].strip()))
        if selected[0] == 'concept':
            return {'op': 'concept', 'concept_id': selected[1]}
        constructor = next(row for row in nested if row['id'] == selected[1])
        arguments = {slot: build(slot_sort, depth - 1, path + '.' + slot)
                     for slot, slot_sort in constructor['arguments'].items()}
        return None if any(value is None for value in arguments.values()) else {'op': constructor['id'], 'arguments': arguments}

    expression = build('semantic_expression', 3, 'meaning')
    if expression is None:
        st.caption('No source-grounded registered composition is available here.')
        return None
    def preview(node):
        if node['op'] == 'concept':
            return label(next(row for row in applicable if row['id'] == node['concept_id']))
        return node['op'] + '(' + ', '.join(name + '=' + preview(value) for name, value in node['arguments'].items()) + ')'
    st.caption('Preview: ' + preview(expression))
    return compose_term_interpretation(question['anchor'], response['branch_id'], expression)


def _option_submission(response, question, option, actor, reason, *, context_document=None, composed=None):
    target = question.get('decision_target', question['anchor'])
    payload = dict(option.get('payload', {}))
    if context_document is not None:
        payload['document'] = context_document
    if composed is not None:
        payload['claim'] = composed
    decision = service.review_decision(response, option['action'], target, payload,
                                       actor, reason, option.get('depends_on', []))
    semantic_target = option.get('semantic_target')
    if semantic_target is None:
        semantic_target = service.normalize_decision_target(decision['action'], decision['payload'], decision['targets'])
    events = [{'event_id': 'management:' + uuid4().hex, 'action': 'manage',
               'target': target, 'facet': facet, 'semantic_target': semantic_target,
               'branch_id': response['branch_id'], 'actor': actor,
               'created_at': service._now(), 'reason': reason,
               'depends_on': list(decision['depends_on'])}
              for facet in option.get('management_facets', [])]
    return [decision], events


def _question_controls(st, root, response, question, questions, actor, reason):
    st.subheader('Current question')
    if question is None:
        st.info('No current scholar question. Review history and execution remain available.')
        return
    ids = [row['id'] for row in questions]
    index = ids.index(question['id'])
    left, right = st.columns(2)
    if left.button('Previous', key='k2_previous', disabled=index == 0):
        st.session_state['k2_question'] = ids[index - 1]; st.rerun()
    if right.button('Next pending', key='k2_next', disabled=index == len(ids) - 1):
        st.session_state['k2_question'] = ids[index + 1]; st.rerun()
    st.write(question['title'])
    options = list(question.get('options', []))
    if question['kind'] == 'term_interpretation':
        options.insert(max(0, len(options) - 1), {'id': 'local-compose',
            'label': 'Compose a local interpretation from registered concepts',
            'mode': 'compose', 'action': 'set_term_interpretation', 'payload': {},
            'assertions': ['Human-authored interpretation for this occurrence only.',
                           'No numerical value or producer is created.'],
            'management_facets': [], 'depends_on': []})
    if not options:
        st.caption('No supported interpretation is available for this source location yet.')
        return
    option_ids = [row['id'] for row in options]
    selected_id = st.radio('Interpretation', option_ids,
        format_func=lambda ident: next(row['label'] for row in options if row['id'] == ident),
        key='k2_option:' + question['id'])
    option = next(row for row in options if row['id'] == selected_id)
    st.caption('This selection is not saved. Only Confirm and re-run records a decision.')
    context_document = None
    if option.get('requires_context_picker'):
        sources = list_review_sources(root)
        source_id = st.selectbox('Additional source', [row['id'] for row in sources], key='k2_context_source')
        unit = st.selectbox('Source section', _units(root, source_id), key='k2_context_unit')
        context_document = service.review_context_document(root, source_id, unit)
    composed = None
    if option.get('mode') == 'compose':
        try:
            composed = _compose_controls(st, response, question)
        except ValueError:
            st.caption('This combination is outside the current registry or source. Choose another.')
    assertions = option.get('assertions') or []
    if assertions:
        st.caption('This choice will assert:')
        for assertion in assertions:
            st.write('• ' + assertion)
    with st.expander('Why these options?'):
        st.write(question.get('evidence', {}))
    if st.button('Confirm and re-run', key='k2_save',
                 disabled=not actor['id'] or not reason or option.get('mode') == 'compose' and composed is None):
        try:
            decisions, events = _option_submission(response, question, option, actor, reason,
                                                     context_document=context_document, composed=composed)
            _submit(st, root, response, decisions=decisions, management_events=events)
        except (ValueError, KeyError, TypeError) as error:
            st.error('Not saved: ' + str(error))


def _history(st, root, response, actor):
    with st.expander('Decision history and retract'):
        decisions = response['session']['decisions']
        if not decisions:
            st.caption('No saved decisions yet.')
            return
        status = response['compilation']['replay']['decision_status']
        for row in decisions:
            st.write(row['targets'][0].get('quote', ''), row['reason'], status.get(row['decision_id'], {}).get('status'))
        action_labels = {'declare_parameter': 'Standalone numerical-check value', 'set_quantity_semantics': 'Quantity interpretation',
            'set_term_boundary': 'Term boundary', 'set_term_interpretation': 'Term interpretation',
            'bind_value': 'Source binding', 'attach_context': 'Additional context', 'retract': 'Retraction'}
        labels = {row['decision_id']: str(index + 1) + ' · ' + action_labels.get(row['action'], row['action'].replace('_', ' '))
                  + ' · ' + row['targets'][0].get('quote', '') + ' · ' + row['reason']
                  for index, row in enumerate(decisions)}
        selected_id = st.selectbox('Decision to retract', [row['decision_id'] for row in reversed(decisions)],
            key='k2_retract_target', format_func=labels.__getitem__)
        why = st.text_input('Reason for retracting', key='k2_retract_reason')
        if st.button('Retract and re-run', key='k2_retract', disabled=not why.strip() or not actor['id']):
            selected = next(row for row in decisions if row['decision_id'] == selected_id)
            primary_doc = response['packet']['primary_documents'][0]
            base_target = anchor_for(response['packet'], primary_doc['doc_id'], 0, 1)
            decision = service.review_decision(response, 'retract', base_target,
                                               {'decision_id': selected_id}, actor, why.strip())
            _submit(st, root, response, decisions=[decision])


def _management(st, root, response, question, target, actor, reason):
    with st.expander('Management'):
        scopes = [row for row in response['managed_scope'] if row['managed']]
        st.caption('A managed facet stays under review after its interpretation is retracted.')
        action = st.selectbox('Scope action', ['manage', 'unmanage'], key='k2_management_action')
        if action == 'unmanage' and scopes:
            groups = _managed_interpretation_groups(scopes)
            index = st.selectbox('Managed interpretation', range(len(groups)), key='k2_release_scope',
                format_func=lambda i: (groups[i][0]['target']['quote'] + ' · '
                    + ('interpretation takeover (' + str(len(groups[i])) + ' facets)'
                       if groups[i][0].get('semantic_target') is not None else groups[i][0]['facet'])))
            release_scopes = groups[index]
            manage_target = facet = semantic_target = None
        else:
            release_scopes = []
            choices = []
            if question and question.get('anchor'):
                for option in question.get('options', []):
                    for offered in option.get('management_facets', []):
                        choices.append((question['anchor'], offered, option.get('semantic_target'),
                                        offered.replace('_', ' ').title()))
                if question['kind'] in ('term_boundary', 'term_interpretation'):
                    facet = question['kind']
                    normalized = service.normalize_decision_target('set_' + facet, {}, [question['anchor']])
                    choices.append((question['anchor'], facet, normalized,
                                    'Term boundary' if facet == 'term_boundary' else 'Term meaning'))
            if not choices and target is not None:
                choices = [(target, facet, None, facet.replace('_', ' ').title())
                           for facet in review_jobs.FACETS]
            unique = list({(facet, str(semantic)): (anchor, facet, semantic, label)
                           for anchor, facet, semantic, label in choices}.values())
            if unique:
                selected = st.selectbox('Reviewed aspect', range(len(unique)), key='k2_facet',
                    format_func=lambda index: unique[index][3])
                manage_target, facet, semantic_target, _ = unique[selected]
            else:
                manage_target = facet = semantic_target = None
        note = st.text_input('Management note', value=reason, key='k2_management_reason')
        label = 'Release this interpretation takeover' if action == 'unmanage' else 'Save management and re-run'
        disabled = (not actor['id'] or not note.strip()
                    or (action == 'unmanage' and not release_scopes)
                    or (action != 'unmanage' and manage_target is None))
        if st.button(label, key='k2_manage', disabled=disabled):
            if action == 'unmanage':
                _submit(st, root, response, management_events=release_interpretation_events(
                    release_scopes, response['branch_id'], actor, note.strip(), service._now()))
            else:
                event = {'event_id': 'management:' + uuid4().hex, 'action': action,
                         'target': manage_target, 'facet': facet, 'branch_id': response['branch_id'],
                         'actor': actor, 'created_at': service._now(), 'reason': note.strip()}
                if semantic_target is not None:
                    event['semantic_target'] = semantic_target
                _submit(st, root, response, management_events=[event])
        for row in response['managed_scope']:
            st.write(row['target']['quote'], row['facet'], row['status'])


def _execution(st, root, response):
    with st.expander('Run current reviewed model'):
        prior = st.session_state.get('k2_execution')
        if prior:
            if service.review_execution_stale(prior, response):
                st.warning('STALE — re-run required')
            else:
                st.write('Status: ' + prior['status'])
                st.write('Graph: ' + prior.get('graph_status', 'unknown'))
                if prior['status'] == 'executed' and prior.get('graph_status') == 'partial':
                    st.write('Numerical check: executed for current closed region')
                st.write('Job: ' + prior['job_id'] + ' · revision ' + str(prior['revision']) +
                         ' · branch ' + prior['branch_id'])
                st.caption('Analysis identity: ' + prior['analysis_identity'])
                st.write('Inputs', prior['inputs'])
                quantities = prior.get('output_quantities')
                if quantities:
                    rows = []
                    for name, quantity in quantities.items():
                        representation = quantity.get('representation') or {}
                        numerator = representation.get('kind') == 'fraction_numerator'
                        denominator = representation.get('denominator_value')
                        amount = (str(quantity['value']) + '/' + str(denominator)
                                  if numerator and denominator is not None else str(quantity['value']))
                        meaning = ((quantity.get('coordinate_kind') or '') + ' ' + quantity.get('unit', 'unknown')).strip()
                        if numerator:
                            meaning = 'Fraction of a day' if quantity.get('unit') == 'day_fraction' else 'Fraction numerator'
                        rows.append({'Output': name, 'Value': amount, 'Quantity meaning': meaning})
                    st.table(rows)
                    with st.expander('Execution evidence'):
                        st.json(quantities)
                else:
                    st.write('Outputs', prior.get('named_outputs', prior.get('outputs', {})))
                if prior.get('unresolved'):
                    st.write('Unresolved', prior['unresolved'])
        names = service.review_execution_inputs(response['graph'])
        inputs = {}
        for name in names:
            raw = st.text_input('Value for ' + name, key='k2_input:' + name)
            if raw.strip():
                try:
                    inputs[name] = int(raw.strip())
                except ValueError:
                    st.error('Use an exact integer for ' + name)
        if st.button('Run reviewed model', key='k2_run', disabled=len(inputs) != len(names)):
            try:
                displayed = st.session_state['k2_displayed']
                st.session_state['k2_execution'] = service.execute_review_job(
                    root, response['job']['job_id'], inputs,
                    expected_revision=displayed['revision'], expected_digest=displayed['digest'])
                st.rerun()
            except (ValueError, OSError, RuntimeError) as error:
                st.error('Execution did not run: ' + str(error))


def _diagnostics(st, response, hidden_questions=()):
    groups = {'system_diagnostic': 'System diagnostics',
              'decision_issue': 'Decisions needing review',
              'future_semantic_question': 'Future semantic work'}
    for category, label in groups.items():
        rows = [row for row in response['review_forms'] if row.get('category') == category]
        if rows:
            with st.expander(label + ' · ' + str(len(rows))):
                if category == 'system_diagnostic':
                    st.caption('The analysis has an internal consistency problem. This is not a historical interpretation question.')
                for row in rows:
                    st.write(row['question'].get('reason', category))
                    with st.expander('Technical details'):
                        st.json(row['question'])
    if hidden_questions:
        with st.expander('Future semantic work · ' + str(len(hidden_questions))):
            st.caption('These records have no grounded resolving answer and are not annotation prompts.')
            for question in hidden_questions:
                st.write(question['title'])
                with st.expander('Technical details'):
                    st.json(question.get('evidence', {}))


def render(root, language='en'):
    import streamlit as st
    st = _LocalizedStreamlit(st, language)
    st.subheader('Parser Inspector')
    requested = st.session_state.pop('k2_requested_job', None) or st.query_params.get('review_job')
    manual_job = requested or st.session_state.get('k2_active_saved_job')
    handoff = st.session_state.pop('k2_requested_selection', None)
    if handoff:
        st.session_state['k2_source'] = handoff['source_id']
        st.session_state['k2_section'] = handoff['unit_id']
    if requested:
        try:
            _set_selection_from_job(st, root, requested)
        except (ValueError, OSError):
            requested = None
    selection = _selection_picker(st, root)
    if selection is None:
        return None
    if manual_job:
        try:
            saved = review_jobs.load_job(root, manual_job)['source_selection']
            same_visible_selection = (saved.get('source_id') == selection['source_id']
                                      and saved.get('primary_unit_ids') == selection['primary_unit_ids'])
        except (ValueError, OSError):
            same_visible_selection = False
        if same_visible_selection:
            response = service.compile_review_job(root, manual_job)
            st.session_state['k2_active_saved_job'] = manual_job
        else:
            st.session_state.pop('k2_active_saved_job', None)
            response = service.resolve_current_review_job(root, selection)
    else:
        response = service.resolve_current_review_job(root, selection)
    job_id = response['job']['job_id']
    actor, reason = _session_advanced(st, root, response,
                                      response['job']['source_selection'] if manual_job else selection)
    if response['freshness']['status'] != 'current':
        st.error('This job is read-only under the current analysis: ' + response['freshness']['reason'])
        with st.expander('Saved history'):
            for row in response['job']['session']['decisions']:
                st.write(row['reason'], row['targets'])
        return response
    if st.session_state.get('k2_procedure_view') != 'Procedure Model':
        st.caption('Data-flow status: ' + _data_flow_status(response['summary']['graph_status']) + ' ⓘ')
    last = st.session_state.get('k2_last_effects')
    if last and last[:2] == (job_id, response['job']['revision']):
        st.success(last[2].get('message_en') or last[2].get('message') or 'Saved and recompiled.')
        with st.expander('What changed'):
            st.write(last[2])
    all_questions = response.get('questions', [])
    questions = [question for question in all_questions
                 if any(option.get('action') != 'defer' for option in question.get('options', []))]
    hidden_questions = [question for question in all_questions if question not in questions]
    if 'k2_question' not in st.session_state or st.session_state.get('k2_source_job') != job_id:
        st.session_state['k2_question'] = None
    question = next((row for row in questions if row['id'] == st.session_state.get('k2_question')), None)
    source_col, choice_col = st.columns([7, 3])
    with source_col:
        target = _source_view(st, root, response, question, questions)
        if st.session_state.get('k2_procedure_view') != 'Procedure Model':
            _boundary_save(st, root, response, actor, reason.strip())
    with choice_col:
        question = next((row for row in questions if row['id'] == st.session_state.get('k2_question')), None)
        if st.session_state.get('k2_procedure_view') == 'Procedure Model':
            _procedure_details(st, response)
        else:
            _scholar_review_details(st, root, response, question, actor, reason.strip())
            if question is not None or not st.session_state.get('k2_scholar_selected'):
                _question_controls(st, root, response, question, questions, actor, reason.strip())
    _history(st, root, response, actor)
    _management(st, root, response, question, target, actor, reason.strip())
    _diagnostics(st, response, hidden_questions)
    _execution(st, root, response)
    st.session_state['k2_displayed'] = {'job_id': job_id, 'revision': response['job']['revision'],
                                        'digest': response['job_digest']}
    return response
