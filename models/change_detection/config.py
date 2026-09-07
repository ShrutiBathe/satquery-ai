"""
Configuration for SatQuery AI Change Detection.

This module contains paths and inference settings for ChangeFormerV6.
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

# models/change_detection/
CURRENT_DIR = Path(__file__).resolve().parent

# satquery-ai/
PROJECT_ROOT = CURRENT_DIR.parent.parent


# ---------------------------------------------------------------------------
# ChangeFormer paths
# ---------------------------------------------------------------------------

# Official ChangeFormer repository cloned alongside satquery-ai.
#
# Expected:
#
# D:/Projects/satquery-ai/
# ├── satquery-ai/
# └── ChangeFormer/
#
# In WSL this becomes:
# /mnt/d/Projects/satquery-ai/ChangeFormer
#
CHANGEFORMER_ROOT = PROJECT_ROOT.parent / "ChangeFormer"


# Official pretrained LEVIR-CD checkpoint
CHECKPOINT_DIR = (
    CHANGEFORMER_ROOT
    / "checkpoints"
    / "ChangeFormer_LEVIR"
    / (
        "CD_ChangeFormerV6_LEVIR_"
        "b16_lr0.0001_adamw_train_test_200_"
        "linear_ce_multi_train_True_"
        "multi_infer_False_shuffle_AB_False_"
        "embed_dim_256"
    )
)

CHECKPOINT_PATH = CHECKPOINT_DIR / "best_ckpt.pt"


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

MODEL_NAME = "ChangeFormerV6"

N_CLASS = 2

EMBED_DIM = 256

# CPU-only because the current machine does not have CUDA.
DEVICE = "cpu"


# ---------------------------------------------------------------------------
# Image processing
# ---------------------------------------------------------------------------

# ChangeFormer LEVIR-CD model was trained using 256x256 image patches.
IMAGE_SIZE = 256


# ---------------------------------------------------------------------------
# Change mask processing
# ---------------------------------------------------------------------------

# Minimum connected-component area in pixels.
#
# Small components are usually noise.
MIN_COMPONENT_AREA = 20


# Morphological kernel size used to clean the predicted mask.
MORPH_KERNEL_SIZE = 3


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "change_detection"

MASK_DIR = OUTPUT_DIR / "masks"

OVERLAY_DIR = OUTPUT_DIR / "overlays"


# Create output folders when this module is imported.
MASK_DIR.mkdir(parents=True, exist_ok=True)
OVERLAY_DIR.mkdir(parents=True, exist_ok=True)