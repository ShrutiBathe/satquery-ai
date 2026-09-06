from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Saved Insights Component
Catalog of pinned and bookmarked geospatial discoveries with export features.
"""

import streamlit as st
from typing import List, Dict, Any
from utils.state import set_page
from utils.export_utils import generate_markdown_report


def render_saved_insights_page() -> None:
    """Render the Saved Insights catalog view."""
    render_html("""
<div style="margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
            <h2 style="font-size: 1.85rem; margin: 0 0 0.3rem 0; font-weight: 700; color: #FFFFFF;">
                Saved Discoveries & Insights
            </h2>
            <p style="color: #94A3B8; font-size: 0.92rem; margin: 0;">
                Curated collection of flagged satellite discoveries, structural detections, and bi-temporal findings.
            </p>
        </div>
        <span class="sq-badge sq-badge-cyan">BOOKMARKED DISCOVERIES</span>
    </div>
</div>
""")

    saved_items: List[Dict[str, Any]] = st.session_state.get("saved_insights", [])

    if not saved_items:
        # Empty State
        render_html("""
<div style="background: rgba(14, 22, 43, 0.5); border: 1px dashed rgba(56, 189, 248, 0.25); border-radius: 16px; padding: 4rem 2rem; text-align: center; max-width: 640px; margin: 3rem auto;">
    <div style="font-size: 3rem; margin-bottom: 0.8rem;">🔖</div>
    <h3 style="font-size: 1.25rem; color: #F8FAFC; margin-bottom: 0.5rem;">No Saved Discoveries Yet</h3>
    <p style="color: #94A3B8; font-size: 0.88rem; max-width: 440px; margin: 0 auto 1.5rem auto;">
        When SatQuery finishes analyzing your imagery, click <b>Save Insight</b> on the results card to bookmark your findings here for future operational review.
    </p>
</div>
""")
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button("🛰️ Go to Analysis Workspace", type="primary", use_container_width=True):
                set_page("new_analysis")
                st.rerun()
        return

    # Render Grid of Saved Insights
    for idx, item in enumerate(saved_items):
        ins_id = item.get("id", f"INS-{idx}")
        conf_pct = int(item.get("confidence", 0.90) * 100)
        thumb = item.get("thumbnail")

        with st.container():
            c_card, c_action = st.columns([3.5, 1.2])

            with c_card:
                render_html(f"""
<div style="background: rgba(14, 22, 43, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
        <span class="sq-badge sq-badge-cyan">{ins_id} • {item.get('task_name')}</span>
        <span style="font-size: 0.78rem; color: #64748B; font-family: monospace;">{item.get('timestamp')}</span>
    </div>
    <div style="font-size: 1.05rem; font-weight: 600; color: #38BDF8; margin-bottom: 0.5rem;">
        "{item.get('query')}"
    </div>
    <div style="font-size: 0.9rem; color: #E2E8F0; line-height: 1.5; margin-bottom: 0.8rem;">
        {item.get('answer')}
    </div>
    <div style="display: flex; gap: 1rem; font-size: 0.76rem; color: #94A3B8;">
        <div>Confidence: <b style="color: #10B981;">{conf_pct}%</b></div>
        <div>Reference: <b style="color: #00F0FF;">{item.get('analysis_id')}</b></div>
    </div>
</div>
""")

            with c_action:
                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
                if st.button("📂 Open Result", key=f"open_ins_{ins_id}", use_container_width=True):
                    st.session_state["query_text"] = item.get("query", "")
                    st.session_state["analysis_step"] = 4
                    set_page("new_analysis")
                    st.rerun()

                # Report download
                fake_task = {"title": item.get("task_name", "Analysis")}
                md_rep = generate_markdown_report(item, item.get("query", ""), fake_task)
                st.download_button(
                    label="📄 Export Report",
                    data=md_rep,
                    file_name=f"Report_{ins_id}.md",
                    mime="text/markdown",
                    key=f"dl_ins_{ins_id}",
                    use_container_width=True
                )

                if st.button("🗑️ Delete", key=f"del_ins_{ins_id}", use_container_width=True):
                    st.session_state["saved_insights"] = [i for i in saved_items if i.get("id") != ins_id]
                    st.rerun()
