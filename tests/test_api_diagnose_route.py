"""HTTP coverage for the /diagnose route.

The diagnose module is covered in places, but the route's response contract
(structured issues, legacy strings, summary counts) was not exercised.
"""

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


def _diagnose(circuit):
    return client.post("/diagnose", json={"circuit_json": circuit})


def test_response_has_the_documented_shape():
    response = _diagnose(
        {
            "circuit_name": "LED",
            "components": ["battery", "resistor", "led"],
            "connections": ["battery -> resistor -> led"],
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert body["circuit_name"] == "LED"
    assert isinstance(body["passed"], bool)
    assert isinstance(body["issues"], list)
    assert isinstance(body["legacy_issues"], list)
    assert set(body["summary"]) == {"errors", "warnings", "info"}


def test_missing_power_source_is_a_structured_error():
    response = _diagnose(
        {
            "circuit_name": "No Power",
            "components": ["resistor", "led"],
            "connections": ["resistor -> led"],
        }
    )

    body = response.json()
    assert body["passed"] is False
    assert body["summary"]["errors"] == 1

    issue = body["issues"][0]
    assert issue["severity"] == "error"
    assert issue["code"] == "NO_POWER_SOURCE"
    assert "power source" in issue["message"]
    assert issue["suggestion"]
    assert body["legacy_issues"][0].startswith("Error: ")


def test_floating_component_is_a_warning_not_a_failure():
    response = _diagnose(
        {
            "circuit_name": "Floating LED",
            "components": ["battery", "resistor", "led"],
            "connections": ["battery -> resistor"],
        }
    )

    body = response.json()
    assert body["passed"] is True
    assert body["summary"] == {"errors": 0, "warnings": 1, "info": 0}

    issue = body["issues"][0]
    assert issue["code"] == "FLOATING_COMPONENT"
    assert issue["severity"] == "warning"
    assert "led" in issue["message"]


def test_empty_circuit_gets_the_default_name():
    body = _diagnose({}).json()

    assert body["circuit_name"] == "Unnamed Circuit"
    assert body["passed"] is False
    assert body["issues"][0]["code"] == "NO_POWER_SOURCE"


def test_circuit_json_must_be_an_object():
    response = client.post("/diagnose", json={"circuit_json": []})

    assert response.status_code == 422


def test_route_requires_an_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", "secret-key")

    response = _diagnose({"components": [], "connections": []})

    assert response.status_code == 401
