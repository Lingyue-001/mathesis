"""Scholar-facing source segmentation controls; all mutations go through the store."""
import streamlit as st
import re
from html import escape
from streamlit.components.v2 import component

from source_adapters import corpus_index as index
from source_adapters import corpus_review as store


# Presentation only: related document types share hue, with distinct lightness.
_TYPE_TONES = {
    'procedure': (214, 91), 'alternative_procedure': (214, 84),
    'computational_exposition': (214, 96),
    'parameter': (155, 92), 'parameter_block': (155, 83),
    'reference_data': (36, 93), 'table': (36, 84),
    'heading': (268, 88), 'discourse': (268, 96),
}


def _type_style(code):
    hue, light = _TYPE_TONES[code]
    return (f'background:hsl({hue} 40% {light}%);color:hsl({hue} 35% 27%);'
            'border-radius:4px;padding:2px 7px;font-size:.78rem;'
            'font-weight:500;white-space:nowrap;line-height:1.5')


def _type_badge(code):
    return f'<span style="{_type_style(code)}">{escape(code)}</span>'


def _type_labels(label, units):
    """Decorate the existing searchable select; never change its value or events.

    Streamlit options are plain text. Its pinned version exposes original option
    indices in data-key, including after filtering. Scope to the accessible list
    label so a relation/type/source selector cannot inherit another list's colors.
    """
    scope = f'[role="listbox"][aria-label="{label}"] [role="option"]'
    rules = [f'{scope} {{gap:8px;}}', f'{scope}::after {{margin-left:auto;flex-shrink:0;}}']
    for code in _TYPE_TONES:
        positions = ','.join(f'[data-key="{i}"]' for i,u in enumerate(units) if u['type'] == code)
        if positions:
            rules.append(f'{scope}:is({positions})::after {{content:"{code}";{_type_style(code)}}}')
    st.html('<style>' + '\n'.join(rules) + '</style>')


# Only static trusted markup/code. Source text enters via data + textContent.
def _boundary_component():
    return component(
        'segmentation_boundaries',
        html='<div class="source" role="group" aria-label="拆分边界"></div>',
        css='''
        .source {line-height:2.4; white-space:pre-wrap; font-size:1.1rem;}
        button {font:inherit; color:inherit; background:transparent; padding:0 2px;
          border:0; border-right:2px solid transparent; cursor:pointer;}
        button:hover {background:#ececec; color:#111;}
        button[aria-pressed="true"] {border-right-color:#bb4819; background:#ffe3ce; color:#111;}
        ''',
        js='''export default function({parentElement, data, setStateValue}) {
          const host = parentElement.querySelector('.source');
          host.replaceChildren();
          const selected = new Set(data.boundaries || []);
          const chars = [...data.text];
          chars.forEach((char, i) => {
            const button = document.createElement('button');
            button.textContent = char;
            button.type = 'button';
            button.dataset.boundary = String(i + 1);
            button.setAttribute('aria-label', `第 ${i + 1} 字「${char}」后拆分`);
            button.setAttribute('aria-pressed', String(selected.has(i + 1)));
            button.disabled = i + 1 === chars.length;
            button.addEventListener('click', () => {
              selected.has(i + 1) ? selected.delete(i + 1) : selected.add(i + 1);
              button.setAttribute('aria-pressed', String(selected.has(i + 1)));
              setStateValue('boundaries', [...selected].sort((a,b) => a-b));
            });
            host.append(button);
          });
        }''')


def _status(unit):
    return unit['human_review'][-1]['status'].upper() if unit['human_review'] else 'UNREVIEWED'


def _label(unit, *, review=False):
    sections = ','.join(map(str, unit['sections']))
    text = unit['text_original'].strip()
    end = re.search(r'[，。；：！？、,.!?;:\r\n]', text)
    preview = text[:end.start()].rstrip() if end else text
    label = f"§{sections} · {preview} · {unit['source_spans'][0]['start']}"
    if review:
        status = {'ACCEPTED': '已审·原样接受', 'MODIFIED': '已审·已修改',
                  'STALE': '待重审'}.get(_status(unit))
        if status:
            label += f' · [{status}]'
    return label


