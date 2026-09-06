from fastapi import FastAPI, HTTPException

from backend.schemas import AnalysisRequest, AnalysisResult
from backend.service import analyze
from backend.validator import validate_request


app = FastAPI(
    title="SatQuery AI API",
    description="Backend API for SatQuery AI remote-sensing analysis",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "satquery-backend",
    }


@app.post("/analyze", response_model=AnalysisResult)
def analyze_image(request: AnalysisRequest):
    valid, message = validate_request(request)

    if not valid:
        raise HTTPException(
            status_code=400,
            detail=message,
        )

    return analyze(request)