from .graph import run_graph
from .validators import validate_required_images


def understand_query(
    query: str,
    image_count: int,
    metadata: dict | None = None
) -> dict:
    """
    Public entry point used by the backend.

    Runs the AI Agent through LangGraph and validates
    whether enough images are available for the selected task.
    """

    result = run_graph(
        query=query,
        image_count=image_count,
        metadata=metadata
    )

    if not validate_required_images(
        result["task"],
        image_count
    ):
        raise ValueError(
            f"Task '{result['task']}' requires "
            f"{result['required_images']} image(s), "
            f"but only {image_count} image(s) were provided."
        )

    return result