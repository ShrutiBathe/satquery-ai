"""
SatQuery AI - UI Rendering Utilities
Provides safe HTML string rendering without markdown code-block indentation bugs.
"""

import streamlit as st


def safe_html(html_str: str) -> str:
    """
    Remove all leading and trailing indentation from multiline HTML strings
    and eliminate empty lines so that Streamlit's Markdown parser never interprets
    lines with 4+ leading spaces or lines following blank lines as preformatted
    <pre><code> code blocks.
    """
    if not html_str:
        return ""
    lines = [line.strip() for line in html_str.splitlines() if line.strip()]
    return "\n".join(lines)


def render_html(html_str: str) -> None:
    """Directly render safe HTML into Streamlit without markdown code block interference."""
    if not html_str:
        return
    cleaned = safe_html(html_str)
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)

