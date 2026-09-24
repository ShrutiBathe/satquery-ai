from pathlib import Path

import numpy as np
from PIL import Image
import rasterio
from rasterio.warp import reproject, Resampling

from .validation import validate_images
from .bands import select_rgb_bands
OUTPUT_DIR = Path("outputs/processed")

# Preserve uploaded resolution for evidence and model preprocessing. VQA and
# Grounding perform their own model-side preprocessing; resizing here makes
# the frontend evidence visibly blurry.
import os

# Optional down‑scale dimension for large images.
# If GROUNDING_MAX_DIM is set, images will be resized to a square of that size.
_env_max = os.getenv('GROUNDING_MAX_DIM')
if _env_max and _env_max.isdigit():
    max_dim = int(_env_max)
    TARGET_SIZE = (max_dim, max_dim)
else:
    TARGET_SIZE = None


def _read_image(image_path: str):
    """
    Read an ordinary image or GeoTIFF.

    Returns:
        image_data: NumPy array
        metadata: dictionary containing image/geospatial information
    """

    path = Path(image_path)
    extension = path.suffix.lower()

    # ---------------------------------------------------------
    # GeoTIFF / TIFF
    # ---------------------------------------------------------
    if extension in {".tif", ".tiff"}:

        with rasterio.open(path) as src:

            data = src.read()

            metadata = {
                "width": src.width,
                "height": src.height,
                "bands": src.count,
                "dtype": str(data.dtype),
                "crs": str(src.crs) if src.crs else None,
                "transform": tuple(src.transform),
                "resolution": src.res,
                "bounds": tuple(src.bounds)
            }

        return data, metadata

    # ---------------------------------------------------------
    # PNG / JPEG
    # ---------------------------------------------------------
    image = Image.open(path)

    data = np.array(image)

    if data.ndim == 2:
        channels = 1
    else:
        channels = data.shape[2]

    metadata = {
        "width": image.width,
        "height": image.height,
        "channels": channels,
        "dtype": str(data.dtype)
    }

    return data, metadata

def _save_rgb_image(data, output_path, band_first=False):
    """
    Save an image as PNG.

    band_first=True:
        data shape is (bands, height, width)

    band_first=False:
        data shape is (height, width, channels)
    """

    # ---------------------------------------------------------
    # Convert band-first satellite data to RGB image format
    # ---------------------------------------------------------

    if band_first and data.ndim == 3:

        if data.shape[0] < 3:
            raise ValueError(
                "Satellite image must contain at least 3 bands "
                "for RGB conversion."
            )

        data = data[:3]

        data = np.transpose(
            data,
            (1, 2, 0)
        )

    # ---------------------------------------------------------
    # Convert to uint8
    # ---------------------------------------------------------

    if data.dtype != np.uint8:

        data = data.astype(np.float32)

        min_value = data.min()
        max_value = data.max()

        if max_value > min_value:

            data = (
                (data - min_value)
                / (max_value - min_value)
                * 255
            )

        data = np.clip(
            data,
            0,
            255
        ).astype(np.uint8)

    # ---------------------------------------------------------
    # Save PNG
    # ---------------------------------------------------------

    image = Image.fromarray(data)

    image.save(output_path)

def _resize_data(data, target_size, band_first=False):
    """
    Resize image data.

    For GeoTIFF satellite data:
        band_first=True
        shape = (bands, height, width)

    For normal PNG/JPEG images:
        band_first=False
        shape = (height, width, channels)

    target_size = (height, width)
    """

    target_height, target_width = target_size

    # ---------------------------------------------------------
    # Band-first satellite data
    # Shape: (bands, height, width)
    # ---------------------------------------------------------

    if band_first and data.ndim == 3:

        resized = np.empty(
            (
                data.shape[0],
                target_height,
                target_width
            ),
            dtype=data.dtype
        )

        for band in range(data.shape[0]):

            band_image = Image.fromarray(data[band])

            band_image = band_image.resize(
                (target_width, target_height),
                Image.Resampling.BILINEAR
            )

            resized[band] = np.array(band_image)

        return resized

    # ---------------------------------------------------------
    # Normal RGB / grayscale image
    # Shape: (height, width, channels)
    # ---------------------------------------------------------

    image = Image.fromarray(data)

    image = image.resize(
        (target_width, target_height),
        Image.Resampling.BILINEAR
    )

    return np.array(image)
 
