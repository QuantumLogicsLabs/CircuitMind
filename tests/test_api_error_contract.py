"""Error-contract tests for the API.

Clients need stable behaviour for unknown paths, wrong methods, invalid
bodies and unhandled exceptions. The last case is also the boundary that must
not leak internal exception text.
"""

import logging
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def test_unknown_path_is_a_json_404():
    response = client.get("/no-such-endpoint")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "Not Found"}


def test_wrong_method_is_a_json_405():
    response = client.get("/generate")

    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


def test_invalid_body_lists_the_field_errors():
    response = client.post("/generate", json={})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail
    assert detail[0]["loc"] == ["body", "prompt"]


def test_non_json_body_is_rejected():
    response = client.post(
        "/explain", content="not json", headers={"content-type": "text/plain"}
    )

    assert response.status_code == 422


def test_unhandled_errors_are_generic_and_logged(monkeypatch, caplog):
    def explode(circuit):
        raise RuntimeError("secret-internal-detail")

    monkeypatch.setattr(api_app, "explain_circuit", explode)
    safe_client = TestClient(app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR):
        response = safe_client.post(
            "/explain", json={"circuit_json": {"components": [], "connections": []}}
        )

    assert response.status_code == 500
    assert response.json() == {
        "error": "Internal server error. Please try again."
    }
    assert "secret-internal-detail" not in response.text
    assert "secret-internal-detail" in caplog.text
