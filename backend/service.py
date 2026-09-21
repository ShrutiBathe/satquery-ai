"""
SatQuery AI - Backend Analysis Service

Main orchestration layer for the SatQuery AI prototype.

Responsibilities:
- Validate the incoming analysis request at the service level
- Understand the natural-language query
- Determine the required analysis task
- Delegate image validation to geo.validation
- Delegate image preprocessing to geo.preprocessing
- Execute the appropriate specialist adapter
- Build the standardized AnalysisResult
- Maintain a structured execution trace

The service does NOT perform:
- Image format validation
- Image resizing
- RGB band selection
- GeoTIFF reading
- GeoTIFF alignment
- Model-specific preprocessing

Those responsibilities belong to the geo module and AI model modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent.router import understand_query as run_agent_router
from backend.errors import ModelError, ValidationError
from backend.schemas import AnalysisRequest, AnalysisResult

# ---------------------------------------------------------------------------
# Query routing
# ---------------------------------------------------------------------------

def understand_query(
    query: str,
    image_count: int,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Route a request through the AI Agent's public LangGraph interface.

    Keeping this thin adapter in the backend makes ``agent.router`` the
    single owner of routing logic while preserving the backend's existing
    orchestration interface.
    """

    try:
        return run_agent_router(
            query=query,
            image_count=image_count,
            metadata=metadata,
        )
    except ValueError as exc:
        # Agent validation failures are client-correctable input errors,
        # not backend/model failures.
        raise ValidationError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Trace utilities
# ---------------------------------------------------------------------------

def _add_trace(
    trace: list[dict[str, Any]],
    stage: str,
    details: str,
    step: int | None = None,
    status: str = "completed",
    latency: str = "N/A",
) -> None:
    """
    Add a structured execution-trace item.

    The frontend expects trace entries to be dictionaries containing
    fields such as step, stage, details and latency.
    """

    if step is None:
        step = len(trace) + 1

    trace.append(
        {
            "step": step,
            "stage": stage,
            "details": details,
            "status": status,
            "latency": latency,
        }
    )


def _normalize_trace(
    trace: list[Any],
    default_stage: str = "Analysis Step",
) -> list[dict[str, Any]]:
    """
    Normalize trace entries returned by specialist modules.

    Supports both:
    - structured dictionaries
    - legacy string trace entries
    """

    normalized: list[dict[str, Any]] = []

    for index, item in enumerate(trace, start=1):

        if isinstance(item, dict):
            normalized.append(
                {
                    "step": item.get("step", index),
                    "stage": item.get("stage", default_stage),
                    "details": item.get("details", ""),
                    "status": item.get("status", "completed"),
                    "latency": item.get("latency", "N/A"),
                }
            )

        else:
            normalized.append(
                {
                    "step": index,
                    "stage": default_stage,
                    "details": str(item),
                    "status": "completed",
                    "latency": "N/A",
                }
            )

    return normalized


# ---------------------------------------------------------------------------
# Specialist adapters
# ---------------------------------------------------------------------------

def run_vqa(
    image_path: str,
    query: str,
) -> dict[str, Any]:
    """
    VQA specialist adapter.

    Import lazily so the backend can start without downloading SmolVLM.
    """

    from models.vqa.inference import run_vqa as model_run_vqa
    result = model_run_vqa(image_path, query)
    result.setdefault("visual_evidence", {"image_a": image_path})
    result.setdefault("trace", [{"stage": "VQA Specialist", "details": "SmolVLM inference completed."}])
    result.setdefault("confidence_breakdown", {"model": "not provided by SmolVLM"})
    return result


def run_grounding(
    image_path: str,
    query: str,
) -> dict[str, Any]:
    """
    Visual grounding specialist adapter.

    Import lazily so Grounding DINO is loaded only for grounding requests.
    """

    from models.grounding.grounding import run_grounding as model_run_grounding
    result = model_run_grounding(image_path, query)
    detections = result.get("detections", [])
    result["answer"] = f"Detected {len(detections)} matching object(s)."
    result["summary_bullets"] = [
        f"Grounding DINO returned {len(detections)} detection(s).",
        "Bounding boxes are shown in the generated visualization.",
    ]
    evidence_path = (
        result.get("output_paths", [None])[0]
        if result.get("output_paths")
        else None
    )
    result["visual_evidence"] = {
        "image_a": image_path,
        "annotated_bboxes": evidence_path,
    }
    result["trace"] = [{"stage": "Grounding Specialist", "details": "Grounding DINO inference completed."}]
    return result


