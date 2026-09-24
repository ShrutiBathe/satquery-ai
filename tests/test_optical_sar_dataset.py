from models.optical_sar.dataset import OpticalSARDataset


OPTICAL = "data/sentinel2_rgb_visual.tif"

VV = "data/sar/sentinel1_vv.tif"

VH = "data/sar/sentinel1_vh.tif"


print("=" * 60)
print("OPTICAL-SAR DATASET TEST")
print("=" * 60)


dataset = OpticalSARDataset(
    optical_path=OPTICAL,
    vv_path=VV,
    vh_path=VH,
    patch_size=256,
    stride=256
)


print("\nDataset created.")

print(
    "Number of patches:",
    len(dataset)
)


# ------------------------------------------------------------
# Read first sample
# ------------------------------------------------------------

sample = dataset[0]


print("\nFirst sample:")

print(
    "Optical shape:",
    sample["optical"].shape
)

print(
    "SAR shape:",
    sample["sar"].shape
)

print(
    "Patch index:",
    sample["index"]
)

print(
    "Position:",
    sample["row"],
    sample["col"]
)


# ------------------------------------------------------------
# Verify shapes
# ------------------------------------------------------------

assert sample["optical"].shape == (
    3,
    256,
    256
)

assert sample["sar"].shape == (
    2,
    256,
    256
)


# ------------------------------------------------------------
# Verify values
# ------------------------------------------------------------

print("\nOptical range:")

print(
    float(sample["optical"].min()),
    "to",
    float(sample["optical"].max())
)


print("\nSAR range:")

print(
    float(sample["sar"].min()),
    "to",
    float(sample["sar"].max())
)


assert sample["optical"].min() >= 0
assert sample["optical"].max() <= 1

assert sample["sar"].min() >= 0
assert sample["sar"].max() <= 1


print("\n" + "=" * 60)
print("OPTICAL-SAR DATASET TEST SUCCESSFUL")
print("=" * 60)