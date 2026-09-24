from .config import REQUIRED_IMAGES


def understand_query(
    query: str,
    image_count: int,
    metadata: dict | None = None
) -> dict:

    q = query.lower().strip()

    # Optical-SAR
    if (
        ("optical" in q and "sar" in q)
        or "optical-sar" in q
        or "optical sar" in q
    ):
        task = "optical_sar"
        reason = "User wants joint analysis of optical and SAR imagery."

    # Change Detection
    elif any(
        keyword in q
        for keyword in [
            "change",
            "changed",
            "difference",
            "compare",
            "comparison",
            "before and after",
            "between two images",
        ]
    ):
        task = "change_detection"
        reason = "User is asking about changes or differences between images."

    # Grounding
    elif any(
        keyword in q
        for keyword in [
            "where",
            "find",
            "locate",
            "location",
            "highlight",
            "mark",
            "region",
            "bounding",
        ]
    ):
        task = "grounding"
        reason = "User wants to locate or highlight an object or region."

       # Ambiguous / General Query
    else:
        task = "vqa"
        reason = (
            "The query is ambiguous, so the request is routed "
            "to VQA for general image analysis."
        )

    return {
        "task": task,
        "required_images": REQUIRED_IMAGES[task],
        "reason": reason,
    }