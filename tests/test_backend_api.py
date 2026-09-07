from fastapi.testclient import TestClient

from backend.main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_optical_sar_endpoint_accepts_image_c() -> None:
    client = TestClient(app)
    files = {
        "image_a": ("optical.png", b"not-an-image", "image/png"),
        "image_b": ("vv.png", b"not-an-image", "image/png"),
        "image_c": ("vh.png", b"not-an-image", "image/png"),
    }
    response = client.post(
        "/api/v1/analyze",
        data={
            "query": "Compare optical and SAR imagery.",
            "mode": "optical_sar",
        },
        files=files,
    )
    assert response.status_code in {400, 503}
    assert "detail" in response.json()