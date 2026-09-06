from backend.schemas import AnalysisRequest, AnalysisResult


def analyze(request: AnalysisRequest) -> AnalysisResult:
    """
    Main SatQuery analysis pipeline.

    This will later connect:
    AI Agent → Geo preprocessing → AI Models.
    """

    trace = [
        "Request received",
        "Backend analysis started",
    ]

    # Temporary dummy task.
    # Later this will come from the AI Agent.
    task = "vqa"

    trace.append(f"Task selected: {task}")

    return AnalysisResult(
        success=True,
        task=task,
        answer=f"Dummy response for query: {request.query}",
        confidence=0.50,
        evidence=[],
        output_paths=[],
        statistics={},
        trace=trace,
        error=None,
    )