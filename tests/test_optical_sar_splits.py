from models.optical_sar.multiscene_dataset import (
    MultiSceneOpticalSARDataset
)

from models.optical_sar.splits import (
    create_scene_split
)


print("=" * 70)
print("OPTICAL-SAR TRAIN / VALIDATION / TEST SPLIT")
print("=" * 70)


dataset = MultiSceneOpticalSARDataset(
    scenes_root="data/scenes",
    patch_size=256,
    stride=256
)


train_dataset, validation_dataset, test_dataset = (
    create_scene_split(dataset)
)


print("\nDataset split:")

print(
    "Training patches:",
    len(train_dataset)
)

print(
    "Validation patches:",
    len(validation_dataset)
)

print(
    "Test patches:",
    len(test_dataset)
)


assert len(train_dataset) == 48
assert len(validation_dataset) == 16
assert len(test_dataset) == 16


print("\nChecking training sample...")

train_sample = train_dataset[0]

print(
    "Scene:",
    train_sample["scene_name"]
)

print(
    "Optical:",
    train_sample["optical"].shape
)

print(
    "SAR:",
    train_sample["sar"].shape
)


print("\nChecking validation sample...")

validation_sample = validation_dataset[0]

print(
    "Scene:",
    validation_sample["scene_name"]
)


print("\nChecking test sample...")

test_sample = test_dataset[0]

print(
    "Scene:",
    test_sample["scene_name"]
)


assert train_sample["scene_name"] in [
    "scene_001",
    "scene_002",
    "scene_003"
]

assert validation_sample["scene_name"] == "scene_004"

assert test_sample["scene_name"] == "scene_005"


print("\n" + "=" * 70)
print("TRAIN / VALIDATION / TEST SPLIT SUCCESSFUL")
print("=" * 70)