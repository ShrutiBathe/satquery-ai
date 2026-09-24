from models.optical_sar.multiscene_dataset import (
    MultiSceneOpticalSARDataset
)


print("=" * 70)
print("MULTI-SCENE OPTICAL-SAR DATASET TEST")
print("=" * 70)


dataset = MultiSceneOpticalSARDataset(
    scenes_root="data/scenes",
    patch_size=256,
    stride=256
)


print("\nScenes loaded:")

for i, name in enumerate(dataset.scene_names):

    scene_dataset = dataset.datasets[i]

    print(
        f"  {i + 1}. {name} "
        f"→ {len(scene_dataset)} patches"
    )


print("\nTotal patches:")
print(len(dataset))


print("\nChecking first sample...")

sample = dataset[0]

print(
    "Scene:",
    sample["scene_name"]
)

print(
    "Optical shape:",
    sample["optical"].shape
)

print(
    "SAR shape:",
    sample["sar"].shape
)

print(
    "Optical range:",
    sample["optical"].min().item(),
    "to",
    sample["optical"].max().item()
)

print(
    "SAR range:",
    sample["sar"].min().item(),
    "to",
    sample["sar"].max().item()
)


assert len(dataset) > 0

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

assert 0.0 <= sample["optical"].min()
assert sample["optical"].max() <= 1.0

assert 0.0 <= sample["sar"].min()
assert sample["sar"].max() <= 1.0


print("\n" + "=" * 70)
print("MULTI-SCENE DATASET TEST SUCCESSFUL")
print("=" * 70)