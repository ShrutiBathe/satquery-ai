from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Image Upload Area and Step Indicator Component
Handles Single Image, Compare (A/B), and Optical + SAR uploaders with metadata inspection.
"""

import streamlit as st
from PIL import Image
import os
from datetime import date
from typing import Optional, Dict, Any

import config.settings as cfg
from utils.validators import validate_file_format, format_file_size
from utils.image_utils import generate_mock_geospatial_metadata
from services.sample_data import (
    generate_change_detection_scenario,
    generate_grounding_scenario,
    generate_optical_sar_scenario,
    generate_vqa_scenario
)


def render_step_indicator(current_step: int) -> None:
    """Render the horizontal 4-step workflow indicator."""
    steps = [
        (1, "DATA", "Upload imagery"),
        (2, "QUERY", "Natural language"),
        (3, "ANALYSIS", "Agentic routing"),
        (4, "INSIGHT", "Evidence & answer")
    ]

    html = '<div class="sq-step-container">'
    for idx, (num, name, desc) in enumerate(steps):
        status_class = ""
        num_display = f"0{num}"
        if num < current_step:
            status_class = "completed"
            num_display = "✓"
        elif num == current_step:
            status_class = "active"

        html += f"""
        <div class="sq-step-item {status_class}">
            <div class="sq-step-num">{num_display}</div>
            <div>
                <div style="line-height: 1.1;">{num_display} {name}</div>
                <div style="font-size: 0.68rem; color: #64748B; font-weight: normal; margin-top: 2px;">{desc}</div>
            </div>
        </div>
        """
        if idx < len(steps) - 1:
            html += '<div class="sq-step-arrow">→</div>'

    html += '</div>'
    render_html(html)


def render_mode_selector() -> str:
    """Render the Analysis Mode Selector."""
    st.markdown('<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.6rem; font-family: monospace;">SELECT SATELLITE SENSOR WORKFLOW:</div>', unsafe_allow_html=True)

    current_mode = st.session_state.get("analysis_mode", cfg.MODE_AUTO)

    st.markdown('<div class="sq-modality-wrapper">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    mode_cols = [
        (col1, cfg.MODE_COMPARE, "⏱️ BI-TEMPORAL IMAGES\nDual-Epoch Urban & Surface (2024-2026)"),
        (col2, cfg.MODE_OPTICAL_SAR, "📡 OPTICAL + SAR FUSION\nMicrowave Radar & Flood Inundation"),
        (col3, cfg.MODE_SINGLE, "🛰️ SINGLE VHR SCENE\n0.3m-0.5m GSD Grounding & VQA"),
        (col4, cfg.MODE_AUTO, "⚡ AUTONOMOUS ROUTER\nDynamic Heuristic Task Selection")
    ]

    for col, m_id, label in mode_cols:
        with col:
            is_sel = current_mode == m_id
            btn_type = "primary" if is_sel else "secondary"
            if st.button(label, key=f"mode_btn_{m_id}", type=btn_type, use_container_width=True):
                st.session_state["analysis_mode"] = m_id
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Mode contextual helper banner (Aerospace Mission HUD)
    if current_mode == cfg.MODE_COMPARE:
        render_html("""
<div class="sq-mission-briefing">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.05rem;">⏱️</span>
            <span style="font-weight: 700; color: #00F0FF; letter-spacing: 0.04em; font-family: monospace; font-size: 0.82rem;">MISSION DIRECTIVE: BI-TEMPORAL CHANGE DETECTION</span>
            <span class="sq-badge sq-badge-cyan">CO-REGISTERED EO</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.45rem;">
            <span class="sq-telemetry-tag">RESOLUTION: 10m GSD</span>
            <span class="sq-telemetry-tag">DELTA: 2024 → 2026</span>
        </div>
    </div>
    <div style="color: #94A3B8; font-size: 0.80rem; margin-top: 5px; line-height: 1.45;">
        Upload two aligned satellite scenes acquired across different temporal dates (Baseline vs Post-Event) to detect structural growth, infrastructure changes, and surface alterations.
    </div>