def _align_geotiffs(
    before_path,
    after_path,
    output_before,
    output_after
):
    """
    Align the AFTER GeoTIFF to the BEFORE GeoTIFF grid.
    """

    # Read BEFORE image
    with rasterio.open(before_path) as before:

        before_data = before.read()

        before_crs = before.crs
        before_transform = before.transform
        before_width = before.width
        before_height = before.height

        before_profile = before.profile.copy()
        before_profile.pop("blockxsize", None)
        before_profile.pop("blockysize", None)
        before_profile.pop("tiled", None)

    # Read AFTER image
    with rasterio.open(after_path) as after:

        aligned_after = np.empty(
            (
                after.count,
                before_height,
                before_width
            ),
            dtype=after.dtypes[0]
        )

        # Reproject AFTER to BEFORE grid
        reproject(
            source=after.read(),
            destination=aligned_after,
            src_transform=after.transform,
            src_crs=after.crs,
            dst_transform=before_transform,
            dst_crs=before_crs,
            resampling=Resampling.bilinear
        )

        after_profile = before_profile.copy()

        after_profile.update(
            width=before_width,
            height=before_height,
            transform=before_transform,
            crs=before_crs,
            count=after.count,
            dtype=aligned_after.dtype
        )

    # Save BEFORE
    with rasterio.open(
        output_before,
        "w",
        **before_profile
    ) as dst:

        dst.write(before_data)

    # Save aligned AFTER
    with rasterio.open(
        output_after,
        "w",
        **after_profile
    ) as dst:

        dst.write(aligned_after)

    return {
        "aligned": True,
        "width": before_width,
        "height": before_height,
        "crs": str(before_crs) if before_crs else None
    }       
def _save_geotiff(data, output_path, source_metadata):
    """
    Save multiband GeoTIFF with correct geospatial
    information after resizing.
    """

    height = data.shape[1]
    width = data.shape[2]
    bands = data.shape[0]

    original_width = source_metadata.get(
        "original_width",
        source_metadata["width"]
    )

    original_height = source_metadata.get(
        "original_height",
        source_metadata["height"]
    )

    original_transform = rasterio.Affine(
        *source_metadata["transform"]
    )

    scale_x = original_width / width
    scale_y = original_height / height

    new_transform = original_transform * rasterio.Affine.scale(
        scale_x,
        scale_y
    )

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        width=width,
        height=height,
        count=bands,
        dtype=data.dtype,
        crs=source_metadata["crs"],
        transform=new_transform
    ) as dst:

        dst.write(data)

def preprocess_optical_sar(
    optical_path: str,
    vv_path: str,
    vh_path: str,
) -> dict:
    """Validate the three modality paths without converting their bands."""

    paths = [Path(optical_path), Path(vv_path), Path(vh_path)]
    if any(not path.exists() for path in paths):
        missing = next(path for path in paths if not path.exists())
        return {"success": False, "image_paths": [], "metadata": {}, "error": f"Image file not found: {missing}"}

    if any(path.suffix.lower() not in {".tif", ".tiff"} for path in paths):
        return {
            "success": False,
            "image_paths": [],
            "metadata": {},
            "error": "Optical-SAR requires GeoTIFF/TIFF optical, SAR VV, and SAR VH inputs.",
        }

    try:
        import rasterio

        metadata = {}
        with rasterio.open(paths[0]) as optical, rasterio.open(paths[1]) as vv, rasterio.open(paths[2]) as vh:
            if optical.count < 3:
                raise ValueError("Optical input must contain at least 3 channels.")
            for name, source in (("SAR VV", vv), ("SAR VH", vh)):
                if source.count < 1:
                    raise ValueError(f"{name} input must contain at least one band.")
                if (source.width, source.height) != (optical.width, optical.height):
                    raise ValueError(f"{name} dimensions do not match the optical input.")
                if source.crs != optical.crs:
                    raise ValueError(f"{name} CRS does not match the optical input.")
            metadata = {
                "width": optical.width,
                "height": optical.height,
                "optical_bands": optical.count,
                "vv_bands": vv.count,
                "vh_bands": vh.count,
                "crs": str(optical.crs) if optical.crs else None,
                "paired": True,
            }
        return {"success": True, "image_paths": [str(path) for path in paths], "metadata": metadata, "error": None}
    except Exception as exc:
        return {"success": False, "image_paths": [], "metadata": {}, "error": str(exc)}


