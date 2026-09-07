import os
import torch
from torch.utils.data import Dataset

from models.optical_sar.dataset import OpticalSARDataset


class MultiSceneOpticalSARDataset(Dataset):

    def __init__(
        self,
        scenes_root="data/scenes",
        patch_size=256,
        stride=256
    ):

        self.scenes_root = scenes_root
        self.patch_size = patch_size
        self.stride = stride

        self.datasets = []
        self.scene_names = []

        if not os.path.isdir(scenes_root):
            raise FileNotFoundError(
                f"Scenes directory not found: {scenes_root}"
            )

        scene_dirs = sorted(
            [
                name
                for name in os.listdir(scenes_root)
                if os.path.isdir(
                    os.path.join(scenes_root, name)
                )
            ]
        )

        if not scene_dirs:
            raise ValueError(
                "No scene directories found."
            )

        for scene_name in scene_dirs:

            scene_dir = os.path.join(
                scenes_root,
                scene_name
            )

            optical = os.path.join(
                scene_dir,
                "optical.tif"
            )

            vv = os.path.join(
                scene_dir,
                "vv.tif"
            )

            vh = os.path.join(
                scene_dir,
                "vh.tif"
            )

            if not all(
                os.path.exists(path)
                for path in [optical, vv, vh]
            ):
                print(
                    f"Skipping incomplete scene: "
                    f"{scene_name}"
                )
                continue

            dataset = OpticalSARDataset(
                optical_path=optical,
                vv_path=vv,
                vh_path=vh,
                patch_size=patch_size,
                stride=stride
            )

            self.datasets.append(dataset)
            self.scene_names.append(scene_name)

        if not self.datasets:
            raise ValueError(
                "No valid scenes found."
            )

        # Build a global index:
        # (scene_index, local_patch_index)
        self.index_map = []

        for scene_index, dataset in enumerate(
            self.datasets
        ):

            for patch_index in range(
                len(dataset)
            ):

                self.index_map.append(
                    (
                        scene_index,
                        patch_index
                    )
                )

    def __len__(self):

        return len(self.index_map)

    def __getitem__(self, index):

        scene_index, patch_index = (
            self.index_map[index]
        )

        sample = self.datasets[
            scene_index
        ][patch_index]

        sample = dict(sample)

        sample["scene_index"] = scene_index
        sample["scene_name"] = (
            self.scene_names[scene_index]
        )

        return sample