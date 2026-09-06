from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Visual Evidence Card & Class Legend Component
Displays class labels, color chips, detection counts, and quantitative metrics.
"""

import streamlit as st
from typing import Dict, Any, List


def render_evidence_card(evidence: Dict[str, Any], metrics: Dict[str, Any]) -> None:
    """Render the visual evidence legend and quantitative metrics."""
    render_html("""
<div style="background: rgba(14, 22, 43, 0.65); border: 1px solid rgba(56, 189, 248, 0.18); border-radius: 12px; padding: 1.1rem; margin-top: 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; border-bottom: 1px solid rgba(56, 189, 248, 0.12); padding-bottom: 0.5rem;">
        <span style="font-family: 'Space Grotesk', sans-serif; font-size: 0.88rem; font-weight: 700; color: #F8FAFC;">
            GROUNDED EVIDENCE & METRICS
        </span>
        <span class="sq-badge sq-badge-cyan">SPATIAL GROUND TRUTH</span>
    </div>
    <p style="font-size: 0.8rem; color: #94A3B8; margin: 0 0 0.8rem 0;">
        Highlighted visual overlays represent the exact pixels and spatial regions used by the specialist agent to verify the answer.
    </p>
</div>
""")

    # Render Class Legend Chips
    labels: List[Dict[str, Any]] = evidence.get("labels", [])
    if labels:
        legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">'
        for item in labels:
            name = item.get("name", "Class")
            color = item.get("color", "#00F0FF")
            count = item.get("count", "")
            count_str = f" ({count})" if count != "" else ""

            legend_html += f"""
            <div style="display: inline-flex; align-items: center; gap: 0.45rem; background: rgba(6, 9, 19, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); padding: 0.3rem 0.65rem; border-radius: 6px; font-size: 0.78rem;">
                <span style="display: inline-block; width: 10px; height: 10px; border-radius: 2px; background-color: {color}; box-shadow: 0 0 6px {color};"></span>
                <span style="color: #F8FAFC; font-weight: 500;">{name}</span>
                <span style="color: #94A3B8; font-family: monospace;">{count_str}</span>
            </div>
            """
        legend_html += '</div>'
        render_html(legend_html)

    # Render Quantitative Telemetry Metrics Table
    if metrics:
        render_html(
            '<div style="font-size: 0.76rem; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">QUANTITATIVE EXTRACTIONS</div>'
        )

        cols = st.columns(len(metrics))
        for idx, (m_key, m_val) in enumerate(metrics.items()):
            with cols[idx]:
                val = m_val.get("value", "N/A")
                unit = m_val.get("unit", "")
                render_html(f"""
<div style="background: rgba(6, 9, 19, 0.6); padding: 0.65rem; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.12); text-align: center;">
    <div style="font-size: 0.72rem; color: #94A3B8; margin-bottom: 2px;">{m_key}</div>
    <div style="font-size: 1.15rem; font-weight: 700; color: #00F0FF; font-family: 'Space Grotesk', sans-serif;">{val}</div>
    <div style="font-size: 0.68rem; color: #64748B;">{unit}</div>
</div>
""")
