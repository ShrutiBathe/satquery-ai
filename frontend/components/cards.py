from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Specialist Quick Analysis Cards
Displays the 4 interactive workflow shortcut cards.
"""

import streamlit as st
import textwrap
import config.settings as cfg
from utils.state import set_page
from services.sample_data import (
    generate_vqa_scenario,
    generate_grounding_scenario,
    generate_change_detection_scenario,
    generate_optical_sar_scenario
)


def render_quick_cards() -> None:
    """Render the 4 specialist workflow cards on the landing page."""
    cards_header = """
    <div style="margin: 3rem 0 1.2rem 0;">
    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
    <div>
    <h2 style="font-size: 1.5rem; margin: 0 0 0.3rem 0; font-weight: 700;">Specialist Geospatial Workflows</h2>
    <p style="color: #94A3B8; font-size: 0.92rem; margin: 0;">
    SatQuery's agentic router dispatches natural-language prompts to dedicated vision-language and remote sensing models.
    </p>
    </div>
    <span class="sq-badge sq-badge-cyan">4 SPECIALIST PIPELINES</span>
    </div>
    </div>
    """
    render_html(cards_header)

    col1, col2, col3, col4 = st.columns(4)

    cards_data = [
        {
            "id": cfg.WORKFLOW_VQA,
            "icon": "👁️",
            "badge": "VQA Engine",
            "badge_class": "sq-badge-cyan",
            "title": "Visual Question Answering",
            "desc": "Ask open-ended questions about objects, scenes, and environmental status in remote-sensing scenes.",
            "example": "What is visible in this area?",
            "mode": cfg.MODE_SINGLE,
            "scenario_fn": generate_vqa_scenario
        },
        {
            "id": cfg.WORKFLOW_GROUNDING,
            "icon": "🎯",
            "badge": "Grounding",
            "badge_class": "sq-badge-cyan",
            "title": "Visual Grounding",
            "desc": "Locate requested structures or regions with spatial bounding boxes and segmentation contours.",
            "example": "Where are the buildings?",
            "mode": cfg.MODE_SINGLE,
            "scenario_fn": generate_grounding_scenario
        },
        {
            "id": cfg.WORKFLOW_CHANGE,
            "icon": "⏱️",
            "badge": "Bi-Temporal",
            "badge_class": "sq-badge-rose",
            "title": "Change Detection",
            "desc": "Compare imagery captured across different dates to identify and explain surface changes.",
            "example": "What changed between 2024 & 2026?",
            "mode": cfg.MODE_COMPARE,
            "scenario_fn": generate_change_detection_scenario
        },
        {
            "id": cfg.WORKFLOW_OPTICAL_SAR,
            "icon": "📡",
            "badge": "Radar Fusion",
            "badge_class": "sq-badge-purple",
            "title": "Multimodal Optical + SAR",
            "desc": "Fuse complementary optical reflectance and cloud-penetrating Synthetic Aperture Radar.",
            "example": "Compare this region using both sensors.",
            "mode": cfg.MODE_OPTICAL_SAR,
            "scenario_fn": generate_optical_sar_scenario
        }
    ]

    columns = [col1, col2, col3, col4]

    for idx, card in enumerate(cards_data):
        with columns[idx]:
            card_html = safe_html(f"""
<div class="sq-card" style="height: 275px; display: flex; flex-direction: column; justify-content: space-between;">
<div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
<span style="font-size: 1.6rem;">{card['icon']}</span>
<span class="sq-badge {card['badge_class']}">{card['badge']}</span>
</div>
<h3 style="font-size: 1.05rem; margin: 0 0 0.4rem 0; color: #F8FAFC;">{card['title']}</h3>
<p style="font-size: 0.82rem; color: #94A3B8; line-height: 1.45; margin: 0 0 0.8rem 0;">{card['desc']}</p>
</div>
<div>
<div style="font-size: 0.74rem; color: #64748B; margin-bottom: 0.3rem; font-family: 'JetBrains Mono', monospace;">SAMPLE QUERY:</div>
<div style="font-size: 0.78rem; color: #38BDF8; font-style: italic; background: rgba(56, 189, 248, 0.08); padding: 0.35rem 0.55rem; border-radius: 6px; border: 1px dashed rgba(56, 189, 248, 0.25); margin-bottom: 0.7rem;">"{card['example']}"</div>
</div>
</div>
""")
            render_html(card_html)

            if st.button(f"Launch {card['badge']}", key=f"launch_card_{card['id']}", use_container_width=True):
                # Populate state with the scenario for instant gratification
                scenario_data = card["scenario_fn"]()
                st.session_state["uploaded_image_a"] = scenario_data["image_a"]
                st.session_state["uploaded_image_b"] = scenario_data.get("image_b")
                st.session_state["image_a_name"] = scenario_data["image_a_name"]
                st.session_state["image_b_name"] = scenario_data.get("image_b_name")
                st.session_state["query_text"] = scenario_data["default_query"]
                st.session_state["analysis_mode"] = card["mode"]
                st.session_state["analysis_step"] = 2  # Proceed to query review
                st.session_state["is_processing"] = False
                st.session_state["pipeline_completed"] = False
                set_page("new_analysis")
                st.rerun()
