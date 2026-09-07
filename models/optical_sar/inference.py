import os
import torch
import torch.nn.functional as F

from models.optical_sar.model import OpticalSARModel
from models.optical_sar.multiscene_dataset import MultiSceneOpticalSARDataset


CHECKPOINT = "models/optical_sar/checkpoints/optical_sar_best.pth"


def load_model():
    print("=" * 70)
    print("LOADING TRAINED OPTICAL-SAR MODEL")
    print("=" * 70)

    if not os.path.exists(CHECKPOINT):
        raise FileNotFoundError(
            f"Checkpoint not found: {CHECKPOINT}"
        )

    # Load training checkpoint
    checkpoint = torch.load(
        CHECKPOINT,
        map_location="cpu"
    )

    # Recreate model using saved configuration
    trained_model = OpticalSARModel(
        feature_dim=checkpoint.get("feature_dim", 128),
        fused_dim=checkpoint.get("fused_dim", 128)
    )

    # IMPORTANT:
    # The checkpoint contains metadata + model_state_dict.
    trained_model.load_state_dict(
        checkpoint["model_state_dict"]
    )

    trained_model.eval()

    print("✓ Model loaded successfully")
    print(f"✓ Checkpoint: {CHECKPOINT}")
    print(
        f"✓ Trained epoch: "
        f"{checkpoint.get('epoch', 'unknown')}"
    )
    print(
        f"✓ Validation loss: "
        f"{checkpoint.get('validation_loss', 'unknown')}"
    )

    return trained_model


def analyze_scene(trained_model, dataset, index):

    sample = dataset[index]

    optical = sample["optical"].unsqueeze(0)
    sar = sample["sar"].unsqueeze(0)

    scene_name = sample["scene_name"]
    row = sample["row"]
    col = sample["col"]

    print("\n" + "=" * 70)
    print("OPTICAL-SAR ANALYSIS")
    print("=" * 70)

    print(f"Scene: {scene_name}")
    print(f"Patch index: {index}")
    print(f"Patch position: row={row}, col={col}")

    # --------------------------------------------------
    # INPUT INFORMATION
    # --------------------------------------------------

    print("\nInput tensors:")
    print(f"Optical shape: {optical.shape}")
    print(f"SAR shape:     {sar.shape}")

    print("\nInput ranges:")

    print(
        f"Optical: "
        f"{optical.min().item():.4f} "
        f"to "
        f"{optical.max().item():.4f}"
    )

    print(
        f"SAR:     "
        f"{sar.min().item():.4f} "
        f"to "
        f"{sar.max().item():.4f}"
    )

    # --------------------------------------------------
    # MODEL INFERENCE
    # --------------------------------------------------

    with torch.no_grad():

        outputs = trained_model(
            optical,
            sar
        )

    optical_features = outputs["optical_features"]
    sar_features = outputs["sar_features"]
    fused_features = outputs["fused_features"]

    # --------------------------------------------------
    # FEATURE COMPARISON
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
    # FEATURE NORMS
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
    # OUTPUT SHAPES
    # --------------------------------------------------

    print("\nFeature shapes:")

    print(
        f"Optical features: "
        f"{optical_features.shape}"
    )

    print(
        f"SAR features:     "
        f"{sar_features.shape}"
    )

    print(
        f"Fused features:   "
        f"{fused_features.shape}"
    )

    # --------------------------------------------------
    # COMPARISON RESULTS
    # --------------------------------------------------

    print("\nFeature comparison:")

    print(
        f"Cosine similarity: "
        f"{cosine_similarity:.6f}"
    )

    print(
        f"Feature MSE:       "
        f"{feature_mse:.6f}"
    )

    print(
        f"Feature MAE:       "
        f"{feature_mae:.6f}"
    )

    # --------------------------------------------------
    # NORMS
    # --------------------------------------------------

    print("\nFeature norms:")

    print(
        f"Optical norm:      "
        f"{optical_norm:.6f}"
    )

    print(
        f"SAR norm:          "
        f"{sar_norm:.6f}"
    )

    print(
        f"Fused norm:        "
        f"{fused_norm:.6f}"
    )

    # --------------------------------------------------
    # PROTOTYPE INTERPRETATION
    # --------------------------------------------------

    if cosine_similarity >= 0.8:
        agreement = "HIGH"

    elif cosine_similarity >= 0.5:
        agreement = "MODERATE"

    else:
        agreement = "LOW"

    print("\n" + "-" * 70)

    print(
        f"Optical-SAR feature agreement: "
        f"{agreement}"
    )

    print("-" * 70)

    # --------------------------------------------------
    # RESULT OBJECT
    # --------------------------------------------------

    return {
        "scene": scene_name,
        "patch_index": index,
        "cosine_similarity": cosine_similarity,
        "feature_mse": feature_mse,
        "feature_mae": feature_mae,
        "optical_norm": optical_norm,
        "sar_norm": sar_norm,
        "fused_norm": fused_norm,
        "agreement": agreement,
    }


def main():

    # ==================================================
    # LOAD DATASET
    # ==================================================

    print("=" * 70)
    print("LOADING DATASET")
    print("=" * 70)

    dataset = MultiSceneOpticalSARDataset(
        scenes_root="data/scenes",
        patch_size=256,
        stride=256
    )

    print(
        f"Total patches: "
        f"{len(dataset)}"
    )

    print(
        f"Scenes: "
        f"{dataset.scene_names}"
    )

    # ==================================================
    # LOAD TRAINED MODEL
    # ==================================================

    trained_model = load_model()

    # ==================================================
    # FIND HELD-OUT TEST SCENE
    # ==================================================

    test_index = None

    for index, (scene_index, patch_index) in enumerate(
        dataset.index_map
    ):

        if dataset.scene_names[scene_index] == "scene_005":

            test_index = index
            break

    if test_index is None:

        raise RuntimeError(
            "scene_005 was not found in the dataset."
        )

    print(
        f"\nUsing held-out test patch: "
        f"{test_index}"
    )

    # ==================================================
    # RUN ANALYSIS
    # ==================================================

    result = analyze_scene(
        trained_model,
        dataset,
        test_index
    )

    # ==================================================
    # FINAL RESULT
    # ==================================================

    print("\n" + "=" * 70)
    print("INFERENCE COMPLETE")
    print("=" * 70)

    print("\nResult dictionary:")

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )


if __name__ == "__main__":
    main()