"""
SatQuery AI — Interactive AI Assistant for Multimodal Remote-Sensing Image Analysis
Problem Statement ID: SIH26167
Smart India Hackathon 2026

Main Streamlit Application Entrypoint
"""

import streamlit as st
import os
import textwrap
from pathlib import Path

# Streamlit Page Configuration - Must be the first Streamlit command
st.set_page_config(
    page_title="SatQuery AI | Geospatial Intelligence Assistant",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

import config.settings as cfg
from utils.ui_utils import safe_html, render_html
from utils.state import init_session_state, set_page, clear_analysis_inputs
from components.header import render_header
from components.sidebar import render_sidebar
from components.hero import render_hero
from components.cards import render_quick_cards
from components.upload import render_step_indicator, render_upload_area
from components.query_input import render_query_composer
from components.workflow import render_processing_pipeline
from components.result_viewer import render_visual_result_viewer
from components.evidence import render_evidence_card
from components.confidence import render_answer_panel
from components.analysis_trace import render_analysis_trace
from components.follow_up import render_follow_up_chat
from components.history import render_history_page
from components.saved_insights import render_saved_insights_page
from components.api_docs import render_api_spec_page
from components.settings_view import render_settings_page
from components.dashboard import (
    render_telemetry_kpis,
    render_mission_map,
    render_quick_query_hud,
    render_intel_and_constellation_section
)


def inject_custom_styles() -> None:
    """Load and inject custom Deep Orbit dark / pro dark / light CSS styles."""
    css_path = cfg.STYLES_DIR / "theme.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            custom_css = f.read()
        st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

    curr_theme = st.session_state.get("app_theme", "dark")
    if curr_theme == "light":
        light_css_path = cfg.STYLES_DIR / "light_theme.css"
        if light_css_path.exists():
            with open(light_css_path, "r", encoding="utf-8") as f:
                light_css = f.read()
            st.markdown(f"<style>{light_css}</style>", unsafe_allow_html=True)
    elif curr_theme == "pro_dark":
        pro_dark_css_path = cfg.STYLES_DIR / "pro_dark_theme.css"
        if pro_dark_css_path.exists():
            with open(pro_dark_css_path, "r", encoding="utf-8") as f:
                pro_dark_css = f.read()
            st.markdown(f"<style>{pro_dark_css}</style>", unsafe_allow_html=True)


def main() -> None:
    # 1. Initialize persistent session state
    init_session_state()

    # 2. Inject CSS design system
    inject_custom_styles()

    # 3. Render Global Chrome (Sidebar & Top Header)
    render_sidebar()
    render_header()

    # 4. View Router
    current_page = st.session_state.get("current_page", "home")

    if current_page == "home":
        _render_home_view()
    elif current_page == "new_analysis":
        _render_new_analysis_view()
    elif current_page == "history":
        render_history_page()
    elif current_page == "saved_insights":
        render_saved_insights_page()
    elif current_page == "api_spec":
        render_api_spec_page()
    elif current_page == "settings":
        render_settings_page()
    else:
        _render_home_view()


def _render_home_view() -> None:
    """Professional Geospatial Intelligence Mission Dashboard View."""
    # 1. Hero & Orbit HUD
    render_hero()

    # 2. Live Telemetry Metric KPIs Strip
    render_telemetry_kpis()

    # 3. Instant Query Launchpad
    render_quick_query_hud()

    # 4. Specialist Workflows Station
    render_quick_cards()

    # 5. Interactive Global Mission Operations Tracking Map
    render_mission_map()

    # 6. Live Intelligence Stream & Constellation Fleet Status
    render_intel_and_constellation_section()

    # 7. Informational Highlights Section
    info_html = f"""
    <div style="margin-top: 3.5rem; background: rgba(14, 22, 43, 0.5); border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 16px; padding: 2rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid rgba(56, 189, 248, 0.12); padding-bottom: 0.8rem;">
    <div style="display: flex; align-items: center; gap: 0.6rem;">
    <span style="font-size: 1.3rem;">🛡️</span>
    <h3 style="margin: 0; font-size: 1.15rem; color: #FFFFFF;">About SatQuery AI Architecture</h3>
    </div>
    <span class="sq-badge sq-badge-cyan">MISSION ARCHITECTURE</span>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; font-size: 0.86rem; color: #94A3B8; line-height: 1.6;">
    <div>
    <h4 style="color: #38BDF8; font-size: 0.95rem; margin-bottom: 0.4rem;">Natural Language Grounding</h4>
    Non-technical analysts, disaster response commanders, and urban researchers can query complex multispectral rasters using plain English without requiring manual GIS indexing.
    </div>
    <div>
    <h4 style="color: #00F0FF; font-size: 0.95rem; margin-bottom: 0.4rem;">Autonomous Agentic Routing</h4>
    SatQuery's intent router automatically validates input dimensions, checks temporal and spectral compatibility, and routes tasks to specialized neural backbones.
    </div>
    <div>
    <h4 style="color: #A855F7; font-size: 0.95rem; margin-bottom: 0.4rem;">Evidence-Backed Insights</h4>
    Unlike ungrounded LLMs, every response is paired with spatial bounding coordinates, differential change heatmaps, or segmentation masks with quantified confidence metrics.
    </div>
    </div>
    </div>
    """
    render_html(info_html)


def _render_new_analysis_view() -> None:
    """Interactive Analysis Workspace View (Steps 1 to 4)."""
    step = st.session_state.get("analysis_step", 1)

    if step in (1, 2):
        # Progress indicator (Step 1 or 2 depending on upload state)
        active_step_num = 2 if (st.session_state.get("uploaded_image_a") is not None and st.session_state.get("query_text")) else 1
        render_step_indicator(active_step_num)

        # Upload and Query components
        render_upload_area()
        render_query_composer()

    elif step == 3:
        # Step 3: Pipeline Processing Visualizer
        render_step_indicator(3)
        render_processing_pipeline()

    elif step == 4:
        # Step 4: Results & Visual Evidence View
        render_step_indicator(4)
        _render_results_workspace()


def _render_results_workspace() -> None:
    """Step 4 Results Screen."""
    result = st.session_state.get("analysis_result")
    detected_task = st.session_state.get("detected_task", {})
    evidence = st.session_state.get("visual_evidence", {})
    confidence = st.session_state.get("confidence", 0.90)
    breakdown = st.session_state.get("confidence_breakdown", {})
    query = st.session_state.get("query_text", "")
    trace = st.session_state.get("analysis_trace", [])

    if not result:
        st.warning("No analysis results found. Please configure a new analysis.")
        if st.button("Start Analysis"):
            st.session_state["analysis_step"] = 1
            st.rerun()
        return

    # Results Header
    c_head, c_btn = st.columns([3, 1])
    with c_head:
        render_html(
            f"""
            <div>
                <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.2rem;">
                    <span class="sq-badge sq-badge-green">● ANALYSIS COMPLETE</span>
                    <span class="sq-badge sq-badge-cyan">REF: {result.get('analysis_id', 'ANL-001')}</span>
                </div>
                <h2 style="font-size: 1.85rem; font-weight: 700; color: #FFFFFF; margin: 0 0 0.2rem 0;">
                    Evidence-Grounded Satellite Insight
                </h2>
                <p style="color: #94A3B8; font-size: 0.9rem; margin: 0;">
                    Query: <i style="color: #38BDF8;">"{query}"</i>
                </p>
            </div>
            """
        )

    with c_btn:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Start New Analysis", type="primary", use_container_width=True):
            clear_analysis_inputs()
            st.session_state["analysis_step"] = 1
            st.rerun()

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # Main Split View (Left: Visual Evidence, Right: AI Answer & Metrics)
    col_visual, col_answer = st.columns([1.35, 1])

    with col_visual:
        render_visual_result_viewer(evidence, detected_task.get("id", "general"))
        render_evidence_card(evidence, result.get("metrics", {}))

    with col_answer:
        render_answer_panel(result, confidence, breakdown, query, detected_task)
        render_analysis_trace(trace, detected_task, confidence)

    # Full Width Follow-up Chat Component
    render_follow_up_chat(result)


if __name__ == "__main__":
    main()
