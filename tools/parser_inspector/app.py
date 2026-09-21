"""Parser Inspector: source review and the read-only R1–R4 shell."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from tools.parser_inspector.shell import render_navigation

st.set_page_config(page_title='MATHesis Inspector', layout='wide')
if 'inspector_language' not in st.session_state:
    st.session_state.inspector_language = 'en'


def set_language(language):
    st.session_state.inspector_language = language


language = st.session_state.inspector_language
st.html('''<style>
div.st-key-language_en, div.st-key-language_zh {
  position: fixed; top: 4.5rem; z-index: 100000;
}
div.st-key-language_en { right: 9rem; }
div.st-key-language_zh { right: 6.6rem; }
div.st-key-language_en button, div.st-key-language_zh button {
  min-height: unset; padding: .2rem; border: 0; border-radius: 0; background: transparent;
  box-shadow: none; color: inherit; font-size: .875rem;
}
div.st-key-language_en button:hover, div.st-key-language_zh button:hover { background: transparent; text-decoration: underline; }
</style>''')
st.html('<style>div.st-key-language_' + language + ' button { font-weight: 700; }</style>')
st.button('EN', key='language_en', on_click=set_language, args=('en',))
st.button('CH', key='language_zh', on_click=set_language, args=('zh',))

page = render_navigation(language)
if page == 'Segmentation Review':
    from tools.parser_inspector.segmentation_review import render
    render(ROOT)
    st.stop()
if page == 'Corpus Full Text':
    from tools.parser_inspector.segmentation_review import render_full_text
    render_full_text(ROOT)
    st.stop()
from tools.parser_inspector.readable import render
render(ROOT, language)