def _text_runs(unit, *, compared=(), reference=None):
    """Highlight changed block membership by source address, never substring match.

    A split keeps the leading part; following parts have moved into new blocks.
    A merge highlights text outside the selected original block. No text is edited.
    """
    start = unit['source_spans'][0]['start']
    if reference is None:
        reference = next((u for u in compared if any(a <= start < b for a,b in index.unit_anchor(u))), unit)
    original = {s['start']+i: char for s in reference['source_spans'] for i,char in enumerate(s['text'])}
    moved = (start != reference['source_spans'][0]['start']
             and all(a in original and b-1 in original for a,b in index.unit_anchor(unit)))
    runs = []
    for span in unit['source_spans']:
        for i,char in enumerate(span['text'], span['start']):
            changed = moved or original.get(i) != char
            if runs and runs[-1]['changed'] == changed:
                runs[-1]['text'] += char
            else:
                runs.append({'text': char, 'changed': changed})
    return runs


def has_unsaved_changes(exclude=()):
    for name, default in st.session_state.get('seg_draft_defaults', {}).items():
        if any(name.startswith(prefix) for prefix in exclude):
            continue
        value = st.session_state.get(name, default)
        if name.startswith('seg_boundaries:'):
            value = (value or {}).get('boundaries', [])
        if value != default:
            return True
    return False


def _clear_draft():
    st.session_state['seg_draft_defaults'] = {}
    st.session_state['seg_editor_epoch'] = st.session_state.get('seg_editor_epoch', 0) + 1


def _select_unit(widget, value):
    if has_unsaved_changes():
        return
    _clear_draft()
    st.session_state[widget] = value


def _select_effective_unit(widget, focus_key, units, value):
    """Move a reviewed-partition cursor and retain its source address."""
    if has_unsaved_changes():
        return
    _clear_draft()
    st.session_state[widget] = value
    st.session_state[focus_key] = index.unit_anchor(units[value])


def guard_selection(widget, previous):
    """Also reject navigation queued before disabled controls reach the browser."""
    if has_unsaved_changes():
        st.session_state[widget] = previous
    else:
        _clear_draft()


def guard_effective_selection(widget, focus_key, units, previous):
    if has_unsaved_changes():
        st.session_state[widget] = previous
        return
    selected = st.session_state.get(widget, previous)
    if not isinstance(selected, int) or not 0 <= selected < len(units):
        selected = previous
        st.session_state[widget] = selected
    st.session_state[focus_key] = index.unit_anchor(units[selected])
    _clear_draft()


def _draft_field(name, default):
    st.session_state.setdefault('seg_draft_defaults', {})[name] = default
    st.session_state.setdefault('seg_draft_rendered_defaults', {})[name] = default
    return name


def _relations(unit, units):
    if not unit['relations']:
        st.caption('relations：无')
    for relation in unit['relations']:
        ids = relation.get('target_ids', []) + [relation.get('target_id')]
        targets = [u for u in units if u['id'] in ids or
                   (relation.get('target_spans') and index.overlaps(index.unit_anchor(u), relation['target_spans']))]
        st.text(relation['kind'] + ' → 关联原文')
        for target in targets:
            st.caption(_label(target))
            st.text(target['text_original'])
        if not targets or relation.get('needs_review'):
            st.caption('关联目标待复核。' if not targets else '关联目标已重新分块，待复核；以上保留各块完整原文。')
        if relation.get('basis'):
            st.caption(relation['basis'])


def _card(unit, units, *, machine=False, compared=(), reference=None):
    with st.container(border=True):
        if machine:
            st.caption(f"machine confidence: {unit['detection']['confidence']} · rule: {unit['detection']['rule']}")
        runs = _text_runs(unit, compared=compared, reference=reference)
        if any(run['changed'] for run in runs):
            pieces = [('<mark class="seg-source-change" style="background:color-mix(in srgb,currentColor 10%,transparent);color:inherit;border-radius:3px">'
                       + escape(run['text']) + '</mark>') if run['changed'] else escape(run['text']) for run in runs]
            st.html('<div class="seg-source-text" style="white-space:pre-wrap;line-height:1.7">' + ''.join(pieces) + '</div>')
        else:
            st.text(unit['text_original'])
        st.caption('sections: ' + ', '.join(map(str, unit['sections'])) + ' · source spans: ' +
                   ', '.join(f"{s['start']}–{s['end']}" for s in unit['source_spans']))
        _relations(unit, units)


