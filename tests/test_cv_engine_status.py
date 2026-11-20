"""
Tests for CV engine availability reporting.

ultralytics is an optional dependency. Without it, the routes used to fail
with a generic 500 ImportError; they should instead advertise the problem
and answer 503 with an actionable message.
"""

import pytest
from fastapi.testclient import TestClient

import cv_module.cv_api as cv_api


@pytest.fixture
def client():
    return TestClient(cv_api.app)


def test_status_reports_engine_missing(client, monkeypatch):
    monkeypatch.setattr(cv_api, "engine_available", lambda: False)

    body = client.get("/cv/status").json()

    assert body["engine_available"] is False
    assert body["status"] == "engine_missing"


def test_status_prefers_ready_when_model_and_engine_exist(client, monkeypatch):
    monkeypatch.setattr(cv_api, "engine_available", lambda: True)
    monkeypatch.setattr(cv_api.os.path, "exists", lambda p: True)

    body = client.get("/cv/status").json()

    assert body["engine_available"] is True
    assert body["status"] == "ready"


def test_image_route_returns_503_without_engine(client, monkeypatch):
    monkeypatch.setattr(cv_api, "engine_available", lambda: False)
    monkeypatch.setattr(
        cv_api, "image_to_circuit_json",
        lambda *a, **k: pytest.fail("inference must not run without the engine"),
    )

    response = client.post(
        "/cv/image-to-circuit",
        files={"image": ("circuit.png", b"fake", "image/png")},
    )

    assert response.status_code == 503
    assert "ultralytics" in response.json()["detail"]


def test_batch_route_returns_503_without_engine(client, monkeypatch):
    monkeypatch.setattr(cv_api, "engine_available", lambda: False)

    response = client.post(
        "/cv/batch-process",
        files=[("images", ("one.png", b"a", "image/png"))],
    )

    assert response.status_code == 503


def test_route_processes_normally_with_engine(client, monkeypatch):
    monkeypatch.setattr(cv_api, "engine_available", lambda: True)
    monkeypatch.setattr(
        cv_api, "image_to_circuit_json",
        lambda image_path, model_path: {"components": ["battery"], "connections": []},
    )

    response = client.post(
        "/cv/image-to-circuit",
        files={"image": ("circuit.png", b"fake", "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
