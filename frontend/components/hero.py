from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Hero Banner Component
Renders the high-impact geospatial hero banner and primary call-to-actions.
"""

import streamlit as st
import config.settings as cfg
from utils.state import set_page


def render_hero() -> None:
    """Render the landing hero section."""
    hero_html = safe_html(f"""
<div style="text-align: center; max-width: 860px; margin: 1.5rem auto 2.2rem auto;">
    <div style="margin-bottom: 0.6rem;">
        <span class="sq-badge sq-badge-cyan">● MULTIMODAL EARTH OBSERVATION AI PLATFORM</span>
    </div>
    <h1 style="font-size: 2.85rem; line-height: 1.15; margin: 0.4rem 0 0.8rem 0; font-weight: 700; letter-spacing: -0.025em; background: linear-gradient(180deg, #FFFFFF 0%, #B4C6E7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        {cfg.TAGLINE}
    </h1>
    <p style="font-size: 1.15rem; color: #94A3B8; max-width: 680px; margin: 0 auto 1.8rem auto; line-height: 1.5;">
        {cfg.APP_SUBTITLE}. Upload multispectral or SAR imagery and ask questions in plain English—SatQuery autonomously routes your query to specialist AI models.
    </p>
</div>
""")
    render_html(hero_html)

    # CTAs
    col_cta1, col_cta2, col_cta3 = st.columns([1, 1.2, 1])
    with col_cta2:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 Start New Analysis", type="primary", use_container_width=True, key="hero_start_btn"):
                set_page("new_analysis")
                st.session_state["analysis_step"] = 1
                st.rerun()
        with c2:
            if st.button("🧭 Explore Workflows", use_container_width=True, key="hero_explore_btn"):
                st.session_state["scroll_to_cards"] = True
                st.rerun()

    st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)

    # High-Resolution Satellite Remote Sensing Visual Hero
    hero_img_path = cfg.ASSETS_DIR / "satellite_hero.jpg"
    if hero_img_path.exists():
        st.image(str(hero_img_path), caption="Live Earth Observation Telemetry Feed • Sentinel-5 Optical/SAR Orbit (792 km SSO)", use_container_width=True)