def run_change_detection(
    image1_path: str,
    image2_path: str,
) -> dict[str, Any]:
    """
    Change detection specialist adapter.

    Import lazily so ChangeFormer and its checkpoint are loaded on demand.
    """

    from models.change_detection.change_detection import (
        run_change_detection as model_run_change_detection,
    )
    result = model_run_change_detection(image1_path, image2_path)

    # If the specialist failed, surface the real error so the user sees
    # an actionable message instead of "Change detected: False; 0.00%".
    if not result.get("success", False):
        error_msg = result.get("error") or "ChangeFormer inference failed (unknown error)."
        raise ModelError(f"Change detection failed: {error_msg}")

    change_detected = result.get("change_detected", False)
    change_pct = result.get("change_percentage", 0.0)
    region_count = len(result.get("detections", []))

    result["answer"] = (
        f"{'Significant land-cover change detected' if change_detected else 'No significant change detected'} "
        f"between the two images. "
        f"{region_count} changed region(s) identified, covering {change_pct:.2f}% of the scene."
    )
    result["visual_evidence"] = {
        "image_a": image1_path,
        "image_b": image2_path,
        "heatmap": result.get("change_mask"),
        "overlay": result.get("visualization"),
        "change_mask": result.get("change_mask"),
    }
    # Evidence list for generic UI sections (paths to generated artefacts)
    result["evidence"] = [
        p for p in [result.get("change_mask"), result.get("visualization")] if p
    ]
    # Summary bullets presented in the answer panel
    result["summary_bullets"] = [
        f"Change detected: {'Yes' if change_detected else 'No'}.",
        f"Detected {region_count} change region(s) in the scene.",
        f"Total changed area: {change_pct:.2f}% of the image.",
        f"Binary change mask and overlay saved for evidence review.",
    ]
    # Statistics
    stats = result.get("statistics", {})
    stats.update({
        "change_percentage": change_pct,
        "region_count": region_count,
        "change_detected": change_detected,
    })
    result["statistics"] = stats
    result["output_paths"] = [
        path for path in [result.get("change_mask"), result.get("visualization")]
        if path
    ]
    result["trace"] = [{"stage": "Change Detection Specialist", "details": "ChangeFormer inference completed successfully."}]
    return result


def run_optical_sar(
    optical_path: str,
    vv_path: str,
    vh_path: str,
) -> dict[str, Any]:
    """
    Optical-SAR specialist adapter.

    The specialist owns modality-specific patch extraction and normalization.
    """

    from models.optical_sar.specialist import run_optical_sar as model_run_optical_sar
    result = model_run_optical_sar(optical_path, vv_path, vh_path)
    comparison = result.get("comparison", {})
    if result.get("status") == "success":
        agreement = result.get("interpretation", {}).get("agreement", "UNKNOWN")
        result["answer"] = (
            f"Optical-SAR feature analysis completed with {agreement.lower()} "
            f"agreement (cosine similarity {comparison.get('cosine_similarity', 0.0):.3f})."
        )
    result["success"] = result.get("status") == "success"
    result["visual_evidence"] = {
        "image_a": optical_path, 
        "image_b": vv_path, 
        "sar_vh": vh_path
    }
    result["trace"] = [{"stage": "Optical-SAR Specialist", "details": "Optical-SAR model inference completed."}]
    return result


# ---------------------------------------------------------------------------
# Result construction
# ---------------------------------------------------------------------------

