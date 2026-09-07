from pathlib import Path

import numpy as np
import rasterio
from PIL import Image


def load_vqa_image(image_path: str):
    """
    Load an image for VQA.

    Supports:
    - JPG / JPEG
    - PNG
    - TIFF / GeoTIFF

    Returns:
        PIL.Image.Image in RGB format
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    suffix = path.suffix.lower()

    # Normal image formats
    if suffix in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        return Image.open(path).convert("RGB")

    # Satellite / GeoTIFF
    if suffix in [".tif", ".tiff"]:
        return load_geotiff_as_rgb(path)

    raise ValueError(
        f"Unsupported image format: {suffix}. "
        "Supported formats: JPG, PNG, TIFF, GeoTIFF, BMP, WEBP."
    )


def load_geotiff_as_rgb(path: Path):
    """
    Convert a GeoTIFF into an RGB PIL image suitable for the VLM.

    Strategy:
    - 3+ bands: use the first 3 bands as RGB
    - 1 band: create a grayscale RGB image
    - 2 bands: use the first band as grayscale
    """

    with rasterio.open(path) as src:

        if src.count >= 3:
            data = src.read([1, 2, 3])

            rgb = np.transpose(data, (1, 2, 0))

        elif src.count == 1:
            data = src.read(1)

            rgb = np.stack([data, data, data], axis=-1)

        else:
            data = src.read(1)

            rgb = np.stack([data, data, data], axis=-1)

    # Convert satellite pixel values to 0-255
    rgb = normalize_to_uint8(rgb)

    return Image.fromarray(rgb, mode="RGB")


def normalize_to_uint8(array):
    """
    Normalize arbitrary satellite pixel values to 0-255.
    """

    array = array.astype(np.float32)

    result = np.zeros_like(array, dtype=np.float32)

    for channel in range(array.shape[-1]):

        band = array[:, :, channel]

        min_val = np.nanpercentile(band, 2)
        max_val = np.nanpercentile(band, 98)

        if max_val <= min_val:
            result[:, :, channel] = 0
            continue

        band = np.clip(band, min_val, max_val)

        result[:, :, channel] = (
            (band - min_val)
            / (max_val - min_val)
            * 255.0
        )

    return result.astype(np.uint8)