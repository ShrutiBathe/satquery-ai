import os

import numpy as np
import rasterio
import torch
from torch.utils.data import Dataset


class OpticalSARDataset(Dataset):

    def __init__(
        self,
        optical_path,
        vv_path,
        vh_path,
        patch_size=256,
        stride=256
    ):

        self.optical_path = optical_path
        self.vv_path = vv_path
        self.vh_path = vh_path

        self.patch_size = patch_size
        self.stride = stride

        # ----------------------------------------------------
        # Read metadata
        # ----------------------------------------------------

        with rasterio.open(optical_path) as optical:

            self.height = optical.height
            self.width = optical.width

            self.optical_crs = optical.crs
            self.optical_transform = optical.transform

        with rasterio.open(vv_path) as vv:

            self.vv_height = vv.height
            self.vv_width = vv.width

            self.vv_crs = vv.crs
            self.vv_transform = vv.transform

        with rasterio.open(vh_path) as vh:

            self.vh_height = vh.height
            self.vh_width = vh.width

            self.vh_crs = vh.crs
            self.vh_transform = vh.transform

        # ----------------------------------------------------
        # Verify spatial compatibility
        # ----------------------------------------------------

        if self.width != self.vv_width:
            raise ValueError(
                "Optical and VV widths do not match."
            )

        if self.height != self.vv_height:
            raise ValueError(
                "Optical and VV heights do not match."
            )

        if self.width != self.vh_width:
            raise ValueError(
                "Optical and VH widths do not match."
            )

        if self.height != self.vh_height:
            raise ValueError(
                "Optical and VH heights do not match."
            )

        if self.optical_crs != self.vv_crs:
            raise ValueError(
                "Optical and VV CRS do not match."
            )

        if self.optical_crs != self.vh_crs:
            raise ValueError(
                "Optical and VH CRS do not match."
            )

        # ----------------------------------------------------
        # Generate patch positions
        # ----------------------------------------------------

        self.patch_positions = []

        for row in range(
            0,
            self.height - patch_size + 1,
            stride
        ):

            for col in range(
                0,
                self.width - patch_size + 1,
                stride
            ):

                self.patch_positions.append(
                    (row, col)
                )

    def __len__(self):

        return len(
            self.patch_positions
        )

    def __getitem__(self, index):

        row, col = self.patch_positions[index]

        # ----------------------------------------------------
        # Read optical patch
        # ----------------------------------------------------

        with rasterio.open(
            self.optical_path
        ) as optical:

            optical_patch = optical.read(
                window=rasterio.windows.Window(
                    col,
                    row,
                    self.patch_size,
                    self.patch_size
                )
            )

        # ----------------------------------------------------
        # Read VV patch
        # ----------------------------------------------------

        with rasterio.open(
            self.vv_path
        ) as vv:

            vv_patch = vv.read(
                1,
                window=rasterio.windows.Window(
                    col,
                    row,
                    self.patch_size,
                    self.patch_size
                )
            )

        # ----------------------------------------------------
        # Read VH patch
        # ----------------------------------------------------

        with rasterio.open(
            self.vh_path
        ) as vh:

            vh_patch = vh.read(
                1,
                window=rasterio.windows.Window(
                    col,
                    row,
                    self.patch_size,
                    self.patch_size
                )
            )

        # ----------------------------------------------------
        # Optical normalization
        # ----------------------------------------------------

        optical_patch = (
            optical_patch.astype(
                np.float32
            ) / 255.0
        )

        # ----------------------------------------------------
        # SAR normalization
        # ----------------------------------------------------

        vv_patch = self._normalize_sar(
            vv_patch
        )

        vh_patch = self._normalize_sar(
            vh_patch
        )

        # ----------------------------------------------------
        # Stack SAR
        # ----------------------------------------------------

        sar_patch = np.stack(
            [
                vv_patch,
                vh_patch
            ],
            axis=0
        )

        # ----------------------------------------------------
        # Convert to tensors
        # ----------------------------------------------------

        optical_tensor = torch.from_numpy(
            optical_patch.copy()
        )

        sar_tensor = torch.from_numpy(
            sar_patch.copy()
        )

        return {
            "optical": optical_tensor,
            "sar": sar_tensor,
            "index": index,
            "row": row,
            "col": col
        }

    @staticmethod
    def _normalize_sar(data):

        data = data.astype(
            np.float32
        )

        valid = (
            np.isfinite(data)
            & (data > -30000)
        )

        result = np.zeros_like(
            data,
            dtype=np.float32
        )

        if not np.any(valid):

            return result

        minimum = np.percentile(
            data[valid],
            2
        )

        maximum = np.percentile(
            data[valid],
            98
        )

        if maximum <= minimum:

            result[valid] = 0.0

            return result

        clipped = np.clip(
            data[valid],
            minimum,
            maximum
        )

        result[valid] = (
            (clipped - minimum)
            / (maximum - minimum)
        )

        return result