import numpy as np
import rasterio

from models.optical_sar.preprocessing import load_sar


OPTICAL = "data/sentinel2_rgb.tif"

VV = "data/sar/sentinel1_vv.tif"
VH = "data/sar/sentinel1_vh.tif"


print("=" * 60)
print("OPTICAL-SAR PREPROCESSING TEST")
print("=" * 60)


# ============================================================
# CHECK OPTICAL
# ============================================================

print("\nChecking optical image...")

with rasterio.open(OPTICAL) as optical:

    print("Optical CRS:", optical.crs)
    print(
        "Optical size:",
        optical.width,
        "x",
        optical.height
    )
    print("Optical bounds:", optical.bounds)

    optical_shape = (
        optical.height,
        optical.width
    )

    optical_crs = optical.crs
    optical_bounds = optical.bounds


# ============================================================
# LOAD VV
# ============================================================

print("\nLoading VV...")

vv = load_sar(VV)

print("VV shape:", vv.shape)
print(
    "VV normalized range:",
    float(vv.min()),
    "to",
    float(vv.max())
)


# ============================================================
# LOAD VH
# ============================================================

print("\nLoading VH...")

vh = load_sar(VH)

print("VH shape:", vh.shape)
print(
    "VH normalized range:",
    float(vh.min()),
    "to",
    float(vh.max())
)


# ============================================================
# CHECK SHAPES
# ============================================================

print("\nChecking dimensions...")

assert vv.shape == optical_shape, (
    f"VV shape {vv.shape} does not match "
    f"optical shape {optical_shape}"
)

assert vh.shape == optical_shape, (
    f"VH shape {vh.shape} does not match "
    f"optical shape {optical_shape}"
)

print("VV matches optical dimensions.")
print("VH matches optical dimensions.")


# ============================================================
# CHECK CRS AND BOUNDS
# ============================================================

print("\nChecking spatial alignment...")

with rasterio.open(VV) as vv_src:

    assert vv_src.crs == optical_crs
    assert vv_src.bounds == optical_bounds

with rasterio.open(VH) as vh_src:

    assert vh_src.crs == optical_crs
    assert vh_src.bounds == optical_bounds

print("VV spatial alignment: OK")
print("VH spatial alignment: OK")


# ============================================================
# CHECK NORMALIZATION
# ============================================================

print("\nChecking normalization...")

assert np.all(vv >= 0)
assert np.all(vv <= 1)

assert np.all(vh >= 0)
assert np.all(vh <= 1)

print("VV normalization: OK")
print("VH normalization: OK")


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 60)
print("OPTICAL-SAR PREPROCESSING SUCCESSFUL")
print("=" * 60)

print("\nReady for:")
print("1. Optical feature extraction")
print("2. SAR feature extraction")
print("3. Optical-SAR feature fusion")
print("4. Comparison / classification")