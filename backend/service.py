"""
SatQuery AI - Analysis Service

This module is the main orchestration layer of the backend.

Current prototype flow:

    Request
       ↓
    Query Understanding / Routing
       ↓
    Input Validation
       ↓
    Specialist Analysis
       ↓
    Evidence + Confidence
       ↓
    AnalysisResult

The agent/, geo/, and models/ folders are intentionally treated as
pluggable components. They can be connected here when teammates push
their implementations.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from backend.schemas import (
    AnalysisRequest,
    AnalysisResult,
    DetectedTask,
    EvidenceItem,
    Metric,
)


# -------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------

SUPPORTED_TASKS = {
    "vqa",
    "visual_grounding",
    "change_detection",
    "optical_sar",
}


# -------------------------------------------------------------------
# Public service entry point
# -------------------------------------------------------------------

def analyze(request: AnalysisRequest) -> AnalysisResult:
    """
    Main SatQuery analysis pipeline.

    This is the function called by FastAPI after receiving and saving
    uploaded images.
    """

    analysis_id = f"ANL-{uuid.uuid4().hex[:10].upper()}"

    trace: list[str] = [
        "Request received",
        "Backend analysis started",
    ]

    try:
        # -----------------------------------------------------------
        # 1. Basic request validation
        # -----------------------------------------------------------

        _validate_request_inputs(request)

        trace.append("Input validation completed")

        # -----------------------------------------------------------
        # 2. Understand query and determine task
        # -----------------------------------------------------------

        task_info = understand_query(
            query=request.query,
            image_count=len(request.image_paths),
            mode=request.mode,
        )

        trace.append(
            f"Task selected: {task_info['task']}"
        )

        trace.append(
            f"Routing reason: {task_info['reason']}"
        )

        # -----------------------------------------------------------
        # 3. Task-specific input validation
        # -----------------------------------------------------------

        _validate_task_inputs(
            task=task_info["task"],
            image_paths=request.image_paths,
        )

        trace.append(
            f"Task input validation passed for {task_info['task']}"
        )

        # -----------------------------------------------------------
        # 4. Run specialist analysis
        # -----------------------------------------------------------

        analysis_output = run_specialist_analysis(
            task=task_info["task"],
            request=request,
            analysis_id=analysis_id,
        )

        trace.extend(
            analysis_output.get("trace", [])
        )

        # -----------------------------------------------------------
        # 5. Build standardized response
        # -----------------------------------------------------------

        result = _build_result(
            analysis_id=analysis_id,
            request=request,
            task_info=task_info,
            analysis_output=analysis_output,
            trace=trace,
        )

        return result

    except ValueError as exc:

        trace.append(f"Validation failed: {exc}")

        return AnalysisResult(
            success=False,
            status="error",
            analysis_id=analysis_id,
            query=request.query,
            mode=request.mode,
            task="",
            answer="",
            confidence=None,
            trace=trace,
            analysis_trace=trace,
            error=str(exc),
        )

    except Exception as exc:

        trace.append(
            f"Unexpected analysis error: {exc}"
        )

        return AnalysisResult(
            success=False,
            status="error",
            analysis_id=analysis_id,
            query=request.query,
            mode=request.mode,
            task="",
            answer="",
            confidence=None,
            trace=trace,
            analysis_trace=trace,
            error=f"Analysis failed: {exc}",
        )


# -------------------------------------------------------------------
# Query understanding / routing
# -------------------------------------------------------------------

def understand_query(
    query: str,
    image_count: int,
    mode: str,
) -> dict[str, Any]:
    """
    Determine which SatQuery specialist should handle the query.

    This is intentionally lightweight for the prototype.

    Later this function can be replaced by the AI Agent team's
    LangGraph/query-understanding implementation without changing
    the rest of the backend.
    """

    query_lower = query.lower().strip()

    # ---------------------------------------------------------------
    # Explicit mode overrides
    # ---------------------------------------------------------------

    if mode == "compare_images":
        return {
            "task": "change_detection",
            "title": "Change Detection",
            "reason": "Compare-images mode explicitly requested.",
            "required_images": 2,
        }

    if mode == "optical_sar":
        return {
            "task": "optical_sar",
            "title": "Optical-SAR Analysis",
            "reason": "Optical-SAR mode explicitly requested.",
            "required_images": 2,
        }

    # ---------------------------------------------------------------
    # Change detection keywords
    # ---------------------------------------------------------------

    change_keywords = [
        "change",
        "changes",
        "changed",
        "difference",
        "differences",
        "before and after",
        "between images",
        "compare",
        "comparison",
        "new construction",
        "demolished",
        "removed",
        "built",
        "development",
        "2024",
        "2025",
        "2026",
    ]

    if any(keyword in query_lower for keyword in change_keywords):
        if image_count >= 2:
            return {
                "task": "change_detection",
                "title": "Change Detection",
                "reason": (
                    "The query describes temporal or comparative "
                    "analysis and two images are available."
                ),
                "required_images": 2,
            }

    # ---------------------------------------------------------------
    # Optical-SAR keywords
    # ---------------------------------------------------------------

    optical_sar_keywords = [
        "sar",
        "synthetic aperture radar",
        "radar",
        "backscatter",
        "sar image",
        "optical and sar",
        "optical-sar",
        "optical sar",
        "flood mapping",
        "flood detection",
    ]

    if any(keyword in query_lower for keyword in optical_sar_keywords):
        if image_count >= 2:
            return {
                "task": "optical_sar",
                "title": "Optical-SAR Analysis",
                "reason": (
                    "The query contains SAR/radar-related terminology "
                    "and two images are available."
                ),
                "required_images": 2,
            }

    # ---------------------------------------------------------------
    # Visual grounding keywords
    # ---------------------------------------------------------------

    grounding_keywords = [
        "where",
        "locate",
        "location",
        "find",
        "highlight",
        "bounding box",
        "bounding boxes",
        "bbox",
        "coordinates",
        "polygon",
        "outline",
        "identify the location",
        "show me where",
    ]

    if any(keyword in query_lower for keyword in grounding_keywords):
        return {
            "task": "visual_grounding",
            "title": "Visual Grounding",
            "reason": (
                "The query asks for the location or spatial extent "
                "of an object or region."
            ),
            "required_images": 1,
        }

    # ---------------------------------------------------------------
    # Default → VQA
    # ---------------------------------------------------------------

    return {
        "task": "vqa",
        "title": "Visual Question Answering",
        "reason": (
            "The query is treated as a visual question about "
            "the supplied remote-sensing image."
        ),
        "required_images": 1,
    }


# -------------------------------------------------------------------
# Task-specific validation
# -------------------------------------------------------------------

def _validate_task_inputs(
    task: str,
    image_paths: list[str],
) -> None:
    """
    Validate that the selected task has the required number of images.
    """

    image_count = len(image_paths)

    if task not in SUPPORTED_TASKS:
        raise ValueError(
            f"Unsupported analysis task: {task}"
        )

    if task in {"vqa", "visual_grounding"}:
        if image_count != 1:
            raise ValueError(
                f"{task} requires exactly one image."
            )

    elif task in {
        "change_detection",
        "optical_sar",
    }:
        if image_count != 2:
            raise ValueError(
                f"{task} requires exactly two images."
            )


# -------------------------------------------------------------------
# Specialist analysis dispatcher
# -------------------------------------------------------------------

def run_specialist_analysis(
    task: str,
    request: AnalysisRequest,
    analysis_id: str,
) -> dict[str, Any]:
    """
    Dispatch the request to the appropriate specialist.

    IMPORTANT:
    The specialist implementations are intentionally isolated behind
    adapter functions.

    When teammates push actual implementations:

        agent/
        geo/
        models/

    we replace the corresponding adapter body rather than rewriting
    the backend pipeline.
    """

    if task == "vqa":
        return run_vqa(
            image_path=request.image_paths[0],
            query=request.query,
            analysis_id=analysis_id,
        )

    if task == "visual_grounding":
        return run_grounding(
            image_path=request.image_paths[0],
            query=request.query,
            analysis_id=analysis_id,
        )

    if task == "change_detection":
        return run_change_detection(
            image1_path=request.image_paths[0],
            image2_path=request.image_paths[1],
            query=request.query,
            analysis_id=analysis_id,
        )

    if task == "optical_sar":
        return run_optical_sar(
            optical_path=request.image_paths[0],
            sar_path=request.image_paths[1],
            query=request.query,
            analysis_id=analysis_id,
        )

    raise ValueError(
        f"No specialist available for task: {task}"
    )


# -------------------------------------------------------------------
# VQA adapter
# -------------------------------------------------------------------

def run_vqa(
    image_path: str,
    query: str,
    analysis_id: str,
) -> dict[str, Any]:
    """
    VQA specialist adapter.

    TODO:
        Connect the AI Models team's VQA implementation here.
    """

    return {
        "answer": (
            "VQA model integration is pending. "
            "The query was successfully routed to the "
            "Visual Question Answering pipeline."
        ),
        "confidence": 0.50,
        "confidence_breakdown": {
            "query_understanding": 0.90,
            "model_confidence": 0.50,
            "evidence_quality": 0.40,
        },
        "summary_bullets": [
            "Query routed to Visual Question Answering.",
            "One satellite image was provided.",
            "VQA specialist model is ready to be connected.",
        ],
        "metrics": {},
        "evidence": [],
        "output_paths": [],
        "trace": [
            "VQA specialist selected",
            "VQA model adapter executed",
        ],
    }


# -------------------------------------------------------------------
# Visual grounding adapter
# -------------------------------------------------------------------

def run_grounding(
    image_path: str,
    query: str,
    analysis_id: str,
) -> dict[str, Any]:
    """
    Visual grounding specialist adapter.

    TODO:
        Connect GeoChat/SAM or the team's grounding implementation.
    """

    return {
        "answer": (
            "Visual grounding model integration is pending. "
            "The query was successfully routed to the "
            "Visual Grounding pipeline."
        ),
        "confidence": 0.50,
        "confidence_breakdown": {
            "query_understanding": 0.90,
            "model_confidence": 0.50,
            "spatial_evidence": 0.40,
        },
        "summary_bullets": [
            "Query routed to Visual Grounding.",
            "One satellite image was provided.",
            "Grounding model adapter is ready for integration.",
        ],
        "metrics": {},
        "evidence": [],
        "output_paths": [],
        "trace": [
            "Visual Grounding specialist selected",
            "Grounding model adapter executed",
        ],
    }


# -------------------------------------------------------------------
# Change detection adapter
# -------------------------------------------------------------------

def run_change_detection(
    image1_path: str,
    image2_path: str,
    query: str,
    analysis_id: str,
) -> dict[str, Any]:
    """
    Bi-temporal change detection specialist adapter.

    TODO:
        Connect Open-CD / BIT-CD or the team's actual
        change-detection implementation.
    """

    return {
        "answer": (
            "Change detection model integration is pending. "
            "Two images were successfully received and routed "
            "to the change detection pipeline."
        ),
        "confidence": 0.50,
        "confidence_breakdown": {
            "query_understanding": 0.90,
            "model_confidence": 0.50,
            "temporal_alignment": 0.50,
        },
        "summary_bullets": [
            "Query routed to Bi-temporal Change Detection.",
            "Two satellite images were provided.",
            "Change detection model adapter is ready for integration.",
        ],
        "metrics": {},
        "evidence": [],
        "output_paths": [],
        "trace": [
            "Change Detection specialist selected",
            "Bi-temporal model adapter executed",
        ],
    }


# -------------------------------------------------------------------
# Optical-SAR adapter
# -------------------------------------------------------------------

def run_optical_sar(
    optical_path: str,
    sar_path: str,
    query: str,
    analysis_id: str,
) -> dict[str, Any]:
    """
    Optical-SAR specialist adapter.

    TODO:
        Connect the team's optical-SAR preprocessing/fusion/model
        implementation.
    """

    return {
        "answer": (
            "Optical-SAR model integration is pending. "
            "The optical and SAR inputs were successfully received "
            "and routed to the multimodal analysis pipeline."
        ),
        "confidence": 0.50,
        "confidence_breakdown": {
            "query_understanding": 0.90,
            "model_confidence": 0.50,
            "modality_alignment": 0.40,
        },
        "summary_bullets": [
            "Query routed to Optical-SAR analysis.",
            "Optical and SAR inputs were provided.",
            "Optical-SAR model adapter is ready for integration.",
        ],
        "metrics": {},
        "evidence": [],
        "output_paths": [],
        "trace": [
            "Optical-SAR specialist selected",
            "Optical-SAR model adapter executed",
        ],
    }


# -------------------------------------------------------------------
# Result construction
# -------------------------------------------------------------------

def _build_result(
    analysis_id: str,
    request: AnalysisRequest,
    task_info: dict[str, Any],
    analysis_output: dict[str, Any],
    trace: list[str],
) -> AnalysisResult:
    """
    Convert specialist output into the standard SatQuery response.
    """

    task_id = task_info["task"]

    trace.append(
        "Specialist analysis completed"
    )

    trace.append(
        "Analysis result assembled"
    )

    evidence_items = _normalise_evidence(
        analysis_output.get("evidence", [])
    )

    visual_evidence = _build_visual_evidence(
        evidence_items
    )

    metrics = _normalise_metrics(
        analysis_output.get("metrics", {})
    )

    confidence = analysis_output.get(
        "confidence"
    )

    return AnalysisResult(
        success=True,
        status="success",
        analysis_id=analysis_id,
        query=request.query,
        mode=request.mode,
        task=task_id,

        detected_task=DetectedTask(
            task_id=task_id,
            title=task_info["title"],
            reason=task_info["reason"],
            required_images=task_info["required_images"],
        ),

        answer=analysis_output.get(
            "answer",
            "",
        ),

        confidence=confidence,

        confidence_breakdown=analysis_output.get(
            "confidence_breakdown",
            {},
        ),

        summary_bullets=analysis_output.get(
            "summary_bullets",
            [],
        ),

        metrics=metrics,

        evidence=evidence_items,

        visual_evidence=visual_evidence,

        output_paths=analysis_output.get(
            "output_paths",
            [],
        ),

        statistics=analysis_output.get(
            "statistics",
            {},
        ),

        trace=trace,

        analysis_trace=trace,

        error=None,
    )


# -------------------------------------------------------------------
# Evidence normalization
# -------------------------------------------------------------------

def _normalise_evidence(
    evidence: list[Any],
) -> list[EvidenceItem]:
    """
    Convert raw evidence dictionaries into EvidenceItem objects.
    """

    normalized: list[EvidenceItem] = []

    for item in evidence:

        if isinstance(item, EvidenceItem):
            normalized.append(item)
            continue

        if isinstance(item, dict):
            normalized.append(
                EvidenceItem(
                    type=str(
                        item.get("type", "unknown")
                    ),
                    label=str(
                        item.get("label", "")
                    ),
                    url=item.get("url"),
                    path=item.get("path"),
                    description=str(
                        item.get("description", "")
                    ),
                )
            )

    return normalized


def _build_visual_evidence(
    evidence: list[EvidenceItem],
) -> dict[str, Any]:
    """
    Create a simple frontend-compatible evidence mapping.

    The frontend API client can later download these URLs and convert
    them into PIL images.
    """

    result: dict[str, Any] = {}

    for item in evidence:

        if item.url:
            result[item.type] = item.url

        elif item.path:
            result[item.type] = item.path

    return result


# -------------------------------------------------------------------
# Metrics normalization
# -------------------------------------------------------------------

def _normalise_metrics(
    metrics: dict[str, Any],
) -> dict[str, Metric]:
    """
    Normalize metrics into the schema expected by the frontend.
    """

    normalized: dict[str, Metric] = {}

    for key, value in metrics.items():

        if isinstance(value, Metric):
            normalized[key] = value

        elif isinstance(value, dict):
            normalized[key] = Metric(
                value=value.get("value"),
                unit=str(
                    value.get("unit", "")
                ),
            )

        else:
            normalized[key] = Metric(
                value=value,
                unit="",
            )

    return normalized


# -------------------------------------------------------------------
# Internal validation
# -------------------------------------------------------------------

def _validate_request_inputs(
    request: AnalysisRequest,
) -> None:
    """
    Additional service-level validation.

    FastAPI performs API-level validation and validator.py handles
    request validation. This function protects the service itself
    when called directly from tests or other Python code.
    """

    if not request.query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if not request.image_paths:
        raise ValueError(
            "At least one image is required."
        )

    if len(request.image_paths) > 2:
        raise ValueError(
            "A maximum of two images is supported."
        )

    for image_path in request.image_paths:

        if not image_path.strip():
            raise ValueError(
                "Image path cannot be empty."
            )

        path = Path(image_path)

        if not path.exists():
            raise ValueError(
                f"Image file does not exist: {image_path}"
            )