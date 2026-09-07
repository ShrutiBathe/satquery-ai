import os
from datetime import datetime, timezone

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds
from pystac_client import Client
import planetary_computer


# ============================================================
# CONFIGURATION
# ============================================================

OPTICAL_PATH = "data/sentinel2_rgb.tif"

OUTPUT_DIR = "data/sar"

VV_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "sentinel1_vv.tif"
)

VH_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "sentinel1_vh.tif"
)

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

COLLECTION = "sentinel-1-rtc"


# Search around the Sentinel-2 acquisition date.
# We allow several days because Sentinel-1 and Sentinel-2
# do not necessarily acquire the same location on the same day.
DATE_WINDOW_DAYS = 30


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# READ EXACT SENTINEL-2 PATCH BOUNDS
# ============================================================

print("=" * 60)
print("SENTINEL-1 / SENTINEL-2 SPATIAL MATCHING")
print("=" * 60)

print("\nReading Sentinel-2 reference image...")

with rasterio.open(OPTICAL_PATH) as optical:

    optical_crs = optical.crs
    optical_bounds = optical.bounds
    optical_width = optical.width
    optical_height = optical.height

    print("Optical CRS:", optical_crs)
    print("Optical size:", optical_width, "x", optical_height)
    print("Optical bounds:", optical_bounds)

    # Convert exact optical patch bounds to WGS84.
    lon_min, lat_min, lon_max, lat_max = transform_bounds(
        optical_crs,
        "EPSG:4326",
        optical_bounds.left,
        optical_bounds.bottom,
        optical_bounds.right,
        optical_bounds.top,
        densify_pts=21
    )


print("\nExact optical patch in WGS84:")

print("Longitude:", lon_min, "to", lon_max)
print("Latitude :", lat_min, "to", lat_max)


# ============================================================
# CREATE EXACT AOI GEOMETRY
# ============================================================

aoi = {
    "type": "Polygon",
    "coordinates": [[
        [lon_min, lat_min],
        [lon_max, lat_min],
        [lon_max, lat_max],
        [lon_min, lat_max],
        [lon_min, lat_min]
    ]]
}


# ============================================================
# OPEN PLANETARY COMPUTER STAC
# ============================================================

print("\nConnecting to Microsoft Planetary Computer...")

catalog = Client.open(
    STAC_URL,
    modifier=planetary_computer.sign_inplace
)

print("Connected.")


# ============================================================
# DETERMINE OPTICAL DATE
# ============================================================

# We know the Sentinel-2 scene date from the project.
OPTICAL_DATE = datetime(
    2026,
    9,
    7,
    tzinfo=timezone.utc
)

start_date = OPTICAL_DATE.replace(
    day=OPTICAL_DATE.day
)

from datetime import timedelta

search_start = OPTICAL_DATE - timedelta(
    days=DATE_WINDOW_DAYS
)

search_end = OPTICAL_DATE + timedelta(
    days=DATE_WINDOW_DAYS
)

datetime_range = (
    search_start.isoformat()
    + "/"
    + search_end.isoformat()
)

print("\nSentinel-1 search period:")
print(datetime_range)


# ============================================================
# SEARCH SENTINEL-1 USING EXACT OPTICAL AOI
# ============================================================

print("\nSearching Sentinel-1 RTC scenes...")
print("Using exact Sentinel-2 patch footprint.")

search = catalog.search(
    collections=[COLLECTION],
    intersects=aoi,
    datetime=datetime_range
)

items = list(search.items())


print("\nSentinel-1 scenes found:", len(items))


if len(items) == 0:

    raise RuntimeError(
        "\nNo Sentinel-1 scenes overlap the Sentinel-2 patch "
        "within the selected date range."
    )


# ============================================================
# DISPLAY CANDIDATES
# ============================================================

print("\nCandidate Sentinel-1 scenes:")

for i, item in enumerate(items):

    item_datetime = item.datetime

    if item_datetime is not None:

        difference = abs(
            (item_datetime - OPTICAL_DATE).total_seconds()
        ) / 86400

        print(
            f"{i}: {item.id}"
            f" | date={item_datetime}"
            f" | difference={difference:.2f} days"
        )

    else:

        print(
            f"{i}: {item.id}"
            " | date=unknown"
        )


# ============================================================
# SELECT CLOSEST TEMPORAL SCENE
# ============================================================

def temporal_distance(item):

    if item.datetime is None:
        return float("inf")

    return abs(
        (item.datetime - OPTICAL_DATE).total_seconds()
    )


items.sort(
    key=temporal_distance
)

item = items[0]


print("\nSelected Sentinel-1 scene:")
print(item.id)

print("Acquisition time:")
print(item.datetime)

print("\nAvailable assets:")
print(list(item.assets.keys()))


