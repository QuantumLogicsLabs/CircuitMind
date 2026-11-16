"""HTTP coverage for the /hint route.

The hint module has rule tests, but the route itself (defaults, payload
pass-through, identify mode and auth) was untested.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import api.app as api_app
from api.app import app
import hint.hint_module as hint_module

client = TestClient(app)


@pytest.fixture(autouse=True)
def force_rule_based(monkeypatch):
    # Keep these route tests offline regardless of the local Groq setup.
    monkeypatch.setattr(hint_module, "GROQ_AVAILABLE", False)


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def test_empty_canvas_gets_a_rule_based_hint():
    response = client.post(
        "/hint",
        json={
            "problem_title": "Half adder",
            "inputs": ["A", "B"],
            "outputs": ["SUM", "CARRY"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "rule-based"
    assert "INPUT" in body["hint"]
    assert "OUTPUT" in body["hint"]


def test_identify_request_names_the_circuit():
    response = client.post(
        "/hint",
        json={
            "request_type": "identify",
            "problem_title": "Design a Half Adder",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["circuit_name"] == "Half Adder"
    assert "Half Adder" in body["hint"]
    assert body["source"] == "rule-based"


def test_payload_defaults_are_filled_before_dispatch(monkeypatch):
    seen = {}

    def fake_hint(payload):
        seen.update(payload)
        return {"hint": "stub", "source": "rule-based"}

    monkeypatch.setattr(api_app, "generate_hint", fake_hint)

    response = client.post(
        "/hint",
        json={
            "problem_title": "Half adder",
            "inputs": ["A"],
            "outputs": ["SUM"],
            "truth_table": [{"A": 0, "SUM": 0}],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"hint": "stub", "source": "rule-based"}
    assert seen["request_type"] == "hint"
    assert seen["problem_description"] == ""
    assert seen["inputs"] == ["A"]
    assert seen["outputs"] == ["SUM"]
    assert seen["truth_table"] == [{"A": 0, "SUM": 0}]
    assert seen["gates"] == []
    assert seen["wires"] == []
    assert seen["last_result"] is None


def test_inputs_must_be_a_list_of_strings():
    response = client.post("/hint", json={"inputs": "A, B"})

    assert response.status_code == 422


def test_route_requires_an_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(api_app, "API_KEY", "secret-key")

    response = client.post("/hint", json={"problem_title": "Half adder"})

    assert response.status_code == 401
