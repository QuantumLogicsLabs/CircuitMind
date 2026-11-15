"""Tests for the CV module batch-size guard."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

import cv_module.cv_api as cv_api
from cv_module.cv_api import MAX_BATCH_IMAGES

app = FastAPI()
app.include_router(cv_api.router)
client = TestClient(app)


def _files(count):
    return [
        ("images", (f"img{i}.png", b"\x89PNG\r\n\x1a\n", "image/png"))
        for i in range(count)
    ]


def test_batch_over_the_limit_is_rejected_before_processing(monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("processing must not start for an oversized batch")

    monkeypatch.setattr(cv_api, "image_to_circuit_json", explode)

    response = client.post("/cv/batch-process", files=_files(MAX_BATCH_IMAGES + 1))

    assert response.status_code == 400
    assert str(MAX_BATCH_IMAGES) in response.json()["detail"]


def test_batch_at_the_limit_is_processed(monkeypatch):
    monkeypatch.setattr(
        cv_api, "image_to_circuit_json", lambda path, model: {"components": []}
    )

    response = client.post("/cv/batch-process", files=_files(MAX_BATCH_IMAGES))

    assert response.status_code == 200
    assert response.json()["total"] == MAX_BATCH_IMAGES
    assert response.json()["successful"] == MAX_BATCH_IMAGES


def test_status_advertises_the_batch_limit():
    response = client.get("/cv/status")
    assert response.status_code == 200
    assert response.json()["max_batch_images"] == MAX_BATCH_IMAGES
