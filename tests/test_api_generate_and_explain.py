"""Behavioural tests for the /generate-and-explain composition route.

The route chains three modules, so it needs coverage for the happy path, the
module error mapping and the request contract on its own.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import app

client = TestClient(app)

LED_CIRCUIT = {
    "circuit_name": "LED Circuit",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
    "confidence": "high",
    "description": "Basic LED circuit",
    "source": "rule-based",
}


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def test_rule_based_prompt_returns_all_three_sections():
    response = client.post(
        "/generate-and-explain", json={"prompt": "make me a LED circuit"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["circuit"]["circuit_name"] == "LED Circuit"
    assert "explanation" in body["explanation"]
    assert "component_details" in body["explanation"]
    assert body["diagnosis"]["circuit_name"] == "LED Circuit"
    assert "issues" in body["diagnosis"]


def test_explain_and_diagnose_receive_the_generated_circuit(monkeypatch):
    seen = {}

    monkeypatch.setattr(api_app, "generate_circuit", lambda prompt: LED_CIRCUIT)
    monkeypatch.setattr(
        api_app,
        "explain_circuit",
        lambda circuit: seen.setdefault("explain", circuit) and {},
    )
    monkeypatch.setattr(
        api_app,
        "diagnose_circuit",
        lambda circuit: seen.setdefault("diagnose", circuit) and {},
    )

    response = client.post("/generate-and-explain", json={"prompt": "LED"})

    assert response.status_code == 200
    assert seen["explain"] is LED_CIRCUIT
    assert seen["diagnose"] is LED_CIRCUIT


def test_generation_error_is_mapped_to_422(monkeypatch):
    monkeypatch.setattr(
        api_app,
        "generate_circuit",
        lambda prompt: {"error": "cannot generate", "components": [], "connections": []},
    )

    response = client.post("/generate-and-explain", json={"prompt": "nonsense"})

    assert response.status_code == 422
    assert response.json()["detail"] == "cannot generate"


@pytest.mark.parametrize("prompt", ["", "   ", "x" * 1001])
def test_invalid_prompts_are_rejected(prompt):
    response = client.post("/generate-and-explain", json={"prompt": prompt})

    assert response.status_code == 422


def test_route_requires_an_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", "secret-key")

    response = client.post("/generate-and-explain", json={"prompt": "LED"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"
