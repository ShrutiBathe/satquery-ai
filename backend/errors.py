class SatQueryError(Exception):
    """Base exception for SatQuery backend errors."""
    pass


class ValidationError(SatQueryError):
    """Raised when a request is invalid."""
    pass


class ModelError(SatQueryError):
    """Raised when a model fails during inference."""
    pass