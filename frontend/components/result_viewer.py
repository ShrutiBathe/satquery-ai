from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Interactive Visual Result Viewer Component
Renders task-tailored multi-tab evidence imagery (Originals, Bounding Boxes, Segmentation Masks, Change Maps).
"""

import streamlit as st
from PIL import Image
from typing import Dict, Any

import config.settings as cfg
from utils.image_utils import image_to_bytes, normalize_float_image


def render_visual_result_viewer(evidence: Dict[str, Any], task_id: str) -> None:
    """Render interactive tabs for visual evidence according to detected workflow."""
    
    # Pre-process evidence dictionary: convert string paths to PIL Images
    for key, val in list(evidence.items()):
        if isinstance(val, str):
            try:
                img = Image.open(val)
                evidence[key] = normalize_float_image(img)
            except Exception:
                pass

    render_html("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
    <h3 style="font-size: 1.15rem; margin: 0; font-weight: 700; color: #F8FAFC;">
        Visual Remote Sensing Evidence
    </h3>
    <span class="sq-badge sq-badge-cyan">INTERACTIVE MULTI-LAYER VIEWER</span>
</div>
""")

    ev_type = evidence.get("type", task_id)

    if ev_type == "change_detection" or task_id == cfg.WORKFLOW_CHANGE:
        _render_change_detection_tabs(evidence)
    elif ev_type == "grounding" or task_id == cfg.WORKFLOW_GROUNDING:
        _render_grounding_tabs(evidence)
    elif ev_type == "optical_sar" or task_id == cfg.WORKFLOW_OPTICAL_SAR:
        _render_optical_sar_tabs(evidence)
    else:  # VQA or general
        _render_vqa_tabs(evidence)


def _render_change_detection_tabs(evidence: Dict[str, Any]) -> None:
    """Tabs for Bi-temporal Change Detection."""
    img_a = evidence.get("image_a")
    img_b = evidence.get("image_b")
    heatmap = evidence.get("heatmap")
    overlay = evidence.get("overlay")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Baseline (Date A)",
        "📅 Post-Event (Date B)",
        "🔥 Difference Heatmap",
        "🎯 Change Overlay"
    ])

    with tab1:
        if img_a:
            st.image(img_a, caption="Baseline Imagery (Pre-Event)", use_container_width=True)
            _render_download_btn(img_a, "SatQuery_Baseline_A.png")

    with tab2:
        if img_b:
            st.image(img_b, caption="Post-Event Imagery (Date B)", use_container_width=True)
            _render_download_btn(img_b, "SatQuery_PostEvent_B.png")

    with tab3:
        if heatmap:
            st.image(heatmap, caption="Continuous Differential Radiometric Heatmap", use_container_width=True)
            _render_download_btn(heatmap, "SatQuery_Change_Heatmap.png")

    with tab4:
        if overlay:
            st.image(overlay, caption="High-Confidence Surface Change Composite Mask", use_container_width=True)
            _render_download_btn(overlay, "SatQuery_Change_Overlay.png")


def _render_grounding_tabs(evidence: Dict[str, Any]) -> None:
    """Tabs for Visual Grounding & Localization."""
    img_a = evidence.get("image_a")
    bboxes_img = evidence.get("annotated_bboxes") or evidence.get("grounding_visualization")
    seg_img = evidence.get("seg_overlay")

    tabs_to_render = []
    if img_a: tabs_to_render.append(("🛰️ Original Scene", img_a, "Raw Satellite Scene", "SatQuery_Scene_Raw.png"))
    if bboxes_img: tabs_to_render.append(("🎯 Grounded Bounding Boxes", bboxes_img, "Spatial Bounding Boxes with Class Labels", "SatQuery_Grounded_BBoxes.png"))
    if seg_img: tabs_to_render.append(("📐 Segmentation Contours", seg_img, "Sub-pixel Segmentation Polygons", "SatQuery_Segmentation_Mask.png"))

    if not tabs_to_render:
        st.info("No visual evidence provided for Visual Grounding.")
        return

    created_tabs = st.tabs([t[0] for t in tabs_to_render])

    for idx, tab in enumerate(created_tabs):
        with tab:
            _, img, caption, filename = tabs_to_render[idx]
            st.image(img, caption=caption, use_container_width=True)
            _render_download_btn(img, filename)


def _render_optical_sar_tabs(evidence: Dict[str, Any]) -> None:
    """Tabs for Optical + SAR multimodal fusion."""
    img_opt = evidence.get("image_a")
    img_sar = evidence.get("image_b")
    fused = evidence.get("fused_overlay")
    
    tabs_to_render = []
    if img_opt: tabs_to_render.append(("☀️ Optical (Multispectral)", img_opt, "Optical RGB (Cloud & Haze Obscured)", "SatQuery_Optical_RGB.png"))
    if img_sar: tabs_to_render.append(("📡 SAR Radar (C-Band Backscatter)", img_sar, "Sentinel-1 SAR Radar", "SatQuery_SAR_Backscatter.png"))
    if fused: tabs_to_render.append(("⚡ Multimodal Fused Inundation", fused, "Fused Multimodal Mask", "SatQuery_Fused_SAR_Optical.png"))
    
    if not tabs_to_render:
        st.info("No visual evidence provided for Optical SAR.")
        return
        
    created_tabs = st.tabs([t[0] for t in tabs_to_render])
    
    for idx, tab in enumerate(created_tabs):
        with tab:
            _, img, caption, filename = tabs_to_render[idx]
            st.image(img, caption=caption, use_container_width=True)
            _render_download_btn(img, filename)


def _render_vqa_tabs(evidence: Dict[str, Any]) -> None:
    """Tabs for Visual Question Answering."""
    img = evidence.get("image_a")
    att = evidence.get("attention_overlay")

    tab1, tab2 = st.tabs([
        "🛰️ Target Satellite Scene",
        "👁️ Cross-Attention Saliency"
    ])

    with tab1:
        if img:
            st.image(img, caption="Analyzed Satellite Scene", use_container_width=True)
            _render_download_btn(img, "SatQuery_Analyzed_Scene.png")

    with tab2:
        if att:
            st.image(att, caption="Vision-Language Attention Saliency Layer", use_container_width=True)
            _render_download_btn(att, "SatQuery_Attention_Map.png")


def _render_download_btn(image: Image.Image, filename: str) -> None:
    """Render image download button."""
    try:
        raw_bytes = image_to_bytes(image)
        st.download_button(
            label="💾 Download Evidence Image",
            data=raw_bytes,
            file_name=filename,
            mime="image/png",
            use_container_width=True
        )
    except Exception:
        pass
