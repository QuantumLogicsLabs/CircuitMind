"""Regression tests: module errors must surface as HTTP 422.

/generate and /export already mapped module-level errors to 422, but
/explain and /diagnose returned them with HTTP 200, so clients could not
tell a successful explanation from a rejected payload.
"""

import pytest
from fastapi.testclient import TestClient

import api.app as app_module


@pytest.fixture()
def client():
    return TestClient(app_module.app)


def test_explain_module_error_returns_422(client, monkeypatch):
    monkeypatch.setattr(
        app_module, "explain_circuit", lambda circuit: {"error": "bad payload"}
    )
    response = client.post("/explain", json={"circuit_json": {"components": []}})
    assert response.status_code == 422
    assert response.json()["detail"] == "bad payload"


def test_diagnose_module_error_returns_422(client, monkeypatch):
    monkeypatch.setattr(
        app_module, "diagnose_circuit", lambda circuit: {"error": "bad payload"}
    )
    response = client.post("/diagnose", json={"circuit_json": {"components": []}})
    assert response.status_code == 422
    assert response.json()["detail"] == "bad payload"


def test_explain_success_still_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "explain_circuit",
        lambda circuit: {"explanation": "A simple circuit.", "warnings": []},
    )
    response = client.post("/explain", json={"circuit_json": {"components": ["led"]}})
    assert response.status_code == 200
    assert response.json()["explanation"] == "A simple circuit."


def test_diagnose_success_still_returns_200(client, monkeypatch):
    monkeypatch.setattr(
        app_module,
        "diagnose_circuit",
        lambda circuit: {"passed": True, "issues": []},
    )
    response = client.post("/diagnose", json={"circuit_json": {"components": []}})
    assert response.status_code == 200
    assert response.json()["passed"] is True


def test_explain_error_key_falsy_is_not_422(client, monkeypatch):
    # Only a truthy error message signals a rejected payload.
    monkeypatch.setattr(
        app_module, "explain_circuit", lambda circuit: {"explanation": "ok", "error": ""}
    )
    response = client.post("/explain", json={"circuit_json": {"components": []}})
    assert response.status_code == 200
