# Copyright (c) 2026 James Hawkins. PolyForm Noncommercial License 1.0.0 — see LICENSE.md.
"""Noesi "Learn the audit" course, hosted on Streamlit.

Serves the self-contained learn.html (built from apps/studio-ui by
scripts/build-learn-standalone.mjs). The course is static teaching content:
no Noesi server, no data, no session. Progress is kept in the visitor's
browser only.
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Learn the audit — Noesi", page_icon="📘",
                   layout="wide", initial_sidebar_state="collapsed")

# Give the course the whole page: trim Streamlit's own padding and header.
st.markdown(
    """<style>
    .block-container {padding: 0.5rem 0.5rem 0 0.5rem; max-width: 100%;}
    header[data-testid="stHeader"] {height: 0; visibility: hidden;}
    footer {visibility: hidden;}
    </style>""",
    unsafe_allow_html=True,
)

html = (Path(__file__).parent / "learn.html").read_text(encoding="utf-8")
components.html(html, height=1400, scrolling=True)