def _build_result(
    request: AnalysisRequest,
    task: str,
    detected_task: dict[str, Any],
    specialist_result: dict[str, Any],
    trace: list[dict[str, Any]],
) -> AnalysisResult:
    """
    Convert a specialist result into the standard AnalysisResult schema.
    """

    specialist_trace = _normalize_trace(
        specialist_result.get("trace", []),
        default_stage="Specialist Analysis",
    )

    for item in specialist_trace:
        item["step"] = len(trace) + 1
        trace.append(item)

    _add_trace(
        trace,
        "Specialist Analysis",
        "Specialist analysis completed.",
    )

    # Evidence normalization
    evidence = specialist_result.get("evidence", [])

    if evidence is None:
        evidence = []

    normalized_evidence = []
    for item in evidence:
        if isinstance(item, dict):
            normalized_evidence.append(item)
        else:
            normalized_evidence.append(
                {
                    "type": "visual_evidence",
                    "label": "Generated evidence",
                    "path": str(item),
                    "description": "Evidence generated by the specialist model.",
                }
            )
    evidence = normalized_evidence

    # Visual evidence normalization
    visual_evidence = specialist_result.get(
        "visual_evidence",
        {},
    )

    if visual_evidence is None:
        visual_evidence = {}

    # Statistics normalization
    statistics = specialist_result.get(
        "statistics",
        {},
    )

    if statistics is None:
        statistics = {}

    # Output paths normalization
    output_paths = specialist_result.get(
        "output_paths",
        [],
    )

    if output_paths is None:
        output_paths = []

    # Summary bullets normalization
    summary_bullets = specialist_result.get(
        "summary_bullets",
        [],
    )

    if summary_bullets is None:
        summary_bullets = []

    _add_trace(
        trace,
        "Result Assembly",
        "Analysis result assembled successfully.",
    )

    return AnalysisResult(
        success=bool(specialist_result.get("success", False)),
        status=(
            "success"
            if specialist_result.get("success", False)
            else "failed"
        ),
        query=request.query,
        mode=request.mode,
        task=task,
        detected_task={
            "task_id": task,
            "title": task.replace("_", " ").title(),
            "reason": detected_task.get("reason", ""),
            "required_images": detected_task.get(
                "required_images",
                1,
            ),
        },
        answer=specialist_result.get("answer", ""),
        confidence=specialist_result.get("confidence"),
        confidence_breakdown=specialist_result.get(
            "confidence_breakdown",
            {},
        ),
        summary_bullets=summary_bullets,
        metrics=specialist_result.get("metrics", {}),
        evidence=evidence,
        visual_evidence=visual_evidence,
        output_paths=output_paths,
        statistics=statistics,
        trace=trace,
        analysis_trace=trace,
        error=specialist_result.get("error"),
    )


# ---------------------------------------------------------------------------
# Main analysis orchestration
# ---------------------------------------------------------------------------

