import os
from datetime import datetime, timedelta

import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform_bounds
from pystac_client import Client
import planetary_computer


# ============================================================
# CONFIG
# ============================================================

NUM_SCENES = 5
PATCH_SIZE = 1024

OUTPUT_DIR = "data/scenes"

# Start around the location of our current successful scene.
# We will search nearby Sentinel-2 acquisitions.
REFERENCE_OPTICAL = "data/sentinel2_rgb.tif"

PC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


# ============================================================
# HELPERS
# ============================================================

def save_window(asset_url, bounds, output_path, band_index=1):
    """
    Read a spatial window from a remote COG and save it locally.
    """

    with rasterio.open(asset_url) as src:

        sar_bounds = transform_bounds(
            "EPSG:32651",
            src.crs,
            *bounds
        )

        left, bottom, right, top = sar_bounds

        window = rasterio.windows.from_bounds(
            left,
            bottom,
            right,
            top,
            transform=src.transform
        )

        window = window.round_offsets().round_lengths()

        data = src.read(
            band_index,
            window=window
        )

        profile = src.profile.copy()

        profile.update(
            {
                "driver": "GTiff",
                "height": data.shape[0],
                "width": data.shape[1],
                "count": 1,
                "dtype": data.dtype,
                "compress": "deflate",
            }
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data, 1)

        return data.shape


def find_sar_scene(
    catalog,
    optical_bounds_wgs84,
    target_date
):
    """
    Find the closest Sentinel-1 RTC scene covering
    the optical area.
    """

    start_date = target_date - timedelta(days=30)
    end_date = target_date + timedelta(days=30)

    search = catalog.search(
        collections=["sentinel-1-rtc"],
        intersects={
            "type": "Polygon",
            "coordinates": [[
                [optical_bounds_wgs84[0], optical_bounds_wgs84[1]],
                [optical_bounds_wgs84[2], optical_bounds_wgs84[1]],
                [optical_bounds_wgs84[2], optical_bounds_wgs84[3]],
                [optical_bounds_wgs84[0], optical_bounds_wgs84[3]],
                [optical_bounds_wgs84[0], optical_bounds_wgs84[1]],
            ]]
        },
        datetime=f"{start_date.isoformat()}/{end_date.isoformat()}",
    )

    scenes = list(search.get_items())

    if not scenes:
        return None

    scenes.sort(
        key=lambda item: abs(
            item.datetime.replace(tzinfo=None) -
            target_date
        )
    )

    return scenes[0]


# ============================================================
# CONNECT TO PLANETARY COMPUTER
# ============================================================

print("=" * 70)
print("SATQUERY MULTI-SCENE DATASET DOWNLOADER")
print("=" * 70)

catalog = Client.open(
    PC_URL,
    modifier=planetary_computer.sign_inplace
)


# ============================================================
# GET REFERENCE LOCATION
# ============================================================

with rasterio.open(REFERENCE_OPTICAL) as src:

    reference_bounds = src.bounds
    reference_crs = src.crs

    reference_wgs84 = transform_bounds(
        reference_crs,
        "EPSG:4326",
        *reference_bounds
    )

print("\nReference location:")
print("WGS84 bounds:", reference_wgs84)


# ============================================================
# FIND SENTINEL-2 SCENES
# ============================================================

reference_date = datetime(
    2026,
    9,
    7
)

search_start = reference_date - timedelta(days=180)
search_end = reference_date + timedelta(days=30)

search = catalog.search(
    collections=["sentinel-2-l2a"],
    intersects={
        "type": "Polygon",
        "coordinates": [[
            [reference_wgs84[0], reference_wgs84[1]],
            [reference_wgs84[2], reference_wgs84[1]],
            [reference_wgs84[2], reference_wgs84[3]],
            [reference_wgs84[0], reference_wgs84[3]],
            [reference_wgs84[0], reference_wgs84[1]],
        ]]
    },
    datetime=f"{search_start.isoformat()}/{search_end.isoformat()}",
    query={
        "eo:cloud_cover": {
            "lt": 30
        }
    }
)

sentinel2_scenes = list(search.get_items())


print("\nSentinel-2 scenes found:", len(sentinel2_scenes))


# ============================================================
# SORT BY DATE
# ============================================================

sentinel2_scenes.sort(
    key=lambda item: abs(
        item.datetime.replace(tzinfo=None) -
        reference_date
    )
)


# Remove duplicate acquisition dates
selected_s2 = []

seen_dates = set()

for scene in sentinel2_scenes:

    date_key = scene.datetime.date()

    if date_key not in seen_dates:

        selected_s2.append(scene)
        seen_dates.add(date_key)

    if len(selected_s2) >= NUM_SCENES:
        break


print("\nSelected Sentinel-2 scenes:")

for i, scene in enumerate(selected_s2):

    print(
        f"{i + 1}: "
        f"{scene.id} | "
        f"{scene.datetime} | "
        f"cloud={scene.properties.get('eo:cloud_cover')}"
    )


# ============================================================
# PROCESS EACH SCENE
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


