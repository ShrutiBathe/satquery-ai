"""
SatQuery AI - High-Fidelity Mock Service for Demo Mode
Simulates the autonomous agentic routing, specialist analysis, visual evidence synthesis,
and execution trace generation according to the backend integration contract.
"""

from typing import Dict, Any, List, Optional
import time
import random
from PIL import Image

import config.settings as cfg
from services.sample_data import (
    generate_change_detection_scenario,
    generate_grounding_scenario,
    generate_optical_sar_scenario,
    generate_vqa_scenario
)
from utils.image_utils import create_change_heatmap, create_annotated_bboxes


def determine_workflow_from_query(query: str, mode: str, has_image_b: bool) -> str:
    """Simulate autonomous Agentic Intent Routing based on natural language."""
    q_lower = query.lower() if query else ""

    # Explicit mode overrides
    if mode == cfg.MODE_COMPARE:
        return cfg.WORKFLOW_CHANGE
    elif mode == cfg.MODE_OPTICAL_SAR:
        return cfg.WORKFLOW_OPTICAL_SAR

    # Auto Detect keyword semantic matching
    if any(k in q_lower for k in ["change", "different", "difference", "between", "2024", "2026", "timeline", "newly built", "developed"]):
        return cfg.WORKFLOW_CHANGE
    elif any(k in q_lower for k in ["sar", "radar", "backscatter", "penetrat", "optical + sar", "multimodal"]):
        return cfg.WORKFLOW_OPTICAL_SAR
    elif any(k in q_lower for k in ["where", "locate", "find", "bounding", "polygon", "highlight", "coordinates", "tanks", "buildings"]):
        return cfg.WORKFLOW_GROUNDING
    elif has_image_b:
        return cfg.WORKFLOW_CHANGE
    else:
        return cfg.WORKFLOW_VQA


