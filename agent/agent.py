from .query_understanding import understand_query
from .validators import validate_agent_output


def run_agent(
    query: str,
    image_count: int,
    metadata: dict | None = None
) -> dict:

    result = understand_query(
        query=query,
        image_count=image_count,
        metadata=metadata
    )

    if not validate_agent_output(result):
        raise ValueError("Invalid AI Agent output.")

    return result