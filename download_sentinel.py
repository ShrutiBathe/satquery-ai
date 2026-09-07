import os
import pystac_client
import planetary_computer
import rasterio
from rasterio.windows import Window
import numpy as np

# --------------------------------------------------
# Planetary Computer
# --------------------------------------------------

CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

SCENE_ID = "S2B_MSIL2A_20260907T024519_R132_T51UVR_20260907T045612"

print("Connecting to Planetary Computer...")
catalog = pystac_client.Client.open(
    CATALOG_URL,
    modifier=planetary_computer.sign_inplace,
)

# --------------------------------------------------
# Find the exact Sentinel-2 scene
# --------------------------------------------------

print("Finding Sentinel-2 scene...")

search = catalog.search(
    collections=["sentinel-2-l2a"],
    ids=[SCENE_ID],
)

items = list(search.items())

if not items:
    raise RuntimeError("Scene not found.")

item = items[0]

print("Scene found:")
print(item.id)

print("\nAvailable assets:")
print(list(item.assets.keys()))

# --------------------------------------------------
# Get RGB bands
# --------------------------------------------------

bands = {
    "B02": "blue",
    "B03": "green",
    "B04": "red",
}

for band in bands:
    if band not in item.assets:
        raise RuntimeError(f"{band} not found in scene assets.")

# --------------------------------------------------
# Open Blue band to determine a small test area
# --------------------------------------------------

print("\nOpening satellite data...")

blue_url = item.assets["B02"].href

with rasterio.open(blue_url) as src:

    print("CRS:", src.crs)
    print("Image size:", src.width, "x", src.height)
    print("Resolution:", src.res)

    # Take a 1024 x 1024 pixel area from the center
    size = 1024

    col = max(0, (src.width - size) // 2)
    row = max(0, (src.height - size) // 2)

    window = Window(col, row, size, size)

    profile = src.profile.copy()
    profile.update(
        width=size,
        height=size,
        count=3,
        dtype="uint16",
        compress="deflate",
        driver="GTiff",
    )

# --------------------------------------------------
# Read B02, B03, B04
# --------------------------------------------------

print("\nReading B02, B03, B04...")

arrays = []

for band in ["B04", "B03", "B02"]:

    print("Reading", band)

    url = item.assets[band].href

    with rasterio.open(url) as src:
        data = src.read(1, window=window)

        arrays.append(data)

# --------------------------------------------------
# Create RGB GeoTIFF
# --------------------------------------------------

rgb = np.stack(arrays)

os.makedirs("data", exist_ok=True)

output = "data/sentinel2_rgb.tif"

profile.update(
    transform=rasterio.open(blue_url).window_transform(window)
)

with rasterio.open(output, "w", **profile) as dst:
    dst.write(rgb)

print("\n===================================")
print("SUCCESS!")
print("RGB GeoTIFF created:")
print(output)
print("===================================")