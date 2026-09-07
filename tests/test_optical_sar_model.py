import torch
import rasterio
import numpy as np

from models.optical_sar.model import OpticalSARModel
from models.optical_sar.preprocessing import load_sar


OPTICAL = "data/sentinel2_rgb_visual.tif"

VV = "data/sar/sentinel1_vv.tif"
VH = "data/sar/sentinel1_vh.tif"


print("=" * 60)
print("OPTICAL-SAR MODEL TEST")
print("=" * 60)


# ============================================================
# LOAD OPTICAL
# ============================================================

print("\nLoading optical image...")

with rasterio.open(OPTICAL) as src:

    optical = src.read()

print("Optical shape:", optical.shape)


# ============================================================
# CONVERT OPTICAL TO FLOAT
# ============================================================

optical = optical.astype(
    np.float32
) / 255.0


# ============================================================
# LOAD SAR
# ============================================================

print("\nLoading SAR...")

vv = load_sar(VV)
vh = load_sar(VH)

print("VV shape:", vv.shape)
print("VH shape:", vh.shape)


# ============================================================
# STACK SAR
# ============================================================

sar = np.stack(
    [vv, vh],
    axis=0
)

print("SAR shape:", sar.shape)


# ============================================================
# CONVERT TO PYTORCH
# ============================================================

optical_tensor = torch.from_numpy(
    optical
).unsqueeze(0)

sar_tensor = torch.from_numpy(
    sar
).unsqueeze(0)


print("\nPyTorch tensors:")

print(
    "Optical:",
    optical_tensor.shape
)

print(
    "SAR:",
    sar_tensor.shape
)


# ============================================================
# CREATE MODEL
# ============================================================

print("\nCreating Optical-SAR model...")

model = OpticalSARModel()

model.eval()


# ============================================================
# FORWARD PASS
# ============================================================

print("\nRunning forward pass...")

with torch.no_grad():

    outputs = model(
        optical_tensor,
        sar_tensor
    )


# ============================================================
# OUTPUTS
# ============================================================

print("\nModel outputs:")

for name, tensor in outputs.items():

    print(
        name,
        ":",
        tensor.shape
    )


# ============================================================
# FINAL CHECK
# ============================================================

assert outputs[
    "optical_features"
].shape == (1, 128)

assert outputs[
    "sar_features"
].shape == (1, 128)

assert outputs[
    "fused_features"
].shape == (1, 128)


print("\n" + "=" * 60)
print("OPTICAL-SAR MODEL FORWARD PASS SUCCESSFUL")
print("=" * 60)