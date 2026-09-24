import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from models.optical_sar.multiscene_dataset import (
    MultiSceneOpticalSARDataset
)

from models.optical_sar.splits import (
    create_scene_split
)

from models.optical_sar.model import (
    OpticalSARModel
)


# ============================================================
# CONFIG
# ============================================================

SCENES_ROOT = "data/scenes"

CHECKPOINT_DIR = (
    "models/optical_sar/checkpoints"
)

BEST_MODEL_PATH = os.path.join(
    CHECKPOINT_DIR,
    "optical_sar_best.pth"
)

PATCH_SIZE = 256
STRIDE = 256

BATCH_SIZE = 4

EPOCHS = 10

LEARNING_RATE = 1e-3

DEVICE = torch.device("cpu")


# ============================================================
# DATASET
# ============================================================

print("=" * 70)
print("LOADING MULTI-SCENE DATASET")
print("=" * 70)

dataset = MultiSceneOpticalSARDataset(
    scenes_root=SCENES_ROOT,
    patch_size=PATCH_SIZE,
    stride=STRIDE
)


# ============================================================
# TRAIN / VALIDATION / TEST SPLIT
# ============================================================

train_dataset, validation_dataset, test_dataset = (
    create_scene_split(dataset)
)


print("\nDataset sizes:")

print(
    "Training:",
    len(train_dataset)
)

print(
    "Validation:",
    len(validation_dataset)
)

print(
    "Test:",
    len(test_dataset)
)


# ============================================================
# DATALOADERS
# ============================================================

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

validation_loader = DataLoader(
    validation_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# ============================================================
# MODEL
# ============================================================

print("\nCreating Optical-SAR model...")

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
# LOSS
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

best_validation_loss = float("inf")


print("\n" + "=" * 70)
print("MULTI-SCENE OPTICAL-SAR TRAINING")
print("=" * 70)


for epoch in range(EPOCHS):

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    model.train()

    training_loss = 0.0

    for batch in train_loader:

        optical = batch["optical"].to(DEVICE)
        sar = batch["sar"].to(DEVICE)

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

        loss = loss_function(
            optical_features,
            sar_features
        )

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()

        training_loss += loss.item()


    average_training_loss = (
        training_loss /
        len(train_loader)
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    model.eval()

    validation_loss = 0.0

    with torch.no_grad():

        for batch in validation_loader:

            optical = batch["optical"].to(DEVICE)
            sar = batch["sar"].to(DEVICE)

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

            loss = loss_function(
                optical_features,
                sar_features
            )

            validation_loss += loss.item()


    average_validation_loss = (
        validation_loss /
        len(validation_loader)
    )


    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    print(
        f"Epoch [{epoch + 1}/{EPOCHS}] "
        f"Train Loss: "
        f"{average_training_loss:.6f} "
        f"Val Loss: "
        f"{average_validation_loss:.6f}"
    )


    # --------------------------------------------------------
    # SAVE BEST MODEL
    # --------------------------------------------------------

    if average_validation_loss < best_validation_loss:

        best_validation_loss = (
            average_validation_loss
        )

        torch.save(
            {
                "model_state_dict":
                    model.state_dict(),

                "feature_dim":
                    128,

                "fused_dim":
                    128,

                "epoch":
                    epoch + 1,

                "validation_loss":
                    average_validation_loss
            },
            BEST_MODEL_PATH
        )

        print(
            "  ✓ Best model saved"
        )


# ============================================================
# LOAD BEST MODEL
# ============================================================

print("\n" + "=" * 70)
print("LOADING BEST MODEL")
print("=" * 70)


checkpoint = torch.load(
    BEST_MODEL_PATH,
    map_location=DEVICE
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()


print(
    "Best epoch:",
    checkpoint["epoch"]
)

print(
    "Best validation loss:",
    checkpoint["validation_loss"]
)


# ============================================================
# TEST
# ============================================================

print("\n" + "=" * 70)
print("FINAL TEST")
print("=" * 70)


test_loss = 0.0


with torch.no_grad():

    for batch in test_loader:

        optical = batch["optical"].to(DEVICE)
        sar = batch["sar"].to(DEVICE)

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

        loss = loss_function(
            optical_features,
            sar_features
        )

        test_loss += loss.item()


average_test_loss = (
    test_loss /
    len(test_loader)
)


print(
    f"Test Loss: {average_test_loss:.6f}"
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("MULTI-SCENE TRAINING COMPLETE")
print("=" * 70)

print("\nBest checkpoint:")
print(BEST_MODEL_PATH)

print("\nFinal test loss:")
print(f"{average_test_loss:.6f}")