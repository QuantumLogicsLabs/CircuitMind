"""The CV router is mounted on the main API.

cv_module.cv_api builds an APIRouter but api/app.py never attached it, so the
image endpoints existed only in a standalone app that nobody deploys. These
tests keep the router mounted and reachable.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def test_cv_status_is_reachable():
    response = client.get("/cv/status")

    assert response.status_code == 200
    body = response.json()
    assert body["module"] == "Computer Vision"
    assert body["status"] in {"ready", "running_on_fallback_weights"}
    assert "PNG" in body["supported_formats"]


def test_openapi_lists_the_cv_endpoints():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/cv/status" in paths
    assert "/cv/image-to-circuit" in paths
    assert "/cv/batch-process" in paths


def test_cv_upload_rejects_a_non_image_content_type():
    response = client.post(
        "/cv/image-to-circuit",
        files={"image": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()


def test_cv_batch_requires_images():
    response = client.post("/cv/batch-process")

    assert response.status_code == 422


def test_mounting_the_router_keeps_the_core_routes():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/cv/status").status_code == 200
