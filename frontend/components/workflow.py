from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Analysis Processing & Agentic Pipeline Stepper
Visualizes the multi-stage autonomous reasoning pipeline and detected task HUD.
"""

import streamlit as st
import time
from typing import Dict, Any

import config.settings as cfg
from services.api_client import client


def render_processing_pipeline() -> None:
    """Render the animated pipeline progression and execute backend analysis."""
    render_html("""
<div style="text-align: center; margin: 1rem auto 1.8rem auto; max-width: 720px;">
    <div style="margin-bottom: 0.4rem;">
        <span class="sq-badge sq-badge-cyan">● REASONING PIPELINE IN PROGRESS</span>
    </div>
    <h2 style="font-size: 2.1rem; margin: 0 0 0.4rem 0; font-weight: 700; color: #FFFFFF;">
        Analyzing Your Satellite Imagery
    </h2>
    <p style="color: #94A3B8; font-size: 0.95rem; margin: 0;">
        SatQuery is parsing your natural language query, evaluating radiometric dimensions, and routing to specialist neural nodes.
    </p>
</div>
""")

    query = st.session_state.get("query_text", "")
    mode = st.session_state.get("analysis_mode", cfg.MODE_AUTO)
    img_a = st.session_state.get("uploaded_image_a")
    img_b = st.session_state.get("uploaded_image_b")
    meta_a = st.session_state.get("image_metadata_a")
    meta_b = st.session_state.get("image_metadata_b")
    demo_mode = st.session_state.get("demo_mode", True)

    col_stages, col_detected = st.columns([1.5, 1])

    stages_placeholder = col_stages.empty()
    detected_placeholder = col_detected.empty()

    # Pre-execute client call to obtain final result and detected task
    with st.spinner("Dispatching agentic graph..."):
        result_payload = client.analyze(
            image_a=img_a,
            image_b=img_b,
            query=query,
            mode=mode,
            metadata_a=meta_a,
            metadata_b=meta_b,
            demo_mode=demo_mode
        )

    if result_payload.get("status") == "error":
        st.error(f"Analysis Failed: {result_payload.get('error')}")
        if st.button("↩ Return to Inputs"):
            st.session_state["analysis_step"] = 1
            st.session_state["is_processing"] = False
            st.rerun()
        return

    detected_task = result_payload.get("detected_task", {})

    # Stepper simulation through the 7 stages
    total_stages = len(cfg.PIPELINE_STAGES)
    stage_progress = st.progress(0.0)

    for current_idx in range(total_stages):
        # Render stages list
        stages_html = '<div style="background: rgba(14, 22, 43, 0.6); padding: 1.2rem; border-radius: 14px; border: 1px solid rgba(56, 189, 248, 0.18);">'
        for idx, stage in enumerate(cfg.PIPELINE_STAGES):
            if idx < current_idx:
                status_icon = "✓"
                status_color = "#10B981"
                stage_class = "done"
            elif idx == current_idx:
                status_icon = "●"
                status_color = "#00F0FF"
                stage_class = "active"
            else:
                status_icon = "○"
                status_color = "#64748B"
                stage_class = "pending"

            stages_html += f"""
            <div class="sq-pipeline-stage {stage_class}">
                <div class="sq-stage-icon" style="color: {status_color};">{status_icon}</div>
                <div>
                    <div class="sq-stage-title">{stage['name']}</div>
                    <div class="sq-stage-desc">{stage['desc']}</div>
                </div>
            </div>
            """
        stages_html += "</div>"
        stages_placeholder.markdown(safe_html(stages_html), unsafe_allow_html=True)

        # Render Detected Task HUD
        if current_idx >= 2:  # After Query Understanding & Validation
            task_hud_html = safe_html(f"""
<div style="background: rgba(14, 22, 43, 0.7); border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 14px; padding: 1.2rem; box-shadow: 0 0 24px rgba(0, 240, 255, 0.12);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; border-bottom: 1px solid rgba(56, 189, 248, 0.15); padding-bottom: 0.5rem;">
        <span style="font-family: 'Space Grotesk', sans-serif; font-size: 0.82rem; font-weight: 700; color: #00F0FF; letter-spacing: 0.05em;">AUTONOMOUSLY ROUTED WORKFLOW</span>
        <span class="sq-badge sq-badge-cyan">AGENT DECISION</span>
    </div>
    <div style="font-size: 1.35rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem; font-family: 'Space Grotesk', sans-serif;">
        {detected_task.get('title', 'Specialist Analysis')}
    </div>
    <div style="font-size: 0.82rem; color: #94A3B8; line-height: 1.5; margin-bottom: 1rem;">
        <b>Routing Rationale:</b><br>{detected_task.get('reason', 'Query semantic vectors mapped to specialist workflow.')}
    </div>
    <div style="background: rgba(6, 9, 19, 0.6); padding: 0.7rem; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.12); font-size: 0.78rem;">
        <div style="color: #64748B; font-family: monospace;">INPUT MODALITY:</div>
        <div style="color: #38BDF8; font-weight: 500; margin-bottom: 0.4rem;">{detected_task.get('input_modality', 'Multispectral')}</div>
        <div style="color: #64748B; font-family: monospace;">SPECIALIST MODEL:</div>
        <div style="color: #A855F7; font-weight: 500;">{detected_task.get('model_pipeline', 'Transformer Attention')}</div>
    </div>
</div>
""")
            detected_placeholder.markdown(task_hud_html, unsafe_allow_html=True)
        else:
            detected_placeholder.markdown(
                safe_html("""
                <div style="background: rgba(14, 22, 43, 0.4); border: 1px dashed rgba(56, 189, 248, 0.2); border-radius: 14px; padding: 2rem 1.2rem; text-align: center; color: #64748B;">
                    <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">⚡</div>
                    <div style="font-size: 0.88rem; font-weight: 600; color: #94A3B8;">Routing Agent Evaluating...</div>
                    <div style="font-size: 0.76rem; margin-top: 0.3rem;">Determining optimal specialist neural model</div>
                </div>
                """),
                unsafe_allow_html=True
            )

        stage_progress.progress((current_idx + 1) / total_stages)
        time.sleep(0.35)  # Realistic transition pacing

    # Store analysis results into session state
    st.session_state["current_analysis_id"] = result_payload.get("analysis_id")
    st.session_state["detected_task"] = detected_task
    st.session_state["analysis_result"] = result_payload
    st.session_state["confidence"] = result_payload.get("confidence", 0.90)
    st.session_state["confidence_breakdown"] = result_payload.get("confidence_breakdown", {})
    st.session_state["visual_evidence"] = result_payload.get("visual_evidence", {})
    st.session_state["analysis_trace"] = result_payload.get("analysis_trace", [])

    # Append to history store
    history_record = {
        "id": result_payload.get("analysis_id"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query": query,
        "mode": mode,
        "task_name": detected_task.get("title", "Geospatial Analysis"),
        "task_id": detected_task.get("id", "general"),
        "image_count": 2 if img_b is not None else 1,
        "confidence": result_payload.get("confidence", 0.90),
        "status": "Completed"
    }
    st.session_state["history"].insert(0, history_record)

    # Transition to Step 4 (Results)
    st.session_state["analysis_step"] = 4
    st.session_state["is_processing"] = False
    st.session_state["pipeline_completed"] = True
    st.rerun()
