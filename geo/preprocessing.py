from pathlib import Path

import numpy as np
from PIL import Image
import rasterio
from rasterio.warp import reproject, Resampling

from .validation import validate_images
from .bands import select_rgb_bands
OUTPUT_DIR = Path("outputs/processed")

# Target size for model-ready images.
# Set to None to keep the original size.
TARGET_SIZE = (100, 150)


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

def preprocess_images(
    image_paths: list[str],
    task: str
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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    task = task.lower().strip().replace("-", "_").replace(" ", "_")

    processed_paths = []

    try:

                # =====================================================
        # CHANGE DETECTION
        # =====================================================

        if task == "change_detection":

            before_path = Path(image_paths[0])
            after_path = Path(image_paths[1])

            # Change detection requires GeoTIFF images
            if (
                before_path.suffix.lower() not in {".tif", ".tiff"}
                or after_path.suffix.lower() not in {".tif", ".tiff"}
            ):
                return {
                    "success": False,
                    "image_paths": [],
                    "metadata": {},
                    "error": (
                        "Change detection requires two "
                        "GeoTIFF/TIFF images."
                    )
                }

            # Output files
            output_before = OUTPUT_DIR / "before.tif"
            output_after = OUTPUT_DIR / "after.tif"

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

            optical_path = Path(image_paths[0])
            sar_path = Path(image_paths[1])

            optical_data, optical_metadata = _read_image(
                str(optical_path)
            )

            sar_data, sar_metadata = _read_image(
                str(sar_path)
            )

            # Resize both images to the common target size
            if TARGET_SIZE is not None:

                optical_data = _resize_data(
                    optical_data,
                    TARGET_SIZE,
                    band_first=optical_path.suffix.lower()
                    in {".tif", ".tiff"}
                )

                sar_data = _resize_data(
                    sar_data,
                    TARGET_SIZE,
                    band_first=sar_path.suffix.lower()
                    in {".tif", ".tiff"}
                )

            optical_output = OUTPUT_DIR / "optical.tif"
            sar_output = OUTPUT_DIR / "sar.tif"

            if optical_path.suffix.lower() in {".tif", ".tiff"}:
                _save_geotiff(
                    optical_data,
                    optical_output,
                    optical_metadata
                )
            else:
                _save_rgb_image(
                    optical_data,
                    optical_output.with_suffix(".png"),
                    band_first=False
                )
                optical_output = optical_output.with_suffix(".png")

            if sar_path.suffix.lower() in {".tif", ".tiff"}:
                _save_geotiff(
                    sar_data,
                    sar_output,
                    sar_metadata
                )
            else:
                _save_rgb_image(
                    sar_data,
                    sar_output.with_suffix(".png"),
                    band_first=False
                )
                sar_output = sar_output.with_suffix(".png")

            return {
                "success": True,
                "image_paths": [
                    str(optical_output),
                    str(sar_output)
                ],
                  "metadata": {
                    "optical": {
                        **optical_metadata,
                        "width": TARGET_SIZE[1],
                        "height": TARGET_SIZE[0]
                    },
                    "sar": {
                        **sar_metadata,
                        "width": TARGET_SIZE[1],
                        "height": TARGET_SIZE[0]
                    },
                    "paired": True
                },
                "error": None
            }
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

            output_path = OUTPUT_DIR / "image1.png"

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

            output_path = OUTPUT_DIR / "image1.tif"

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

        output_path = OUTPUT_DIR / "image1.png"

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