</div>
""")
    elif current_mode == cfg.MODE_OPTICAL_SAR:
        render_html("""
<div class="sq-mission-briefing sq-mission-briefing-purple">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.05rem;">📡</span>
            <span style="font-weight: 700; color: #A855F7; letter-spacing: 0.04em; font-family: monospace; font-size: 0.82rem;">MISSION DIRECTIVE: MULTIMODAL OPTICAL + SAR RADAR FUSION</span>
            <span class="sq-badge sq-badge-purple">SENSOR COMPLEMENTARITY</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.45rem;">
            <span class="sq-telemetry-tag">RADAR: C-SAR (VV+VH)</span>
            <span class="sq-telemetry-tag">OPTICAL: RGB (10m)</span>
        </div>
    </div>
    <div style="color: #94A3B8; font-size: 0.80rem; margin-top: 5px; line-height: 1.45;">
        Upload complementary optical reflectance imagery and cloud-penetrating Synthetic Aperture Radar (SAR C-Band) to delineate water bodies and flood extents in all weather conditions.
    </div>
</div>
""")
    elif current_mode == cfg.MODE_SINGLE:
        render_html("""
<div class="sq-mission-briefing">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.05rem;">🛰️</span>
            <span style="font-weight: 700; color: #00F0FF; letter-spacing: 0.04em; font-family: monospace; font-size: 0.82rem;">MISSION DIRECTIVE: SINGLE SCENE VQA & GROUNDING</span>
            <span class="sq-badge sq-badge-cyan">VHR SPATIAL REASONING</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.45rem;">
            <span class="sq-telemetry-tag">GSD: 0.3m – 0.5m</span>
            <span class="sq-telemetry-tag">BBOX: 2D GROUNDING</span>
        </div>
    </div>
    <div style="color: #94A3B8; font-size: 0.80rem; margin-top: 5px; line-height: 1.45;">
        Upload a high-resolution satellite scene for visual grounding of requested objects with bounding boxes or open-ended visual question answering.
    </div>
</div>
""")
    else:
        render_html("""
<div class="sq-mission-briefing">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
            <span style="font-size: 1.05rem;">⚡</span>
            <span style="font-weight: 700; color: #00F0FF; letter-spacing: 0.04em; font-family: monospace; font-size: 0.82rem;">AUTONOMOUS SENSOR ROUTING ENGINE</span>
            <span class="sq-badge sq-badge-green">AI HEURISTICS</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.45rem;">
            <span class="sq-telemetry-tag">DYNAMIC REASONING</span>
        </div>
    </div>
    <div style="color: #94A3B8; font-size: 0.80rem; margin-top: 5px; line-height: 1.45;">
        SatQuery automatically determines the optimal specialist workflow (Bi-temporal, Optical+SAR, Grounding, or VQA) based on your uploaded imagery and query prompt.
    </div>
