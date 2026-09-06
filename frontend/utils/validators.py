"""
SatQuery AI - Input and Query Validators
"""

from typing import Tuple, Optional, Any
import os
import config.settings as cfg


def validate_file_format(filename: str) -> Tuple[bool, Optional[str]]:
    """Check if the uploaded file extension is supported."""
    if not filename:
        return False, "No file provided."
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in cfg.SUPPORTED_EXTENSIONS:
        supported_str = ", ".join(cfg.SUPPORTED_EXTENSIONS)
        return False, f"Unsupported format '{ext}'. Supported formats: {supported_str}"
    
    return True, None


def validate_images(image_a: Any, image_b: Any, mode: str) -> Tuple[bool, Optional[str]]:
    """Validate that the necessary images are provided for the selected mode."""
    if mode in (cfg.MODE_SINGLE, cfg.MODE_AUTO):
        if image_a is None:
            return False, "Please upload at least one satellite image to begin analysis."
    
    elif mode == cfg.MODE_COMPARE:
        if image_a is None and image_b is None:
            return False, "Bi-temporal change detection requires two satellite images (Date A and Date B)."
        if image_a is None:
            return False, "Missing initial baseline image (Date A). Please upload Image A."
        if image_b is None:
            return False, "Missing comparison image (Date B). Temporal comparison requires two compatible images."
    
    elif mode == cfg.MODE_OPTICAL_SAR:
        if image_a is None and image_b is None:
            return False, "Optical + SAR multimodal analysis requires both an Optical RGB image and a SAR radar image."
        if image_a is None:
            return False, "Missing Optical satellite image. Please upload multispectral/RGB imagery."
        if image_b is None:
            return False, "Missing SAR image. Optical + SAR analysis requires Synthetic Aperture Radar imagery."
            
    return True, None


def validate_query(query: str) -> Tuple[bool, Optional[str]]:
    """Validate natural language query."""
    clean = query.strip() if query else ""
    if not clean:
        return False, "Please enter a natural-language question about your satellite imagery."
    if len(clean) < 4:
        return False, "Query is too brief. Please enter a specific question (e.g., 'Where are the buildings?')."
    return True, None


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
