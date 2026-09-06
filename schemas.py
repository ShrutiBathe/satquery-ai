from typing import Any
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    query: str = Field(..., min_length=1)
    image_paths: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    success: bool
    task: str
    answer: str = ""
    confidence: float | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    output_paths: list[str] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)
    trace: list[str] = Field(default_factory=list)
    error: str | None = None