for scene_number, s2_scene in enumerate(
    selected_s2,
    start=1
):

    print("\n" + "=" * 70)
    print(
        f"PROCESSING SCENE {scene_number}/{len(selected_s2)}"
    )
    print("=" * 70)

    print("Sentinel-2:")
    print(s2_scene.id)

    scene_dir = os.path.join(
        OUTPUT_DIR,
        f"scene_{scene_number:03d}"
    )

    os.makedirs(
        scene_dir,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Sentinel-2 assets
    # --------------------------------------------------------

    assets = s2_scene.assets

    b02 = assets["B02"].href
    b03 = assets["B03"].href
    b04 = assets["B04"].href


    # --------------------------------------------------------
    # Read a 1024x1024 patch from the center of the scene
    # --------------------------------------------------------

    with rasterio.open(b02) as src:

        width = src.width
        height = src.height

        center_col = width // 2
        center_row = height // 2

        col_off = center_col - PATCH_SIZE // 2
        row_off = center_row - PATCH_SIZE // 2

        window = Window(
            col_off,
            row_off,
            PATCH_SIZE,
            PATCH_SIZE
        )

        transform = src.window_transform(window)

        blue = src.read(
            1,
            window=window
        )

    with rasterio.open(b03) as src:

        green = src.read(
            1,
            window=window
        )

    with rasterio.open(b04) as src:

        red = src.read(
            1,
            window=window
        )


    # --------------------------------------------------------
    # Create RGB visual image
    # --------------------------------------------------------

    rgb = np.stack(
        [
            red,
            green,
            blue
        ],
        axis=0
    ).astype(np.float32)


    visual = np.zeros_like(
        rgb,
        dtype=np.uint8
    )


    for band in range(3):

        values = rgb[band]

        valid = (
            np.isfinite(values) &
            (values > 0)
        )

        if np.any(valid):

            low = np.percentile(
                values[valid],
                2
            )

            high = np.percentile(
                values[valid],
                98
            )

            if high > low:

                stretched = np.clip(
                    (values - low) /
                    (high - low) *
                    255,
                    0,
                    255
                )

                visual[band] = (
                    stretched.astype(np.uint8)
                )


    optical_path = os.path.join(
        scene_dir,
        "optical.tif"
    )


    with rasterio.open(
        optical_path,
        "w",
        driver="GTiff",
        height=PATCH_SIZE,
        width=PATCH_SIZE,
        count=3,
        dtype="uint8",
        crs="EPSG:32651",
        transform=transform,
        compress="deflate"
    ) as dst:

        dst.write(visual)


    # --------------------------------------------------------
    # Optical bounds
    # --------------------------------------------------------

    optical_bounds = rasterio.transform.array_bounds(
        PATCH_SIZE,
        PATCH_SIZE,
        transform
    )

    left, bottom, right, top = optical_bounds


    optical_bounds_wgs84 = transform_bounds(
        "EPSG:32651",
        "EPSG:4326",
        left,
        bottom,
        right,
        top
    )


    # --------------------------------------------------------
    # Find matching Sentinel-1
    # --------------------------------------------------------

    s1_scene = find_sar_scene(
        catalog,
        optical_bounds_wgs84,
        s2_scene.datetime.replace(tzinfo=None)
    )


    if s1_scene is None:

        print(
            "WARNING: No Sentinel-1 scene found."
        )

        continue


    print("\nSentinel-1:")
    print(s1_scene.id)
    print("Acquisition:", s1_scene.datetime)


    # --------------------------------------------------------
    # Get VV/VH
    # --------------------------------------------------------

    s1_assets = s1_scene.assets

    vv_url = s1_assets["vv"].href
    vh_url = s1_assets["vh"].href


    # --------------------------------------------------------
    # Download matching SAR patches
    # --------------------------------------------------------

    vv_path = os.path.join(
        scene_dir,
        "vv.tif"
    )

    vh_path = os.path.join(
        scene_dir,
        "vh.tif"
    )


    print("Extracting VV...")

    save_window(
        vv_url,
        optical_bounds,
        vv_path
    )


    print("Extracting VH...")

    save_window(
        vh_url,
        optical_bounds,
        vh_path
    )


    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata_path = os.path.join(
        scene_dir,
        "metadata.txt"
    )

    with open(
        metadata_path,
        "w"
    ) as f:

        f.write(
            f"Sentinel-2 ID: {s2_scene.id}\n"
        )

        f.write(
            f"Sentinel-2 Date: {s2_scene.datetime}\n"
        )

        f.write(
            f"Sentinel-2 Cloud Cover: "
            f"{s2_scene.properties.get('eo:cloud_cover')}\n"
        )

        f.write(
            f"Sentinel-1 ID: {s1_scene.id}\n"
        )

        f.write(
            f"Sentinel-1 Date: {s1_scene.datetime}\n"
        )

        f.write(
            f"Optical Bounds: {optical_bounds}\n"
        )

        f.write(
            f"Optical WGS84 Bounds: "
            f"{optical_bounds_wgs84}\n"
        )


    print("\nScene saved:")
    print(scene_dir)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("MULTI-SCENE DATASET DOWNLOAD COMPLETE")
print("=" * 70)

print("\nDataset location:")
print(OUTPUT_DIR)