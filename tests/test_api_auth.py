"""API-key authentication behaviour.

``verify_api_key`` is a no-op when CIRCUITMIND_API_KEY is unset and otherwise
requires a matching X-API-Key header. These tests pin both modes.
"""

import sys
import os

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import app

client = TestClient(app)

EXPLAIN_BODY = {
    "circuit_json": {
        "circuit_name": "LED",
        "components": ["battery", "resistor", "led"],
        "connections": ["battery -> resistor -> led"],
    }
}


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def test_open_access_when_key_not_configured(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", None)

    response = client.post("/explain", json=EXPLAIN_BODY)

    assert response.status_code == 200


def test_missing_header_is_rejected_when_key_configured(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", "secret-key")

    response = client.post("/explain", json=EXPLAIN_BODY)

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_wrong_key_is_rejected(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", "secret-key")

    response = client.post(
        "/explain", json=EXPLAIN_BODY, headers={"X-API-Key": "wrong"}
    )

    assert response.status_code == 401


def test_correct_key_is_accepted(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", "secret-key")

    response = client.post(
        "/explain", json=EXPLAIN_BODY, headers={"X-API-Key": "secret-key"}
    )

    assert response.status_code == 200


def test_health_routes_do_not_require_a_key(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", "secret-key")

    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
