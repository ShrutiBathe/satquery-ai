from backend.schemas import AnalysisRequest


def validate_request(request: AnalysisRequest) -> tuple[bool, str]:
    """
    Basic backend request validation.
    """

    if not request.query.strip():
        return False, "Query cannot be empty."

    if not request.image_paths:
        return False, "At least one image is required."

    return True, "Request is valid."