"""Regression tests for HintRequest.request_type validation.

The model accepted any string, so a typo such as "identfy" silently fell
back to a normal hint instead of identifying the circuit or rejecting the
request.
"""

import pytest
from fastapi.testclient import TestClient

import api.app as app_module


@pytest.fixture()
def client(monkeypatch):
    captured = {}

    def fake_hint(payload):
        captured.update(payload)
        return {"hint": "stub", "source": "rule-based"}

    monkeypatch.setattr(app_module, "generate_hint", fake_hint)
    return TestClient(app_module.app), captured


def test_default_request_type_is_hint(client):
    http, captured = client
    response = http.post("/hint", json={"problem_title": "Adder"})
    assert response.status_code == 200
    assert captured["request_type"] == "hint"


def test_identify_is_accepted(client):
    http, captured = client
    response = http.post("/hint", json={"request_type": "identify"})
    assert response.status_code == 200
    assert captured["request_type"] == "identify"


def test_request_type_is_case_insensitive(client):
    http, captured = client
    response = http.post("/hint", json={"request_type": " Identify "})
    assert response.status_code == 200
    assert captured["request_type"] == "identify"


def test_unknown_request_type_is_rejected(client):
    http, _ = client
    response = http.post("/hint", json={"request_type": "solve"})
    assert response.status_code == 422
    assert "request_type" in response.text
