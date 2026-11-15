"""Tests for the shared Streamlit payload loader."""

from utils.payload_loader import load_circuit_payload


CIRCUIT = {"circuit_name": "LED", "components": ["battery", "led"], "connections": []}


def test_bare_circuit_object_is_returned():
    payload, error = load_circuit_payload('{"components": ["battery"], "connections": []}')
    assert error is None
    assert payload == {"components": ["battery"], "connections": []}


def test_circuit_json_envelope_is_unwrapped():
    payload, error = load_circuit_payload('{"circuit_json": {"components": [], "connections": []}}')
    assert error is None
    assert payload == {"components": [], "connections": []}


def test_empty_input_is_reported():
    assert load_circuit_payload("") == (None, "Paste a circuit JSON object first.")
    assert load_circuit_payload("   \n") == (None, "Paste a circuit JSON object first.")


def test_invalid_json_is_reported_without_raising():
    payload, error = load_circuit_payload("{not json")
    assert payload is None
    assert error.startswith("Invalid JSON:")


def test_json_array_is_rejected():
    payload, error = load_circuit_payload("[1, 2, 3]")
    assert payload is None
    assert "must be an object" in error


def test_envelope_holding_a_non_object_is_rejected():
    payload, error = load_circuit_payload('{"circuit_json": ["battery"]}')
    assert payload is None
    assert "must be an object" in error


def test_valid_circuit_round_trips_unchanged():
    import json
    payload, error = load_circuit_payload(json.dumps(CIRCUIT))
    assert error is None
    assert payload == CIRCUIT
