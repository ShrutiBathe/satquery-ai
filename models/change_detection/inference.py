"""
ChangeFormerV6 inference engine.

This module:
1. Loads the ChangeFormerV6 model.
2. Loads the pretrained LEVIR-CD checkpoint.
3. Preprocesses before/after images.
4. Runs binary change detection.
5. Returns the predicted change mask.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
import torch
from PIL import Image

from models.basic_model import CDEvaluator

from .config import (
    CHECKPOINT_DIR,
    CHECKPOINT_PATH,
    EMBED_DIM,
    IMAGE_SIZE,
    N_CLASS,
    MODEL_NAME,
)


class ChangeFormerInference:
    """
    Wrapper around the official ChangeFormerV6 implementation.
    """

    def __init__(
        self,
        checkpoint_dir: str | Path | None = None,
        checkpoint_name: str = "best_ckpt.pt",
        device: str = "cpu",
        image_size: int = IMAGE_SIZE,
        embed_dim: int = EMBED_DIM,
    ):
        self.device = torch.device(device)
        self.image_size = image_size
        self.embed_dim = embed_dim

        self.checkpoint_dir = Path(
            checkpoint_dir if checkpoint_dir is not None else CHECKPOINT_DIR
        )

        self.checkpoint_name = checkpoint_name

        self.model = None

        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """
        Create ChangeFormerV6 and load the pretrained checkpoint.
        """

        if not self.checkpoint_dir.exists():
            raise FileNotFoundError(
                f"ChangeFormer checkpoint directory does not exist:\n"
                f"{self.checkpoint_dir}"
            )

        checkpoint_path = self.checkpoint_dir / self.checkpoint_name

        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"ChangeFormer checkpoint does not exist:\n"
                f"{checkpoint_path}"
            )

        class Args:
            pass

        args = Args()

        args.n_class = N_CLASS
        args.gpu_ids = []
        args.net_G = MODEL_NAME
        args.embed_dim = self.embed_dim
        args.checkpoint_dir = str(self.checkpoint_dir)
        args.output_folder = str(
            Path("outputs") / "change_detection" / "inference"
        )

        self.model = CDEvaluator(args)

        # PyTorch >= 2.6 defaults torch.load() to weights_only=True.
        #
        # The official ChangeFormer checkpoint contains objects that require
        # the old loading behavior. We therefore explicitly use
        # weights_only=False inside our patched CDEvaluator implementation.
        self.model.load_checkpoint(self.checkpoint_name)

        self.model.net_G.to(self.device)
        self.model.net_G.eval()

    # ------------------------------------------------------------------
    # Image loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_image(path: str | Path) -> np.ndarray:
        """
        Load an image as RGB uint8 numpy array.

        Supports:
        - PNG
        - JPEG
        - TIFF
        - GeoTIFF where PIL can read the data
        """

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        image = Image.open(path)

        # Convert to RGB so the model always receives 3 channels.
        image = image.convert("RGB")

        image = np.array(image)

        return image

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------

    def _preprocess(
        self,
        image: np.ndarray,
    ) -> torch.Tensor:
        """
        Convert an RGB numpy image into a ChangeFormer input tensor.

        Output:
            Tensor with shape [1, 3, H, W]
        """

        image = cv2.resize(
            image,
            (self.image_size, self.image_size),
            interpolation=cv2.INTER_LINEAR,
        )

        image = image.astype(np.float32)

        # Convert [0,255] -> [0,1]
        image = image / 255.0

        # ChangeFormer training pipeline uses normalized RGB input.
        mean = np.array(
            [0.485, 0.456, 0.406],
            dtype=np.float32,
        )

        std = np.array(
            [0.229, 0.224, 0.225],
            dtype=np.float32,
        )

        image = (image - mean) / std

        # HWC -> CHW
        image = np.transpose(image, (2, 0, 1))

        # CHW -> BCHW
        tensor = torch.from_numpy(image).unsqueeze(0)

        tensor = tensor.to(
            self.device,
            dtype=torch.float32,
        )

        return tensor

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    @torch.no_grad()
    def predict(
        self,
        before_path: str | Path,
        after_path: str | Path,
    ) -> np.ndarray:
        """
        Run ChangeFormer inference.

        Args:
            before_path:
                Earlier image.

            after_path:
                Later image.

        Returns:
            Binary change mask with shape [256, 256].

            Values:
                0 = unchanged
                1 = changed
        """

        before_image = self._load_image(before_path)
        after_image = self._load_image(after_path)

        before_tensor = self._preprocess(before_image)
        after_tensor = self._preprocess(after_image)

        # ChangeFormer forward pass.
        output = self.model.net_G(
            before_tensor,
            after_tensor,
        )

        # The official ChangeFormer model returns multiple outputs.
        #
        # The final output is the highest-level prediction.
        if isinstance(output, (list, tuple)):
            prediction = output[-1]
        else:
            prediction = output

        # Convert logits -> predicted class.
        prediction = torch.argmax(
            prediction,
            dim=1,
        )

        prediction = prediction.squeeze(0)

        # CPU numpy.
        mask = prediction.cpu().numpy().astype(np.uint8)

        return mask

    # ------------------------------------------------------------------
    # Original-size mask
    # ------------------------------------------------------------------

    def predict_original_size(
        self,
        before_path: str | Path,
        after_path: str | Path,
    ) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Run prediction and resize the binary mask back to the original
        before-image dimensions.

        Returns:
            mask:
                Binary uint8 mask.

            original_size:
                (width, height)
        """

        before_image = self._load_image(before_path)

        height, width = before_image.shape[:2]

        mask = self.predict(
            before_path,
            after_path,
        )

        mask = cv2.resize(
            mask,
            (width, height),
            interpolation=cv2.INTER_NEAREST,
        )

        mask = (mask > 0).astype(np.uint8)

        return mask, (width, height)


# ----------------------------------------------------------------------
# Singleton model loader
# ----------------------------------------------------------------------

_MODEL = None


def get_model() -> ChangeFormerInference:
    """
    Return a lazily-loaded ChangeFormer model.

    Loading the model only once avoids reloading the ~1 GB checkpoint
    every time run_change_detection() is called.
    """

    global _MODEL

    if _MODEL is None:
        _MODEL = ChangeFormerInference()

    return _MODEL