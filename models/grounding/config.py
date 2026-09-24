import torch
from pathlib import Path
from PIL import Image
from transformers import (
    AutoProcessor,
    AutoModelForZeroShotObjectDetection,
)


MODEL_ID = "IDEA-Research/grounding-dino-tiny"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

BOX_THRESHOLD = 0.40
TEXT_THRESHOLD = 0.30


class GroundingModel:
    """Grounding DINO model wrapper."""

    def __init__(self):
        self.device = DEVICE

        print(f"Loading Grounding DINO on {self.device}...")

        self.processor = AutoProcessor.from_pretrained(MODEL_ID)

        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(
            MODEL_ID
        ).to(self.device)

        self.model.eval()

        print("Grounding DINO loaded successfully.")

    def predict(
        self,
        image: Image.Image,
        query: str,
        box_threshold: float = BOX_THRESHOLD,
        text_threshold: float = TEXT_THRESHOLD,
    ):
        if not query or not query.strip():
            raise ValueError("Grounding query cannot be empty.")

        image = image.convert("RGB")

        inputs = self.processor(
            images=image,
            text=query.strip(),
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.no_grad():
            outputs = self.model(**inputs)

        results = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs["input_ids"],
            threshold=box_threshold,
            text_threshold=text_threshold,
            target_sizes=[image.size[::-1]],
        )

        result = results[0]

        detections = []

        for box, score, label in zip(
            result["boxes"],
            result["scores"],
            result["labels"],
        ):
            detections.append(
                {
                    "label": str(label),
                    "confidence": round(float(score), 4),
                    "box": [
                        round(float(value), 2)
                        for value in box.tolist()
                    ],
                }
            )

        return {
            "success": True,
            "query": query,
            "detections": detections,
            "evidence": [],
            "output_paths": [],
            "statistics": {
                "num_detections": len(detections),
            },
            "error": None,
        }


_model = None


def get_grounding_model():
    """Load the model once and reuse it."""

    global _model

    if _model is None:
        _model = GroundingModel()

    return _model


def run_grounding(
    image_path: str,
    query: str,
    box_threshold: float = BOX_THRESHOLD,
    text_threshold: float = TEXT_THRESHOLD,
) -> dict:
    """
    Run text-guided visual grounding.

    Args:
        image_path: Path to input image.
        query: Natural-language object/region description.
        box_threshold: Bounding-box confidence threshold.
        text_threshold: Text matching threshold.

    Returns:
        Structured grounding result.
    """

    try:
        image_path = Path(image_path)

        if not image_path.exists():
            return {
                "success": False,
                "query": query,
                "detections": [],
                "evidence": [],
                "output_paths": [],
                "statistics": {},
                "error": f"Image not found: {image_path}",
            }

        image = Image.open(image_path).convert("RGB")

        model = get_grounding_model()

        return model.predict(
            image=image,
            query=query,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
        )

    except Exception as exc:
        return {
            "success": False,
            "query": query,
            "detections": [],
            "evidence": [],
            "output_paths": [],
            "statistics": {},
            "error": str(exc),
        }