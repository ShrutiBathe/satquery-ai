from pathlib import Path
from typing import Any, Dict, List, Tuple

import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import (
    AutoModelForZeroShotObjectDetection,
    AutoProcessor,
)


# ============================================================
# Configuration
# ============================================================

MODEL_ID = "IDEA-Research/grounding-dino-tiny"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Grounding DINO candidate thresholds.
# We intentionally do not use 0.40 here because it removed
# almost all useful small-object detections in the satellite image.
BOX_THRESHOLD = 0.25
TEXT_THRESHOLD = 0.20

# Tiling configuration.
GRID_ROWS = 3
GRID_COLS = 3
TILE_OVERLAP = 0.20

# Final filtering.
MIN_CONFIDENCE = 0.25

# NMS IoU threshold.
NMS_IOU_THRESHOLD = 0.45

# Object queries where image-sized detections are almost
# certainly scene-level false positives.
OBJECT_QUERY_KEYWORDS = {
    "building",
    "buildings",
    "residential building",
    "industrial building",
    "warehouse",
    "vehicle",
    "vehicles",
    "ship",
    "ships",
    "airplane",
    "airplanes",
}


# ============================================================
# Prompt normalization
# ============================================================

def normalize_query(query: str) -> str:
    """
    Normalize a user query into a Grounding DINO-friendly prompt.
    """

    query = query.strip().lower()

    if not query:
        raise ValueError("Grounding query cannot be empty.")

    # Remove an existing final period so we can add exactly one.
    query = query.rstrip(".")

    # Grounding DINO generally works better with natural-language
    # phrases than isolated class names.
    return f"a {query}."


# ============================================================
# Grounding model
# ============================================================

class GroundingModel:
    """
    Lazy-loaded Grounding DINO wrapper.
    """

    def __init__(self):
        print(f"Loading Grounding DINO on {DEVICE}...")

        self.processor = AutoProcessor.from_pretrained(MODEL_ID)

        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(
            MODEL_ID
        ).to(DEVICE)

        self.model.eval()

        print("Grounding DINO loaded successfully.")

    @torch.inference_mode()
    def predict(
        self,
        image: Image.Image,
        query: str,
        box_threshold: float = BOX_THRESHOLD,
        text_threshold: float = TEXT_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """
        Run Grounding DINO on one image/tile.
        """

        prompt = normalize_query(query)

        inputs = self.processor(
            images=image,
            text=prompt,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(DEVICE) if hasattr(value, "to") else value
            for key, value in inputs.items()
        }

        outputs = self.model(**inputs)

        target_sizes = torch.tensor(
            [[image.height, image.width]],
            device=DEVICE,
        )

        results = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs["input_ids"],
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            target_sizes=target_sizes,
        )

        result = results[0]

        boxes = result.get("boxes", [])
        scores = result.get("scores", [])

        # Transformers versions differ in how labels are exposed.
        text_labels = result.get("text_labels")

        if text_labels is None:
            text_labels = result.get("labels", [])

        detections = []

        for i, box in enumerate(boxes):
            score = float(scores[i])

            box_values = [float(v) for v in box.tolist()]

            if i < len(text_labels):
                label = str(text_labels[i])
            else:
                label = prompt

            detections.append(
                {
                    "label": label,
                    "confidence": round(score, 4),
                    "box": box_values,
                }
            )

        return detections


# ============================================================
# Lazy model instance
# ============================================================

_model = None


def get_grounding_model() -> GroundingModel:
    global _model

    if _model is None:
        _model = GroundingModel()

    return _model


# ============================================================
# Tiling
# ============================================================

def create_tiles(
    image: Image.Image,
    rows: int = GRID_ROWS,
    cols: int = GRID_COLS,
    overlap: float = TILE_OVERLAP,
) -> List[Tuple[Image.Image, int, int, int, int]]:
    """
    Create overlapping tiles.

    Returns:
        [
            (
                tile_image,
                x_offset,
                y_offset,
                tile_width,
                tile_height,
            ),
            ...
        ]
    """

    image_width, image_height = image.size

    # Tile size is based on the requested grid.
    tile_width = image_width // cols
    tile_height = image_height // rows

    # Calculate stride using overlap.
    stride_x = max(
        1,
        int(tile_width * (1.0 - overlap)),
    )

    stride_y = max(
        1,
        int(tile_height * (1.0 - overlap)),
    )

    tiles = []

    y_positions = []
    x_positions = []

    y = 0
    while True:
        y_positions.append(y)

        if y + tile_height >= image_height:
            break

        next_y = y + stride_y

        # Make sure the final tile touches the image boundary.
        if next_y + tile_height > image_height:
            next_y = image_height - tile_height

        if next_y == y:
            break

        y = next_y

    x = 0
    while True:
        x_positions.append(x)

        if x + tile_width >= image_width:
            break

        next_x = x + stride_x

        if next_x + tile_width > image_width:
            next_x = image_width - tile_width

        if next_x == x:
            break

        x = next_x

    for y_offset in y_positions:
        for x_offset in x_positions:

            x2 = min(
                x_offset + tile_width,
                image_width,
            )

            y2 = min(
                y_offset + tile_height,
                image_height,
            )

            tile = image.crop(
                (
                    x_offset,
                    y_offset,
                    x2,
                    y2,
                )
            )

            tiles.append(
                (
                    tile,
                    x_offset,
                    y_offset,
                    tile.width,
                    tile.height,
                )
            )

    return tiles


