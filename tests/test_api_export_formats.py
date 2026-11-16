"""HTTP coverage for the /export formats that had none.

Only SPICE was exercised through the API. These tests drive gate_json and
SVG through the route and pin the default format and gate_json shape.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import app

client = TestClient(app)

LED_CIRCUIT = {
    "circuit_name": "LED",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
}

HALF_ADDER = {
    "circuit_name": "Half Adder",
    "components": [
        "input_a",
        "input_b",
        "xor",
        "and",
        "sum_output",
        "carry_output",
    ],
    "connections": [
        "input_a -> xor -> sum_output",
        "input_b -> xor",
        "input_a -> and -> carry_output",
        "input_b -> and",
    ],
}


def _export(circuit, export_format=None):
    body = {"circuit_json": circuit}
    if export_format is not None:
        body["export_format"] = export_format
    return client.post("/export", json=body)


@pytest.fixture(autouse=True)
def reset_limiter():
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


def test_default_format_is_spice():
    response = _export(LED_CIRCUIT)

    assert response.status_code == 200
    body = response.json()
    assert body["format"] == "spice"
    assert body["spice_netlist"].splitlines()[-1] == ".end"


def test_gate_json_preserves_the_digital_circuit():
    response = _export(HALF_ADDER, "gate_json")

    assert response.status_code == 200
    body = response.json()
    assert body["format"] == "gate_json"

    gate_json = body["gate_json"]
    gates = gate_json["gates"]
    types = [gate["type"] for gate in gates]

    assert gate_json["inputCounter"] == 2
    assert gate_json["outputCounter"] == 2
    assert types.count("INPUT") == 2
    assert {"XOR", "AND"} <= set(types)
    assert {"A", "B", "SUM", "CARRY"} <= {gate["label"] for gate in gates}


def test_gate_json_wires_every_connection_once():
    gate_json = _export(HALF_ADDER, "gate_json").json()["gate_json"]

    assert gate_json["gateIdCounter"] == 6
    assert gate_json["wireIdCounter"] == 6
    assert len(gate_json["wires"]) == 6
    assert all(
        wire["fromId"] != wire["toId"] for wire in gate_json["wires"]
    )


def test_gate_json_is_timestamped_in_utc():
    gate_json = _export(HALF_ADDER, "gate_json").json()["gate_json"]

    assert gate_json["exportedAt"].endswith("Z")
    assert gate_json["exportedAt"][:2].isdigit()


def test_svg_export_returns_markup():
    response = _export(LED_CIRCUIT, "svg")

    assert response.status_code == 200
    body = response.json()
    assert body["format"] == "svg"
    assert "<svg" in body["svg_markup"]
    assert "Led" in body["svg_markup"]


def test_svg_export_rejects_a_circuit_with_nothing_to_draw():
    response = _export({"circuit_name": "Empty", "components": [], "connections": []}, "svg")

    assert response.status_code == 422
    assert "No drawable components" in response.json()["detail"]
