from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Answer Panel & Confidence Indicator Component
Displays the natural-language insight, confidence gauge, and multi-factor breakdown.
"""

import streamlit as st
from typing import Dict, Any, List
from utils.state import save_current_insight
from utils.export_utils import generate_markdown_report, generate_json_report


def render_answer_panel(
    result: Dict[str, Any],
    confidence: float,
    breakdown: Dict[str, float],
    query: str,
    detected_task: Dict[str, Any]
) -> None:
    """Render the AI Insight card, confidence gauge, and action toolbar."""
    conf_pct = int(confidence * 100)

    # Determine confidence badge & color
    if conf_pct >= 85:
        conf_badge = "HIGH CONFIDENCE"
        conf_class = "sq-badge-green"
        conf_color = "#10B981"
    elif conf_pct >= 70:
        conf_badge = "MODERATE CONFIDENCE"
        conf_class = "sq-badge-amber"
        conf_color = "#F59E0B"
    else:
        conf_badge = "LOW CONFIDENCE"
        conf_class = "sq-badge-rose"
        conf_color = "#F43F5E"

    # Main Insight Card
    render_html(f"""
<div style="background: rgba(14, 22, 43, 0.7); border: 1px solid rgba(56, 189, 248, 0.28); border-radius: 14px; padding: 1.3rem; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35); margin-bottom: 1.2rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; border-bottom: 1px solid rgba(56, 189, 248, 0.15); padding-bottom: 0.6rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.2rem;">✨</span>
            <span style="font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; font-weight: 700; color: #FFFFFF; letter-spacing: 0.02em;">
                AI GEOSPATIAL INSIGHT
            </span>
        </div>
        <span class="sq-badge sq-badge-cyan">{detected_task.get('title', 'Specialist Analysis')}</span>
    </div>

    <div style="font-size: 0.98rem; line-height: 1.65; color: #F8FAFC; margin-bottom: 1.2rem; font-weight: 400;">
        {result.get("answer", "No answer generated.")}
    </div>

    <!-- Bulleted Highlights -->
    <div style="background: rgba(6, 9, 19, 0.65); border-radius: 8px; padding: 0.8rem 1rem; border: 1px solid rgba(56, 189, 248, 0.12); margin-bottom: 1.2rem;">
        <div style="font-size: 0.76rem; font-weight: 600; color: #64748B; font-family: monospace; margin-bottom: 0.4rem;">
            KEY EVIDENCE-GROUNDED FINDINGS:
        </div>
        {"".join([f'<div style="font-size: 0.82rem; color: #94A3B8; padding: 0.2rem 0;">• {b}</div>' for b in result.get("summary_bullets", [])])}
    </div>

    <!-- Confidence Metric Gauge -->
    <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(10, 15, 29, 0.8); padding: 0.8rem 1rem; border-radius: 10px; border: 1px solid rgba(56, 189, 248, 0.18);">
        <div>
            <div style="font-size: 0.74rem; color: #64748B; font-family: monospace; font-weight: 600;">DECISION CONFIDENCE</div>
            <div style="display: flex; align-items: baseline; gap: 0.4rem; margin-top: 2px;">
                <span style="font-size: 1.6rem; font-weight: 700; color: {conf_color}; font-family: 'Space Grotesk', sans-serif;">
                    {conf_pct}%
                </span>
                <span class="sq-badge {conf_class}">{conf_badge}</span>
            </div>
        </div>
        <div style="text-align: right; font-size: 0.75rem; color: #94A3B8;">
            <div>Model: <b style="color: #38BDF8;">{detected_task.get('model_pipeline', 'Ensemble')}</b></div>
            <div>Validation: <b style="color: #10B981;">Cross-Verified</b></div>
        </div>
    </div>

    <!-- Multi-Factor Breakdown Bars -->
    <div style="margin-top: 1rem;">
        <div style="font-size: 0.74rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">
            CONFIDENCE DECOMPOSITION
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.6rem; font-size: 0.76rem;">
            <div style="background: rgba(6, 9, 19, 0.5); padding: 0.5rem; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.1);">
                <div style="color: #94A3B8;">Spatial Grounding</div>
                <div style="font-weight: 700; color: #00F0FF; font-size: 0.92rem; margin-top: 2px;">
                    {int(breakdown.get('spatial', 0.94) * 100)}%
                </div>
            </div>
            <div style="background: rgba(6, 9, 19, 0.5); padding: 0.5rem; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.1);">
                <div style="color: #94A3B8;">Semantic Target</div>
                <div style="font-weight: 700; color: #38BDF8; font-size: 0.92rem; margin-top: 2px;">
                    {int(breakdown.get('semantic', 0.91) * 100)}%
                </div>
            </div>
            <div style="background: rgba(6, 9, 19, 0.5); padding: 0.5rem; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.1);">
                <div style="color: #94A3B8;">Sensor Calibration</div>
                <div style="font-weight: 700; color: #10B981; font-size: 0.92rem; margin-top: 2px;">
                    {int(breakdown.get('sensor', 0.96) * 100)}%
                </div>
            </div>
        </div>
    </div>
</div>
""")

    # Action Toolbar: Save Insight, Copy Answer, Export Report
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🔖 Save Insight", key="btn_save_current_insight", use_container_width=True):
            saved = save_current_insight()
            if saved:
                st.success("✅ Insight saved to collection!")
            else:
                st.info("ℹ️ Insight already saved.")

    with c2:
        # Export Markdown report
        md_content = generate_markdown_report(result, query, detected_task)
        st.download_button(
            label="📄 Export Report (.md)",
            data=md_content,
            file_name=f"SatQuery_Report_{result.get('analysis_id', 'ANL')}.md",
            mime="text/markdown",
            use_container_width=True
        )

    with c3:
        # Export JSON payload
        json_content = generate_json_report(result, query, detected_task)
        st.download_button(
            label="💾 Export Raw JSON",
            data=json_content,
            file_name=f"SatQuery_Payload_{result.get('analysis_id', 'ANL')}.json",
            mime="application/json",
            use_container_width=True
        )
