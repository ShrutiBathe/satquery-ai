"""
SatQuery AI - Configuration & Constants
Problem Statement ID: SIH26167
Interactive AI Assistant for Multimodal Remote-Sensing Image Analysis
"""

import os
from pathlib import Path

# Application Metadata
APP_NAME = "SatQuery AI"
APP_SUBTITLE = "Interactive AI Assistant for Multimodal Remote-Sensing Image Analysis"
TAGLINE = "Ask your satellite data anything."
PROBLEM_STATEMENT_ID = "SIH26167"
APP_VERSION = "1.0.0-Beta"
ORGANIZATION = "Smart India Hackathon 2026"

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
STYLES_DIR = BASE_DIR / "styles"

# Default API Configuration
DEFAULT_BACKEND_URL = os.getenv("SATQUERY_BACKEND_URL", "http://localhost:8000")
API_TIMEOUT_SECONDS = 60

# Analysis Modes
MODE_AUTO = "auto_detect"
MODE_SINGLE = "single_image"
MODE_COMPARE = "compare_images"
MODE_OPTICAL_SAR = "optical_sar"

ANALYSIS_MODES = [
    {
        "id": MODE_AUTO,
        "name": "Auto Detect",
        "badge": "Agentic AI",
        "description": "SatQuery autonomously determines the specialist workflow based on your natural language question.",
        "icon": "⚡"
    },
    {
        "id": MODE_SINGLE,
        "name": "Single Image",
        "badge": "VQA / Grounding",
        "description": "Examine a single satellite scene for object detection, scene classification, or feature counting.",
        "icon": "🛰️"
    },
    {
        "id": MODE_COMPARE,
        "name": "Compare Images",
        "badge": "Change Detection",
        "description": "Temporal pair analysis across two dates to identify infrastructure, environmental, or land-cover changes.",
        "icon": "⏱️"
    },
    {
        "id": MODE_OPTICAL_SAR,
        "name": "Optical + SAR",
        "badge": "Multimodal Fusion",
        "description": "Fuse multispectral optical imagery with weather-invariant Synthetic Aperture Radar backscatter.",
        "icon": "📡"
    }
]

# Specialist Workflows
WORKFLOW_VQA = "vqa"
WORKFLOW_GROUNDING = "visual_grounding"
WORKFLOW_CHANGE = "change_detection"
WORKFLOW_OPTICAL_SAR = "optical_sar_fusion"

SPECIALIST_WORKFLOWS = {
    WORKFLOW_VQA: {
        "title": "Visual Question Answering",
        "tag": "VQA Engine",
        "icon": "❓",
        "color": "#38BDF8",
        "description": "Ask questions about objects, scenes, environmental status, and content in satellite imagery.",
        "example_query": "What is the dominant land cover and are there industrial facilities present?",
        "suggested_queries": [
            "What objects are visible in this scene?",
            "Is there any active construction visible?",
            "What is the condition of the agricultural fields?",
            "Are there ships docked at the harbor?"
        ]
    },
    WORKFLOW_GROUNDING: {
        "title": "Visual Grounding",
        "tag": "Spatial Localization",
        "icon": "🎯",
        "color": "#00F0FF",
        "description": "Locate requested objects, structures, or ecological regions directly with spatial bounding boxes and masks.",
        "example_query": "Where are the buildings and solar farm arrays?",
        "suggested_queries": [
            "Where are the buildings?",
            "Locate all storage tanks in the industrial area",
            "Highlight the runway and aircraft",
            "Detect water reservoirs and ponds"
        ]
    },
    WORKFLOW_CHANGE: {
        "title": "Change Detection",
        "tag": "Bi-Temporal Siamese",
        "icon": "🔄",
        "color": "#F43F5E",
        "description": "Compare imagery captured across different dates to quantify, highlight, and explain visible surface changes.",
        "example_query": "What changed between 2024 and 2026?",
        "suggested_queries": [
            "What changed between these two dates?",
            "Highlight newly constructed structures",
            "Detect areas with vegetation clearing",
            "Identify expanded urban boundaries"
        ]
    },
    WORKFLOW_OPTICAL_SAR: {
        "title": "Multimodal Optical + SAR",
        "tag": "Radar Fusion",
        "icon": "📡",
        "color": "#A855F7",
        "description": "Combine complementary information from multispectral optical reflectance and radar backscatter for cloud-penetrating analysis.",
        "example_query": "Compare this region using both optical and SAR sensors to map flood extents.",
        "suggested_queries": [
            "Map flood inundation through cloud cover",
            "Compare optical vs SAR backscatter patterns",
            "Detect metallic structures using radar response",
            "Evaluate soil moisture and water pooling"
        ]
    }
}

# Pipeline Execution Stages
PIPELINE_STAGES = [
    {
        "id": "query_received",
        "name": "Query Received",
        "desc": "Natural language query parsed and session context tokenized."
    },
    {
        "id": "query_understanding",
        "name": "Query Understanding",
        "desc": "Intent extraction, temporal cues identification, and semantic target tagging."
    },
    {
        "id": "input_validation",
        "name": "Input Validation",
        "desc": "Spatial alignment, band verification, resolution compatibility, and coordinate check."
    },
    {
        "id": "agentic_routing",
        "name": "Agentic Routing",
        "desc": "Autonomous selection of specialist model pipeline based on query intent & modality."
    },
    {
        "id": "specialist_analysis",
        "name": "Specialist Analysis",
        "desc": "Deep neural tensor evaluation across optical/SAR spatial layers."
    },
    {
        "id": "evidence_generation",
        "name": "Evidence Generation",
        "desc": "Spatial grounding mask calculation, bounding boxes projection, and change heatmap synthesis."
    },
    {
        "id": "final_response",
        "name": "Final Response",
        "desc": "Formulating natural language synthesis grounded in visual evidence."
    }
]

# Supported File Formats
SUPPORTED_EXTENSIONS = [".tif", ".tiff", ".geotiff", ".png", ".jpg", ".jpeg"]
MAX_UPLOAD_SIZE_MB = 50

# UI Theme Colors (Dark Geospatial Slate)
COLORS = {
    "bg_dark": "#060913",
    "bg_card": "rgba(13, 21, 39, 0.75)",
    "bg_card_hover": "rgba(18, 30, 56, 0.85)",
    "border_subtle": "rgba(56, 189, 248, 0.18)",
    "border_active": "rgba(0, 240, 255, 0.6)",
    "accent_cyan": "#00F0FF",
    "accent_blue": "#38BDF8",
    "accent_indigo": "#6366F1",
    "accent_purple": "#A855F7",
    "accent_emerald": "#10B981",
    "accent_amber": "#F59E0B",
    "accent_rose": "#F43F5E",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B"
}