</div>
""")

    return current_mode


def _render_metadata_drawer(metadata: Dict[str, Any], key_suffix: str) -> None:
    """Render expandable image metadata drawer."""
    with st.expander("🔍 View Image Geospatial Metadata", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**CRS:** `{metadata.get('crs', 'EPSG:4326')}`")
            st.markdown(f"**Projection:** `{metadata.get('projection', 'UTM')}`")
            st.markdown(f"**Resolution:** `{metadata.get('ground_sample_distance', '0.5m/px')}`")
            st.markdown(f"**Dimensions:** `{metadata.get('dimensions', '1024×1024 px')}`")
        with c2:
            st.markdown(f"**Sensor Platform:** `{metadata.get('sensor', 'Multispectral')}`")
            st.markdown(f"**Spectral Channels:** `{metadata.get('spectral_bands', 'RGB')}`")
            st.markdown(f"**Cloud Cover:** `{metadata.get('cloud_cover', '< 1%')}`")
            st.markdown(f"**Provider:** `{metadata.get('data_provider', 'ESA Copernicus')}`")


def render_upload_area() -> None:
    """Render the upload dropzones according to active analysis mode."""
    mode = render_mode_selector()

    if mode == cfg.MODE_COMPARE:
        _render_compare_uploader()
    elif mode == cfg.MODE_OPTICAL_SAR:
        _render_optical_sar_uploader()
    elif mode == cfg.MODE_SINGLE:
        _render_single_uploader()
    else:  # cfg.MODE_AUTO
        _render_auto_uploader()


def _render_auto_uploader() -> None:
    """Flexible dual uploader for Auto Detect mode allowing 1 or 2 images."""
    c_a, c_b = st.columns(2)
    img_a = st.session_state.get("uploaded_image_a")
    img_b = st.session_state.get("uploaded_image_b")
    name_a = st.session_state.get("image_a_name", "Image_A.tif")
    name_b = st.session_state.get("image_b_name", "Image_B.tif")

    with c_a:
        st.markdown("**🛰️ PRIMARY SATELLITE SCENE (Image A)**")
        st.caption("Baseline / Optical Scene")
        if img_a is None:
            f_a = st.file_uploader("Upload Image A", type=["tif", "tiff", "png", "jpg", "jpeg"], key="up_auto_a")
            if f_a is not None:
                pil_a = Image.open(f_a)
                st.session_state["uploaded_image_a"] = pil_a
                st.session_state["image_a_name"] = f_a.name
                st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(f_a.name, img_size=pil_a.size)
                st.rerun()
        else:
            st.image(img_a, caption=f"Image A: {name_a}", use_container_width=True)
            if st.button("Remove Image A", key="rem_auto_a", use_container_width=True):
                st.session_state["uploaded_image_a"] = None
                st.session_state["image_a_name"] = None
                st.rerun()

    with c_b:
        st.markdown("**📡 SECONDARY SCENE (Image B - Optional)**")
        st.caption("Post-Event / SAR Microwave Scene")
        if img_b is None:
            f_b = st.file_uploader("Upload Image B (Optional)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="up_auto_b")
            if f_b is not None:
                pil_b = Image.open(f_b)
                st.session_state["uploaded_image_b"] = pil_b
                st.session_state["image_b_name"] = f_b.name
                st.session_state["image_metadata_b"] = generate_mock_geospatial_metadata(f_b.name, sensor_type="SAR / Post-Event", img_size=pil_b.size)
                st.rerun()
        else:
            st.image(img_b, caption=f"Image B: {name_b}", use_container_width=True)
            if st.button("Remove Image B", key="rem_auto_b", use_container_width=True):
                st.session_state["uploaded_image_b"] = None
                st.session_state["image_b_name"] = None
                st.rerun()

    # Pre-bundled scenario loaders
    st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⏱️ Load 2024-2026 Change Pair", key="auto_load_change", use_container_width=True):
            sc = generate_change_detection_scenario()
            st.session_state["uploaded_image_a"] = sc["image_a"]
            st.session_state["uploaded_image_b"] = sc["image_b"]
            st.session_state["image_a_name"] = sc["image_a_name"]
            st.session_state["image_b_name"] = sc["image_b_name"]
            st.session_state["query_text"] = sc["default_query"]
            st.session_state["analysis_mode"] = cfg.MODE_COMPARE
            st.rerun()
    with c2:
        if st.button("📡 Load Optical + SAR Pair", key="auto_load_sar", use_container_width=True):
            sc = generate_optical_sar_scenario()
            st.session_state["uploaded_image_a"] = sc["image_a"]
            st.session_state["uploaded_image_b"] = sc["image_b"]
            st.session_state["image_a_name"] = sc["image_a_name"]
            st.session_state["image_b_name"] = sc["image_b_name"]
            st.session_state["query_text"] = sc["default_query"]
            st.session_state["analysis_mode"] = cfg.MODE_OPTICAL_SAR
            st.rerun()
    with c3:
        if st.button("🛰️ Load Grounding Depot Scene", key="auto_load_grounding", use_container_width=True):
            sc = generate_grounding_scenario()
            st.session_state["uploaded_image_a"] = sc["image_a"]
            st.session_state["uploaded_image_b"] = None
            st.session_state["image_a_name"] = sc["image_a_name"]
            st.session_state["image_b_name"] = None
            st.session_state["query_text"] = sc["default_query"]
            st.session_state["analysis_mode"] = cfg.MODE_SINGLE
            st.rerun()


def _render_single_uploader() -> None:
    """Uploader for Single High-Resolution Optical Scene."""
    img_a = st.session_state.get("uploaded_image_a")
    name_a = st.session_state.get("image_a_name", "satellite_image.tif")

    col_main, col_sample = st.columns([1.3, 1])

    with col_main:
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
        if img_a is None:
            uploaded_file = st.file_uploader(
                "Upload High-Resolution Satellite Scene (GeoTIFF / PNG / JPG)",
                type=["tif", "tiff", "png", "jpg", "jpeg"],
                key="uploader_single",
                help="Accepts GeoTIFF, TIFF, PNG, JPG satellite scenes up to 50MB."
            )
            if uploaded_file is not None:
                try:
                    pil_img = Image.open(uploaded_file)
                    st.session_state["uploaded_image_a"] = pil_img
                    st.session_state["image_a_name"] = uploaded_file.name
                    st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(
                        uploaded_file.name,
                        img_size=pil_img.size
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not load image: {str(e)}")
        else:
            meta = st.session_state.get("image_metadata_a") or generate_mock_geospatial_metadata(name_a, img_size=img_a.size)
            st.session_state["image_metadata_a"] = meta

            render_html(f"""
