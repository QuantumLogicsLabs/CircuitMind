"""Tests for the CV module status endpoint."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from cv_module.cv_api import MODEL_DISPLAY_PATH, router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _status():
    response = client.get("/cv/status")
    assert response.status_code == 200
    return response.json()


def test_status_does_not_leak_the_absolute_model_path():
    payload = _status()
    assert payload["model_path"] == MODEL_DISPLAY_PATH
    assert ":" not in payload["model_path"]
    assert not payload["model_path"].startswith(("/", "\\"))
    assert MODEL_DISPLAY_PATH not in payload.get("active_weights", "")


def test_status_reports_custom_or_fallback_weights():
    payload = _status()
    assert payload["active_weights"] in ("custom", "yolov8n.pt")
    assert payload["status"] in ("ready", "running_on_fallback_weights")
    assert payload["model_exists"] is (payload["active_weights"] == "custom")
