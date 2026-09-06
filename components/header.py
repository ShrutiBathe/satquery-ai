from utils.ui_utils import safe_html, render_html
import streamlit as st
import textwrap
import config.settings as cfg


def render_header() -> None:
    """Render top application HUD bar."""
    is_demo = st.session_state.get("demo_mode", True)
    curr_page = st.session_state.get("current_page", "home")

    page_titles = {
        "home": "Overview",
        "new_analysis": "Analysis Workspace",
        "history": "Analysis History",
        "saved_insights": "Saved Discoveries",
        "api_spec": "Agent Architecture & API Spec",
        "settings": "Settings"
    }
    active_title = page_titles.get(curr_page, "Workspace")

    status_badge = (
        '<span class="sq-badge sq-badge-cyan">⚡ DEMO SIMULATION MODE</span>'
        if is_demo else
        '<span class="sq-badge sq-badge-green">● AI BACKEND CONNECTED</span>'
    )

    header_html = safe_html(f"""
<div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 1.1rem; border-bottom: 1px solid rgba(56, 189, 248, 0.15); margin-bottom: 1.5rem;">
    <div style="display: flex; align-items: center; gap: 0.85rem;">
        <div style="width: 38px; height: 38px; border-radius: 9px; background: linear-gradient(135deg, #00F0FF 0%, #0077B6 100%); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; box-shadow: 0 0 16px rgba(0, 240, 255, 0.35);">
            🛰️
        </div>
        <div>
            <div style="display: flex; align-items: center; gap: 0.55rem;">
                <span style="font-family: 'Space Grotesk', sans-serif; font-size: 1.25rem; font-weight: 700; color: var(--text-pure); letter-spacing: -0.01em;">SATQUERY AI</span>
                <span class="sq-badge sq-badge-cyan">ENTERPRISE EO</span>
            </div>
            <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: -2px;">
                {cfg.TAGLINE} • <span style="color: var(--cyan-accent);">{active_title}</span>
            </div>
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 0.8rem;">
        {status_badge}
    </div>
</div>
""")
    render_html(header_html)
