from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Settings & About Component
Allows configuring confidence thresholds, API endpoints, and displays SIH project information.
"""

import streamlit as st
import config.settings as cfg
from utils.state import clear_analysis_inputs


def render_settings_page() -> None:
    """Render the Settings and About view."""
    render_html("""
<div style="margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
            <h2 style="font-size: 1.85rem; margin: 0 0 0.3rem 0; font-weight: 700; color: var(--text-pure);">
                System Settings & Preferences
            </h2>
            <p style="color: var(--text-muted); font-size: 0.92rem; margin: 0;">
                Configure interface theme, model confidence thresholds, and inspect platform metadata.
            </p>
        </div>
        <span class="sq-badge sq-badge-cyan">PREFERENCES</span>
    </div>
</div>
""")

    c1, c2 = st.columns(2)

    with c1:
        # Appearance / Theme Preference Card
        theme_names = {
            "dark": ("Dark Orbit", "sq-badge-cyan", "Cyberpunk Space Void with Neon Accents"),
            "pro_dark": ("Enterprise Obsidian", "sq-badge-purple", "Professional Midnight Slate with Royal Blue Accents"),
            "light": ("Light Cleanroom", "sq-badge-green", "Daylight Precision with Crisp High-Contrast Styling")
        }
        curr_theme = st.session_state.get("app_theme", "dark")
        theme_title, theme_badge_class, theme_desc = theme_names.get(
            curr_theme, ("Dark Orbit", "sq-badge-cyan", "Cyberpunk Space Void with Neon Accents")
        )

        render_html(f"""
<div style="background: var(--bg-glass); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1.1rem; margin-bottom: 0.9rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
        <h4 style="color: var(--text-pure); margin: 0; font-size: 0.98rem; font-weight: 600;">Interface Theme</h4>
        <span class="sq-badge {theme_badge_class}" style="font-size: 0.7rem;">{theme_title.upper()} MODE</span>
    </div>
    <p style="font-size: 0.8rem; color: var(--text-muted); margin: 0 0 0.75rem 0;">
        Active: <span style="color: var(--cyan-accent); font-weight: 600;">{theme_title}</span> — {theme_desc}.
    </p>
</div>
""")

        # Single Dropdown Selector for 3 Themes
        theme_options = {
            "🌌 Dark Orbit (Cyberpunk Space)": "dark",
            "💼 Enterprise Obsidian (Professional Dark)": "pro_dark",
            "☀️ Light Cleanroom (Daylight Precision)": "light"
        }
        rev_theme_options = {v: k for k, v in theme_options.items()}
        current_option_label = rev_theme_options.get(curr_theme, "🌌 Dark Orbit (Cyberpunk Space)")

        col_drop, _ = st.columns([2.0, 2.0])
        with col_drop:
            selected_label = st.selectbox(
                "Interface Theme Mode",
                options=list(theme_options.keys()),
                index=list(theme_options.keys()).index(current_option_label),
                key="interface_theme_dropdown",
                help="Select your preferred visual mode for charts, maps, and workflows."
            )
            selected_key = theme_options[selected_label]
            if selected_key != curr_theme:
                st.session_state["app_theme"] = selected_key
                st.rerun()

        st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

        render_html("""
<div style="background: var(--bg-glass); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1.1rem; margin-bottom: 1.2rem;">
    <h4 style="color: var(--text-pure); margin-top: 0;">Inference & Threshold Settings</h4>
    <p style="font-size: 0.8rem; color: var(--text-muted);">Adjust sensitivity thresholds for object grounding and change detection.</p>
</div>
""")

        st.slider("Grounding Confidence Threshold (τ)", min_value=0.50, max_value=0.98, value=0.85, step=0.01, help="Minimum prediction confidence required to render spatial bounding boxes.")
        st.slider("Change Detection Sensitivity", min_value=0.5, max_value=2.0, value=1.2, step=0.1, help="Multiplicative scalar on radiometric difference tensors.")
        st.selectbox("Default CRS Projection", ["EPSG:4326 (WGS 84)", "EPSG:3857 (Web Mercator)", "UTM Zone 43N"], index=0)

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        if st.button("Reset All Session State & Data", type="secondary"):
            clear_analysis_inputs()
            st.session_state["history"] = []
            st.session_state["saved_insights"] = []
            st.success("All temporary state cleared.")
            st.rerun()

    with c2:
        render_html(f"""
<div style="background: var(--bg-glass); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 1.2rem;">
    <h4 style="color: var(--text-pure); margin-top: 0;">Project Information</h4>
    <div style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.7;">
        <div><b>Project Title:</b> SatQuery AI</div>
        <div><b>Tagline:</b> {cfg.TAGLINE}</div>
        <div><b>Platform:</b> SatQuery Enterprise Geospatial AI</div>
        <div><b>Mission Profile:</b> <span style="color: var(--cyan-accent); font-weight: 600;">Autonomous Multimodal EO Analysis</span></div>
        <div><b>Category:</b> Space Technology / AI Geospatial Intelligence</div>
        <div><b>Version:</b> {cfg.APP_VERSION}</div>
    </div>
    <div style="margin-top: 1rem; padding-top: 0.8rem; border-top: 1px solid var(--border-subtle); font-size: 0.8rem; color: var(--text-faint);">
        Built with high-end Python Streamlit, modular visual evidence viewers, procedural remote-sensing simulation, and integration-ready API contracts.
    </div>
</div>
""")
