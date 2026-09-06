
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff"
}


def validate_images(
    image_paths: list[str],
    task: str
) -> dict:

    # Check whether images were provided
    if not image_paths:
        return {
            "valid": False,
            "message": "No images were provided."
        }

    # Normalize task name
    task = task.lower().strip().replace("-", "_").replace(" ", "_")

    # Required number of images
    required_counts = {
        "vqa": 1,
        "grounding": 1,
        "change_detection": 2
    }

    # Check image count
    if task in required_counts:

        required = required_counts[task]

        if len(image_paths) != required:

            task_name = task.replace("_", " ").title()

            return {
                "valid": False,
                "message": (
                    f"{task_name} requires exactly "
                    f"{required} image(s)."
                )
            }

    # Optical-SAR
    elif task == "optical_sar":

        if len(image_paths) < 2:
            return {
                "valid": False,
                "message": (
                    "Optical-SAR requires at least "
                    "two images."
                )
            }

    # Unsupported task
    else:
        return {
            "valid": False,
            "message": f"Unsupported task: {task}"
        }

    # Check each image
    for image_path in image_paths:

        path = Path(image_path)

        # Check file exists
        if not path.exists():
            return {
                "valid": False,
                "message": f"Image file not found: {image_path}"
            }

        # Check extension
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return {
                "valid": False,
                "message": (
                    f"Unsupported image format: {path.suffix}. "
                    "Supported formats are JPG, JPEG, PNG, TIF and TIFF."
                )
            }

    # All checks passed
    return {
        "valid": True,
        "message": "Input images are valid."
    }
