"""
Tests that the CV routes offload blocking inference to a worker thread.

YOLO inference and OpenCV wire tracing are CPU-bound and can take seconds.
Running them directly inside the async handlers blocks the event loop, so
both routes must go through run_in_threadpool.
"""

import pytest
from fastapi.testclient import TestClient

import cv_module.cv_api as cv_api


@pytest.fixture
def client():
    return TestClient(cv_api.app)


@pytest.fixture
def captured(monkeypatch):
    calls = []

    async def fake_run_in_threadpool(func, *args, **kwargs):
        calls.append((func, args, kwargs))
        return func(*args, **kwargs)

    monkeypatch.setattr(cv_api, "run_in_threadpool", fake_run_in_threadpool)
    return calls


def test_image_route_offloads_to_threadpool(client, captured, monkeypatch):
    def fake_infer(path, model):
        return {"components": ["battery"], "connections": []}

    monkeypatch.setattr(cv_api, "image_to_circuit_json", fake_infer)

    response = client.post(
        "/cv/image-to-circuit",
        files={"image": ("circuit.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(captured) == 1
    assert captured[0][0] is fake_infer


def test_batch_route_offloads_each_image(client, captured, monkeypatch):
    def fake_infer(path, model):
        return {"components": [], "connections": []}

    monkeypatch.setattr(cv_api, "image_to_circuit_json", fake_infer)

    response = client.post(
        "/cv/batch-process",
        files=[
            ("images", ("one.png", b"a", "image/png")),
            ("images", ("two.png", b"b", "image/png")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["successful"] == 2
    assert len(captured) == 2
    assert all(call[0] is fake_infer for call in captured)


def test_inference_failure_still_returns_500(client, captured, monkeypatch):
    def boom(path, model):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(cv_api, "image_to_circuit_json", boom)

    response = client.post(
        "/cv/image-to-circuit",
        files={"image": ("circuit.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 500
    assert "model exploded" in response.json()["detail"]


def test_batch_keeps_going_after_one_failure(client, captured, monkeypatch):
    def flaky(path, model):
        raise RuntimeError("bad image")

    monkeypatch.setattr(cv_api, "image_to_circuit_json", flaky)

    response = client.post(
        "/cv/batch-process",
        files=[("images", ("one.png", b"a", "image/png"))],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["failed"] == 1
    assert body["results"][0]["success"] is False


def test_rejects_non_image_content_type(client, captured):
    response = client.post(
        "/cv/image-to-circuit",
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert captured == []