def preprocess_images(
    image_paths: list[str],
    task: str,
    output_dir: str | Path | None = None,
) -> dict:

    # ---------------------------------------------------------
    # 1. Validate inputs
    # ---------------------------------------------------------

    validation = validate_images(image_paths, task)

    if not validation["valid"]:
        return {
            "success": False,
            "image_paths": [],
            "metadata": {},
            "error": validation["message"]
        }

    # ---------------------------------------------------------
    # 2. Create output directory
    # ---------------------------------------------------------

    output_root = Path(output_dir) if output_dir is not None else OUTPUT_DIR
    output_root.mkdir(parents=True, exist_ok=True)

    task = task.lower().strip().replace("-", "_").replace(" ", "_")

    processed_paths = []

    try:

                # =====================================================
        # CHANGE DETECTION
        # =====================================================

        if task == "change_detection":

            before_path = Path(image_paths[0])
            after_path = Path(image_paths[1])

            before_is_geotiff = before_path.suffix.lower() in {".tif", ".tiff"}
            after_is_geotiff = after_path.suffix.lower() in {".tif", ".tiff"}

            # GeoTIFF pairs are aligned on their spatial grid. Ordinary
            # image pairs have no CRS/grid to align, so require matching
            # dimensions and let ChangeFormer perform its model resize.
            if not before_is_geotiff or not after_is_geotiff:
                # Non‑GeoTIFF images: ensure they have matching dimensions.
                with Image.open(before_path) as before_image, Image.open(after_path) as after_image:
                    before_size = before_image.size  # (width, height)
                    if after_image.size != before_size:
                        # Resize after‑image to match before‑image dimensions.
                        after_image = after_image.resize(before_size, Image.Resampling.BILINEAR)
                    # Save the (possibly resized) images to the output directory.
                    output_before = output_root / "before.png"
                    output_after = output_root / "after.png"
                    before_image.save(output_before)
                    after_image.save(output_after)

                return {
                    "success": True,
                    "image_paths": [str(output_before), str(output_after)],
                    "metadata": {
                        "aligned": False,
                        "geospatial_alignment": "not applicable",
                        "width": before_size[0],
                        "height": before_size[1],
                    },
                    "error": None,
                }

            # Output files
            output_before = output_root / "before.tif"
            output_after = output_root / "after.tif"

            # Align AFTER image to BEFORE image grid
            alignment = _align_geotiffs(
                before_path,
                after_path,
                output_before,
                output_after
            )

            # Read metadata of aligned images
            _, before_metadata = _read_image(
                str(output_before)
            )

            _, after_metadata = _read_image(
                str(output_after)
            )

            return {
                "success": True,
                "image_paths": [
                    str(output_before),
                    str(output_after)
                ],
                "metadata": {
                    "aligned": alignment["aligned"],
                    "width": alignment["width"],
                    "height": alignment["height"],
                    "crs": alignment["crs"],
                    "before": before_metadata,
                    "after": after_metadata
                },
                "error": None
            }

        
                # =====================================================
        # NORMAL TASKS
        # =====================================================
                # OPTICAL-SAR
        if task == "optical_sar":
            # Ensure three modality images are provided: optical, SAR VV, SAR VH
            if len(image_paths) != 3:
                return {
                    "success": False,
                    "image_paths": [],
                    "metadata": {},
                    "error": "Optical-SAR task requires exactly three image paths (optical, SAR VV, SAR VH).",
                }
            return preprocess_optical_sar(*image_paths)
        data, metadata = _read_image(image_paths[0])

        extension = Path(image_paths[0]).suffix.lower()

        # Apply resizing if a target size is configured
        if TARGET_SIZE is not None:
            data = _resize_data(
                                data,
                                TARGET_SIZE,
                                band_first=extension in {".tif", ".tiff"}
                                )

            metadata["original_width"] = metadata["width"]
            metadata["original_height"] = metadata["height"]

            metadata["width"] = TARGET_SIZE[1]
            metadata["height"] = TARGET_SIZE[0]

        # -----------------------------------------------------
        # Convert multispectral data to RGB
        # for VQA / Grounding
        # -----------------------------------------------------

        if (
            task in {"vqa", "grounding"}
            and extension in {".tif", ".tiff"}
            and data.ndim == 3
        ):
            data = select_rgb_bands(
                data,
                (1, 2, 3)
            )
                # -----------------------------------------------------
        # VQA / Grounding RGB output
        # -----------------------------------------------------

        if task in {"vqa", "grounding"}:

            output_path = output_root / "image1.png"

            _save_rgb_image(
                            data,
                            output_path,
                            band_first=False
                            )

            processed_paths.append(str(output_path))

            metadata["channels"] = 3
            metadata["output_format"] = "RGB"

            return {
                "success": True,
                "image_paths": processed_paths,
                "metadata": metadata,
                "error": None
            }

        # -----------------------------------------------------
        # GeoTIFF
        # -----------------------------------------------------

        if extension in {".tif", ".tiff"}:

            output_path = output_root / "image1.tif"

            _save_geotiff(
                data,
                output_path,
                metadata
            )

            processed_paths.append(str(output_path))

            return {
                "success": True,
                "image_paths": processed_paths,
                "metadata": metadata,
                "error": None
            }

        # -----------------------------------------------------
        # PNG / JPEG
        # -----------------------------------------------------

        output_path = output_root / "image1.png"

        _save_rgb_image(
                        data,
                        output_path,
                        band_first=False
                        )

        processed_paths.append(str(output_path))

        return {
            "success": True,
            "image_paths": processed_paths,
            "metadata": metadata,
            "error": None
        }

    except Exception as e:

        return {
            "success": False,
            "image_paths": [],
            "metadata": {},
            "error": str(e)
        }