def _source_picker(root, *, full_text=False):
    sources = {s['id']: s for s in index.list_review_sources(root)}
    if not sources:
        st.info('没有已登记的 calendars-*.md。请在现有 source_texts registry 登记 source id。')
        return
    source, navigation = st.columns([5, 1], vertical_alignment='bottom')
    source_id = source.selectbox('Source', list(sources), format_func=lambda key: sources[key]['label'], key='seg_source',
                             disabled=has_unsaved_changes(), on_change=guard_selection,
                             args=('seg_source', st.session_state.get('seg_source', next(iter(sources)))))
    navigation.button('返回 Review' if full_text else 'Full text',
                      key='seg_back_review' if full_text else 'seg_full_text',
                      disabled=has_unsaved_changes(), on_click=_select_unit,
                      args=('inspector_page', 'Segmentation Review' if full_text else 'Corpus Full Text'))
    return source_id


def _keep_review_state():
    # Keep absent widgets and resend their values when the review page remounts.
    for name in list(st.session_state):
        if name.startswith('seg_auto:') or name in ('seg_reviewer', 'seg_actor', 'seg_note'):
            st.session_state[name] = st.session_state[name]


def render_full_text(root):
    """Read-only continuous view of effective units; no compiler or new data path."""
    _keep_review_state()
    st.header('Corpus Full Text')
    source_id = _source_picker(root, full_text=True)
    if source_id is None:
        return
    if not all(path.exists() for path in store.paths(root, source_id)):
        st.info('尚未生成分块，请返回 Review 生成 corpus index。')
        return
    try:
        state = store.load(root, source_id)
    except (ValueError, OSError) as error:
        st.error(str(error))
        return
    if state['stale']:
        st.warning(f"STALE：以下为旧分块，来源变化后尚未重验。{state['stale_reason']}")
    units = sorted(state['effective']['units'], key=lambda u: u['source_spans'][0]['start'])
    st.caption(f"EFFECTIVE · {len(units)} 块 · Revision {len(state['overrides'].get('history', []))}。"
               '按原文顺序连读全部有效分块；包含尚未人工审阅的块。')
    paragraphs = []
    for unit in units:
        sections = ', '.join(map(str, unit['sections']))
        paragraphs.append(f'<section data-unit-id="{escape(unit["id"], quote=True)}">'
                          f'<p style="white-space:pre-wrap;line-height:2">{_type_badge(unit["type"])} '
                          f'<small>§{escape(sections)}</small>　'
                          f'<span class="seg-full-text-source">{escape(unit["text_original"])}</span></p></section>')
    st.html('<article class="seg-full-text">' + ''.join(paragraphs) + '</article>')


