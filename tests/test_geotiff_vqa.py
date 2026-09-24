import numpy as np
import rasterio
from rasterio.transform import from_origin

from models.vqa.inference import run_vqa


IMAGE_PATH = "tests/test_satellite.tif"


# Create a small 3-band satellite-like image
width = 256
height = 256

data = np.zeros((3, height, width), dtype=np.uint16)

# Red band
data[0] = np.random.randint(100, 5000, (height, width))

# Green band
data[1] = np.random.randint(100, 5000, (height, width))

# Blue band
data[2] = np.random.randint(100, 5000, (height, width))


with rasterio.open(
    IMAGE_PATH,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=3,
    dtype="uint16",
    crs="EPSG:4326",
    transform=from_origin(73.8, 18.6, 0.0001, 0.0001),
) as dst:
    dst.write(data)


print("Synthetic GeoTIFF created:", IMAGE_PATH)


# Run SatQuery VQA
result = run_vqa(
    image_path=IMAGE_PATH,
    query="What is visible in this image?"
)


print("\n===== GEOTIFF VQA TEST =====")
print("Success:", result["success"])
print("Answer:", result["answer"])
print("Confidence:", result["confidence"])
print("Error:", result["error"])
print("============================")