# ============================================================
# FIND VV / VH ASSETS
# ============================================================

vv_asset = None
vh_asset = None


for name, asset in item.assets.items():

    name_lower = name.lower()

    if vv_asset is None and (
        name_lower == "vv"
        or name_lower.endswith("/vv")
        or name_lower.endswith("_vv")
    ):
        vv_asset = asset

    if vh_asset is None and (
        name_lower == "vh"
        or name_lower.endswith("/vh")
        or name_lower.endswith("_vh")
    ):
        vh_asset = asset


# Fallback: search asset names containing vv/vh.
if vv_asset is None:

    for name, asset in item.assets.items():

        if "vv" in name.lower():

            vv_asset = asset
            break


if vh_asset is None:

    for name, asset in item.assets.items():

        if "vh" in name.lower():

            vh_asset = asset
            break


if vv_asset is None:

    raise RuntimeError(
        "Could not find VV asset in Sentinel-1 item."
    )


if vh_asset is None:

    raise RuntimeError(
        "Could not find VH asset in Sentinel-1 item."
    )


print("\nVV asset found:")
print(vv_asset.href)

print("\nVH asset found:")
print(vh_asset.href)


# ============================================================
# DOWNLOAD EXACT OPTICAL AREA FROM SAR
# ============================================================

def download_sar_patch(asset, output_path, band_name):

    print("\n----------------------------------------")
    print("Processing", band_name)
    print("----------------------------------------")

    print("Opening SAR COG...")

    with rasterio.open(asset.href) as src:

        print("SAR CRS:", src.crs)
        print("SAR size:", src.width, "x", src.height)
        print("SAR bounds:", src.bounds)

        # Transform exact optical bounds into SAR CRS.
        sar_left, sar_bottom, sar_right, sar_top = transform_bounds(
            optical_crs,
            src.crs,
            optical_bounds.left,
            optical_bounds.bottom,
            optical_bounds.right,
            optical_bounds.top,
            densify_pts=21
        )

        print("\nRequested SAR bounds:")
        print(
            sar_left,
            sar_bottom,
            sar_right,
            sar_top
        )

        # Check actual geographic overlap.
        overlap_left = max(
            sar_left,
            src.bounds.left
        )

        overlap_bottom = max(
            sar_bottom,
            src.bounds.bottom
        )

        overlap_right = min(
            sar_right,
            src.bounds.right
        )

        overlap_top = min(
            sar_top,
            src.bounds.top
        )

        if (
            overlap_left >= overlap_right
            or overlap_bottom >= overlap_top
        ):

            raise RuntimeError(
                f"{band_name} does not overlap "
                "the Sentinel-2 patch."
            )

        print("\nSpatial overlap confirmed.")

        # Convert requested geographic area into a raster window.
        window = from_bounds(
            sar_left,
            sar_bottom,
            sar_right,
            sar_top,
            src.transform
        )

        # Round and clamp window.
        window = window.round_offsets().round_lengths()

        print("Reading SAR window:")
        print(window)

        data = src.read(
            1,
            window=window
        )

        print("Raw SAR shape:", data.shape)
        print("Raw SAR dtype:", data.dtype)

        # ----------------------------------------------------
        # IMPORTANT:
        # Save the actual SAR values, not a visual stretch.
        # ----------------------------------------------------

        profile = src.profile.copy()

        profile.update(
            driver="GTiff",
            height=data.shape[0],
            width=data.shape[1],
            transform=src.window_transform(window),
            count=1,
            dtype="float32",
            compress="deflate"
        )

        data = data.astype(np.float32)

        with rasterio.open(
            output_path,
            "w",
            **profile
        ) as dst:

            dst.write(
                data,
                1
            )

    print("\nSaved:")
    print(output_path)


# ============================================================
# DOWNLOAD VV
# ============================================================

download_sar_patch(
    vv_asset,
    VV_OUTPUT,
    "VV"
)


# ============================================================
# DOWNLOAD VH
# ============================================================

download_sar_patch(
    vh_asset,
    VH_OUTPUT,
    "VH"
)


# ============================================================
# FINAL VERIFICATION
# ============================================================

print("\n" + "=" * 60)
print("SENTINEL-1 DOWNLOAD COMPLETE")
print("=" * 60)


for path in [
    VV_OUTPUT,
    VH_OUTPUT
]:

    with rasterio.open(path) as src:

        data = src.read(1)

        valid = np.isfinite(data)

        print("\n", path)
        print("CRS:", src.crs)
        print(
            "Size:",
            src.width,
            "x",
            src.height
        )
        print("Bounds:", src.bounds)

        if np.any(valid):

            print(
                "Value range:",
                float(np.nanmin(data)),
                "to",
                float(np.nanmax(data))
            )

        else:

            print("WARNING: No valid pixels!")

print("\nDONE.")