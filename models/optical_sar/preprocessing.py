import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np


def reproject_to_reference(
    source_path,
    reference_path,
    output_path,
    resampling=Resampling.bilinear
):
    """
    Reproject a source raster so that it matches
    the CRS, resolution, transform and dimensions
    of the reference raster.
    """

    with rasterio.open(reference_path) as reference:

        reference_crs = reference.crs
        reference_transform = reference.transform
        reference_width = reference.width
        reference_height = reference.height

        profile = reference.profile.copy()

    with rasterio.open(source_path) as source:

        print("Source CRS:", source.crs)
        print("Reference CRS:", reference_crs)

        profile.update(
            driver="GTiff",
            width=reference_width,
            height=reference_height,
            crs=reference_crs,
            transform=reference_transform,
            count=source.count,
            dtype=source.dtypes[0],
            compress="deflate"
        )

        with rasterio.open(output_path, "w", **profile) as destination:

            for band in range(1, source.count + 1):

                reproject(
                    source=rasterio.band(source, band),
                    destination=rasterio.band(destination, band),
                    src_transform=source.transform,
                    src_crs=source.crs,
                    dst_transform=reference_transform,
                    dst_crs=reference_crs,
                    resampling=resampling
                )

    print("Reprojection complete:")
    print(output_path)


def normalize_sar(data):
    """
    Normalize Sentinel-1 SAR data to 0-1.

    Sentinel-1 RTC rasters may contain -32768 as NoData.
    NoData pixels are excluded from percentile calculation.
    """

    data = data.astype(np.float32)

    # Sentinel-1 NoData value
    valid = np.isfinite(data) & (data > -30000)

    if not np.any(valid):
        raise ValueError(
            "SAR image contains no valid pixels."
        )

    minimum = np.percentile(
        data[valid],
        2
    )

    maximum = np.percentile(
        data[valid],
        98
    )

    # Avoid division by zero
    if maximum <= minimum:
        raise ValueError(
            "SAR image has insufficient valid value variation."
        )

    normalized = np.zeros_like(data)

    clipped = np.clip(
        data[valid],
        minimum,
        maximum
    )

    normalized[valid] = (
        (clipped - minimum)
        / (maximum - minimum)
    )

    # Keep NoData pixels at zero
    normalized[~valid] = 0.0

    return normalized


def load_sar(path):

    with rasterio.open(path) as src:
        data = src.read(1)

    return normalize_sar(data)