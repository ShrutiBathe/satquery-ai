from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Natural Language Query Composer & Pre-Flight Summary
"""

import streamlit as st
from typing import Tuple

import config.settings as cfg
from utils.validators import validate_images, validate_query


def render_query_composer() -> None:
    """Render query input area, suggested chips, and pre-flight validation summary."""
    render_html("""
<div style="margin: 2rem 0 0.6rem 0;">
    <h3 style="font-size: 1.3rem; margin: 0 0 0.3rem 0; font-weight: 700; color: #F8FAFC;">
        What would you like to know?
    </h3>
    <p style="color: #94A3B8; font-size: 0.88rem; margin: 0;">
        Ask any question in natural language. SatQuery validates your inputs, selects the optimal specialist model, and produces visual evidence.
    </p>
</div>
""")

    current_query = st.session_state.get("query_text", "")

    # Query Input Box
    query_text = st.text_area(
        label="Natural-Language Satellite Query",
        value=current_query,
        placeholder="e.g., Where are the industrial facilities and what changed between these images?",
        height=105,
        key="nl_query_input",
        help="Enter an inquiry regarding land cover, infrastructure, change, flood extents, or object coordinates.",
        label_visibility="collapsed"
    )
    st.session_state["query_text"] = query_text

    # Character count
    char_count = len(query_text)
    st.markdown(
        f'<div style="text-align: right; font-size: 0.74rem; color: #64748B; font-family: monospace; margin-top: -8px;">{char_count} characters</div>',
        unsafe_allow_html=True
    )

    # Clickable Suggestion Chips
    st.markdown(
        '<div style="font-size: 0.78rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin: 0.8rem 0 0.4rem 0;">SUGGESTED PROMPTS</div>',
        unsafe_allow_html=True
    )

    suggested_chips = [
        "Where are the buildings?",
        "What changed between these images?",
        "What objects are visible?",
        "Find vegetation and agricultural plots",
        "Map flood extents and water pooling",
        "Compare the two images"
    ]

    cols = st.columns(len(suggested_chips))
    for idx, chip in enumerate(suggested_chips):
        with cols[idx]:
            if st.button(chip, key=f"chip_btn_{idx}", use_container_width=True):
                st.session_state["query_text"] = chip
                st.rerun()

    # Pre-Flight Validation Checks
    img_a = st.session_state.get("uploaded_image_a")
    img_b = st.session_state.get("uploaded_image_b")
    mode = st.session_state.get("analysis_mode", cfg.MODE_AUTO)

    valid_imgs, img_err = validate_images(img_a, img_b, mode)
    valid_q, q_err = validate_query(query_text)
    is_ready = valid_imgs and valid_q

    # Analysis Summary Card
    st.markdown("<div style='margin-top: 1.6rem;'></div>", unsafe_allow_html=True)
    _render_preflight_summary(img_a, img_b, mode, query_text, is_ready, img_err, q_err)


def _render_preflight_summary(
    img_a, img_b, mode, query, is_ready, img_err, q_err
) -> None:
    """Render compact summary card and dispatch button."""
    img_count = (1 if img_a is not None else 0) + (1 if img_b is not None else 0)

    mode_labels = {
        cfg.MODE_AUTO: "⚡ Auto Detect (Agentic Routing)",
        cfg.MODE_SINGLE: "🛰️ Single Image Analysis",
        cfg.MODE_COMPARE: "⏱️ Bi-temporal Comparison",
        cfg.MODE_OPTICAL_SAR: "📡 Optical + SAR Multimodal Fusion"
    }
    mode_str = mode_labels.get(mode, "Auto Detect")

    expected_workflow = (
        "Will be automatically determined by Agent Router"
        if mode == cfg.MODE_AUTO else
        "Explicitly selected by user"
    )

    query_preview = f'"{query}"' if query.strip() else '<span style="color: #64748B;">No query entered yet</span>'

    summary_html = safe_html(f"""
<div style="background: rgba(14, 22, 43, 0.7); border: 1px solid rgba(56, 189, 248, 0.22); border-radius: 12px; padding: 1.2rem; margin-bottom: 1.2rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; border-bottom: 1px solid rgba(56, 189, 248, 0.12); padding-bottom: 0.5rem;">
        <span style="font-family: 'Space Grotesk', sans-serif; font-size: 0.95rem; font-weight: 700; color: #F8FAFC; letter-spacing: 0.04em;">ANALYSIS PRE-FLIGHT SUMMARY</span>
        <span class="sq-badge {'sq-badge-green' if is_ready else 'sq-badge-amber'}">
            {'● READY TO ANALYZE' if is_ready else '○ AWAITING INPUTS'}
        </span>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; font-size: 0.82rem; color: #94A3B8;">
        <div>
            <div style="color: #64748B; font-weight: 600; font-family: monospace;">IMAGES UPLOADED:</div>
            <div style="color: #F8FAFC; font-weight: 500; margin-top: 2px;">{img_count} satellite scene(s)</div>
        </div>
        <div>
            <div style="color: #64748B; font-weight: 600; font-family: monospace;">ANALYSIS MODE:</div>
            <div style="color: #F8FAFC; font-weight: 500; margin-top: 2px;">{mode_str}</div>
        </div>
        <div>
            <div style="color: #64748B; font-weight: 600; font-family: monospace;">EXPECTED WORKFLOW:</div>
            <div style="color: #00F0FF; font-weight: 500; margin-top: 2px;">{expected_workflow}</div>
        </div>
    </div>
    <div style="margin-top: 0.8rem; padding-top: 0.7rem; border-top: 1px dashed rgba(56, 189, 248, 0.12); font-size: 0.84rem;">
        <span style="color: #64748B; font-family: monospace; font-weight: 600;">ACTIVE QUERY: </span>
        <span style="color: #38BDF8;">{query_preview}</span>
    </div>
</div>
""")
    render_html(summary_html)

    # Show helpful guidance if not ready
    if not is_ready:
        err_msg = img_err or q_err or "Please provide satellite imagery and an inquiry."
        st.warning(f"⚠️ {err_msg}")

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if st.button(
            "✨ Analyze with SatQuery AI",
            type="primary",
            use_container_width=True,
            disabled=not is_ready,
            key="btn_run_analysis_main"
        ):
            st.session_state["analysis_step"] = 3
            st.session_state["is_processing"] = True
            st.session_state["pipeline_completed"] = False
            st.rerun()
