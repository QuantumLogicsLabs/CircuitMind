"""Regression tests: CV API must not leak exception details to clients.

The 500 handler and the batch endpoint echoed str(exception) in the
response, exposing internal paths and library internals.
"""

import pytest
from fastapi.testclient import TestClient

import cv_module.cv_api as cv_api

SECRET = "super-secret internal detail at C:/private/models/best.pt"


@pytest.fixture()
def client():
    return TestClient(cv_api.app)


def test_image_to_circuit_hides_exception_text(client, monkeypatch):
    def boom(**_kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(cv_api, "image_to_circuit_json", boom)

    response = client.post(
        "/cv/image-to-circuit",
        files={"image": ("board.png", b"\x89PNG", "image/png")},
    )

    assert response.status_code == 500
    assert SECRET not in response.text
    assert "Error processing image" in response.json()["detail"]


def test_image_to_circuit_rejects_non_image(client):
    response = client.post(
        "/cv/image-to-circuit",
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_batch_process_hides_exception_text(client, monkeypatch):
    def boom(*_args, **_kwargs):
        raise RuntimeError(SECRET)

    monkeypatch.setattr(cv_api, "image_to_circuit_json", boom)

    response = client.post(
        "/cv/batch-process",
        files=[
            ("images", ("a.png", b"\x89PNG", "image/png")),
            ("images", ("b.png", b"\x89PNG", "image/png")),
        ],
    )

    body = response.json()
    assert response.status_code == 200
    assert body["failed"] == 2
    assert SECRET not in response.text
    assert all("processing failed" in r["error"] for r in body["results"])


def test_batch_process_reports_success(client, monkeypatch):
    monkeypatch.setattr(
        cv_api,
        "image_to_circuit_json",
        lambda *_args, **_kwargs: {"components": ["led"], "connections": []},
    )

    response = client.post(
        "/cv/batch-process",
        files=[("images", ("a.png", b"\x89PNG", "image/png"))],
    )

    body = response.json()
    assert body["successful"] == 1
    assert body["results"][0]["circuit_data"]["components"] == ["led"]
