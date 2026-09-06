"""
SatQuery AI - Image Annotation and Geospatial Utilities
Provides visual evidence rendering (bounding boxes, segmentation masks, change overlays).
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import random


def create_annotated_bboxes(
    image: Image.Image,
    bboxes: List[Dict[str, Any]],
    border_color: str = "#00F0FF",
    fill_alpha: int = 40
) -> Image.Image:
    """
    Draw bounding boxes on an image with labels and transparent fill.
    bboxes format: [{"box": [ymin, xmin, ymax, xmax], "label": str, "score": float, "color": str (optional)}]
    Coordinates normalized between 0.0 and 1.0 or pixel coordinates.
    """
    canvas = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_canvas = ImageDraw.Draw(canvas)

    width, height = canvas.size

    for item in bboxes:
        box = item.get("box", [0, 0, 0, 0])
        label = item.get("label", "Target")
        score = item.get("score", 0.9)
        color_hex = item.get("color", border_color)

        # Handle normalized vs pixel coordinates
        if all(0.0 <= coord <= 1.0 for coord in box):
            ymin, xmin, ymax, xmax = box
            x0 = int(xmin * width)
            y0 = int(ymin * height)
            x1 = int(xmax * width)
            y1 = int(ymax * height)
        else:
            x0, y0, x1, y1 = [int(v) for v in box]

        # Parse RGB color
        try:
            rgb = ImageColor.getrgb(color_hex)
        except Exception:
            rgb = (0, 240, 255)

        fill_color = (rgb[0], rgb[1], rgb[2], fill_alpha)
        stroke_color = (rgb[0], rgb[1], rgb[2], 230)

        # Translucent fill
        draw_overlay.rectangle([x0, y0, x1, y1], fill=fill_color, outline=stroke_color, width=2)

        # Corner accent markers (geospatial HUD crosshair style)
        corner_len = min(12, max(4, int(min(x1 - x0, y1 - y0) * 0.2)))
        for cx, cy in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
            dx = corner_len if cx == x0 else -corner_len
            dy = corner_len if cy == y0 else -corner_len
            draw_overlay.line([(cx, cy), (cx + dx, cy)], fill=stroke_color, width=3)
            draw_overlay.line([(cx, cy), (cx, cy + dy)], fill=stroke_color, width=3)

        # Label pill badge
        label_text = f"{label} ({int(score * 100)}%)"
        text_bbox = draw_canvas.textbbox((x0, y0 - 18), label_text)
        draw_overlay.rectangle(
            [text_bbox[0] - 3, text_bbox[1] - 2, text_bbox[2] + 3, text_bbox[3] + 2],
            fill=(10, 15, 29, 210),
            outline=stroke_color,
            width=1
        )
        draw_overlay.text((x0, y0 - 18), label_text, fill=(248, 250, 252, 255))

    # Composite translucent overlay with canvas
    result = Image.alpha_composite(canvas, overlay)
    return result.convert("RGB")


def create_segmentation_overlay(
    image: Image.Image,
    mask_array: np.ndarray,
    color_hex: str = "#00F0FF",
    alpha: float = 0.45
) -> Image.Image:
    """
    Overlay a binary or continuous 2D mask on the base satellite image.
    """
    base = image.copy().convert("RGBA")
    width, height = base.size

    # Resize mask if needed
    if mask_array.shape != (height, width):
        mask_img = Image.fromarray((mask_array * 255).astype(np.uint8))
        mask_img = mask_img.resize((width, height), resample=Image.Resampling.NEAREST)
        mask_norm = np.array(mask_img) / 255.0
    else:
        mask_norm = mask_array.astype(float)
        if mask_norm.max() > 1.0:
            mask_norm /= 255.0

    rgb = ImageColor.getrgb(color_hex)
    colored_mask = np.zeros((height, width, 4), dtype=np.uint8)
    colored_mask[:, :, 0] = rgb[0]
    colored_mask[:, :, 1] = rgb[1]
    colored_mask[:, :, 2] = rgb[2]
    colored_mask[:, :, 3] = (mask_norm * alpha * 255).astype(np.uint8)

    overlay_img = Image.fromarray(colored_mask, mode="RGBA")
    composite = Image.alpha_composite(base, overlay_img)
    return composite.convert("RGB")


def create_change_heatmap(
    image_a: Image.Image,
    image_b: Image.Image,
    sensitivity: float = 1.0
) -> Tuple[Image.Image, Image.Image]:
    """
    Generate synthetic bi-temporal difference heatmap and high-contrast change overlay.
    Returns (heatmap_image, composite_overlay_image).
    """
    # Resize to match
    size = image_a.size
    img_b_resized = image_b.copy().resize(size)

    arr_a = np.array(image_a.convert("RGB"), dtype=np.float32)
    arr_b = np.array(img_b_resized.convert("RGB"), dtype=np.float32)

    # Compute color difference
    diff = np.sqrt(np.sum((arr_b - arr_a) ** 2, axis=2))
    diff_norm = (diff - diff.min()) / (diff.max() - diff.min() + 1e-5)
    diff_norm = np.clip(diff_norm * sensitivity, 0.0, 1.0)

    # Synthetic heatmap coloring: deep blue (low/no change) to cyan, yellow, bright coral red (major change)
    h, w = diff_norm.shape
    heatmap_arr = np.zeros((h, w, 3), dtype=np.uint8)

    # Map scalar to color
    val = diff_norm
    r = np.clip((val - 0.5) * 2.0 * 255, 0, 255).astype(np.uint8)
    g = np.clip((1.0 - np.abs(val - 0.5) * 2.0) * 230, 0, 230).astype(np.uint8)
    b = np.clip((0.5 - val) * 2.0 * 255, 0, 255).astype(np.uint8)

    heatmap_arr[:, :, 0] = r
    heatmap_arr[:, :, 1] = g
    heatmap_arr[:, :, 2] = b

    heatmap_img = Image.fromarray(heatmap_arr, mode="RGB")

    # Composite overlay on post-event image B
    base = img_b_resized.convert("RGBA")
    mask_high_change = (diff_norm > 0.42).astype(np.float32)
    overlay = np.zeros((h, w, 4), dtype=np.uint8)
    overlay[:, :, 0] = 244  # Rose red for changed areas
    overlay[:, :, 1] = 63
    overlay[:, :, 2] = 94
    overlay[:, :, 3] = (mask_high_change * 160).astype(np.uint8)

    overlay_img = Image.fromarray(overlay, mode="RGBA")
    composite = Image.alpha_composite(base, overlay_img).convert("RGB")

    return heatmap_img, composite


def generate_mock_geospatial_metadata(
    filename: str,
    sensor_type: str = "Optical (Sentinel-2)",
    img_size: Tuple[int, int] = (1024, 1024)
) -> Dict[str, Any]:
    """Generate realistic geospatial telemetry metadata for remote sensing display."""
    lat_center = random.uniform(12.5, 28.5)
    lon_center = random.uniform(73.0, 85.0)
    delta = 0.04

    return {
        "filename": filename,
        "crs": "EPSG:4326 (WGS 84 / Geographic)",
        "projection": "UTM Zone 43N / Transverse Mercator",
        "bounds": {
            "north": f"{lat_center + delta:.4f}° N",
            "south": f"{lat_center - delta:.4f}° N",
            "east": f"{lon_center + delta:.4f}° E",
            "west": f"{lon_center - delta:.4f}° E"
        },
        "ground_sample_distance": "0.50 m/pixel",
        "dimensions": f"{img_size[0]} × {img_size[1]} px",
        "sensor": sensor_type,
        "spectral_bands": "Band 2 (Blue), Band 3 (Green), Band 4 (Red), Band 8 (NIR)" if "Optical" in sensor_type else "C-Band SAR (VV + VH Dual-Pol)",
        "cloud_cover": "0.8% (Analysis-grade clear)" if "Optical" in sensor_type else "N/A (SAR Cloud-Penetrating)",
        "radiometric_resolution": "16-bit Unsigned Integer",
        "data_provider": "ESA Copernicus / ISRO NRSC Open Access"
    }


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    """Convert PIL image to byte buffer for download."""
    buf = io.BytesIO()
    image.save(buf, format=format)
    return buf.getvalue()
