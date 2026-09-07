import rasterio
import numpy as np

INPUT = "data/sentinel2_rgb.tif"
OUTPUT = "data/sentinel2_rgb_visual.tif"


def stretch_band(band):
    # Remove NoData / black pixels
    valid = band[band > 0]

    low = np.percentile(valid, 2)
    high = np.percentile(valid, 98)

    print(f"Stretch: {low:.2f} -> {high:.2f}")

    band = np.clip(band, low, high)

    # Convert to 0-255
    band = ((band - low) / (high - low) * 255)

    return band.astype(np.uint8)


print("Opening satellite GeoTIFF...")

with rasterio.open(INPUT) as src:

    print("Size:", src.width, "x", src.height)
    print("Bands:", src.count)
    print("CRS:", src.crs)

    # Our RGB GeoTIFF:
    # Band 1 = B04 Red
    # Band 2 = B03 Green
    # Band 3 = B02 Blue

    red = src.read(1)
    green = src.read(2)
    blue = src.read(3)

    print("\nApplying contrast stretch...")

    red = stretch_band(red)
    green = stretch_band(green)
    blue = stretch_band(blue)

    rgb = np.stack([red, green, blue])

    profile = src.profile.copy()

    profile.update(
        driver="GTiff",
        dtype="uint8",
        count=3,
        compress="deflate",
        photometric="RGB"
    )

    with rasterio.open(OUTPUT, "w", **profile) as dst:
        dst.write(rgb)


print("\n===================================")
print("SUCCESS!")
print("Visual RGB GeoTIFF created:")
print(OUTPUT)
print("===================================")