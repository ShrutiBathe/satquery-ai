"""
SatQuery AI - FastAPI Backend

API layer responsible for:
1. Receiving natural-language queries and satellite images.
2. Validating incoming requests.
3. Saving uploaded files temporarily.
4. Calling the SatQuery analysis service.
5. Returning a standardized AnalysisResult.

The actual AI/ML orchestration belongs in backend/service.py.
"""

import json
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.schemas import AnalysisRequest, AnalysisResult
from backend.service import analyze


# -------------------------------------------------------------------
# Application configuration
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

RUNTIME_DIR = BASE_DIR / "runtime"
UPLOAD_DIR = RUNTIME_DIR / "uploads"
EVIDENCE_DIR = RUNTIME_DIR / "evidence"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
}


# -------------------------------------------------------------------
# FastAPI application
# -------------------------------------------------------------------

app = FastAPI(
    title="SatQuery AI API",
    description=(
        "Backend API for SatQuery AI - "
        "interactive multimodal remote-sensing image analysis."
    ),
    version="0.2.0",
)


# -------------------------------------------------------------------
# CORS
# -------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Static evidence files
# -------------------------------------------------------------------

app.mount(
    "/outputs",
    StaticFiles(directory=str(EVIDENCE_DIR)),
    name="outputs",
)


# -------------------------------------------------------------------
# Health endpoint
# -------------------------------------------------------------------

@app.get("/health")
def health_check():
    """
    Basic backend health check.
    """

    return {
        "status": "ok",
        "service": "satquery-backend",
        "version": "0.2.0",
    }


# -------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------

def _validate_upload_extension(filename: Optional[str]) -> None:
    """
    Validate uploaded image extension.
    """

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must have a filename.",
        )

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported image format '{extension}'. "
                f"Supported formats: {sorted(SUPPORTED_EXTENSIONS)}"
            ),
        )


def _save_upload(
    upload: UploadFile,
    destination: Path,
) -> None:
    """
    Save an UploadFile to disk.
    """

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded image: {exc}",
        ) from exc


def _parse_metadata(
    metadata: Optional[str],
) -> dict:
    """
    Parse metadata JSON received through multipart/form-data.

    Empty metadata is treated as an empty dictionary.
    """

    if not metadata:
        return {}

    try:
        parsed = json.loads(metadata)

        if not isinstance(parsed, dict):
            raise ValueError("Metadata must be a JSON object.")

        return parsed

    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metadata JSON: {exc}",
        ) from exc


# -------------------------------------------------------------------
# Main analysis endpoint
# -------------------------------------------------------------------

@app.post(
    "/api/v1/analyze",
    response_model=AnalysisResult,
)
async def analyze_image(
    query: str = Form(...),
    mode: str = Form("auto_detect"),
    metadata_a: Optional[str] = Form(None),
    metadata_b: Optional[str] = Form(None),
    image_a: UploadFile = File(...),
    image_b: Optional[UploadFile] = File(None),
):
    """
    Run SatQuery AI analysis.

    Expected multipart/form-data:

        query
        mode
        metadata_a
        metadata_b
        image_a
        image_b (optional)

    The endpoint saves uploaded images and passes their filesystem
    paths to the internal analysis service.
    """

    # ---------------------------------------------------------------
    # Basic query validation
    # ---------------------------------------------------------------

    if not query or not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    query = query.strip()

    # ---------------------------------------------------------------
    # Validate mode
    # ---------------------------------------------------------------

    valid_modes = {
        "auto_detect",
        "single_image",
        "compare_images",
        "optical_sar",
    }

    if mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid mode '{mode}'. "
                f"Expected one of: {sorted(valid_modes)}"
            ),
        )

    # ---------------------------------------------------------------
    # Validate uploaded files
    # ---------------------------------------------------------------

    _validate_upload_extension(image_a.filename)

    if image_b is not None:
        _validate_upload_extension(image_b.filename)

    # ---------------------------------------------------------------
    # Create unique analysis directory
    # ---------------------------------------------------------------

    analysis_id = f"ANL-{uuid.uuid4().hex[:10].upper()}"

    analysis_upload_dir = UPLOAD_DIR / analysis_id
    analysis_upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Save image A
    # ---------------------------------------------------------------

    image_a_extension = Path(image_a.filename).suffix.lower()

    image_a_path = (
        analysis_upload_dir / f"image_a{image_a_extension}"
    )

    _save_upload(
        image_a,
        image_a_path,
    )

    image_paths = [str(image_a_path)]

    # ---------------------------------------------------------------
    # Save image B if supplied
    # ---------------------------------------------------------------

    if image_b is not None:

        image_b_extension = Path(image_b.filename).suffix.lower()

        image_b_path = (
            analysis_upload_dir / f"image_b{image_b_extension}"
        )

        _save_upload(
            image_b,
            image_b_path,
        )

        image_paths.append(str(image_b_path))

    # ---------------------------------------------------------------
    # Parse metadata
    # ---------------------------------------------------------------

    parsed_metadata_a = _parse_metadata(metadata_a)
    parsed_metadata_b = _parse_metadata(metadata_b)

    # ---------------------------------------------------------------
    # Build internal backend request
    # ---------------------------------------------------------------

    request = AnalysisRequest(
        query=query,
        image_paths=image_paths,
        mode=mode,
        metadata_a=parsed_metadata_a,
        metadata_b=parsed_metadata_b,
    )

    # ---------------------------------------------------------------
    # Run SatQuery analysis service
    # ---------------------------------------------------------------

    try:

        result = analyze(request)

        # Make sure the generated analysis ID is available
        # even if service.py does not generate one yet.
        if not result.analysis_id:
            result.analysis_id = analysis_id

        return result

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"SatQuery analysis failed: {exc}",
        ) from exc


# -------------------------------------------------------------------
# Backward-compatible endpoint
# -------------------------------------------------------------------

@app.post(
    "/analyze",
    response_model=AnalysisResult,
)
async def analyze_image_legacy(
    query: str = Form(...),
    mode: str = Form("auto_detect"),
    metadata_a: Optional[str] = Form(None),
    metadata_b: Optional[str] = Form(None),
    image_a: UploadFile = File(...),
    image_b: Optional[UploadFile] = File(None),
):
    """
    Backward-compatible alias for /api/v1/analyze.

    This allows older frontend code or teammates' testing code
    to continue using /analyze.
    """

    return await analyze_image(
        query=query,
        mode=mode,
        metadata_a=metadata_a,
        metadata_b=metadata_b,
        image_a=image_a,
        image_b=image_b,
    )