def analyze(request: AnalysisRequest) -> AnalysisResult:
    """
    Main SatQuery AI analysis pipeline.

    Pipeline
    --------
    1. Validate request-level information
    2. Understand the natural-language query
    3. Determine analysis task
    4. Validate images through geo.validation
    5. Preprocess images through geo.preprocessing
    6. Run the appropriate specialist adapter
    7. Assemble AnalysisResult
    """

    from geo.preprocessing import preprocess_images
    from geo.validation import validate_images

    trace: list[dict[str, Any]] = []

    _add_trace(
        trace,
        "Request Received",
        "Backend analysis request received.",
    )

    # ------------------------------------------------------------------
    # 1. Request-level validation
    # ------------------------------------------------------------------

    if not request.query or not request.query.strip():
        raise ValidationError(
            "Analysis query cannot be empty."
        )

    if not request.image_paths:
        raise ValidationError(
            "At least one image must be provided."
        )

    if len(request.image_paths) > 3:
        raise ValidationError(
            "A maximum of three images is supported."
        )

    _add_trace(
        trace,
        "Request Validation",
        "Query and request structure are valid.",
    )

    # ------------------------------------------------------------------
    # 2. Query understanding / routing
    # ------------------------------------------------------------------

    routing = understand_query(
    query=request.query,
    image_count=len(request.image_paths),
    metadata=request.metadata_a
)

    # Explicit UI modes are user-selected workflow contracts. Auto Detect
    # remains fully agent-routed, while compare/optical modes must not fall
    # back to single-image VQA when a query uses ambiguous wording.
    if request.mode == "compare_images":
        routing = {
            "task": "change_detection",
            "required_images": 2,
            "reason": "Compare-images mode explicitly selects change detection.",
        }
        if len(request.image_paths) != 2:
            raise ValidationError("Compare-images mode requires exactly two images.")
    elif request.mode == "optical_sar":
        routing = {
            "task": "optical_sar",
            "required_images": 3,
            "reason": "Optical-SAR mode explicitly selects optical plus SAR analysis.",
        }
        if len(request.image_paths) != 3:
            raise ValidationError(
                "Optical-SAR mode requires exactly three images: optical, SAR VV, and SAR VH."
            )

    task = routing["task"]

    _add_trace(
        trace,
        "Query Understanding",
        routing["reason"],
    )

    _add_trace(
        trace,
        "Task Routing",
        f"Query routed to the '{task}' analysis pipeline.",
    )

    # ------------------------------------------------------------------
    # 3. Geo image validation
    # ------------------------------------------------------------------

    validation_result = validate_images(
        request.image_paths,
        task,
    )

    if not validation_result.get("valid", False):
        message = validation_result.get(
            "message",
            "Image validation failed.",
        )

        _add_trace(
            trace,
            "Image Validation",
            message,
            status="failed",
        )

        raise ValidationError(message)

    _add_trace(
        trace,
        "Image Validation",
        validation_result.get(
            "message",
            "Input images are valid.",
        ),
    )

    # ------------------------------------------------------------------
    # 4. Geo preprocessing
    # ------------------------------------------------------------------

    _add_trace(
        trace,
        "Image Preprocessing",
        "Starting Geo image preprocessing.",
        status="running",
    )

    processing_dir = Path(request.image_paths[0]).parent / "processed"
    if task == "optical_sar":
        from geo.preprocessing import preprocess_optical_sar
        preprocessing_result = preprocess_optical_sar(*request.image_paths)
    else:
        preprocessing_result = preprocess_images(
            request.image_paths,
            task,
            output_dir=processing_dir,
        )

    if not preprocessing_result.get("success", False):
        message = preprocessing_result.get(
            "error",
            "Image preprocessing failed.",
        )

        _add_trace(
            trace,
            "Image Preprocessing",
            message,
            status="failed",
        )

        raise ValidationError(message)

    processed_paths = preprocessing_result.get(
        "image_paths",
        [],
    )

    if not processed_paths:
        message = (
            "Image preprocessing completed but returned "
            "no processed image paths."
        )

        _add_trace(
            trace,
            "Image Preprocessing",
            message,
            status="failed",
        )

        raise ValidationError(message)

    preprocessing_metadata = preprocessing_result.get(
        "metadata",
        {},
    )

    _add_trace(
        trace,
        "Image Preprocessing",
        (
            f"Geo preprocessing completed successfully for "
            f"{len(processed_paths)} image(s)."
        ),
    )

    # ------------------------------------------------------------------
    # 5. Specialist execution
    # ------------------------------------------------------------------

    try:

        if task == "vqa":

            specialist_result = run_vqa(
                image_path=processed_paths[0],
                query=request.query,
            )

        elif task == "grounding":

            specialist_result = run_grounding(
                image_path=processed_paths[0],
                query=request.query,
            )

        elif task == "change_detection":

            if len(processed_paths) < 2:
                raise ModelError(
                    "Change detection requires two processed images."
                )

            specialist_result = run_change_detection(
                image1_path=processed_paths[0],
                image2_path=processed_paths[1],
            )

        elif task == "optical_sar":

            if len(processed_paths) < 3:
                raise ModelError(
                    "Optical-SAR analysis requires three processed images: optical, SAR VV, and SAR VH."
                )

            specialist_result = run_optical_sar(
                optical_path=processed_paths[0],
                vv_path=processed_paths[1],
                vh_path=processed_paths[2],
            )

        else:
            raise ValidationError(
                f"Unsupported analysis task: {task}"
            )

    except (ValidationError, ModelError):
        raise

    except Exception as exc:
        raise ModelError(
            f"Specialist analysis failed: {exc}"
        ) from exc

    # ------------------------------------------------------------------
    # 6. Add preprocessing metadata to statistics
    # ------------------------------------------------------------------

    if preprocessing_metadata:
        specialist_statistics = specialist_result.get(
            "statistics",
            {},
        )

        if specialist_statistics is None:
            specialist_statistics = {}

        specialist_statistics.setdefault(
            "preprocessing",
            preprocessing_metadata,
        )

        specialist_result["statistics"] = specialist_statistics

    # ------------------------------------------------------------------
    # 7. Build standardized result
    # ------------------------------------------------------------------

    return _build_result(
        request=request,
        task=task,
        detected_task=routing,
        specialist_result=specialist_result,
        trace=trace,
    )
