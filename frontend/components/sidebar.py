from utils.ui_utils import safe_html, render_html
import streamlit as st
import textwrap
import config.settings as cfg
from utils.state import set_page, clear_analysis_inputs
from services.sample_data import (
    generate_change_detection_scenario,
    generate_grounding_scenario,
    generate_optical_sar_scenario,
    generate_vqa_scenario
)


def render_sidebar() -> None:
    """Render the application sidebar."""
    with st.sidebar:
        # Top Brand Section
        brand_html = safe_html(f"""
<div style="text-align: center; padding: 0.8rem 0 1.2rem 0;">
<div style="width: 52px; height: 52px; margin: 0 auto 0.6rem auto; border-radius: 14px; background: linear-gradient(135deg, #00F0FF 0%, #0077B6 100%); display: flex; align-items: center; justify-content: center; font-size: 1.8rem; box-shadow: 0 0 24px rgba(0, 240, 255, 0.4);">
🛰️
</div>
<h2 style="font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; margin: 0; color: #FFFFFF; font-weight: 700; letter-spacing: -0.01em;">SATQUERY AI</h2>
<div style="font-size: 0.74rem; color: #38BDF8; font-family: 'JetBrains Mono', monospace; margin-top: 2px;">
AUTONOMOUS GEOSPATIAL INTELLIGENCE
</div>
</div>
""")
        render_html(brand_html)

        st.markdown("---")

        # Main Navigation
        st.markdown('<div style="font-size: 0.72rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.6rem;">NAVIGATION</div>', unsafe_allow_html=True)

        curr_page = st.session_state.get("current_page", "home")

        nav_items = [
            ("home", "🌐 Overview & Dashboard"),
            ("new_analysis", "⚡ New Analysis"),
            ("history", f"📜 Analysis History ({len(st.session_state.get('history', []))})"),
            ("saved_insights", f"🔖 Saved Insights ({len(st.session_state.get('saved_insights', []))})"),
            ("api_spec", "🧩 Architecture & API Spec"),
            ("settings", "⚙️ System Settings")
        ]

        for page_id, label in nav_items:
            is_active = curr_page == page_id
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{page_id}", use_container_width=True, type=btn_type):
                set_page(page_id)
                st.rerun()

        st.markdown("---")

        # Demo Mode Toggle & Quick Pre-loads
        st.markdown('<div style="font-size: 0.72rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.6rem;">OPERATING MODE</div>', unsafe_allow_html=True)
        
        demo_mode = st.toggle(
            "Demo Simulation Mode",
            value=st.session_state.get("demo_mode", True),
            help="Toggle between high-fidelity simulated response and live backend REST connection."
        )
        st.session_state["demo_mode"] = demo_mode

        if demo_mode:
            demo_alert_html = safe_html("""
<div style="font-size: 0.76rem; color: #94A3B8; background: rgba(0, 240, 255, 0.05); padding: 0.6rem; border-radius: 8px; border: 1px solid rgba(0, 240, 255, 0.15); margin-bottom: 0.8rem;">
💡 <b>Demo Mode Active:</b> Evaluators can test full end-to-end workflows with pre-bundled remote sensing scenes.
</div>
""")
            render_html(demo_alert_html)

            # Quick Scenario Selector
            st.markdown('<div style="font-size: 0.72rem; color: #64748B; font-weight: 600; margin-bottom: 0.4rem;">QUICK TEST SCENARIOS</div>', unsafe_allow_html=True)
            scenarios = [
                ("change", "🔄 Urban Change (2024-2026)"),
                ("grounding", "🎯 Industrial Tanks Grounding"),
                ("optical_sar", "📡 Flood Inundation (SAR+Opt)"),
                ("vqa", "❓ Port Maritime Activity (VQA)")
            ]

            for s_key, s_label in scenarios:
                if st.button(s_label, key=f"quick_s_{s_key}", use_container_width=True):
                    if s_key == "change":
                        data = generate_change_detection_scenario()
                        st.session_state["uploaded_image_a"] = data["image_a"]
                        st.session_state["uploaded_image_b"] = data["image_b"]
                        st.session_state["image_a_name"] = data["image_a_name"]
                        st.session_state["image_b_name"] = data["image_b_name"]
                        st.session_state["query_text"] = data["default_query"]
                        st.session_state["analysis_mode"] = cfg.MODE_COMPARE
                    elif s_key == "grounding":
                        data = generate_grounding_scenario()
                        st.session_state["uploaded_image_a"] = data["image_a"]
                        st.session_state["uploaded_image_b"] = None
                        st.session_state["image_a_name"] = data["image_a_name"]
                        st.session_state["image_b_name"] = None
                        st.session_state["query_text"] = data["default_query"]
                        st.session_state["analysis_mode"] = cfg.MODE_SINGLE
                    elif s_key == "optical_sar":
                        data = generate_optical_sar_scenario()
                        st.session_state["uploaded_image_a"] = data["image_a"]
                        st.session_state["uploaded_image_b"] = data["image_b"]
                        st.session_state["image_a_name"] = data["image_a_name"]
                        st.session_state["image_b_name"] = data["image_b_name"]
                        st.session_state["query_text"] = data["default_query"]
                        st.session_state["analysis_mode"] = cfg.MODE_OPTICAL_SAR
                    elif s_key == "vqa":
                        data = generate_vqa_scenario()
                        st.session_state["uploaded_image_a"] = data["image_a"]
                        st.session_state["uploaded_image_b"] = None
                        st.session_state["image_a_name"] = data["image_a_name"]
                        st.session_state["image_b_name"] = None
                        st.session_state["query_text"] = data["default_query"]
                        st.session_state["analysis_mode"] = cfg.MODE_SINGLE

                    st.session_state["analysis_step"] = 2
                    st.session_state["is_processing"] = False
                    st.session_state["pipeline_completed"] = False
                    set_page("new_analysis")
                    st.rerun()

        st.markdown("---")

        # System Status HUD
        st.markdown('<div style="font-size: 0.72rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.6rem;">SYSTEM HEALTH</div>', unsafe_allow_html=True)
        
        status_items = [
            ("Agentic Router", "Active", "#10B981"),
            ("VQA Engine", "Ready", "#10B981"),
            ("Visual Grounding", "Ready", "#10B981"),
            ("Change Detection", "Ready", "#10B981"),
            ("Optical + SAR Core", "Ready", "#10B981")
        ]

        status_html = '<div style="background: rgba(10, 15, 29, 0.6); padding: 0.6rem 0.8rem; border-radius: 8px; border: 1px solid rgba(56, 189, 248, 0.12);">'
        for name, stat, color in status_items:
            status_html += f'<div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.76rem; padding: 0.18rem 0;"><span style="color: #94A3B8;">{name}</span><span style="color: {color}; font-weight: 600;">● {stat}</span></div>'
        status_html += "</div>"
        render_html(status_html)

        st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset Workspace", use_container_width=True):
            clear_analysis_inputs()
            set_page("home")
            st.rerun()