def execute_mock_analysis(
    image_a: Optional[Image.Image],
    image_b: Optional[Image.Image],
    query: str,
    mode: str = cfg.MODE_AUTO,
    metadata_a: Optional[Dict[str, Any]] = None,
    metadata_b: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute simulated analysis pipeline matching backend JSON contract.
    """
    has_b = image_b is not None
    task_id = determine_workflow_from_query(query, mode, has_b)
    analysis_id = f"SQ-{random.randint(10000, 99999)}"

    # If the user is running an uploaded or scenario-based image, produce corresponding evidence
    if task_id == cfg.WORKFLOW_CHANGE:
        scenario = generate_change_detection_scenario()
        active_img_a = image_a if image_a is not None else scenario["image_a"]
        active_img_b = image_b if image_b is not None else scenario["image_b"]

        heatmap, overlay = create_change_heatmap(active_img_a, active_img_b)

        visual_evidence = {
            "type": "change_detection",
            "image_a": active_img_a,
            "image_b": active_img_b,
            "heatmap": heatmap,
            "overlay": overlay,
            "labels": scenario["visual_evidence"]["labels"]
        }
        answer = scenario["answer"]
        metrics = scenario["metrics"]
        bullets = scenario["summary_bullets"]
        confidence = scenario["confidence"]
        breakdown = scenario["confidence_breakdown"]
        task_info = scenario["detected_task"]

    elif task_id == cfg.WORKFLOW_GROUNDING:
        scenario = generate_grounding_scenario()
        active_img = image_a if image_a is not None else scenario["image_a"]

        # Synthesize bounding boxes if custom image
        w, h = active_img.size
        bboxes = [
            {"box": [0.15, 0.12, 0.42, 0.38], "label": "Industrial Facility #1", "score": 0.94, "color": "#00F0FF"},
            {"box": [0.18, 0.55, 0.45, 0.85], "label": "Logistics Shed #2", "score": 0.91, "color": "#38BDF8"},
            {"box": [0.60, 0.25, 0.85, 0.52], "label": "Storage Tank Array", "score": 0.96, "color": "#00F0FF"},
            {"box": [0.65, 0.62, 0.88, 0.90], "label": "Containment Berm", "score": 0.88, "color": "#10B981"}
        ]
        annotated_img = create_annotated_bboxes(active_img, bboxes)

        visual_evidence = {
            "type": "grounding",
            "image_a": active_img,
            "annotated_bboxes": annotated_img,
            "seg_overlay": scenario["visual_evidence"]["seg_overlay"],
            "bboxes": bboxes,
            "labels": scenario["visual_evidence"]["labels"]
        }
        answer = scenario["answer"]
        metrics = scenario["metrics"]
        bullets = scenario["summary_bullets"]
        confidence = scenario["confidence"]
        breakdown = scenario["confidence_breakdown"]
        task_info = scenario["detected_task"]

    elif task_id == cfg.WORKFLOW_OPTICAL_SAR:
        scenario = generate_optical_sar_scenario()
        active_img_a = image_a if image_a is not None else scenario["image_a"]
        active_img_b = image_b if image_b is not None else scenario["image_b"]

        visual_evidence = {
            "type": "optical_sar",
            "image_a": active_img_a,
            "image_b": active_img_b,
            "fused_overlay": scenario["visual_evidence"]["fused_overlay"],
            "labels": scenario["visual_evidence"]["labels"]
        }
        answer = scenario["answer"]
        metrics = scenario["metrics"]
        bullets = scenario["summary_bullets"]
        confidence = scenario["confidence"]
        breakdown = scenario["confidence_breakdown"]
        task_info = scenario["detected_task"]

    else:  # VQA
        scenario = generate_vqa_scenario()
        active_img = image_a if image_a is not None else scenario["image_a"]

        visual_evidence = {
            "type": "vqa",
            "image_a": active_img,
            "attention_overlay": scenario["visual_evidence"]["attention_overlay"],
            "labels": scenario["visual_evidence"]["labels"]
        }
        answer = scenario["answer"]
        metrics = scenario["metrics"]
        bullets = scenario["summary_bullets"]
        confidence = scenario["confidence"]
        breakdown = scenario["confidence_breakdown"]
        task_info = scenario["detected_task"]

    # Generate 6-Stage Execution Trace
    analysis_trace = [
        {
            "step": 1,
            "stage": "Query Understanding",
            "details": f"Parsed query token sequence ({len(query.split())} tokens). Intent identified: {task_info['title']}.",
            "latency": "142 ms",
            "agent_node": "RouterAgent_v2"
        },
        {
            "step": 2,
            "stage": "Input Validation",
            "details": f"Sensor channels verified. Dimensional alignment checked: 1024×1024 px. CRS: EPSG:4326 verified.",
            "latency": "68 ms",
            "agent_node": "GeospatialValidatorNode"
        },
        {
            "step": 3,
            "stage": "Agentic Routing",
            "details": f"Autonomous routing decision: Selected specialist pipeline '{task_info['model_pipeline']}'.",
            "latency": "180 ms",
            "agent_node": "DispatcherNode"
        },
        {
            "step": 4,
            "stage": "Specialist Inference",
            "details": f"Executed forward pass on {task_info['input_modality']} spatial tensor. 12 attention heads activated.",
            "latency": "1.24 s",
            "agent_node": "SpecialistWorkerPool"
        },
        {
            "step": 5,
            "stage": "Evidence Generation",
            "details": "Calculated spatial masks, bounding box anchors, and confidence thresholds (τ > 0.85).",
            "latency": "310 ms",
            "agent_node": "EvidenceSynthesisNode"
        },
        {
            "step": 6,
            "stage": "Answer Formulation",
            "details": f"Synthesized natural language insight cross-verified against detected visual evidence.",
            "latency": "225 ms",
            "agent_node": "InsightSynthesizer"
        }
    ]

    return {
        "status": "success",
        "analysis_id": analysis_id,
        "query": query,
        "mode": mode,
        "detected_task": task_info,
        "answer": answer,
        "confidence": confidence,
        "confidence_breakdown": breakdown,
        "summary_bullets": bullets,
        "metrics": metrics,
        "visual_evidence": visual_evidence,
        "analysis_trace": analysis_trace
    }


def generate_mock_follow_up(original_result: Dict[str, Any], user_query: str) -> str:
    """Generate simulated context-aware follow up response."""
    q = user_query.lower()
    task_id = original_result.get("detected_task", {}).get("id", "")

    if "south" in q or "southern" in q:
        return (
            "Examining the southern coordinates: Surface reflectance remains consistent with baseline data. "
            "No substantial construction, earthwork, or anomalous water ponding was detected in the southern perimeter."
        )
    elif "area" in q or "hectare" in q or "size" in q:
        return (
            "Based on pixel resolution calibration (0.5m/px Ground Sampling Distance), "
            "the largest detected continuous region measures approximately 3.82 hectares (± 0.15 ha margin of error)."
        )
    elif "confidence" in q or "accuracy" in q:
        return (
            "Confidence is calculated across three orthogonal vectors: Spatial Grounding (95%), "
            "Semantic Category Alignment (92%), and Radiometric Sensor Calibration (96%). "
            "Overall ensemble score is 93%."
        )
    elif "road" in q or "infrastructure" in q:
        return (
            "The primary road corridor connects directly to the arterial highway with an average width of 14.5 meters. "
            "Pavement shows high specular uniformity indicative of recent hot-mix asphalt application."
        )
    else:
        return (
            f"Regarding '{user_query}': Spatial analysis across the active remote sensing layers confirms "
            "that all detections remain consistent with the primary findings. "
            "No conflicting spectral signatures were identified within the specified region of interest."
        )
