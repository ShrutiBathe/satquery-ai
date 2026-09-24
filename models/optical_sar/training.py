import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from models.optical_sar.dataset import OpticalSARDataset
from models.optical_sar.model import OpticalSARModel


# ============================================================
# CONFIG
# ============================================================

OPTICAL = "data/sentinel2_rgb_visual.tif"
VV = "data/sar/sentinel1_vv.tif"
VH = "data/sar/sentinel1_vh.tif"

CHECKPOINT_DIR = "models/optical_sar/checkpoints"

BATCH_SIZE = 2
EPOCHS = 5
LEARNING_RATE = 1e-3

DEVICE = torch.device("cpu")


# ============================================================
# DATASET
# ============================================================

dataset = OpticalSARDataset(
    optical_path=OPTICAL,
    vv_path=VV,
    vh_path=VH,
    patch_size=256,
    stride=256
)

print("Dataset size:", len(dataset))


# ============================================================
# DATALOADER
# ============================================================

loader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)


# ============================================================
# MODEL
# ============================================================

model = OpticalSARModel(
    feature_dim=128,
    fused_dim=128
)

model = model.to(DEVICE)


# ============================================================
# OPTIMIZER
# ============================================================

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# ============================================================
# TRAINING LOSS
# ============================================================

loss_function = nn.MSELoss()


# ============================================================
# CHECKPOINT DIRECTORY
# ============================================================

os.makedirs(
    CHECKPOINT_DIR,
    exist_ok=True
)


# ============================================================
# TRAINING
# ============================================================

print("\n" + "=" * 60)
print("OPTICAL-SAR TRAINING")
print("=" * 60)

for epoch in range(EPOCHS):

    model.train()

    epoch_loss = 0.0

    for batch in loader:

        optical = batch["optical"].to(DEVICE)
        sar = batch["sar"].to(DEVICE)

        # ----------------------------------------------------
        # Forward pass
        # ----------------------------------------------------

        outputs = model(
            optical,
            sar
        )

        optical_features = outputs[
            "optical_features"
        ]

        sar_features = outputs[
            "sar_features"
        ]

        # ----------------------------------------------------
        # Simple multimodal alignment objective
        # ----------------------------------------------------

        loss = loss_function(
            optical_features,
            sar_features
        )

        # ----------------------------------------------------
        # Backpropagation
        # ----------------------------------------------------

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

        epoch_loss += loss.item()

    average_loss = (
        epoch_loss / len(loader)
    )

    print(
        f"Epoch [{epoch + 1}/{EPOCHS}] "
        f"Loss: {average_loss:.6f}"
    )


# ============================================================
# SAVE MODEL
# ============================================================

checkpoint_path = os.path.join(
    CHECKPOINT_DIR,
    "optical_sar_model.pth"
)

torch.save(
    {
        "model_state_dict": model.state_dict(),
        "feature_dim": 128,
        "fused_dim": 128
    },
    checkpoint_path
)


print("\n" + "=" * 60)
print("TRAINING COMPLETE")
print("=" * 60)

print("\nModel saved to:")
print(checkpoint_path)