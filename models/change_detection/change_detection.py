"""
SatQuery AI - Change Detection Specialist

Public API:

    run_change_detection(before_path, after_path)

The function returns structured evidence suitable for the SatQuery AI
agent/backend.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .config import (
    MASK_DIR,
    MIN_COMPONENT_AREA,
    MORPH_KERNEL_SIZE,
    OVERLAY_DIR,
)
from .inference import get_model


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def _clean_mask(mask: np.ndarray) -> np.ndarray:
    """
    Remove small noise and clean the binary change mask.
    """

    binary = (mask > 0).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (
            MORPH_KERNEL_SIZE,
            MORPH_KERNEL_SIZE,
        ),
    )

    # Remove tiny holes/noise.
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel,
    )

    # Connect nearby changed pixels.
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel,
    )

    # Remove tiny connected components.
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary,
        connectivity=8,
    )

    cleaned = np.zeros_like(binary)

    for label_id in range(1, num_labels):
        area = stats[label_id, cv2.CC_STAT_AREA]

        if area >= MIN_COMPONENT_AREA:
            cleaned[labels == label_id] = 255

    return cleaned


def _calculate_change_percentage(
    mask: np.ndarray,
) -> float:
    """
    Calculate percentage of pixels classified as changed.
    """

    total_pixels = mask.shape[0] * mask.shape[1]

    if total_pixels == 0:
        return 0.0

    changed_pixels = np.count_nonzero(mask > 0)

    percentage = (
        changed_pixels / total_pixels
    ) * 100.0

    return round(float(percentage), 2)


def _extract_change_regions(
    mask: np.ndarray,
) -> list[dict[str, Any]]:
    """
    Extract connected components from the change mask.

    Returns bounding boxes in:

        [x1, y1, x2, y2]

    format.
    """

    binary = (mask > 0).astype(np.uint8)

    num_labels, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            binary,
            connectivity=8,
        )
    )

    regions = []

    for label_id in range(1, num_labels):

        x = int(stats[label_id, cv2.CC_STAT_LEFT])
        y = int(stats[label_id, cv2.CC_STAT_TOP])

        width = int(stats[label_id, cv2.CC_STAT_WIDTH])
        height = int(stats[label_id, cv2.CC_STAT_HEIGHT])

        area = int(stats[label_id, cv2.CC_STAT_AREA])

        if area < MIN_COMPONENT_AREA:
            continue

        x2 = x + width
        y2 = y + height

        # Confidence here is NOT a neural-network confidence.
        #
        # ChangeFormer itself produces a pixel classification.
        # We therefore derive a simple region confidence from the
        # proportion of changed pixels inside the component bounding box.
        region_mask = (
            labels[y:y2, x:x2] == label_id
        )

        box_area = width * height

        if box_area > 0:
            confidence = area / box_area
        else:
            confidence = 0.0

        confidence = min(
            max(float(confidence), 0.0),
            1.0,
        )

        regions.append(
            {
                "label": "changed_area",
                "confidence": round(confidence, 4),
                "box": [x, y, x2, y2],
                "area_pixels": area,
                "centroid": [
                    round(float(centroids[label_id][0]), 2),
                    round(float(centroids[label_id][1]), 2),
                ],
            }
        )

    # Largest changed regions first.
    regions.sort(
        key=lambda item: item["area_pixels"],
        reverse=True,
    )

    return regions


def _save_mask(
    mask: np.ndarray,
    output_path: Path,
) -> None:
    """
    Save binary mask.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cv2.imwrite(
        str(output_path),
        mask,
    )