# ============================================================
# Box utilities
# ============================================================

def clip_box(
    box: List[float],
    image_width: int,
    image_height: int,
) -> List[float]:
    """
    Clip a bounding box to image boundaries.
    """

    x1, y1, x2, y2 = box

    x1 = max(0.0, min(x1, float(image_width)))
    y1 = max(0.0, min(y1, float(image_height)))

    x2 = max(0.0, min(x2, float(image_width)))
    y2 = max(0.0, min(y2, float(image_height)))

    return [x1, y1, x2, y2]


def box_area(box: List[float]) -> float:
    x1, y1, x2, y2 = box

    width = max(0.0, x2 - x1)
    height = max(0.0, y2 - y1)

    return width * height


def box_iou(
    box_a: List[float],
    box_b: List[float],
) -> float:
    """
    Calculate IoU between two boxes.
    """

    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_width = max(0.0, inter_x2 - inter_x1)
    inter_height = max(0.0, inter_y2 - inter_y1)

    intersection = inter_width * inter_height

    area_a = box_area(box_a)
    area_b = box_area(box_b)

    union = area_a + area_b - intersection

    if union <= 0:
        return 0.0

    return intersection / union


# ============================================================
# Geometry filtering
# ============================================================

def is_scene_sized_box(
    box: List[float],
    image_width: int,
    image_height: int,
    query: str,
) -> bool:
    """
    Reject boxes that look like scene-level detections.

    We apply this aggressively to object queries such as:
    building, vehicle, ship, airplane, warehouse.

    Large-area classes such as water, trees, and roads are
    handled more conservatively.
    """

    x1, y1, x2, y2 = box

    width = max(0.0, x2 - x1)
    height = max(0.0, y2 - y1)

    width_ratio = width / image_width
    height_ratio = height / image_height

    area_ratio = (width * height) / (
        image_width * image_height
    )

    normalized_query = query.strip().lower()

    # Object-level detections should not normally occupy
    # almost an entire dimension of the image.
    if normalized_query in OBJECT_QUERY_KEYWORDS:

        if width_ratio > 0.80:
            return True

        if height_ratio > 0.80:
            return True

        if area_ratio > 0.55:
            return True

    return False


def filter_detection(
    detection: Dict[str, Any],
    image_width: int,
    image_height: int,
    query: str,
) -> bool:
    """
    Return True if detection should be retained.
    """

    confidence = float(
        detection["confidence"]
    )

    if confidence < MIN_CONFIDENCE:
        return False

    box = detection["box"]

    if len(box) != 4:
        return False

    x1, y1, x2, y2 = box

    if x2 <= x1 or y2 <= y1:
        return False

    if is_scene_sized_box(
        box,
        image_width,
        image_height,
        query,
    ):
        return False

    # Reject extremely tiny numerical boxes.
    width = x2 - x1
    height = y2 - y1

    if width < 3 or height < 3:
        return False

    return True


# ============================================================
# NMS
# ============================================================