<div class="sq-hud-viewport">
    <div class="sq-hud-corner sq-hud-tl"></div>
    <div class="sq-hud-corner sq-hud-tr"></div>
    <div class="sq-hud-corner sq-hud-bl"></div>
    <div class="sq-hud-corner sq-hud-br"></div>
    <div class="sq-hud-overlay-tag">
        <span>● VHR SCENE</span>
        <span>{img_a.size[0]}×{img_a.size[1]} px</span>
        <span>{name_a}</span>
    </div>
</div>
""")
            st.image(img_a, caption=f"VHR Scene • {img_a.size[0]}×{img_a.size[1]} px", use_container_width=True)
            if st.button("↺ Replace Satellite Scene", key="btn_remove_single", use_container_width=True):
                st.session_state["uploaded_image_a"] = None
                st.session_state["image_a_name"] = None
                st.session_state["image_metadata_a"] = None
                st.rerun()

            _render_metadata_drawer(meta, "single")

    with col_sample:
        render_html("""
<div style="background: rgba(10, 15, 29, 0.8); padding: 1rem 1.15rem; border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.25); margin-bottom: 0.85rem;">
    <div style="font-size: 0.78rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.35rem; font-family: monospace; letter-spacing: 0.04em;">PRE-CALIBRATED BENCHMARK SCENES</div>
    <div style="font-size: 0.76rem; color: #94A3B8; line-height: 1.45;">Load verified satellite test scenes with one click:</div>
