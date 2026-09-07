# Allowed tasks supported by SatQuery AI Agent

ALLOWED_TASKS = {
    "vqa",
    "grounding",
    "change_detection",
    "optical_sar",
}


# Number of images required by each task

REQUIRED_IMAGES = {
    "vqa": 1,
    "grounding": 1,
    "change_detection": 2,
    "optical_sar": 2,
}
