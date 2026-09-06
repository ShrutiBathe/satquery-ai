from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Professional Geospatial Intelligence Dashboard Component
Provides live telemetry KPI cards, interactive orbital mission map (Plotly),
recent intelligence feed, constellation health, and quick query launchpad.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import textwrap
from datetime import date, datetime
from PIL import Image

import config.settings as cfg
from utils.state import set_page
from utils.image_utils import generate_mock_geospatial_metadata
from services.sample_data import (
    generate_change_detection_scenario,
    generate_grounding_scenario,
    generate_optical_sar_scenario,
    generate_vqa_scenario
)


def _h(html_str: str) -> str:
    """Strip all leading whitespace and empty lines to prevent Markdown from creating code blocks."""
    return safe_html(html_str)


def render_telemetry_kpis() -> None:
    """Render top live operational KPI metric strip."""
    st.markdown(
        _h("""
        <div style="margin: 0.5rem 0 1.2rem 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10B981; box-shadow: 0 0 10px #10B981;"></span>
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #10B981; font-weight: 600; letter-spacing: 0.05em;">
        LIVE GEOSPATIAL TELEMETRY FEED • ALL SYSTEMS NOMINAL
        </span>
        </div>
        <span class="sq-badge sq-badge-cyan">REFRESH: 1.0s REAL-TIME</span>
        </div>
        </div>
        """),
        unsafe_allow_html=True
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    kpi_items = [
        {
            "col": col1,
            "icon": "🛰️",
            "label": "INGEST PLATFORMS",
            "value": "4 Constellations",
            "sub": "Sentinel-1/2, Landsat, WV-3",
            "color": "#00F0FF"
        },
        {
            "col": col2,
            "icon": "🌐",
            "label": "ACTIVE AOI SWATH",
            "value": "142,850 km²",
            "sub": "Global Monitored Footprint",
            "color": "#38BDF8"
        },
        {
            "col": col3,
            "icon": "⚡",
            "label": "AGENT ROUTING SPEED",
            "value": "185 ms",
            "sub": "Autonomous Intent Classifier",
            "color": "#A855F7"
        },
        {
            "col": col4,
            "icon": "🎯",
            "label": "LOCALIZATION PRECISION",
            "value": "96.4% IoU",
            "sub": "Sub-Pixel Spatial Grounding",
            "color": "#10B981"
        },
        {
            "col": col5,
            "icon": "🛡️",
            "label": "DECISION CONFIDENCE",
            "value": "93.8% Avg",
            "sub": "Cross-Sensor Verified",
            "color": "#F59E0B"
        }
    ]

    for item in kpi_items:
        with item["col"]:
            card_code = f"""
            <div style="background: rgba(14, 22, 43, 0.7); border: 1px solid rgba(56, 189, 248, 0.18); border-radius: 12px; padding: 0.9rem 1rem; position: relative; overflow: hidden;">
            <div style="position: absolute; top: 8px; right: 10px; font-size: 1.2rem; opacity: 0.65;">{item['icon']}</div>
            <div style="font-size: 0.70rem; color: #64748B; font-family: 'JetBrains Mono', monospace; font-weight: 600; letter-spacing: 0.04em;">{item['label']}</div>
            <div style="font-size: 1.35rem; font-weight: 700; color: {item['color']}; margin: 0.2rem 0; font-family: 'Space Grotesk', sans-serif;">{item['value']}</div>
            <div style="font-size: 0.72rem; color: #94A3B8;">{item['sub']}</div>
            </div>
            """
            st.markdown(_h(card_code), unsafe_allow_html=True)


def render_mission_map() -> None:
    """Render the interactive Global Remote Sensing Mission Operations Map."""
    header_html = safe_html("""
<div style="margin: 2rem 0 0.8rem 0;">
<div style="display: flex; justify-content: space-between; align-items: flex-end;">
<div>
<h3 style="font-size: 1.3rem; margin: 0 0 0.2rem 0; font-weight: 700; color: #F8FAFC;">
Global Satellite Mission Tracking & Active AOIs
</h3>
<p style="color: #94A3B8; font-size: 0.85rem; margin: 0;">
Live orbital coverage, sensor footprints, and scheduled remote sensing missions across key geopolitical and environmental sectors.
</p>
</div>
<div style="display: flex; gap: 0.5rem;">
<span class="sq-badge sq-badge-cyan">ORBITAL TRACKS: LIVE</span>
<span class="sq-badge sq-badge-green">5 ACTIVE MISSIONS</span>
</div>
</div>
</div>
""")
    st.markdown(_h(header_html), unsafe_allow_html=True)

    # Define Active Mission Points
    missions = [
        {
            "name": "Dubai Marina & Industrial Expansion",
            "lat": 25.1972,
            "lon": 55.2744,
            "type": "Bi-Temporal Change Detection",
            "sensor": "Sentinel-2 (10m MSI)",
            "status": "Change Detected (+18.5 Ha)",
            "color": "#F43F5E",
            "size": 16
        },
        {
            "name": "Jamnagar Hydrocarbon Storage Complex",
            "lat": 22.4707,
            "lon": 70.0577,
            "type": "Visual Grounding & Localization",
            "sensor": "WorldView-3 (0.3m VHR)",
            "status": "6/6 Tanks Intact (96.4% Conf)",
            "color": "#00F0FF",
            "size": 16
        },
        {
            "name": "Brahmaputra River Basin Flood Surge",
            "lat": 26.2006,
            "lon": 92.9376,
            "type": "Multimodal Optical + SAR Fusion",
            "sensor": "Sentinel-1 SAR + Sentinel-2",
            "status": "62.4 Ha Inundated (-24 dB SAR)",
            "color": "#A855F7",
            "size": 18
        },
        {
            "name": "Singapore Strait Commercial Anchorage",
            "lat": 1.29027,
            "lon": 103.851959,
            "type": "Visual Question Answering (VQA)",
            "sensor": "Pléiades Neo (0.3m Optical)",
            "status": "2 Panamax Vessels Berthed",
            "color": "#38BDF8",
            "size": 16
        },
        {
            "name": "Amazon Basin Environmental Audit (Pará)",
            "lat": -3.4168,
            "lon": -52.2167,
            "type": "Deforestation & Biomass VQA",
            "sensor": "Landsat-9 OLI-2 (15m)",
            "status": "Canopy Density Baseline 88%",
            "color": "#10B981",
            "size": 14
        }
    ]

    df_missions = pd.DataFrame(missions)

    fig = go.Figure()

    # Add Orbital Ground Track Curves (Simulated Sun-Synchronous SSO Track)
    orbit_lons = [-160, -130, -100, -70, -40, -10, 20, 50, 80, 110, 140, 170]
    orbit_lats = [65, 45, 15, -15, -45, -65, -45, -15, 15, 45, 65, 45]

    fig.add_trace(go.Scattergeo(
        lon=orbit_lons,
        lat=orbit_lats,
        mode="lines",
        line=dict(width=1.5, color="rgba(0, 240, 255, 0.4)", dash="dot"),
        hoverinfo="none",
        name="Sentinel-2 SSO Orbital Track"
    ))

    # Add Mission Points
    fig.add_trace(go.Scattergeo(
        lon=df_missions["lon"],
        lat=df_missions["lat"],
        mode="markers+text",
        marker=dict(
            size=df_missions["size"],
            color=df_missions["color"],
            opacity=0.9,
            symbol="circle",
            line=dict(width=2, color="#FFFFFF")
        ),
        text=[f"📍 {n.split()[0]}" for n in df_missions["name"]],
        textposition="top center",
        textfont=dict(color="#F8FAFC", size=10, family="Inter"),
        customdata=list(zip(df_missions["name"], df_missions["type"], df_missions["sensor"], df_missions["status"])),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>" +
            "<b>Mission Task:</b> %{customdata[1]}<br>" +
            "<b>Ingest Sensor:</b> %{customdata[2]}<br>" +
            "<b>Live Telemetry:</b> <span style='color:#00F0FF;'>%{customdata[3]}</span><br>" +
            "<extra></extra>"
        ),
        name="Active Mission AOIs"
    ))

    # Geospatial Map Layout (Responsive Dark / Pro Dark / Light Theme)
    curr_theme = st.session_state.get("app_theme", "dark")
    if curr_theme == "light":
        map_bg = "#FFFFFF"
        land_col = "#E2E8F0"
        ocean_col = "#F1F5F9"
        border_col = "rgba(2, 132, 199, 0.35)"
    elif curr_theme == "pro_dark":
        map_bg = "#0A0E17"
        land_col = "#162238"
        ocean_col = "#0A0E17"
        border_col = "rgba(56, 189, 248, 0.28)"
    else:
        map_bg = "#060913"
        land_col = "#0E162B"
        ocean_col = "#060913"
        border_col = "rgba(56, 189, 248, 0.22)"

    fig.update_layout(
        geo=dict(
            bgcolor=map_bg,
            showland=True,
            landcolor=land_col,
            showocean=True,
            oceancolor=ocean_col,
            showlakes=True,
            lakecolor=ocean_col,
            showrivers=True,
            rivercolor=border_col,
            showcountries=True,
            countrycolor=border_col,
            countrywidth=0.8,
            coastlinecolor=border_col,
            coastlinewidth=1.0,
            projection_type="natural earth"
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=380,
        paper_bgcolor=map_bg,
        plot_bgcolor=map_bg,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_quick_query_hud() -> None:
    """Render the Mission-Grade Multimodal Satellite Imagery Ingestion & Query Console."""
    hud_html = safe_html("""
<div class="sq-command-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.85rem;">
        <div style="display: flex; align-items: center; gap: 0.95rem;">
            <div class="sq-icon-box">🛰️</div>
            <div>
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-family: 'Space Grotesk', sans-serif; font-size: 1.28rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.01em;">
                        GEOSPATIAL INGESTION & COGNITIVE WORKSPACE
                    </span>
                    <span class="sq-badge sq-badge-cyan">COGNITIVE AGENT</span>
                </div>
                <div style="font-size: 0.81rem; color: #94A3B8; margin-top: 3px;">
                    Multi-Sensor Ground Station • Optical Multispectral, Synthetic Aperture Radar (SAR) & Dual-Epoch Temporal Alignment
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span class="sq-badge sq-badge-green">● SENSORS SYNCHRONIZED</span>
            <span class="sq-badge sq-badge-cyan">PIPELINE 4.2 PRO</span>
        </div>
    </div>
</div>
""")
    render_html(hud_html)

    # Initialize dashboard modality in session state
    if "dash_modality" not in st.session_state:
        current_m = st.session_state.get("analysis_mode", cfg.MODE_COMPARE)
        if current_m == cfg.MODE_OPTICAL_SAR:
            st.session_state["dash_modality"] = "sar_optical"
        elif current_m == cfg.MODE_SINGLE:
            st.session_state["dash_modality"] = "single"
        else:
            st.session_state["dash_modality"] = "compare"

    dash_mode = st.session_state["dash_modality"]

    # 1. Modality Switcher Deck
    st.markdown('<div style="font-size: 0.74rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.65rem; font-family: monospace;">SELECT SATELLITE IMAGERY SENSOR WORKFLOW:</div>', unsafe_allow_html=True)
    st.markdown('<div class="sq-modality-wrapper">', unsafe_allow_html=True)
    c_m1, c_m2, c_m3 = st.columns(3)

    with c_m1:
        is_comp = (dash_mode == "compare")
        if st.button("⏱️ BI-TEMPORAL COMPARISON\nDual-Epoch Urban & Surface Alteration", key="btn_sel_dash_comp", type="primary" if is_comp else "secondary", use_container_width=True):
            st.session_state["dash_modality"] = "compare"
            st.session_state["analysis_mode"] = cfg.MODE_COMPARE
            st.rerun()

    with c_m2:
        is_sar = (dash_mode == "sar_optical")
        if st.button("📡 DUAL-BAND SENSOR FUSION\nMultispectral RGB + SAR Radar Inundation", key="btn_sel_dash_sar", type="primary" if is_sar else "secondary", use_container_width=True):
            st.session_state["dash_modality"] = "sar_optical"
            st.session_state["analysis_mode"] = cfg.MODE_OPTICAL_SAR
            st.rerun()

    with c_m3:
        is_single = (dash_mode == "single")
        if st.button("🛰️ VHR OPTICAL SCENE\n0.3m-0.5m GSD Grounding & VQA", key="btn_sel_dash_single", type="primary" if is_single else "secondary", use_container_width=True):
            st.session_state["dash_modality"] = "single"
            st.session_state["analysis_mode"] = cfg.MODE_SINGLE
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Ingestion Bays & Toolbars Based on Active Modality
    if dash_mode == "compare":
        render_html("""
<div class="sq-mission-briefing">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.05rem;">⏱️</span>
            <span style="font-weight: 700; color: #00F0FF; letter-spacing: 0.04em; font-family: monospace; font-size: 0.82rem;">MISSION DIRECTIVE: BI-TEMPORAL SURFACE & URBAN REASONING</span>
            <span class="sq-badge sq-badge-cyan">CO-REGISTERED EO</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.45rem;">
            <span class="sq-telemetry-tag">RESOLUTION: 10m GSD</span>
            <span class="sq-telemetry-tag">ALIGNMENT: SUB-PIXEL AFFINE</span>
            <span class="sq-telemetry-tag">DELTA: 2024 → 2026</span>
        </div>
    </div>
    <div style="color: #94A3B8; font-size: 0.80rem; margin-top: 5px; line-height: 1.45;">
        Ingest co-registered baseline (T0) and post-event (T1) Earth Observation scenes. The cognitive vision-language agent cross-correlates spectral reflectance shifts to map structural expansion, new developments, and terrain alteration.
    </div>
</div>
""")
        c_a, c_b = st.columns(2)
        with c_a:
            render_html("""
<div class="sq-sensor-bay-frame">
    <div class="sq-sensor-bay-header">
        <div style="display: flex; align-items: center; gap: 0.55rem;">
            <span class="sq-bay-pill">BAY 01</span>
            <span style="font-weight: 600; color: #F8FAFC; font-size: 0.88rem; letter-spacing: 0.02em;">BASELINE REFERENCE (T0)</span>
        </div>
        <span class="sq-badge sq-badge-cyan">PRE-EVENT SCENE</span>
    </div>
    <div style="font-size: 0.74rem; color: #64748B; margin-bottom: 0.6rem; font-family: monospace;">
        PLATFORM: SENTINEL-2 MSI • BANDS: B02, B03, B04, B08 (10m GSD)
    </div>
</div>
""")
            d_a = st.date_input("Acquisition Timestamp (Epoch T0)", value=st.session_state.get("image_a_date", date(2024, 6, 15)), key="dash_date_a")
            st.session_state["image_a_date"] = d_a
            img_a = st.session_state.get("uploaded_image_a")
            name_a = st.session_state.get("image_a_name", "Baseline_Scene.tif")

            if img_a is None:
                f_a = st.file_uploader("Upload Baseline Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="dash_up_bitemp_a")
                if f_a is not None:
                    try:
                        pil_a = Image.open(f_a)
                        st.session_state["uploaded_image_a"] = pil_a
                        st.session_state["image_a_name"] = f_a.name
                        st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(f_a.name, sensor_type="Optical (Baseline)", img_size=pil_a.size)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error reading Image A: {e}")
            else:
                render_html(f"""
<div class="sq-hud-viewport">
    <div class="sq-hud-corner sq-hud-tl"></div>
    <div class="sq-hud-corner sq-hud-tr"></div>
    <div class="sq-hud-corner sq-hud-bl"></div>
    <div class="sq-hud-corner sq-hud-br"></div>
    <div class="sq-hud-overlay-tag">
        <span>● T0 CALIBRATED</span>
        <span>{img_a.size[0]}×{img_a.size[1]} px</span>
        <span>{name_a}</span>
    </div>
</div>
""")
                st.image(img_a, caption=f"Baseline Image A ({d_a}) • {img_a.size[0]}×{img_a.size[1]} px", use_container_width=True)
                if st.button("↺ Replace Baseline Raster", key="dash_rem_bitemp_a", use_container_width=True):
                    st.session_state["uploaded_image_a"] = None
                    st.session_state["image_a_name"] = None
                    st.rerun()

        with c_b:
            render_html("""
<div class="sq-sensor-bay-frame">
    <div class="sq-sensor-bay-header">
        <div style="display: flex; align-items: center; gap: 0.55rem;">
            <span class="sq-bay-pill sq-bay-pill-rose">BAY 02</span>
            <span style="font-weight: 600; color: #F8FAFC; font-size: 0.88rem; letter-spacing: 0.02em;">POST-EVENT MONITORING (T1)</span>
        </div>
        <span class="sq-badge sq-badge-rose">TARGET SCENE</span>
    </div>
    <div style="font-size: 0.74rem; color: #64748B; margin-bottom: 0.6rem; font-family: monospace;">
        PLATFORM: SENTINEL-2 MSI • BANDS: B02, B03, B04, B08 (10m GSD)
    </div>
</div>
""")
            d_b = st.date_input("Acquisition Timestamp (Epoch T1)", value=st.session_state.get("image_b_date", date(2026, 3, 20)), key="dash_date_b")
            st.session_state["image_b_date"] = d_b
            img_b = st.session_state.get("uploaded_image_b")
            name_b = st.session_state.get("image_b_name", "PostEvent_Scene.tif")

            if img_b is None:
                f_b = st.file_uploader("Upload Post-Event Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="dash_up_bitemp_b")
                if f_b is not None:
                    try:
                        pil_b = Image.open(f_b)
                        st.session_state["uploaded_image_b"] = pil_b
                        st.session_state["image_b_name"] = f_b.name
                        st.session_state["image_metadata_b"] = generate_mock_geospatial_metadata(f_b.name, sensor_type="Optical (Post-Event)", img_size=pil_b.size)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error reading Image B: {e}")
            else:
                render_html(f"""
<div class="sq-hud-viewport">
    <div class="sq-hud-corner sq-hud-tl"></div>
    <div class="sq-hud-corner sq-hud-tr"></div>
    <div class="sq-hud-corner sq-hud-bl"></div>
    <div class="sq-hud-corner sq-hud-br"></div>
    <div class="sq-hud-overlay-tag">
        <span>● T1 CALIBRATED</span>
        <span>{img_b.size[0]}×{img_b.size[1]} px</span>
        <span>{name_b}</span>
    </div>
</div>
""")
                st.image(img_b, caption=f"Post-Event Image B ({d_b}) • {img_b.size[0]}×{img_b.size[1]} px", use_container_width=True)
                if st.button("↺ Replace Target Raster", key="dash_rem_bitemp_b", use_container_width=True):
                    st.session_state["uploaded_image_b"] = None
                    st.session_state["image_b_name"] = None
                    st.rerun()

        # Calibration & Benchmark Control Toolbar
        st.markdown('<div class="sq-bay-toolbar">', unsafe_allow_html=True)
        c_swp, c_load, c_clr = st.columns([1, 2.2, 1])
        with c_swp:
            if st.button("⇄ Swap Epochs (T0 ⇄ T1)", key="dash_swap_bitemp", use_container_width=True):
                st.session_state["uploaded_image_a"], st.session_state["uploaded_image_b"] = st.session_state.get("uploaded_image_b"), st.session_state.get("uploaded_image_a")
                st.session_state["image_a_name"], st.session_state["image_b_name"] = st.session_state.get("image_b_name"), st.session_state.get("image_a_name")
                st.session_state["image_a_date"], st.session_state["image_b_date"] = st.session_state.get("image_b_date"), st.session_state.get("image_a_date")
                st.rerun()
        with c_load:
            st.markdown('<div class="sq-benchmark-btn">', unsafe_allow_html=True)
            if st.button("⚡ LOAD BENCHMARK 2024 vs 2026 PAIR (1-CLICK DEMO)", key="dash_load_bitemp_sample", use_container_width=True):
                sc = generate_change_detection_scenario()
                st.session_state["uploaded_image_a"] = sc["image_a"]
                st.session_state["uploaded_image_b"] = sc["image_b"]
                st.session_state["image_a_name"] = sc["image_a_name"]
                st.session_state["image_b_name"] = sc["image_b_name"]
                st.session_state["image_a_date"] = sc["image_a_date"]
                st.session_state["image_b_date"] = sc["image_b_date"]
                st.session_state["dashboard_instant_query_text"] = sc["default_query"]
                st.session_state["query_text"] = sc["default_query"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c_clr:
            if st.button("🗑️ Clear Bays", key="dash_clear_bitemp", use_container_width=True):
                st.session_state["uploaded_image_a"] = None
                st.session_state["uploaded_image_b"] = None
                st.session_state["image_a_name"] = None
                st.session_state["image_b_name"] = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        placeholder_text = "e.g., What infrastructure and land-cover changes occurred between 2024 and 2026?"
        preset_prompts = [
            ("🔍", "CHANGE OVERVIEW", "What changed between 2024 and 2026?"),
            ("🏗️", "INFRASTRUCTURE", "Identify newly built logistics facilities and roads"),
            ("🌊", "COASTAL DYNAMICS", "Detect shoreline erosion or coastal alterations")
        ]

    elif dash_mode == "sar_optical":
        render_html("""
<div class="sq-mission-briefing sq-mission-briefing-purple">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.05rem;">📡</span>
            <span style="font-weight: 700; color: #A855F7; letter-spacing: 0.04em; font-family: monospace; font-size: 0.82rem;">MISSION DIRECTIVE: MULTIMODAL OPTICAL + C-BAND SAR RADAR FUSION</span>
            <span class="sq-badge sq-badge-purple">SENSOR COMPLEMENTARITY</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.45rem;">
            <span class="sq-telemetry-tag">RADAR: C-SAR (VV+VH)</span>
            <span class="sq-telemetry-tag">OPTICAL: RGB (10m)</span>
            <span class="sq-telemetry-tag">WEATHER: ALL-CONDITIONS</span>
        </div>
    </div>
    <div style="color: #94A3B8; font-size: 0.80rem; margin-top: 5px; line-height: 1.45;">
        Fuse high-fidelity optical multispectral reflectance with cloud-penetrating Sentinel-1 SAR microwave radar backscatter. Accurately delineate standing water and flood boundaries beneath heavy cloud cover.
    </div>
</div>
""")
        c_opt, c_sar = st.columns(2)
        with c_opt:
            render_html("""
<div class="sq-sensor-bay-frame">
    <div class="sq-sensor-bay-header">
        <div style="display: flex; align-items: center; gap: 0.55rem;">
            <span class="sq-bay-pill">BAY 01</span>
            <span style="font-weight: 600; color: #F8FAFC; font-size: 0.88rem; letter-spacing: 0.02em;">OPTICAL REFLECTANCE (RGB)</span>
        </div>
        <span class="sq-badge sq-badge-cyan">SENTINEL-2 MSI</span>
    </div>
    <div style="font-size: 0.74rem; color: #64748B; margin-bottom: 0.6rem; font-family: monospace;">
        SURFACE REFLECTANCE • BANDS: 4, 3, 2 (RGB 10m GSD)
    </div>
</div>
""")
            img_opt = st.session_state.get("uploaded_image_a")
            name_opt = st.session_state.get("image_a_name", "Optical_RGB.tif")

            if img_opt is None:
                f_opt = st.file_uploader("Upload Optical RGB Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="dash_up_opt")
                if f_opt is not None:
                    try:
                        pil_opt = Image.open(f_opt)
                        st.session_state["uploaded_image_a"] = pil_opt
                        st.session_state["image_a_name"] = f_opt.name
                        st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(f_opt.name, sensor_type="Optical (Sentinel-2)", img_size=pil_opt.size)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error reading Optical image: {e}")
            else:
                render_html(f"""
<div class="sq-hud-viewport">
    <div class="sq-hud-corner sq-hud-tl"></div>
    <div class="sq-hud-corner sq-hud-tr"></div>
    <div class="sq-hud-corner sq-hud-bl"></div>
    <div class="sq-hud-corner sq-hud-br"></div>
    <div class="sq-hud-overlay-tag">
        <span>● OPTICAL RGB</span>
        <span>{img_opt.size[0]}×{img_opt.size[1]} px</span>
        <span>{name_opt}</span>
    </div>
</div>
""")
                st.image(img_opt, caption=f"Optical RGB • {img_opt.size[0]}×{img_opt.size[1]} px", use_container_width=True)
                if st.button("↺ Replace Optical Scene", key="dash_rem_opt", use_container_width=True):
                    st.session_state["uploaded_image_a"] = None
                    st.session_state["image_a_name"] = None
                    st.rerun()

        with c_sar:
            render_html("""
<div class="sq-sensor-bay-frame">
    <div class="sq-sensor-bay-header">
        <div style="display: flex; align-items: center; gap: 0.55rem;">
            <span class="sq-bay-pill sq-bay-pill-purple">BAY 02</span>
            <span style="font-weight: 600; color: #F8FAFC; font-size: 0.88rem; letter-spacing: 0.02em;">SYNTHETIC APERTURE RADAR</span>
        </div>
        <span class="sq-badge sq-badge-purple">SENTINEL-1 C-SAR</span>
    </div>
    <div style="font-size: 0.74rem; color: #64748B; margin-bottom: 0.6rem; font-family: monospace;">
        MICROWAVE RADAR • C-BAND (5.405 GHz) • POLARIZATION: VV+VH
    </div>
</div>
""")
            img_sar = st.session_state.get("uploaded_image_b")
            name_sar = st.session_state.get("image_b_name", "SAR_Backscatter.tif")

            if img_sar is None:
                f_sar = st.file_uploader("Upload SAR Microwave Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="dash_up_sar")
                if f_sar is not None:
                    try:
                        pil_sar = Image.open(f_sar)
                        st.session_state["uploaded_image_b"] = pil_sar
                        st.session_state["image_b_name"] = f_sar.name
                        st.session_state["image_metadata_b"] = generate_mock_geospatial_metadata(f_sar.name, sensor_type="SAR (Sentinel-1 C-Band)", img_size=pil_sar.size)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error reading SAR image: {e}")
            else:
                render_html(f"""
<div class="sq-hud-viewport">
    <div class="sq-hud-corner sq-hud-tl"></div>
    <div class="sq-hud-corner sq-hud-tr"></div>
    <div class="sq-hud-corner sq-hud-bl"></div>
    <div class="sq-hud-corner sq-hud-br"></div>
    <div class="sq-hud-overlay-tag">
        <span>● SAR RADAR</span>
        <span>{img_sar.size[0]}×{img_sar.size[1]} px</span>
        <span>{name_sar}</span>
    </div>
</div>
""")
                st.image(img_sar, caption=f"SAR Radar Backscatter • {img_sar.size[0]}×{img_sar.size[1]} px", use_container_width=True)
                if st.button("↺ Replace SAR Scene", key="dash_rem_sar", use_container_width=True):
                    st.session_state["uploaded_image_b"] = None
                    st.session_state["image_b_name"] = None
                    st.rerun()

        # Calibration Toolbar
        st.markdown('<div class="sq-bay-toolbar">', unsafe_allow_html=True)
        c_load_sar, c_clr_sar = st.columns([2.4, 1])
        with c_load_sar:
            st.markdown('<div class="sq-benchmark-btn">', unsafe_allow_html=True)
            if st.button("⚡ LOAD DEMO FLOOD INUNDATION (OPTICAL + SAR PAIR)", key="dash_load_sar_sample", use_container_width=True):
                sc = generate_optical_sar_scenario()
                st.session_state["uploaded_image_a"] = sc["image_a"]
                st.session_state["uploaded_image_b"] = sc["image_b"]
                st.session_state["image_a_name"] = sc["image_a_name"]
                st.session_state["image_b_name"] = sc["image_b_name"]
                st.session_state["dashboard_instant_query_text"] = sc["default_query"]
                st.session_state["query_text"] = sc["default_query"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c_clr_sar:
            if st.button("🗑️ Reset Bays", key="dash_clear_sar", use_container_width=True):
                st.session_state["uploaded_image_a"] = None
                st.session_state["uploaded_image_b"] = None
                st.session_state["image_a_name"] = None
                st.session_state["image_b_name"] = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        placeholder_text = "e.g., Compare this region using both optical and SAR radar to delineate flood zones."
        preset_prompts = [
            ("⚡", "SENSOR FUSION", "Compare this region using both optical and SAR radar"),
            ("🌊", "FLOOD DELINEATION", "Map flood extents and water pooling under cloud cover"),
            ("📡", "RADAR ANALYSIS", "Evaluate microwave backscatter attenuation over fields")
        ]

    else:  # single
        render_html("""
<div class="sq-mission-briefing">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.05rem;">🛰️</span>
            <span style="font-weight: 700; color: #00F0FF; letter-spacing: 0.04em; font-family: monospace; font-size: 0.82rem;">MISSION DIRECTIVE: HIGH-RESOLUTION OBJECT LOCALIZATION & VQA</span>
            <span class="sq-badge sq-badge-cyan">VHR SPATIAL REASONING</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.45rem;">
            <span class="sq-telemetry-tag">GSD: 0.3m – 0.5m</span>
            <span class="sq-telemetry-tag">SENSOR: WORLDVIEW-3</span>
            <span class="sq-telemetry-tag">BBOX: 2D GROUNDING</span>
        </div>
    </div>
    <div style="color: #94A3B8; font-size: 0.80rem; margin-top: 5px; line-height: 1.45;">
        Analyze a high-resolution optical satellite scene (0.3m-0.5m GSD) to localize specific objects (fuel tanks, vessels, buildings) with bounding coordinates or answer spatial inquiries.
    </div>
</div>
""")
        c_up_s, c_samp_s = st.columns([1.3, 1])
        with c_up_s:
            render_html("""
<div class="sq-sensor-bay-frame">
    <div class="sq-sensor-bay-header">
        <div style="display: flex; align-items: center; gap: 0.55rem;">
            <span class="sq-bay-pill">BAY 01</span>
            <span style="font-weight: 600; color: #F8FAFC; font-size: 0.88rem; letter-spacing: 0.02em;">VHR SATELLITE SCENE (0.3m - 0.5m GSD)</span>
        </div>
        <span class="sq-badge sq-badge-cyan">SUB-METER OPTICAL</span>
    </div>
    <div style="font-size: 0.74rem; color: #64748B; margin-bottom: 0.6rem; font-family: monospace;">
        PLATFORM: WORLDVIEW-3 / PLEIADES • PAN-SHARPENED MULTISPECTRAL
    </div>
</div>
""")
            img_s = st.session_state.get("uploaded_image_a")
            name_s = st.session_state.get("image_a_name", "Satellite_Scene.tif")

            if img_s is None:
                f_s = st.file_uploader("Upload High-Resolution Satellite Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="dash_up_single")
                if f_s is not None:
                    try:
                        pil_s = Image.open(f_s)
                        st.session_state["uploaded_image_a"] = pil_s
                        st.session_state["image_a_name"] = f_s.name
                        st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(f_s.name, sensor_type="VHR Optical", img_size=pil_s.size)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error reading image: {e}")
            else:
                render_html(f"""
<div class="sq-hud-viewport">
    <div class="sq-hud-corner sq-hud-tl"></div>
    <div class="sq-hud-corner sq-hud-tr"></div>
    <div class="sq-hud-corner sq-hud-bl"></div>
    <div class="sq-hud-corner sq-hud-br"></div>
    <div class="sq-hud-overlay-tag">
        <span>● VHR SCENE</span>
        <span>{img_s.size[0]}×{img_s.size[1]} px</span>
        <span>{name_s}</span>
    </div>
</div>
""")
                st.image(img_s, caption=f"Scene • {img_s.size[0]}×{img_s.size[1]} px", use_container_width=True)
                if st.button("↺ Replace Satellite Scene", key="dash_rem_single", use_container_width=True):
                    st.session_state["uploaded_image_a"] = None
                    st.session_state["image_a_name"] = None
                    st.rerun()

        with c_samp_s:
            render_html("""
<div style="background: rgba(10, 15, 29, 0.8); padding: 1rem 1.15rem; border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.25); margin-bottom: 0.85rem;">
    <div style="font-size: 0.78rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.35rem; font-family: monospace; letter-spacing: 0.04em;">PRE-CALIBRATED BENCHMARK SCENES</div>
    <div style="font-size: 0.76rem; color: #94A3B8; line-height: 1.45;">Load verified satellite test scenes with one click:</div>
</div>
""")
            st.markdown('<div class="sq-benchmark-btn">', unsafe_allow_html=True)
            if st.button("🎯 LOAD FUEL STORAGE TANKS (0.3m GROUNDING)", key="dash_load_depot", use_container_width=True):
                sc = generate_grounding_scenario()
                st.session_state["uploaded_image_a"] = sc["image_a"]
                st.session_state["image_a_name"] = sc["image_a_name"]
                st.session_state["dashboard_instant_query_text"] = sc["default_query"]
                st.session_state["query_text"] = sc["default_query"]
                st.rerun()

            if st.button("🚢 LOAD MARITIME HARBOR (0.5m VQA)", key="dash_load_harbor", use_container_width=True):
                sc = generate_vqa_scenario()
                st.session_state["uploaded_image_a"] = sc["image_a"]
                st.session_state["image_a_name"] = sc["image_a_name"]
                st.session_state["dashboard_instant_query_text"] = sc["default_query"]
                st.session_state["query_text"] = sc["default_query"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        placeholder_text = "e.g., Where are the circular fuel storage tanks and active berths?"
        preset_prompts = [
            ("🎯", "OBJECT LOCALIZATION", "Where are the circular fuel storage tanks?"),
            ("🚢", "MARITIME VQA", "What vessels and active cranes are in the harbor?"),
            ("📐", "FACILITIES GROUNDING", "Locate and bound all industrial warehouses")
        ]

    # 3. Suggested Prompt Chips (Strictly Equal Fixed Height, High-Tech Cards)
    st.markdown('<div style="font-size: 0.74rem; color: #64748B; font-weight: 700; margin: 1.2rem 0 0.45rem 0; font-family: monospace; letter-spacing: 0.06em;">SUGGESTED GEOSPATIAL INTELLIGENCE INQUIRIES:</div>', unsafe_allow_html=True)
    st.markdown('<div class="sq-prompt-chips-wrapper">', unsafe_allow_html=True)
    p_cols = st.columns(len(preset_prompts))
    for idx, (p_icon, p_tag, p_text) in enumerate(preset_prompts):
        with p_cols[idx]:
            if st.button(f'{p_icon} [{p_tag}]\n"{p_text}"', key=f"dash_chip_{dash_mode}_{idx}", use_container_width=True):
                st.session_state["dashboard_instant_query_text"] = p_text
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # 4. Command Input & Launch Button
    query_val = st.session_state.get("dashboard_instant_query_text", "")
    st.markdown("<div style='margin-top: 0.6rem;'></div>", unsafe_allow_html=True)
    c_txt, c_btn = st.columns([3.5, 1.5])
    with c_txt:
        custom_q = st.text_input(
            label="Instant Query",
            value=query_val,
            placeholder=placeholder_text,
            key="dashboard_instant_query_input",
            label_visibility="collapsed"
        )
    with c_btn:
        st.markdown('<div class="sq-launch-btn">', unsafe_allow_html=True)
        if st.button("🚀 EXECUTE REASONING", type="primary", use_container_width=True, key="dashboard_launch_btn"):
            final_query = custom_q.strip() if custom_q.strip() else preset_prompts[0][2]

            # Ensure images are loaded: if user has not uploaded any, auto-attach the scenario for this modality
            if dash_mode == "compare":
                if st.session_state.get("uploaded_image_a") is None or st.session_state.get("uploaded_image_b") is None:
                    sc = generate_change_detection_scenario()
                    st.session_state["uploaded_image_a"] = sc["image_a"]
                    st.session_state["uploaded_image_b"] = sc["image_b"]
                    st.session_state["image_a_name"] = sc["image_a_name"]
                    st.session_state["image_b_name"] = sc["image_b_name"]
                st.session_state["analysis_mode"] = cfg.MODE_COMPARE

            elif dash_mode == "sar_optical":
                if st.session_state.get("uploaded_image_a") is None or st.session_state.get("uploaded_image_b") is None:
                    sc = generate_optical_sar_scenario()
                    st.session_state["uploaded_image_a"] = sc["image_a"]
                    st.session_state["uploaded_image_b"] = sc["image_b"]
                    st.session_state["image_a_name"] = sc["image_a_name"]
                    st.session_state["image_b_name"] = sc["image_b_name"]
                st.session_state["analysis_mode"] = cfg.MODE_OPTICAL_SAR

            else:  # single
                if st.session_state.get("uploaded_image_a") is None:
                    sc = generate_grounding_scenario()
                    st.session_state["uploaded_image_a"] = sc["image_a"]
                    st.session_state["image_a_name"] = sc["image_a_name"]
                st.session_state["analysis_mode"] = cfg.MODE_SINGLE

            st.session_state["query_text"] = final_query
            st.session_state["analysis_step"] = 3
            set_page("new_analysis")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def render_intel_and_constellation_section() -> None:
    """Render recent intelligence detections stream and constellation fleet status."""
    c_feed, c_fleet = st.columns([1.1, 1.1])

    with c_feed:
        feed_header = """
        <div style="margin-bottom: 0.8rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
        <h4 style="margin: 0; font-size: 1.05rem; color: #F8FAFC; font-weight: 700;">
        Live Geospatial Intelligence Alerts
        </h4>
        <span class="sq-badge sq-badge-cyan">4 RECENT EVENTS</span>
        </div>
        </div>
        """
        st.markdown(_h(feed_header), unsafe_allow_html=True)

        alerts = [
            {
                "time": "12m ago",
                "tag": "CRITICAL CHANGE",
                "tag_class": "sq-badge-rose",
                "title": "Industrial Expansion Detected",
                "desc": "5 new logistics facilities and 3.4 km arterial asphalt grid identified in Dubai AOI (+18.5 Ha).",
                "sensor": "Sentinel-2 MSI"
            },
            {
                "time": "34m ago",
                "tag": "RADAR ANOMALY",
                "tag_class": "sq-badge-purple",
                "title": "Severe Flood Inundation Mapped",
                "desc": "SAR microwave backscatter reveals -24.1 dB attenuation across 62.4 Ha of agricultural floodplains.",
                "sensor": "Sentinel-1 SAR C-Band"
            },
            {
                "time": "1h 05m ago",
                "tag": "ASSET AUDIT",
                "tag_class": "sq-badge-cyan",
                "title": "Petrochemical Depot Localized",
                "desc": "6 circular floating-roof tanks and 4 high-bay warehouses verified with 96% spatial precision.",
                "sensor": "WorldView-3 (0.3m)"
            },
            {
                "time": "2h 18m ago",
                "tag": "MARITIME VQA",
                "tag_class": "sq-badge-green",
                "title": "Container Terminal Operations",
                "desc": "Panamax vessel berthed along Quay 1; 4 gantry cranes active. Zero surface petrochemical sheen.",
                "sensor": "Pléiades Neo VHR"
            }
        ]

        for alt in alerts:
            alt_html = safe_html(f"""
<div style="background: rgba(10, 15, 29, 0.7); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.6rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
<span class="sq-badge {alt['tag_class']}">{alt['tag']}</span>
<span style="font-size: 0.72rem; color: #64748B; font-family: monospace;">{alt['time']} • {alt['sensor']}</span>
</div>
<div style="font-size: 0.9rem; font-weight: 600; color: #F8FAFC; margin-bottom: 0.2rem;">{alt['title']}</div>
<div style="font-size: 0.78rem; color: #94A3B8; line-height: 1.4;">{alt['desc']}</div>
</div>
""")
            st.markdown(_h(alt_html), unsafe_allow_html=True)

    with c_fleet:
        fleet_header = """
        <div style="margin-bottom: 0.8rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
        <h4 style="margin: 0; font-size: 1.05rem; color: #F8FAFC; font-weight: 700;">
        Satellite Constellation Fleet
        </h4>
        <span class="sq-badge sq-badge-green">ALL OPERATIONAL</span>
        </div>
        </div>
        """
        st.markdown(_h(fleet_header), unsafe_allow_html=True)

        fleet_data = [
            {"Constellation": "Sentinel-2A/B", "Orbit": "786 km SSO", "Sensor Payload": "Optical (13 Bands)", "GSD": "10m", "Health": "Nominal 🟢"},
            {"Constellation": "Sentinel-1A", "Orbit": "693 km Polar", "Sensor Payload": "C-SAR (VV+VH)", "GSD": "5m", "Health": "Nominal 🟢"},
            {"Constellation": "Landsat-9", "Orbit": "705 km SSO", "Sensor Payload": "VNIR + TIRS-2", "GSD": "15m", "Health": "Nominal 🟢"},
            {"Constellation": "WorldView-3", "Orbit": "617 km SSO", "Sensor Payload": "Super-spectral VHR", "GSD": "0.31m", "Health": "Nominal 🟢"},
            {"Constellation": "Pléiades Neo", "Orbit": "620 km SSO", "Sensor Payload": "Optical RGB+NIR", "GSD": "0.30m", "Health": "Nominal 🟢"}
        ]

        df_fleet = pd.DataFrame(fleet_data)
        st.dataframe(
            df_fleet,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Constellation": st.column_config.TextColumn("Constellation", width="medium"),
                "Orbit": st.column_config.TextColumn("Orbit", width="small"),
                "Sensor Payload": st.column_config.TextColumn("Sensor Payload", width="medium"),
                "GSD": st.column_config.TextColumn("GSD", width="small"),
                "Health": st.column_config.TextColumn("Health", width="small")
            }
        )
