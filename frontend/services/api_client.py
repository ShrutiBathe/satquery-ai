"""
SatQuery AI - Backend API Integration Client

Provides the interface between the Streamlit frontend and the
FastAPI backend.

Supports:

1. Demo Mode
   -> Uses the existing mock service.

2. Live Mode
   -> Sends actual images + query + metadata to FastAPI.

The rest of the frontend should only need to call:

    client.analyze(...)

and should not need to know how the backend API works.
"""

from __future__ import annotations

import io
from typing import Any, Dict, Optional

import requests
from PIL import Image

import config.settings as cfg
from services.mock_service import (
    execute_mock_analysis,
    generate_mock_follow_up,
)


class SatQueryAPIClient:
    """
    Production client contract for SatQuery AI Backend.
    """

    def __init__(
        self,
        base_url: str = cfg.DEFAULT_BACKEND_URL,
    ):
        self.base_url = base_url.rstrip("/")

    # ----------------------------------------------------------------
    # Health check
    # ----------------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        """
        Check whether the FastAPI backend is reachable.
        """

        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5,
            )

            if response.status_code == 200:

                return {
                    "status": "online",
                    "details": response.json(),
                }

            return {
                "status": "degraded",
                "code": response.status_code,
                "error": response.text,
            }

        except requests.exceptions.ConnectionError:

            return {
                "status": "offline",
                "error": (
                    f"Could not connect to backend at "
                    f"'{self.base_url}'."
                ),
            }

        except requests.exceptions.Timeout:

            return {
                "status": "offline",
                "error": "Backend health check timed out.",
            }

        except Exception as exc:

            return {
                "status": "offline",
                "error": str(exc),
            }

    # ----------------------------------------------------------------
    # Main analysis method
    # ----------------------------------------------------------------

    def analyze(
        self,
        image_a: Optional[Image.Image],
        image_b: Optional[Image.Image],
        query: str,
        mode: str = cfg.MODE_AUTO,
        metadata_a: Optional[Dict[str, Any]] = None,
        metadata_b: Optional[Dict[str, Any]] = None,
        demo_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute SatQuery analysis.

        Demo Mode:
            Uses the existing frontend mock service.

        Live Mode:
            Sends images and metadata to the FastAPI backend.
        """

        # ============================================================
        # DEMO MODE
        # ============================================================

        if demo_mode:

            return execute_mock_analysis(
                image_a=image_a,
                image_b=image_b,
                query=query,
                mode=mode,
                metadata_a=metadata_a,
                metadata_b=metadata_b,
            )

        # ============================================================
        # BASIC FRONTEND-SIDE CHECKS
        # ============================================================

        if image_a is None:

            return {
                "status": "error",
                "error": "Image A is required.",
            }

        if not query or not query.strip():

            return {
                "status": "error",
                "error": "Query cannot be empty.",
            }

        # ============================================================
        # PREPARE MULTIPART DATA
        # ============================================================

        try:

            # Convert image A to bytes
            image_a_bytes = self._image_to_bytes(
                image_a
            )

            files = {
                "image_a": (
                    "image_a.png",
                    image_a_bytes,
                    "image/png",
                )
            }

            # --------------------------------------------------------
            # Image B is optional
            # --------------------------------------------------------

            if image_b is not None:

                image_b_bytes = self._image_to_bytes(
                    image_b
                )

                files["image_b"] = (
                    "image_b.png",
                    image_b_bytes,
                    "image/png",
                )

            # --------------------------------------------------------
            # Form fields
            # --------------------------------------------------------

            data = {
                "query": query.strip(),
                "mode": mode,
                "metadata_a": self._metadata_to_json(
                    metadata_a
                ),
                "metadata_b": self._metadata_to_json(
                    metadata_b
                ),
            }

        except Exception as exc:

            return {
                "status": "error",
                "error": (
                    f"Failed to prepare images for backend: "
                    f"{exc}"
                ),
            }

        # ============================================================
        # SEND REQUEST TO FASTAPI
        # ============================================================

        endpoint = (
            f"{self.base_url}/api/v1/analyze"
        )

        try:

            response = requests.post(
                endpoint,
                data=data,
                files=files,
                timeout=cfg.API_TIMEOUT_SECONDS,
            )

        except requests.exceptions.ConnectionError:

            return {
                "status": "error",
                "error": (
                    "Could not connect to SatQuery AI backend "
                    f"at '{self.base_url}'. "
                    "Make sure FastAPI is running."
                ),
            }

        except requests.exceptions.Timeout:

            return {
                "status": "error",
                "error": (
                    "SatQuery backend request timed out."
                ),
            }

        except requests.exceptions.RequestException as exc:

            return {
                "status": "error",
                "error": (
                    f"Backend request failed: {exc}"
                ),
            }

        # ============================================================
        # HANDLE HTTP ERRORS
        # ============================================================

        if response.status_code != 200:

            error_message = self._extract_backend_error(
                response
            )

            return {
                "status": "error",
                "error": error_message,
                "http_status": response.status_code,
            }

        # ============================================================
        # PARSE RESPONSE
        # ============================================================

        try:

            result = response.json()

        except ValueError:

            return {
                "status": "error",
                "error": (
                    "Backend returned an invalid JSON response."
                ),
            }

        # ============================================================
        # NORMALIZE RESPONSE FOR EXISTING FRONTEND
        # ============================================================

        return self._normalize_backend_result(
            result
        )

    # ----------------------------------------------------------------
    # Image conversion
    # ----------------------------------------------------------------

    @staticmethod
    def _image_to_bytes(
        image: Image.Image,
    ) -> bytes:
        """
        Convert a PIL image to PNG bytes.

        The backend receives the image as multipart/form-data.
        """

        buffer = io.BytesIO()

        # Some PIL images can have modes that PNG does not handle
        # consistently. Convert uncommon modes to RGB.
        if image.mode not in {
            "1",
            "L",
            "LA",
            "P",
            "RGB",
            "RGBA",
        }:

            image = image.convert("RGB")

        image.save(
            buffer,
            format="PNG",
        )

        return buffer.getvalue()

    # ----------------------------------------------------------------
    # Metadata conversion
    # ----------------------------------------------------------------

    @staticmethod
    def _metadata_to_json(
        metadata: Optional[Dict[str, Any]],
    ) -> str:
        """
        Convert metadata dictionary to a JSON string suitable for
        multipart/form-data.
        """

        import json

        if not metadata:
            return "{}"

        return json.dumps(
            metadata,
            default=str,
        )

    # ----------------------------------------------------------------
    # Backend error extraction
    # ----------------------------------------------------------------

    @staticmethod
    def _extract_backend_error(
        response: requests.Response,
    ) -> str:
        """
        Extract a useful error message from a FastAPI response.
        """

        try:

            payload = response.json()

            if isinstance(payload, dict):

                detail = payload.get(
                    "detail"
                )

                if detail:
                    return str(detail)

                error = payload.get(
                    "error"
                )

                if error:
                    return str(error)

        except Exception:
            pass

        return (
            f"Backend returned HTTP "
            f"{response.status_code}: "
            f"{response.text}"
        )

    # ----------------------------------------------------------------
    # Response normalization
    # ----------------------------------------------------------------

    @staticmethod
    def _normalize_backend_result(
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Normalize the backend response into the structure expected
        by the existing Streamlit workflow.

        This allows us to change the backend independently without
        rewriting the entire frontend.
        """

        # ------------------------------------------------------------
        # Backend success/error
        # ------------------------------------------------------------

        if result.get("success") is False:

            return {
                "status": "error",
                "error": result.get(
                    "error",
                    "Backend analysis failed.",
                ),
                **result,
            }

        # ------------------------------------------------------------
        # detected_task
        # ------------------------------------------------------------

        detected_task = result.get(
            "detected_task"
        )

        if detected_task is None:

            detected_task = {
                "task_id": result.get(
                    "task",
                    "vqa",
                ),
                "title": result.get(
                    "task",
                    "Visual Question Answering",
                ),
                "reason": "",
                "required_images": 1,
            }

        # Pydantic may return this as a dictionary,
        # but protect against unexpected structures.
        if not isinstance(
            detected_task,
            dict,
        ):

            detected_task = {
                "task_id": result.get(
                    "task",
                    "vqa",
                ),
                "title": str(
                    detected_task
                ),
                "reason": "",
                "required_images": 1,
            }

        # ------------------------------------------------------------
        # Final frontend-compatible result
        # ------------------------------------------------------------

        normalized = {
            "status": result.get(
                "status",
                "success",
            ),

            "success": result.get(
                "success",
                True,
            ),

            "analysis_id": result.get(
                "analysis_id",
                "ANL-UNKNOWN",
            ),

            "query": result.get(
                "query",
                "",
            ),

            "mode": result.get(
                "mode",
                "auto_detect",
            ),

            "task": result.get(
                "task",
                detected_task.get(
                    "task_id",
                    "vqa",
                ),
            ),

            "detected_task": detected_task,

            "answer": result.get(
                "answer",
                "",
            ),

            "confidence": result.get(
                "confidence"
            ),

            "confidence_breakdown": result.get(
                "confidence_breakdown",
                {},
            ),

            "summary_bullets": result.get(
                "summary_bullets",
                [],
            ),

            "metrics": result.get(
                "metrics",
                {},
            ),

            "visual_evidence": result.get(
                "visual_evidence",
                {},
            ),

            "evidence": result.get(
                "evidence",
                [],
            ),

            "output_paths": result.get(
                "output_paths",
                [],
            ),

            "statistics": result.get(
                "statistics",
                {},
            ),

            "analysis_trace": result.get(
                "analysis_trace",
                result.get(
                    "trace",
                    [],
                ),
            ),

            "trace": result.get(
                "trace",
                [],
            ),

            "error": result.get(
                "error"
            ),
        }

        return normalized

    # ----------------------------------------------------------------
    # Follow-up questions
    # ----------------------------------------------------------------

    def follow_up(
        self,
        query: str,
        previous_result: Dict[str, Any],
        demo_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Handle a follow-up question.

        Demo mode uses the existing mock implementation.

        Live follow-up support can be connected later when the
        backend exposes a dedicated follow-up endpoint.
        """

        if demo_mode:

            return generate_mock_follow_up(
                query=query,
                previous_result=previous_result,
            )

        return {
            "status": "error",
            "error": (
                "Live follow-up analysis is not implemented yet."
            ),
        }


# --------------------------------------------------------------------
# Shared client instance
# --------------------------------------------------------------------

client = SatQueryAPIClient()