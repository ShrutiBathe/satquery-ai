from models.optical_sar.specialist import run_optical_sar


def main():

    print("=" * 70)
    print("TESTING OPTICAL-SAR SPECIALIST")
    print("=" * 70)

    optical_path = (
        "data/scenes/scene_005/"
        "optical.tif"
    )

    vv_path = (
        "data/scenes/scene_005/"
        "vv.tif"
    )

    vh_path = (
        "data/scenes/scene_005/"
        "vh.tif"
    )

    result = run_optical_sar(
        optical_path=optical_path,
        vv_path=vv_path,
        vh_path=vh_path,
        patch_index=0
    )

    print("\nResult:")
    print(result)

    print("\n" + "=" * 70)

    if result["status"] == "success":

        print("✓ OPTICAL-SAR SPECIALIST TEST SUCCESSFUL")

        print("=" * 70)

        comparison = result["comparison"]
        interpretation = result["interpretation"]

        print(
            f"\nCosine similarity: "
            f"{comparison['cosine_similarity']:.6f}"
        )

        print(
            f"Feature MSE: "
            f"{comparison['feature_mse']:.6f}"
        )

        print(
            f"Feature MAE: "
            f"{comparison['feature_mae']:.6f}"
        )

        print(
            f"Agreement: "
            f"{interpretation['agreement']}"
        )

    else:

        print("✗ OPTICAL-SAR SPECIALIST TEST FAILED")

        print(
            f"Error: {result.get('error')}"
        )

        raise RuntimeError(
            result.get("error")
        )


if __name__ == "__main__":
    main()