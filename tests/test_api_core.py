"""Behavioural tests for the core FastAPI endpoints.

Covers request validation and how module-level results are mapped onto HTTP
status codes. The suite previously had no API tests at all.
"""

import sys
import os

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app

client = TestClient(app)

LED_BODY = {
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


def test_health_endpoints_report_ok():
    assert client.get("/").json()["status"] == "running"
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("prompt", ["", "   ", "\n\t"])
def test_generate_rejects_blank_prompts(prompt):
    response = client.post("/generate", json={"prompt": prompt})

    assert response.status_code == 422


def test_generate_rejects_overlong_prompt():
    response = client.post("/generate", json={"prompt": "x" * 1001})

    assert response.status_code == 422


def test_generate_maps_module_error_to_422(monkeypatch):
    monkeypatch.setattr(
        "api.app.generate_circuit",
        lambda prompt: {"error": "cannot generate", "components": [], "connections": []},
    )

    response = client.post("/generate", json={"prompt": "a valid prompt"})

    assert response.status_code == 422
    assert response.json()["detail"] == "cannot generate"


def test_generate_returns_rule_based_circuit():
    response = client.post("/generate", json={"prompt": "make me a LED circuit"})

    assert response.status_code == 200
    body = response.json()
    assert body["circuit_name"] == "LED Circuit"
    assert "led" in body["components"]


def test_explain_handles_empty_circuit():
    response = client.post("/explain", json={"circuit_json": {}})

    assert response.status_code == 200
    body = response.json()
    assert "No components provided" in body["explanation"]
    assert body["component_details"] == []


def test_explain_reports_unknown_components():
    body = {
        "circuit_json": {
            "circuit_name": "Mystery",
            "components": ["gizmo"],
            "connections": [],
        }
    }

    response = client.post("/explain", json=body)

    assert response.status_code == 200
    assert any("Unknown component" in warning for warning in response.json()["warnings"])


@pytest.mark.parametrize("fmt", ["pdf", "netlist", ""])
def test_export_rejects_invalid_formats(fmt):
    response = client.post("/export", json={**LED_BODY, "export_format": fmt})

    assert response.status_code == 422


def test_export_rejects_missing_fields():
    response = client.post("/export", json={"circuit_json": {"circuit_name": "x"}})

    assert response.status_code == 422
    assert "Missing required fields" in response.json()["detail"]


def test_export_spice_succeeds():
    response = client.post("/export", json={**LED_BODY, "export_format": "spice"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["spice_netlist"].splitlines()[-1] == ".end"
