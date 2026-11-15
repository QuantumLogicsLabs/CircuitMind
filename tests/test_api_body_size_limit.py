"""Tests for the request body size cap middleware."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from api.app import MAX_REQUEST_BODY_BYTES, BodySizeLimitMiddleware, app


@pytest.fixture()
def client():
    return TestClient(app)


def test_oversized_body_is_rejected_with_413(client):
    oversized = b"x" * (MAX_REQUEST_BODY_BYTES + 1)
    response = client.post(
        "/generate",
        content=oversized,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]


def test_body_at_the_limit_is_not_rejected_by_the_cap(client):
    # One byte under the cap must reach the app (the app may still reject the
    # payload for being invalid JSON; what matters is that it is not a 413).
    at_limit = b"x" * (MAX_REQUEST_BODY_BYTES - 1)
    response = client.post(
        "/generate",
        content=at_limit,
        headers={"content-type": "application/json"},
    )
    assert response.status_code != 413


def test_small_body_passes_through(client):
    assert client.get("/health").status_code == 200


def test_streamed_body_without_content_length_is_capped(client):
    def chunks():
        for _ in range(4):
            yield b"x" * (MAX_REQUEST_BODY_BYTES // 2)

    response = client.post("/generate", content=chunks())
    assert response.status_code == 413


def test_invalid_content_length_is_rejected():
    sent = []
    reached_app = False

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    async def downstream(scope, receive, send):
        nonlocal reached_app
        reached_app = True

    middleware = BodySizeLimitMiddleware(downstream, max_bytes=16)
    scope = {"type": "http", "headers": [(b"content-length", b"not-a-number")]}

    asyncio.run(middleware(scope, receive, send))

    assert sent[0]["status"] == 400
    assert reached_app is False


def test_non_http_scopes_are_ignored():
    sent = []
    reached_app = False

    async def receive():
        return {"type": "lifespan.startup"}

    async def send(message):
        sent.append(message)

    async def downstream(scope, receive, send):
        nonlocal reached_app
        reached_app = True

    middleware = BodySizeLimitMiddleware(downstream, max_bytes=1)
    asyncio.run(middleware({"type": "lifespan"}, receive, send))

    assert reached_app is True
    assert sent == []
