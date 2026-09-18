"""Minimal local UI: inputs, real parser calls, and unprojected JSON."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from source_adapters.corpus import build_source_packet, list_procedures
from tools.parser_inspector.runner import OUTPUT, run, text_packet, refresh_dependencies
from source_adapters.dependencies import validate
from tools.parser_inspector.segmentation_review import has_unsaved_changes, guard_selection

st.set_page_config(page_title='Parser Inspector', layout='wide')
st.title('Parser Inspector')
page = st.sidebar.radio('工作区', ['Segmentation Review', 'Parser stages', 'Corpus Full Text'], index=1, key='inspector_page',
                        disabled=has_unsaved_changes(), on_change=guard_selection,
                        args=('inspector_page', st.session_state.get('inspector_page', 'Parser stages')))
if page == 'Segmentation Review':
    from tools.parser_inspector.segmentation_review import render
    render(ROOT)
    st.stop()
if page == 'Corpus Full Text':
    from tools.parser_inspector.segmentation_review import render_full_text
    render_full_text(ROOT)
    st.stop()
st.caption('直接调用当前 parser；仅显示原始 JSON。每次运行覆盖 output/current/。')

source_mode = st.radio('输入来源', ['粘贴文本', 'Corpus'], horizontal=True, key='source_mode')
if source_mode == 'Corpus':
    procedures = {p['id']: p for p in list_procedures(ROOT)}
    procedure_id = st.selectbox('已登记 corpus procedure', list(procedures),
                                format_func=lambda key: procedures[key]['title'], key='procedure_id')
    try:
        packet = build_source_packet(ROOT, procedure_id)['source_packet']
    except (ValueError, OSError) as error:
        st.error(str(error))
        st.stop()
    for category in ('primary_documents', 'context_documents'):
        for doc in packet[category]:
            st.caption(f"{category} · {doc['doc_id']} · {doc['source']['path']}")
            st.text(doc['text'])
else:
    text = st.text_area('原文（原样传入）', height=180, key='pasted_text')
    packet = text_packet(text)

st.caption('Constructions 自动运行词项层；Compile 通过 parse_packet() 完整编译后才有 selected 状态。')
for column, stage, label in zip(st.columns(3), ('lexical', 'constructions', 'compile'),
                                 ('1. Lexical', '2. Constructions', '3. Compile')):
    if column.button(label, key=stage):
        if not any(d['text'].strip() for d in packet['primary_documents']):
            st.warning('请先输入原文。')
            continue
        with st.spinner('调用 parser…'):
            st.session_state.snapshot = run(packet, stage)
            st.session_state.snapshot_packet = packet

snapshot = st.session_state.get('snapshot')
if source_mode == 'Corpus':
    refresh_dependencies(ROOT)
if not snapshot:
    st.info('选择运行层级后显示原始结果。')
    st.stop()
if st.session_state.snapshot_packet != packet:
    st.info('输入已改变，请重新运行。磁盘 current 仍是上次运行结果。')
    st.stop()

status = snapshot['run.json']
freshness = validate(ROOT, status.get('artifacts', []))
if any(item['status'] == 'stale' for item in freshness):
    st.warning('STALE：所依赖的 effective unit 已改变。原始输出保留，请重新运行此 procedure。')
    st.stop()
if status['status'] == 'error':
    st.error('Parser 调用失败；已完成层的结果保留，后续层为 null。异常见 run.json。')
else:
    st.success('已运行：' + ' → '.join(status['completed_stages']))


def raw(filename):
    st.caption(str(OUTPUT / filename))
    value = snapshot[filename]
    if value is None:
        st.caption('本次未运行此输出（文件内容为 null）。')
    st.code(compact_json(value), language='json', wrap_lines=True)
    with st.expander('树状 JSON · ' + filename):
        st.json(json.dumps(value, ensure_ascii=False, indent=2) + '\n', expanded=1)


def compact_json(value):
    """Display-only whitespace/key grouping; every original field is retained."""
    metadata = {'id', 'kind', 'type', 'status', 'role', 'code', 'start', 'end',
                'analysis_range', 'unit', 'scale', 'representation', 'producer'}

    def inline(item):
        return json.dumps(item, ensure_ascii=False)

    def record(item):
        if not isinstance(item, dict):
            return inline(item)
        location, content = [], []
        for key, field in item.items():
            group = location if key in metadata or key.endswith('_id') else content
            group.append(inline(key) + ': ' + inline(field))
        groups = [', '.join(group) for group in (location, content) if group]
        return '{' + ',\n  '.join(groups) + '}'

    if isinstance(value, list) and value:
        return '[\n' + ',\n'.join('  ' + record(item).replace('\n', '\n  ') for item in value) + '\n]'
    return record(value)


lexical, constructions, compiler = st.tabs(['Lexical candidates', 'Constructions', 'Events / values / diagnostics'])
with lexical:
    raw('lexical_candidates.json')
with constructions:
    st.subheader('Raw construction candidates')
    raw('construction_candidates.json')
    st.subheader('Raw compiler selection（保留全部候选及原生 status）')
    raw('construction_selection.json')
    with st.expander('Raw syntax IR / syntax diagnostics'):
        raw('syntax.json')
with compiler:
    for name in ('events.json', 'values.json', 'diagnostics.json', 'unresolved.json'):
        st.subheader(name)
        raw(name)
    with st.expander('Raw program IR（包含 linked.diagnostics）'):
        raw('program.json')
    with st.expander('完整 parse_packet() 返回值'):
        raw('compiler_report.json')
with st.expander('实际输入 / parser 输入预处理 / inspector 调用状态'):
    for name in ('packet.json', 'documents.json', 'run.json'):
        raw(name)