def render(root):
    from tools.parser_inspector.runner import refresh_dependencies
    refresh_dependencies(root)
    _keep_review_state()
    st.header('Corpus Segmentation Review')
    dirty = has_unsaved_changes()
    if dirty:
        st.warning('有未保存的修改。请先保存当前类型、关系或拆分，再切换文本块／来源；也可明确放弃草稿。')
        st.button('放弃未保存修改', key='seg_discard_draft', on_click=_clear_draft)
    source_id = _source_picker(root)
    if source_id is None:
        return
    def key(name):
        return name + ':' + source_id
    st.caption('审阅分块、类型与关系；原文和机器判断保留。所有修改保存到 override，再生成有效 corpus。')
    with st.expander('后台文件', key='seg_files_panel'):
        for path in (*store.paths(root, source_id), store.workspace(root, source_id) / 'manifest.json'):
            st.caption(str(path))
    identity = st.columns([2, 1, 3])
    reviewer = identity[0].text_input('审阅者', key='seg_reviewer', placeholder='填写姓名或研究者标识')
    actor_type = identity[1].selectbox('操作身份', ['human', 'automated_browser', 'scripted_test'],
                                      key='seg_actor', help='自动化验收必须记录实际 actor，不冒充真人。')
    note = identity[2].text_input('本次备注（可选）', key='seg_note')
    if not all(path.exists() for path in (*store.paths(root, source_id), store.workspace(root, source_id) / 'manifest.json')):
        st.info('尚未生成 corpus index。')
        if st.button('生成 corpus index', key=key('seg_generate')):
            try:
                store.regenerate(root, source_id=source_id)
                st.rerun()
            except (ValueError, OSError) as error:
                st.error(str(error))
        return
    try:
        live = store.load(root, source_id)
    except (ValueError, OSError) as error:
        st.error(str(error))
        return
    snapshot_key = key('seg_snapshot:' + str(root))
    if snapshot_key not in st.session_state:
        st.session_state[snapshot_key] = live
    state = st.session_state[snapshot_key]
    stale_page = state['revision'] != live['revision']
    if live['stale']:
        st.error(f"STALE / 已阻断：{live['stale_reason']}。旧 human_review 与 override 保留，不能在改变后的来源上继续应用。")
    if stale_page and dirty:
        st.warning('来源审阅状态已在其他页面更新。当前草稿保留；请放弃草稿后同步，不能覆盖新状态。')
    elif stale_page:
        st.session_state[snapshot_key] = live
        st.session_state[key('seg_notice')] = '已同步其他页面的修改；旧页面操作未提交，请在当前结果上继续。'
        st.rerun()
    notice = st.session_state.get(key('seg_notice'))
    notification = st.empty()
    if notice:
        notification.success(notice)
    auto, effective = state['auto']['units'], state['effective']['units']
    progress = state['manifest']['review_status']
    with st.container(key='seg_revision_' + state['revision']):
        st.text(f"Review progress: {progress['reviewed']} / {progress['total']}")
        st.caption(f"Modified: {progress['modified']} · Accepted unchanged: {progress['accepted']} · Unreviewed: {progress['unreviewed']}")
        st.caption(f"Revision {len(state['overrides'].get('history', []))} · {state['revision'][:12]}")
    # The navigation list is the reviewed partition.  AUTO remains a source
    # reference, but cannot be allowed to freeze the selector's type badge or
    # hide blocks created by a split/merge.
    first_unreviewed_auto = next((u for u in auto if not u['human_review']), None)
    first_unreviewed = next((i for i, u in enumerate(effective)
                             if first_unreviewed_auto and index.overlaps(index.unit_anchor(u), index.unit_anchor(first_unreviewed_auto))),
                            None)
    st.button('Resume review · 继续未审阅', key=key('seg_resume'), disabled=dirty or first_unreviewed is None,
              on_click=_select_effective_unit, args=(key('seg_auto'), key('seg_focus'), effective, first_unreviewed))
    focus = st.session_state.get(key('seg_focus'))
    focused = next((i for i, u in enumerate(effective)
                    if focus and index.overlaps(index.unit_anchor(u), focus)), None)
    cursor = focused if focused is not None else st.session_state.get(key('seg_auto'), first_unreviewed or 0)
    cursor = min(max(cursor, 0), len(effective) - 1)
    # Resend the selected value when its review label changes. Otherwise the
    # browser retains the old formatted label, which is no longer an option.
    st.session_state[key('seg_auto')] = cursor
    previous, following = st.columns(2)
    previous.button('← 上一块', key=key('seg_previous'), disabled=dirty or cursor == 0,
                    on_click=_select_effective_unit, args=(key('seg_auto'), key('seg_focus'), effective, cursor-1))
    following.button('下一块 →', key=key('seg_next'), disabled=dirty or cursor == len(effective)-1,
                    on_click=_select_effective_unit, args=(key('seg_auto'), key('seg_focus'), effective, cursor+1))
    _type_labels('Current effective unit', effective)
    selected = st.selectbox('Current effective unit', range(len(effective)), key=key('seg_auto'), disabled=dirty,
                            format_func=lambda i: _label(effective[i], review=True), on_change=guard_effective_selection,
                            args=(key('seg_auto'), key('seg_focus'), effective, cursor))
    target = effective[selected]
    anchor = index.unit_anchor(target)
    st.session_state[key('seg_focus')] = anchor
    originals = [u for u in auto if index.overlaps(anchor, index.unit_anchor(u))]
    original = originals[0]
    related = [target]
    disabled = stale_page or live['stale'] or not reviewer.strip()
    if not reviewer.strip():
        st.info('填写审阅者后可保存。')

    def save(action, unit, payload=None):
        try:
            if action == 'split_unit' and has_unsaved_changes(exclude=('seg_boundaries:',)):
                st.error('请先保存类型／关系，再保存拆分；已选边界会保留。')
                return
            updated = store.apply(root, action, index.unit_anchor(unit), payload or {},
                                  revision=state['revision'], actor={'type': actor_type, 'id': reviewer.strip()}, note=note, source_id=source_id)
            refresh_dependencies(root)
            st.session_state[snapshot_key] = updated
            st.session_state[key('seg_focus')] = index.unit_anchor(unit)
            st.session_state[key('seg_notice')] = ('已保存并重新生成 effective。' if updated['revision'] != state['revision']
                                           else '结果未改变，没有新增 override。')
            if action == 'set_relations':
                st.session_state['seg_relations_epoch'] = st.session_state.get('seg_relations_epoch', 0) + 1
            elif action != 'set_type':
                _clear_draft()
            st.rerun()
        except (ValueError, OSError) as error:
            st.error(str(error))


    left, right = st.columns(2)
    left = left.container(key='seg_auto_panel')
    right = right.container(key='seg_effective_panel')
    with left:
        st.subheader('AUTO · 机器原始单元')
        for source_unit in originals:
            _card(source_unit, auto, machine=True, compared=effective)
        questions = [q for q in state['auto']['review_queue'] if any(
            q.get('unit_id') == source_unit['id']
            or set(q.get('sections', [])) & set(source_unit['sections'])
            or q.get('left_section') in source_unit['sections']
            or q.get('right_section') in source_unit['sections']
            for source_unit in originals)]
        st.caption('Machine review queue（人工审阅状态另列）')
        for question in questions:
            st.text(question['kind'])
        if not questions:
            st.caption('没有机器排队问题；仍可人工审阅。')
    with right:
        st.subheader('EFFECTIVE · 当前分块')
        _card(target, effective, reference=original)
        same = (len(originals) == 1 and index.unit_anchor(original) == anchor
                and target['type'] == original['type']
                and index._anchored_relations(original['relations'], auto) == index._anchored_relations(target['relations'], effective))
        st.caption('Auto / effective 内容、边界、类型、关系相同。' if same else
                   '已改变：' + '；'.join(filter(None, [
                       '分块边界' if len(originals) != 1 or index.unit_anchor(original) != anchor else '',
                       '类型' if target['type'] != original['type'] else '',
                       '关系' if index._anchored_relations(target['relations'], effective) != index._anchored_relations(original['relations'], auto) else ''])))
        _editor(state, original, related, effective, disabled, save, key)
    accept, undo, reset, reset_all = st.columns(4)
    if accept.button('Accept · 原样接受', key=key('seg_accept'), disabled=disabled or dirty or not same or _status(original) == 'MODIFIED'):
        save('accept', original)
    if undo.button('Undo · 撤销上次操作', key=key('seg_undo'), disabled=disabled or dirty or not store.active_history(state['overrides'])):
        save('undo', target)
    if reset.button('Reset · 恢复本区域机器结果', key=key('seg_reset'), disabled=disabled or dirty):
        save('reset', target)
    all_anchor = {'source_spans': [span for unit in auto for span in unit['source_spans']]}
    if reset_all.button('退回最初 · 全文恢复机器结果', key=key('seg_reset_all'), disabled=disabled or dirty,
                        help='清空本 corpus 当前全部人工 review 与 override；历史保留，可用 Undo 复原。'):
        save('reset', all_anchor)
    st.caption('本区域 Reset 同时恢复与当前块通过 merge/split 关联的区域；全文恢复清空本 corpus 的当前人工状态。两者均可 Undo。')
    with st.expander('审阅记录', key='seg_history_panel'):
        names = {'accept': '原样接受机器分块', 'set_type': '修改类型', 'set_relations': '修改关系',
                 'split_unit': '拆分文本块', 'merge_up': '向上合并', 'merge_down': '向下合并',
                 'reset': '恢复机器结果', 'undo': '撤销先前判断',
                 'revert_revision': '撤销指定更改', 'restore_revision': '恢复历史状态'}
        history = [h for h in state['overrides'].get('history', []) if index.overlaps(anchor, h['source_spans'])]
        if not history:
            st.caption('尚未人工审阅。')
        for h in reversed(history):
            st.text(f"Rev {h.get('revision', state['overrides']['history'].index(h)+1)} · {h['actor']['id']} · {h['time']}\n"
                    f"{names.get(h['action'], h['action'])} · {h['actor']['type']}")
            if h.get('reverts'):
                st.caption(f"撤销 rev {h['reverts']}，保留原记录。")
            elif h.get('supersedes'):
                st.caption('修订此前区域判断：' + ', '.join(map(str, h['supersedes'])))
            if h.get('note'):
                st.text(h['note'])
            event_revision = h.get('revision', state['overrides']['history'].index(h)+1)
            if st.button(f"View before / after · rev {event_revision}", key=key(f'seg_history_{event_revision}')):
                st.session_state[key('seg_history_selected')] = event_revision
            actions = st.columns(3)
            is_active = h in store.active_history(state['overrides'])
            if actions[0].button(f'撤销此更改 · rev {event_revision}', key=key(f'seg_revert_{event_revision}'),
                                 disabled=disabled or dirty or not is_active):
                save('revert_revision', original, {'revision_id': event_revision})
            if actions[1].button(f'恢复到之前 · rev {event_revision}', key=key(f'seg_restore_before_{event_revision}'),
                                 disabled=disabled or dirty):
                save('restore_revision', original, {'revision_id': event_revision, 'side': 'before'})
            if actions[2].button(f'恢复到之后 · rev {event_revision}', key=key(f'seg_restore_after_{event_revision}'),
                                 disabled=disabled or dirty):
                save('restore_revision', original, {'revision_id': event_revision, 'side': 'after'})
            if st.session_state.get(key('seg_history_selected')) == event_revision:
                before, after = store.history_states(state, h)
                for col, title, rows in zip(st.columns(2), ('Before', 'After'), (before, after)):
                    with col:
                        st.caption(title)
                        for u in rows:
                            if index.overlaps(index.unit_anchor(u), h['source_spans']):
                                _card(u, rows)


