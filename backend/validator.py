"""
SatQuery AI - Backend Request Validation

Backend-side validation for analysis requests.

Frontend validation improves user experience, but backend validation
is still required because the backend must not trust client input.
"""

from backend.schemas import AnalysisRequest


VALID_MODES = {
    "auto_detect",
    "single_image",
    "compare_images",
    "optical_sar",
}


def validate_request(request: AnalysisRequest) -> tuple[bool, str]:
    """
    Validate an internal SatQuery analysis request.

    Returns:
        (True, "Request is valid.") when validation succeeds.
        (False, "<reason>") when validation fails.
    """

    # ---------------------------------------------------------------
    # Query validation
    # ---------------------------------------------------------------

    if not request.query or not request.query.strip():
        return False, "Query cannot be empty."

    # ---------------------------------------------------------------
    # Mode validation
    # ---------------------------------------------------------------

    if request.mode not in VALID_MODES:
        return (
            False,
            (
                f"Invalid analysis mode '{request.mode}'. "
                f"Expected one of: {sorted(VALID_MODES)}"
            ),
        )

    # ---------------------------------------------------------------
    # Image validation
    # ---------------------------------------------------------------

    image_count = len(request.image_paths)

    if image_count == 0:
        return False, "At least one image is required."

    if image_count > 2:
        return False, "A maximum of two images is supported."

    # ---------------------------------------------------------------
    # Mode-specific validation
    # ---------------------------------------------------------------

    if request.mode == "single_image" and image_count != 1:
        return (
            False,
            "Single-image mode requires exactly one image.",
        )

    if request.mode == "compare_images" and image_count != 2:
        return (
            False,
            "Compare-images mode requires exactly two images.",
        )

    if request.mode == "optical_sar" and image_count != 2:
        return (
            False,
            "Optical-SAR mode requires exactly two images.",
        )

    # ---------------------------------------------------------------
    # File-path validation
    # ---------------------------------------------------------------

    for image_path in request.image_paths:
        if not image_path.strip():
            return False, "Image path cannot be empty."

    return True, "Request is valid."