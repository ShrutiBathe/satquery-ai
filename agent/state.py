from typing import TypedDict


class AgentState(TypedDict, total=False):
    query: str
    image_count: int
    metadata: dict | None

    task: str
    required_images: int
    reason: str