</div>
""")
        st.markdown('<div class="sq-benchmark-btn">', unsafe_allow_html=True)
        if st.button("🎯 LOAD FUEL STORAGE TANKS (0.3m GROUNDING)", key="load_sample_grounding", use_container_width=True):
            sc = generate_grounding_scenario()
            st.session_state["uploaded_image_a"] = sc["image_a"]
            st.session_state["image_a_name"] = sc["image_a_name"]
            st.session_state["query_text"] = sc["default_query"]
            st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(sc["image_a_name"], sensor_type=sc["sensor_a"], img_size=sc["image_a"].size)
            st.rerun()

        if st.button("🚢 LOAD MARITIME HARBOR (0.5m VQA)", key="load_sample_vqa", use_container_width=True):
            sc = generate_vqa_scenario()
            st.session_state["uploaded_image_a"] = sc["image_a"]
            st.session_state["image_a_name"] = sc["image_a_name"]
            st.session_state["query_text"] = sc["default_query"]
            st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(sc["image_a_name"], sensor_type=sc["sensor_a"], img_size=sc["image_a"].size)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def _render_compare_uploader() -> None:
    """Bi-temporal side-by-side uploader with date pickers and image swap."""
    c_left, c_right = st.columns(2)

    with c_left:
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
        d_a = st.date_input("Acquisition Date A (Epoch T0)", value=st.session_state.get("image_a_date", date(2024, 6, 15)), key="date_a")
        st.session_state["image_a_date"] = d_a

        img_a = st.session_state.get("uploaded_image_a")
        name_a = st.session_state.get("image_a_name", "Baseline_Scene.tif")

        if img_a is None:
            f_a = st.file_uploader("Upload Baseline Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="up_compare_a")
            if f_a is not None:
                st.session_state["uploaded_image_a"] = Image.open(f_a)
                st.session_state["image_a_name"] = f_a.name
                st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(f_a.name)
                st.rerun()
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
            if st.button("↺ Replace Baseline Raster", key="rem_comp_a", use_container_width=True):
                st.session_state["uploaded_image_a"] = None
                st.session_state["image_a_name"] = None
                st.rerun()

    with c_right:
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
        d_b = st.date_input("Acquisition Date B (Epoch T1)", value=st.session_state.get("image_b_date", date(2026, 3, 20)), key="date_b")
        st.session_state["image_b_date"] = d_b

        img_b = st.session_state.get("uploaded_image_b")
        name_b = st.session_state.get("image_b_name", "PostEvent_Scene.tif")

        if img_b is None:
            f_b = st.file_uploader("Upload Post-Event Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="up_compare_b")
            if f_b is not None:
                st.session_state["uploaded_image_b"] = Image.open(f_b)
                st.session_state["image_b_name"] = f_b.name
                st.session_state["image_metadata_b"] = generate_mock_geospatial_metadata(f_b.name)
                st.rerun()
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
            if st.button("↺ Replace Target Raster", key="rem_comp_b", use_container_width=True):
                st.session_state["uploaded_image_b"] = None
                st.session_state["image_b_name"] = None
                st.rerun()

    # Toolbar
    st.markdown('<div class="sq-bay-toolbar">', unsafe_allow_html=True)
    c_swp, c_load, c_clr = st.columns([1, 2.2, 1])
    with c_swp:
        if st.button("⇄ Swap Epochs (T0 ⇄ T1)", key="btn_swap_images", use_container_width=True):
            st.session_state["uploaded_image_a"], st.session_state["uploaded_image_b"] = st.session_state.get("uploaded_image_b"), st.session_state.get("uploaded_image_a")
            st.session_state["image_a_name"], st.session_state["image_b_name"] = st.session_state.get("image_b_name"), st.session_state.get("image_a_name")
            st.session_state["image_a_date"], st.session_state["image_b_date"] = st.session_state.get("image_b_date"), st.session_state.get("image_a_date")
            st.rerun()
    with c_load:
        st.markdown('<div class="sq-benchmark-btn">', unsafe_allow_html=True)
        if st.button("⚡ LOAD BENCHMARK 2024 vs 2026 PAIR (1-CLICK DEMO)", key="btn_load_compare_demo", use_container_width=True):
            sc = generate_change_detection_scenario()
            st.session_state["uploaded_image_a"] = sc["image_a"]
            st.session_state["uploaded_image_b"] = sc["image_b"]
            st.session_state["image_a_name"] = sc["image_a_name"]
            st.session_state["image_b_name"] = sc["image_b_name"]
            st.session_state["image_a_date"] = sc["image_a_date"]
            st.session_state["image_b_date"] = sc["image_b_date"]
            st.session_state["query_text"] = sc["default_query"]
            st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(sc["image_a_name"], sensor_type=sc["sensor_a"])
            st.session_state["image_metadata_b"] = generate_mock_geospatial_metadata(sc["image_b_name"], sensor_type=sc["sensor_b"])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c_clr:
        if st.button("🗑️ Clear Bays", key="btn_clear_comp_bays", use_container_width=True):
            st.session_state["uploaded_image_a"] = None
            st.session_state["uploaded_image_b"] = None
            st.session_state["image_a_name"] = None
            st.session_state["image_b_name"] = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def _render_optical_sar_uploader() -> None:
    """Multimodal Optical + SAR dual uploader."""
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
            f_opt = st.file_uploader("Upload Optical Satellite Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="up_opt")
            if f_opt is not None:
                st.session_state["uploaded_image_a"] = Image.open(f_opt)
                st.session_state["image_a_name"] = f_opt.name
                st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(f_opt.name, sensor_type="Optical (Sentinel-2)")
                st.rerun()
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
            st.image(img_opt, caption=f"Optical RGB: {name_opt}", use_container_width=True)
            if st.button("↺ Replace Optical Scene", key="rem_opt", use_container_width=True):
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
            f_sar = st.file_uploader("Upload SAR Microwave Scene (GeoTIFF / PNG / JPG)", type=["tif", "tiff", "png", "jpg", "jpeg"], key="up_sar")
            if f_sar is not None:
                st.session_state["uploaded_image_b"] = Image.open(f_sar)
                st.session_state["image_b_name"] = f_sar.name
                st.session_state["image_metadata_b"] = generate_mock_geospatial_metadata(f_sar.name, sensor_type="SAR (Sentinel-1 C-Band)")
                st.rerun()
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
            st.image(img_sar, caption=f"SAR Radar Backscatter: {name_sar}", use_container_width=True)
            if st.button("↺ Replace SAR Scene", key="rem_sar", use_container_width=True):
                st.session_state["uploaded_image_b"] = None
                st.session_state["image_b_name"] = None
                st.rerun()

    # Toolbar
    st.markdown('<div class="sq-bay-toolbar">', unsafe_allow_html=True)
    c_load_sar, c_clr_sar = st.columns([2.4, 1])
    with c_load_sar:
        st.markdown('<div class="sq-benchmark-btn">', unsafe_allow_html=True)
        if st.button("⚡ LOAD DEMO FLOOD INUNDATION (OPTICAL + SAR PAIR)", key="btn_load_sar_demo", use_container_width=True):
            sc = generate_optical_sar_scenario()
            st.session_state["uploaded_image_a"] = sc["image_a"]
            st.session_state["uploaded_image_b"] = sc["image_b"]
            st.session_state["image_a_name"] = sc["image_a_name"]
            st.session_state["image_b_name"] = sc["image_b_name"]
            st.session_state["query_text"] = sc["default_query"]
            st.session_state["image_metadata_a"] = generate_mock_geospatial_metadata(sc["image_a_name"], sensor_type=sc["sensor_a"])
            st.session_state["image_metadata_b"] = generate_mock_geospatial_metadata(sc["image_b_name"], sensor_type=sc["sensor_b"])
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c_clr_sar:
        if st.button("🗑️ Clear Bays", key="btn_clear_sar_bays", use_container_width=True):
            st.session_state["uploaded_image_a"] = None
            st.session_state["uploaded_image_b"] = None
            st.session_state["image_a_name"] = None
            st.session_state["image_b_name"] = None
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