def _editor(state, original, related, effective, disabled, save, key):
    dirty_at_start = has_unsaved_changes()
    anchor = index.unit_anchor(original)
    selected = original['id']
    focus = st.session_state.get(key('seg_focus'), anchor)
    focus_index = next((i for i, u in enumerate(related) if index.unit_anchor(u) == focus), 0)
    editing_key = 'seg_effective:' + state['revision'] + str(selected)
    _type_labels('编辑当前 effective 文本块', related)
    editing = st.selectbox('编辑当前 effective 文本块', range(len(related)), index=focus_index,
                           format_func=lambda i: _label(related[i]), key=editing_key,
                           disabled=has_unsaved_changes(), on_change=guard_selection,
                           args=(editing_key, st.session_state.get(editing_key, focus_index)))
    target = related[editing]
    position = effective.index(target)
    controls = st.columns(3)
    if controls[0].button('Merge ↑', key=key('seg_merge_up'), disabled=disabled or has_unsaved_changes() or position == 0,
                          help='与上一块合并正文，保留当前编辑块的类型和关系，不继承邻块的 alternative 判断。'):
        save('merge_up', target)
    if controls[1].button('Merge ↓', key=key('seg_merge_down'), disabled=disabled or has_unsaved_changes() or position == len(effective)-1,
                          help='与下一块合并正文，保留当前编辑块的类型和关系，不继承邻块的 alternative 判断。'):
        save('merge_down', target)
    controls[2].caption('合并邻块：\n' + '\n'.join(_label(effective[i]) for i in (position-1, position+1) if 0 <= i < len(effective)))
    widget_key = target['id'] + ':' + str(st.session_state.get('seg_editor_epoch', 0))
    st.session_state['seg_draft_rendered_defaults'] = {}
    type_panel, split_panel, relations_panel = st.tabs(
        ['Change type · 修改类型', 'Split · 点击原文边界', 'Edit relation · 编辑关系'],
        key=key('seg_editor_tabs'), on_change='rerun')
    with type_panel:
        with st.expander('分块类型说明 · 含义与边界'):
            st.caption('这是 corpus 分块的文献类型，不是 parser operation 或语义正确性判定。')
            for code, description in index.UNIT_TYPE_DESCRIPTIONS.items():
                st.html(f'<div>{_type_badge(code)} — {escape(description)}</div>')
        kind = st.selectbox('分块类型', index.UNIT_TYPES, index=index.UNIT_TYPES.index(target['type']),
                            key=_draft_field('seg_type:' + widget_key, target['type']), disabled=disabled)
        if st.button('保存类型', key=key('seg_save_type'), disabled=disabled):
            save('set_type', target, {'type': kind})
    with split_panel:
        st.caption('点击某字，在该字之后拆分；可选多个边界，再点取消。计数以 Unicode 字符为准，由后台换算原始 source offset。')
        boundary_key = _draft_field('seg_boundaries:' + widget_key, [])
        previous = st.session_state.get(boundary_key)
        selected_boundaries = previous.get('boundaries', []) if previous else []
        result = _boundary_component()(data={'text': target['text_original'], 'boundaries': selected_boundaries},
                             default={'boundaries': []}, key=boundary_key, on_boundaries_change=lambda: None)
        boundaries = result.boundaries or []
        if boundaries:
            points = [0, *sorted(boundaries), len(target['text_original'])]
            for i, (a, b) in enumerate(zip(points, points[1:]), 1):
                st.text(f"{i}. {target['text_original'][a:b]}")
        if st.button('保存拆分', key=key('seg_split'), disabled=disabled or not boundaries):
            save('split_unit', target, {'boundaries': boundaries})
    with relations_panel:
        widget_key += ':relations:' + str(st.session_state.get('seg_relations_epoch', 0))
        labels = {_label(u): u for u in effective if u['id'] != target['id']}
        st.caption('仅管理 corpus-level structural relations：当前块 → 对应术文。followup 属于 member_roles，由 split/merge 管理；dependency/data-flow 留给 parser/graph。')
        for code, description in index.RELATION_DESCRIPTIONS.items():
            st.text(f'{code} — {description}')
        rows = []
        options = ['请选择对应文本块', *labels]
        allow_alternative = target['type'] == 'alternative_procedure'
        if not allow_alternative:
            st.info('当前块是独立 procedure；不能新增或保留 alternative 关系。若这是另一术法，请先在 Change type 明确修改类型。')
        for i, relation in enumerate(target['relations']):
            current = next((label for label, u in labels.items() if index.unit_anchor(u) == relation.get('target_spans')), options[0])
            columns = st.columns([2, 4, 1])
            kinds = tuple(index.RELATION_DESCRIPTIONS)
            if not allow_alternative:
                columns[0].caption(relation['kind'])
                columns[1].caption(current)
                if columns[2].button('删除关系', key=key(f'seg_delete_relation:{i}'), disabled=disabled or has_unsaved_changes()):
                    save('set_relations', target, {'relations': [r for j, r in enumerate(target['relations']) if j != i]})
            else:
                kind = columns[0].selectbox(f'关系 {i+1} 类型', kinds, index=kinds.index(relation['kind']), key=_draft_field(f'seg_relation_kind:{widget_key}:{i}', relation['kind']), disabled=disabled)
                link = columns[1].selectbox(f'关系 {i+1} 对应文本块', options, index=options.index(current), key=_draft_field(f'seg_relation_target:{widget_key}:{i}', current), disabled=disabled)
                if columns[2].button('删除关系', key=key(f'seg_delete_relation:{i}'), disabled=disabled or has_unsaved_changes()):
                    save('set_relations', target, {'relations': [r for j, r in enumerate(target['relations']) if j != i]})
                else:
                    rows.append({'kind': kind, 'target': link})
        if allow_alternative:
            new_kind = st.selectbox('新增关系类型', ['不新增', *index.RELATION_DESCRIPTIONS], key=_draft_field('seg_relation_new_kind:' + widget_key, '不新增'), disabled=disabled)
            new_target = st.selectbox('新增关系对应文本块', options, key=_draft_field('seg_relation_new_target:' + widget_key, options[0]), disabled=disabled)
            if new_kind != '不新增' or new_target != options[0]:
                rows.append({'kind': new_kind, 'target': new_target})
            if st.button('保存关系', key=key('seg_save_relations'), disabled=disabled):
                relations = []
                for row in rows:
                    if row['kind'] not in index.RELATION_DESCRIPTIONS or row['target'] not in labels:
                        st.error('请选择已定义的关系类型和对应文本块；不需要的行请删除。')
                        break
                    old = next((r for r in target['relations'] if r['kind'] == row['kind'] and r.get('target_spans') == index.unit_anchor(labels[row['target']])), None)
                    relations.append(old or {'kind': row['kind'].strip(), 'target_spans': index.unit_anchor(labels[row['target']]), 'basis': 'human_relation_review'})
                else:
                    save('set_relations', target, {'relations': relations})
    # Rebase dirty status after saving one panel, without dropping other drafts.
    st.session_state['seg_draft_defaults'] = st.session_state['seg_draft_rendered_defaults']
    if has_unsaved_changes() != dirty_at_start:
        st.rerun()
