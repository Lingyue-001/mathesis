"""Shared Inspector chrome; workspace state and review actions stay with their owners."""
import streamlit as st


SCOPE_NOTE = ('Full workflow currently demonstrated on Han Sifen li §38; '
              'other procedures are included at their present stage of analysis.')
PAGE_LABELS = {
    'en': {'Segmentation Review': 'Segmentation Review', 'Parser stages': 'Parser Stages',
           'Corpus Full Text': 'Corpus Browser'},
    'zh': {'Segmentation Review': '语料分块审阅', 'Parser stages': 'Parser 阶段',
           'Corpus Full Text': '语料浏览'},
}

_STYLE = '''<style>
.inspector-identity {font-size:1.3rem; font-weight:650; margin:0 0 1.6rem; line-height:1.4;}
.st-key-inspector_page {width:100%;}
.st-key-inspector_page [data-testid="stRadio"],
.st-key-inspector_page [role="radiogroup"],
.st-key-inspector_page [role="radiogroup"] > div {width:100%;}
.st-key-inspector_page [data-testid="stWidgetLabel"] p {font-size:.8rem; color:#68717c; font-weight:600;}
.st-key-inspector_page [role="radiogroup"] {gap:.4rem;}
.st-key-inspector_page [data-testid="stRadioOption"] {
  width:100%; box-sizing:border-box; margin:0; padding:.65rem .8rem; border-radius:.4rem;
  min-height:2.9rem; cursor:pointer;
}
.st-key-inspector_page [data-testid="stRadioOption"] > div > div:first-child {display:none;}
.st-key-inspector_page [data-testid="stRadioOption"] p {font-size:1rem; line-height:1.5;}
.st-key-inspector_page [data-testid="stRadioOption"][data-selected="true"] {background:rgba(112,130,160,.13);}
.st-key-inspector_page [data-testid="stRadioOption"]:has(input:focus-visible) {outline:2px solid #7587a2; outline-offset:2px;}
.st-key-inspector_page [data-testid="stRadioOption"]:has(input:disabled) {cursor:default; opacity:.55;}
[data-testid="stMainBlockContainer"], [data-testid="stColumn"] {min-width:0;}
[data-testid="stMain"] h1 {overflow-wrap:anywhere;}
@media (max-width:800px) {
  [data-testid="stMainBlockContainer"] {padding-left:1.25rem; padding-right:1.25rem;}
  [data-testid="stHorizontalBlock"] {flex-wrap:wrap;}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 100%; width:100%; min-width:0;}
  [data-testid="stMain"] h1 {font-size:2rem;}
}
</style>'''


def render_page_header(page, language='en'):
    st.html(_STYLE)
    st.title(PAGE_LABELS[language][page])
    st.caption(SCOPE_NOTE)


def render_navigation(language='en'):
    from tools.parser_inspector.segmentation_review import has_unsaved_changes, guard_selection

    st.sidebar.html('<div class="inspector-identity">MATHesis Inspector</div>')
    return st.sidebar.radio('Workspace' if language == 'en' else '工作区',
                            tuple(PAGE_LABELS['en']), index=1, key='inspector_page',
                            width='stretch',
                            format_func=PAGE_LABELS[language].get,
                            disabled=has_unsaved_changes(), on_change=guard_selection,
                            args=('inspector_page', st.session_state.get('inspector_page', 'Parser stages')))
