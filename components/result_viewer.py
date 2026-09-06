from utils.ui_utils import safe_html, render_html
"""
SatQuery AI - Interactive Visual Result Viewer Component
Renders task-tailored multi-tab evidence imagery (Originals, Bounding Boxes, Segmentation Masks, Change Maps).
"""

import streamlit as st
from PIL import Image
from typing import Dict, Any

import config.settings as cfg
from utils.image_utils import image_to_bytes


def render_visual_result_viewer(evidence: Dict[str, Any], task_id: str) -> None:
    """Render interactive tabs for visual evidence according to detected workflow."""
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
    bboxes_img = evidence.get("annotated_bboxes")
    seg_img = evidence.get("seg_overlay")

    tab1, tab2, tab3 = st.tabs([
        "🛰️ Original Scene",
        "🎯 Grounded Bounding Boxes",
        "📐 Segmentation Contours"
    ])

    with tab1:
        if img_a:
            st.image(img_a, caption="Raw Satellite Scene", use_container_width=True)
            _render_download_btn(img_a, "SatQuery_Scene_Raw.png")

    with tab2:
        if bboxes_img:
            st.image(bboxes_img, caption="Spatial Bounding Boxes with Class Labels and Confidence", use_container_width=True)
            _render_download_btn(bboxes_img, "SatQuery_Grounded_BBoxes.png")

    with tab3:
        if seg_img:
            st.image(seg_img, caption="Sub-pixel Segmentation Polygons", use_container_width=True)
            _render_download_btn(seg_img, "SatQuery_Segmentation_Mask.png")


def _render_optical_sar_tabs(evidence: Dict[str, Any]) -> None:
    """Tabs for Optical + SAR multimodal fusion."""
    img_opt = evidence.get("image_a")
    img_sar = evidence.get("image_b")
    fused = evidence.get("fused_overlay")

    tab1, tab2, tab3 = st.tabs([
        "☀️ Optical (Multispectral)",
        "📡 SAR Radar (C-Band Backscatter)",
        "⚡ Multimodal Fused Inundation"
    ])

    with tab1:
        if img_opt:
            st.image(img_opt, caption="Optical RGB (Cloud & Haze Obscured)", use_container_width=True)
            _render_download_btn(img_opt, "SatQuery_Optical_RGB.png")

    with tab2:
        if img_sar:
            st.image(img_sar, caption="Sentinel-1 SAR Radar (Cloud Penetrating Microwave Backscatter)", use_container_width=True)
            _render_download_btn(img_sar, "SatQuery_SAR_Backscatter.png")

    with tab3:
        if fused:
            st.image(fused, caption="Fused Multimodal Surface Water & Flood Extent Mask", use_container_width=True)
            _render_download_btn(fused, "SatQuery_Fused_SAR_Optical.png")


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