def non_maximum_suppression(
    detections: List[Dict[str, Any]],
    iou_threshold: float = NMS_IOU_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Pure-Python confidence-based NMS.

    No torchvision dependency required.
    """

    if not detections:
        return []

    # Highest confidence first.
    sorted_detections = sorted(
        detections,
        key=lambda d: float(d["confidence"]),
        reverse=True,
    )

    kept = []

    while sorted_detections:

        current = sorted_detections.pop(0)

        kept.append(current)

        remaining = []

        for candidate in sorted_detections:

            iou = box_iou(
                current["box"],
                candidate["box"],
            )

            if iou < iou_threshold:
                remaining.append(candidate)

        sorted_detections = remaining

    return kept


# ============================================================
# Visualization
# ============================================================

def save_grounding_visualization(
    image: Image.Image,
    detections: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """
    Draw detections on the image.
    """

    output = image.copy().convert("RGB")

    draw = ImageDraw.Draw(output)

    try:
        font = ImageFont.truetype(
            "arial.ttf",
            18,
        )
    except Exception:
        font = ImageFont.load_default()

    for detection in detections:

        x1, y1, x2, y2 = detection["box"]

        confidence = detection["confidence"]
        label = detection["label"]

        draw.rectangle(
            [x1, y1, x2, y2],
            outline="red",
            width=3,
        )

        text = f"{label} {confidence:.2f}"

        bbox = draw.textbbox(
            (x1, y1),
            text,
            font=font,
        )

        text_height = bbox[3] - bbox[1]

        text_y = max(
            0,
            y1 - text_height - 4,
        )

        draw.rectangle(
            [
                x1,
                text_y,
                bbox[2] + 4,
                y1,
            ],
            fill="red",
        )

        draw.text(
            (x1 + 2, text_y + 2),
            text,
            fill="white",
            font=font,
        )

    output_path = str(output_path)

    Path(output_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.save(output_path)

    return output_path


# ============================================================
# Public API
# ============================================================

def run_grounding(
    image_path: str,
    query: str,
    box_threshold: float = BOX_THRESHOLD,
    text_threshold: float = TEXT_THRESHOLD,
) -> Dict[str, Any]:
    """
    Public grounding interface for SatQuery AI.

    Args:
        image_path:
            Path to JPG, PNG, TIFF, etc.

        query:
            Natural-language grounding query.

        box_threshold:
            Grounding DINO box threshold.

        text_threshold:
            Grounding DINO text threshold.

    Returns:
        Structured dictionary compatible with the agent.
    """

    try:

        image_path_obj = Path(image_path)

        if not image_path_obj.exists():

            return {
                "success": False,
                "query": query,
                "detections": [],
                "evidence": [],
                "output_paths": [],
                "statistics": {
                    "num_detections": 0,
                },
                "error": f"Image not found: {image_path}",
            }

        image = Image.open(
            image_path_obj
        ).convert("RGB")

        image_width, image_height = image.size

        model = get_grounding_model()

        # ----------------------------------------------------
        # Create overlapping tiles.
        # ----------------------------------------------------

        tiles = create_tiles(image)

        print(
            f"Grounding '{query}' using "
            f"{len(tiles)} overlapping tiles..."
        )

        all_detections = []

        # ----------------------------------------------------
        # Run Grounding DINO on each tile.
        # ----------------------------------------------------

        for tile_index, (
            tile,
            x_offset,
            y_offset,
            tile_width,
            tile_height,
        ) in enumerate(tiles, start=1):

            print(
                f"  Tile {tile_index}/{len(tiles)}..."
            )

            tile_detections = model.predict(
                image=tile,
                query=query,
                box_threshold=box_threshold,
                text_threshold=text_threshold,
            )

            # ------------------------------------------------
            # Convert tile coordinates back to original image.
            # ------------------------------------------------

            for detection in tile_detections:

                x1, y1, x2, y2 = detection["box"]

                original_box = [
                    x1 + x_offset,
                    y1 + y_offset,
                    x2 + x_offset,
                    y2 + y_offset,
                ]

                original_box = clip_box(
                    original_box,
                    image_width,
                    image_height,
                )

                detection["box"] = original_box

                if filter_detection(
                    detection,
                    image_width,
                    image_height,
                    query,
                ):
                    all_detections.append(
                        detection
                    )

        # ----------------------------------------------------
        # NMS.
        # ----------------------------------------------------

        final_detections = non_maximum_suppression(
            all_detections,
            iou_threshold=NMS_IOU_THRESHOLD,
        )

        # ----------------------------------------------------
        # Sort by confidence.
        # ----------------------------------------------------

        final_detections.sort(
            key=lambda d: float(d["confidence"]),
            reverse=True,
        )

        # ----------------------------------------------------
        # Visualization.
        # ----------------------------------------------------

        safe_query = (
            query.lower()
            .strip()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )

        output_path = (
            Path("outputs")
            / "grounding"
            / f"{safe_query}.jpg"
        )

        saved_path = save_grounding_visualization(
            image=image,
            detections=final_detections,
            output_path=str(output_path),
        )

        return {
            "success": True,
            "query": query,
            "detections": final_detections,
            "evidence": [saved_path],
            "output_paths": [saved_path],
            "statistics": {
                "num_tiles": len(tiles),
                "raw_detections": len(all_detections),
                "num_detections": len(final_detections),
                "image_width": image_width,
                "image_height": image_height,
            },
            "error": None,
        }

    except Exception as exc:

        return {
            "success": False,
            "query": query,
            "detections": [],
            "evidence": [],
            "output_paths": [],
            "statistics": {
                "num_detections": 0,
            },
            "error": str(exc),
        }