"""
SatQuery AI - Session State Manager
Handles application state across Streamlit reruns.
"""

import streamlit as st
from datetime import date, datetime
from typing import Dict, Any, Optional

import config.settings as cfg


def init_session_state() -> None:
    """Initialize all session state variables if they do not already exist."""
    defaults = {
        # Navigation
        "current_page": "home",  # home, new_analysis, history, saved_insights, api_spec, settings
        "analysis_step": 1,      # 1: Data, 2: Query, 3: Processing, 4: Results
        "analysis_mode": cfg.MODE_AUTO,

        # System & Backend Connectivity
        "demo_mode": True,
        "backend_url": cfg.DEFAULT_BACKEND_URL,
        "active_scenario_id": None,

        # Uploaded Data & Imagery
        "uploaded_image_a": None,
        "uploaded_image_b": None,
        "image_a_name": None,
        "image_b_name": None,
        "image_a_date": date(2024, 6, 15),
        "image_b_date": date(2026, 3, 20),
        "image_metadata_a": None,
        "image_metadata_b": None,

        # Query State
        "query_text": "",
        "suggested_query_applied": False,

        # Execution / Processing State
        "is_processing": False,
        "processing_stage_index": 0,
        "pipeline_completed": False,

        # Results & Evidence
        "current_analysis_id": None,
        "detected_task": None,
        "analysis_result": None,
        "confidence": 0.0,
        "confidence_breakdown": {},
        "visual_evidence": {},
        "analysis_trace": [],
        "active_result_tab": 0,

        # Follow-up Chat
        "follow_up_chat": [],

        # Persistent Repositories (Session-bound)
        "history": [],
        "saved_insights": [],

        # UI Theme
        "app_theme": "dark",

        # Toast / Alert trigger
        "notification": None
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def set_page(page_name: str) -> None:
    """Navigate to a target page."""
    st.session_state["current_page"] = page_name


def set_analysis_step(step: int) -> None:
    """Set the current step in the analysis workflow."""
    st.session_state["analysis_step"] = step


def set_analysis_mode(mode: str) -> None:
    """Set the active analysis mode."""
    st.session_state["analysis_mode"] = mode


def set_query(query: str) -> None:
    """Update the current query text."""
    st.session_state["query_text"] = query


def clear_analysis_inputs() -> None:
    """Reset imagery and query inputs for a new analysis session."""
    st.session_state["uploaded_image_a"] = None
    st.session_state["uploaded_image_b"] = None
    st.session_state["image_a_name"] = None
    st.session_state["image_b_name"] = None
    st.session_state["image_metadata_a"] = None
    st.session_state["image_metadata_b"] = None
    st.session_state["query_text"] = ""
    st.session_state["analysis_step"] = 1
    st.session_state["is_processing"] = False
    st.session_state["pipeline_completed"] = False
    st.session_state["analysis_result"] = None
    st.session_state["detected_task"] = None
    st.session_state["visual_evidence"] = {}
    st.session_state["analysis_trace"] = []
    st.session_state["follow_up_chat"] = []
    st.session_state["active_scenario_id"] = None


def save_current_insight() -> bool:
    """Save the current analysis result to the Saved Insights store."""
    if not st.session_state.get("analysis_result"):
        return False

    result = st.session_state["analysis_result"]
    insight_id = f"INS-{len(st.session_state['saved_insights']) + 1:04d}"

    insight_item = {
        "id": insight_id,
        "analysis_id": st.session_state.get("current_analysis_id", "ANL-001"),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": st.session_state.get("query_text", ""),
        "task_name": st.session_state.get("detected_task", {}).get("title", "Geospatial Analysis"),
        "task_id": st.session_state.get("detected_task", {}).get("id", "general"),
        "answer": result.get("answer", ""),
        "confidence": st.session_state.get("confidence", 0.90),
        "image_count": 2 if st.session_state.get("uploaded_image_b") is not None else 1,
        "thumbnail": st.session_state.get("uploaded_image_a"),
        "summary_bullets": result.get("summary_bullets", []),
        "metrics": result.get("metrics", {})
    }

    # Avoid duplicate saving of identical analysis_id
    existing_ids = [i.get("analysis_id") for i in st.session_state["saved_insights"]]
    if insight_item["analysis_id"] not in existing_ids:
        st.session_state["saved_insights"].insert(0, insight_item)
        return True
    return False
