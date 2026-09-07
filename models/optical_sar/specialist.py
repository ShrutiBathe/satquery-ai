import os
import torch
import torch.nn.functional as F

from models.optical_sar.model import OpticalSARModel
from models.optical_sar.dataset import OpticalSARDataset


CHECKPOINT = "models/optical_sar/checkpoints/optical_sar_best.pth"


def _load_model():
    """
    Load the trained Optical-SAR model.
    """

    if not os.path.exists(CHECKPOINT):
        raise FileNotFoundError(
            f"Optical-SAR checkpoint not found: {CHECKPOINT}"
        )

    checkpoint = torch.load(
        CHECKPOINT,
        map_location="cpu"
    )

    model = OpticalSARModel(
        feature_dim=checkpoint.get("feature_dim", 128),
        fused_dim=checkpoint.get("fused_dim", 128)
    )

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    model.eval()

    return model


def run_optical_sar(
    optical_path,
    vv_path,
    vh_path,
    patch_index=0,
    patch_size=256,
    stride=256
):
    """
    Run Optical-SAR analysis on an optical image
    and corresponding Sentinel-1 VV/VH images.

    Returns a structured dictionary suitable for
    integration with the LangGraph agent.
    """

    # --------------------------------------------------
    # Validate input files
    # --------------------------------------------------

    required_files = {
        "optical": optical_path,
        "vv": vv_path,
        "vh": vh_path
    }

    for name, path in required_files.items():

        if not os.path.exists(path):

            return {
                "task": "optical_sar",
                "status": "error",
                "error": f"{name} file not found: {path}"
            }

    try:

        # --------------------------------------------------
        # Load dataset
        # --------------------------------------------------

        dataset = OpticalSARDataset(
            optical_path=optical_path,
            vv_path=vv_path,
            vh_path=vh_path,
            patch_size=patch_size,
            stride=stride
        )

        if len(dataset) == 0:

            return {
                "task": "optical_sar",
                "status": "error",
                "error": "No valid patches found in the input images."
            }

        if patch_index < 0 or patch_index >= len(dataset):

            return {
                "task": "optical_sar",
                "status": "error",
                "error": (
                    f"Invalid patch_index={patch_index}. "
                    f"Available range: 0-{len(dataset) - 1}"
                )
            }

        # --------------------------------------------------
        # Load trained model
        # --------------------------------------------------

        model = _load_model()

        # --------------------------------------------------
        # Get patch
        # --------------------------------------------------

        sample = dataset[patch_index]

        optical = sample["optical"].unsqueeze(0)
        sar = sample["sar"].unsqueeze(0)

        # --------------------------------------------------
        # Model inference
        # --------------------------------------------------

        with torch.no_grad():

            outputs = model(
                optical,
                sar
            )

        optical_features = outputs["optical_features"]
        sar_features = outputs["sar_features"]
        fused_features = outputs["fused_features"]

        # --------------------------------------------------
        # Feature comparison
        # --------------------------------------------------

        cosine_similarity = F.cosine_similarity(
            optical_features,
            sar_features,
            dim=1
        ).item()

        feature_mse = torch.mean(
            (optical_features - sar_features) ** 2
        ).item()

        feature_mae = torch.mean(
            torch.abs(
                optical_features - sar_features
            )
        ).item()

        # --------------------------------------------------
        # Feature norms
        # --------------------------------------------------

        optical_norm = torch.norm(
            optical_features,
            p=2
        ).item()

        sar_norm = torch.norm(
            sar_features,
            p=2
        ).item()

        fused_norm = torch.norm(
            fused_features,
            p=2
        ).item()

        # --------------------------------------------------
        # Prototype interpretation
        # --------------------------------------------------

        if cosine_similarity >= 0.8:

            agreement = "HIGH"

        elif cosine_similarity >= 0.5:

            agreement = "MODERATE"

        else:

            agreement = "LOW"

        # --------------------------------------------------
        # Return structured result
        # --------------------------------------------------

        return {
            "task": "optical_sar",
            "status": "success",

            "patch": {
                "index": patch_index,
                "row": sample["row"],
                "col": sample["col"],
                "size": patch_size
            },

            "features": {
                "optical_dimension": int(
                    optical_features.shape[1]
                ),
                "sar_dimension": int(
                    sar_features.shape[1]
                ),
                "fused_dimension": int(
                    fused_features.shape[1]
                )
            },

            "comparison": {
                "cosine_similarity": cosine_similarity,
                "feature_mse": feature_mse,
                "feature_mae": feature_mae
            },

            "norms": {
                "optical": optical_norm,
                "sar": sar_norm,
                "fused": fused_norm
            },

            "interpretation": {
                "agreement": agreement
            }
        }

    except Exception as e:

        return {
            "task": "optical_sar",
            "status": "error",
            "error": str(e)
        }