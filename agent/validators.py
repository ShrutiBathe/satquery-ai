from .config import ALLOWED_TASKS, REQUIRED_IMAGES


def validate_task(task: str) -> bool:
    """
    Check whether the selected task is supported.
    """
    return task in ALLOWED_TASKS


def validate_required_images(task: str, image_count: int) -> bool:
    """
    Check whether the provided image count is sufficient
    for the selected task.
    """
    if task not in REQUIRED_IMAGES:
        return False

    return image_count >= REQUIRED_IMAGES[task]


def validate_agent_output(result: dict) -> bool:
    """
    Validate the structure returned by understand_query().
    """

    required_fields = {
        "task",
        "required_images",
        "reason",
    }

    if not required_fields.issubset(result.keys()):
        return False

    if not validate_task(result["task"]):
        return False

    if result["required_images"] != REQUIRED_IMAGES[result["task"]]:
        return False

    if not isinstance(result["reason"], str):
        return False

    return True