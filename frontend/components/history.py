from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Analysis History Component
Displays past queries, analysis runs, confidence scores, and actions (Open, Delete).
"""

import streamlit as st
from typing import List, Dict, Any
from utils.state import set_page


def render_history_page() -> None:
    """Render the Analysis History management view."""
    render_html("""
<div style="margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
            <h2 style="font-size: 1.85rem; margin: 0 0 0.3rem 0; font-weight: 700; color: #FFFFFF;">
                Analysis History
            </h2>
            <p style="color: #94A3B8; font-size: 0.92rem; margin: 0;">
                Review past satellite queries, agent decisions, and evidence logs from this session.
            </p>
        </div>
        <span class="sq-badge sq-badge-cyan">SESSION AUDIT LOG</span>
    </div>
</div>
""")

    history: List[Dict[str, Any]] = st.session_state.get("history", [])

    if not history:
        # Empty State
        render_html("""
<div style="background: rgba(14, 22, 43, 0.5); border: 1px dashed rgba(56, 189, 248, 0.25); border-radius: 16px; padding: 4rem 2rem; text-align: center; max-width: 640px; margin: 3rem auto;">
    <div style="font-size: 3rem; margin-bottom: 0.8rem;">📜</div>
    <h3 style="font-size: 1.25rem; color: #F8FAFC; margin-bottom: 0.5rem;">No Prior Analyses Found</h3>
    <p style="color: #94A3B8; font-size: 0.88rem; max-width: 440px; margin: 0 auto 1.5rem auto;">
        Your remote sensing analyses, agent routing traces, and confidence metrics will be recorded here automatically.
    </p>
</div>
""")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Start Your First Analysis", type="primary", use_container_width=True):
                set_page("new_analysis")
                st.session_state["analysis_step"] = 1
                st.rerun()
        return

    # Filter and Clear Toolbar
    c_search, c_filter, c_clear = st.columns([2, 1.2, 1])

    with c_search:
        search_kw = st.text_input("Search query or ID", placeholder="Filter by keyword...", label_visibility="collapsed")

    with c_filter:
        task_filter = st.selectbox("Workflow Filter", ["All Workflows", "Change Detection", "Visual Grounding", "Optical + SAR", "VQA"], label_visibility="collapsed")

    with c_clear:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state["history"] = []
            st.rerun()

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Filtered records
    filtered = []
    for item in history:
        if search_kw and (search_kw.lower() not in item.get("query", "").lower() and search_kw.lower() not in item.get("id", "").lower()):
            continue
        if task_filter != "All Workflows" and task_filter.lower() not in item.get("task_name", "").lower():
            continue
        filtered.append(item)

    st.markdown(f'<div style="font-size: 0.78rem; color: #64748B; margin-bottom: 0.8rem;">SHOWING {len(filtered)} RECORD(S)</div>', unsafe_allow_html=True)

    for idx, record in enumerate(filtered):
        rec_id = record.get("id", f"ANL-{idx}")
        conf_pct = int(record.get("confidence", 0.90) * 100)

        with st.container():
            render_html(f"""
<div style="background: rgba(14, 22, 43, 0.7); border: 1px solid rgba(56, 189, 248, 0.18); border-radius: 12px; padding: 1.1rem; margin-bottom: 0.9rem;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem;">
        <div>
            <span class="sq-badge sq-badge-cyan">{rec_id}</span>
            <span style="font-size: 0.82rem; color: #64748B; margin-left: 0.6rem; font-family: monospace;">{record.get('timestamp')}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="sq-badge sq-badge-green">CONFIDENCE: {conf_pct}%</span>
            <span class="sq-badge sq-badge-cyan">{record.get('task_name', 'Analysis')}</span>
        </div>
    </div>
    <div style="font-size: 1.05rem; font-weight: 600; color: #F8FAFC; margin-bottom: 0.5rem;">
        "{record.get('query')}"
    </div>
    <div style="display: flex; gap: 1.5rem; font-size: 0.78rem; color: #94A3B8;">
        <div><b>Images:</b> {record.get('image_count', 1)} scene(s)</div>
        <div><b>Status:</b> <span style="color: #10B981;">{record.get('status', 'Completed')}</span></div>
    </div>
</div>
""")

            b_open, b_del, b_spacer = st.columns([1, 1, 4])
            with b_open:
                if st.button("📂 Open Result", key=f"open_hist_{rec_id}", use_container_width=True):
                    # Load analysis view
                    st.session_state["query_text"] = record.get("query", "")
                    st.session_state["analysis_step"] = 4
                    set_page("new_analysis")
                    st.rerun()
            with b_del:
                if st.button("🗑️ Delete", key=f"del_hist_{rec_id}", use_container_width=True):
                    st.session_state["history"] = [h for h in history if h.get("id") != rec_id]
                    st.rerun()