def _save_overlay(
    before_path: str | Path,
    mask: np.ndarray,
    output_path: Path,
) -> None:
    """
    Create an evidence visualization.

    Changed areas are highlighted over the original image.
    """

    before_path = Path(before_path)

    image = cv2.imread(
        str(before_path),
        cv2.IMREAD_COLOR,
    )

    if image is None:
        raise ValueError(
            f"Could not read image for overlay: {before_path}"
        )

    height, width = image.shape[:2]

    if mask.shape[:2] != (height, width):
        mask = cv2.resize(
            mask,
            (width, height),
            interpolation=cv2.INTER_NEAREST,
        )

    changed = mask > 0

    # Create highlighted layer.
    overlay = image.copy()

    # Highlight changed pixels.
    #
    # We deliberately keep this simple so the generated image is easy
    # for the frontend to display.
    overlay[changed] = (
        0.5 * overlay[changed]
        + 0.5 * np.array([0, 0, 255])
    ).astype(np.uint8)

    # Draw connected-component bounding boxes.
    regions = _extract_change_regions(mask)

    for region in regions:

        x1, y1, x2, y2 = region["box"]

        cv2.rectangle(
            overlay,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            2,
        )

        label = "change"

        cv2.putText(
            overlay,
            label,
            (x1, max(y1 - 5, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cv2.imwrite(
        str(output_path),
        overlay,
    )


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------


def run_change_detection(
    before_path: str,
    after_path: str,
) -> dict:
    """
    Run binary bi-temporal change detection.

    Args:
        before_path:
            Path to earlier satellite image.

        after_path:
            Path to later satellite image.

    Returns:
        Structured dictionary:

        {
            "success": True,
            "change_detected": True,
            "change_percentage": 4.72,
            "detections": [...],
            "change_mask": "...",
            "visualization": "...",
            "evidence": [...],
            "statistics": {...},
            "error": None
        }
    """

    try:

        before = Path(before_path)
        after = Path(after_path)

        # ---------------------------------------------------------------
        # Validate inputs
        # ---------------------------------------------------------------

        if not before.exists():
            return {
                "success": False,
                "change_detected": False,
                "change_percentage": 0.0,
                "detections": [],
                "change_mask": None,
                "visualization": None,
                "evidence": [],
                "statistics": {},
                "error": f"Before image not found: {before}",
            }

        if not after.exists():
            return {
                "success": False,
                "change_detected": False,
                "change_percentage": 0.0,
                "detections": [],
                "change_mask": None,
                "visualization": None,
                "evidence": [],
                "statistics": {},
                "error": f"After image not found: {after}",
            }

        # ---------------------------------------------------------------
        # Load ChangeFormer
        # ---------------------------------------------------------------

        model = get_model()

        # ---------------------------------------------------------------
        # Prediction
        # ---------------------------------------------------------------

        raw_mask, original_size = model.predict_original_size(
            before,
            after,
        )

        # ---------------------------------------------------------------
        # Clean prediction
        # ---------------------------------------------------------------

        clean_mask = _clean_mask(raw_mask)

        # Convert to 0/1 representation.
        binary_mask = (
            clean_mask > 0
        ).astype(np.uint8)

        # ---------------------------------------------------------------
        # Statistics
        # ---------------------------------------------------------------

        change_percentage = _calculate_change_percentage(
            binary_mask
        )

        detections = _extract_change_regions(
            binary_mask
        )

        change_detected = len(detections) > 0

        # ---------------------------------------------------------------
        # Output paths
        # ---------------------------------------------------------------

        before_stem = before.stem
        after_stem = after.stem

        output_name = (
            f"{before_stem}_to_{after_stem}"
        )

        mask_path = (
            MASK_DIR
            / f"{output_name}_change_mask.png"
        )

        overlay_path = (
            OVERLAY_DIR
            / f"{output_name}_overlay.png"
        )

        # ---------------------------------------------------------------
        # Save evidence
        # ---------------------------------------------------------------

        _save_mask(
            binary_mask * 255,
            mask_path,
        )

        _save_overlay(
            before,
            binary_mask,
            overlay_path,
        )

        # ---------------------------------------------------------------
        # Return structured result
        # ---------------------------------------------------------------

        return {
            "success": True,

            "change_detected": change_detected,

            "change_percentage": change_percentage,

            "detections": detections,

            "change_mask": str(mask_path),

            "visualization": str(overlay_path),

            "evidence": [
                {
                    "type": "change_mask",
                    "path": str(mask_path),
                },
                {
                    "type": "overlay",
                    "path": str(overlay_path),
                },
            ],

            "statistics": {
                "image_width": original_size[0],
                "image_height": original_size[1],
                "changed_regions": len(detections),
                "changed_pixels": int(
                    np.count_nonzero(binary_mask)
                ),
                "total_pixels": int(
                    binary_mask.shape[0]
                    * binary_mask.shape[1]
                ),
            },

            "error": None,
        }

    except Exception as exc:

        return {
            "success": False,
            "change_detected": False,
            "change_percentage": 0.0,
            "detections": [],
            "change_mask": None,
            "visualization": None,
            "evidence": [],
            "statistics": {},
            "error": str(exc),
        }