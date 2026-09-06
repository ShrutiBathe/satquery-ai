"""
SatQuery AI - Backend API Integration Client
Provides a clean interface connecting the Streamlit frontend to the AI backend service
(LangGraph agent or FastAPI endpoint). Seamlessly switches between Live Mode and Demo Mode.
"""

from typing import Dict, Any, Optional, List
import requests
import time
from PIL import Image

import config.settings as cfg
from services.mock_service import execute_mock_analysis, generate_mock_follow_up


class SatQueryAPIClient:
    """Production client contract for SatQuery AI Backend."""

    def __init__(self, base_url: str = cfg.DEFAULT_BACKEND_URL):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> Dict[str, Any]:
        """Check live backend connectivity and system health."""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=3)
            if resp.status_code == 200:
                return {"status": "online", "details": resp.json()}
            return {"status": "degraded", "code": resp.status_code}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def analyze(
        self,
        image_a: Optional[Image.Image],
        image_b: Optional[Image.Image],
        query: str,
        mode: str = cfg.MODE_AUTO,
        metadata_a: Optional[Dict[str, Any]] = None,
        metadata_b: Optional[Dict[str, Any]] = None,
        demo_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Execute geospatial image analysis.
        In Demo Mode: delegates to high-fidelity procedural simulation.
        In Live Mode: dispatches multipart request to remote backend.
        """
        if demo_mode:
            return execute_mock_analysis(
                image_a=image_a,
                image_b=image_b,
                query=query,
                mode=mode,
                metadata_a=metadata_a,
                metadata_b=metadata_b
            )

        # Real Live Backend Dispatch
        endpoint = f"{self.base_url}/api/v1/analyze"
        try:
            payload = {
                "query": query,
                "mode": mode,
                "metadata_a": metadata_a or {},
                "metadata_b": metadata_b or {}
            }
            # Note: For production, encode images as base64 or multipart form-data
            resp = requests.post(endpoint, json=payload, timeout=cfg.API_TIMEOUT_SECONDS)
            if resp.status_code == 200:
                return resp.json()
            else:
                return {
                    "status": "error",
                    "error": f"Backend returned HTTP {resp.status_code}: {resp.text}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "error": f"Could not connect to SatQuery AI backend at '{self.base_url}'. Ensure the server is running or enable Demo Mode in the sidebar."
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Unexpected error during backend dispatch: {str(e)}"
            }

    def send_follow_up(
        self,
        original_result: Dict[str, Any],
        user_query: str,
        demo_mode: bool = True
    ) -> Dict[str, Any]:
        """Dispatch follow-up conversational query."""
        if demo_mode:
            reply = generate_mock_follow_up(original_result, user_query)
            return {"status": "success", "reply": reply}

        endpoint = f"{self.base_url}/api/v1/chat/follow_up"
        try:
            payload = {
                "analysis_id": original_result.get("analysis_id"),
                "query": user_query
            }
            resp = requests.post(endpoint, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            return {"status": "error", "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global singleton client instance
client = SatQueryAPIClient()
