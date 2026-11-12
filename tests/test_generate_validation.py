"""
CircuitMind - LLM output validation tests
tests/test_generate_validation.py

Malformed LLM responses must never reach the API layer; the generator should
fall back to the rule-based engine instead of returning a broken circuit.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import generate.generate as gen
from generate.generate import _validate_llm_circuit, generate_circuit


VALID_PAYLOAD = {
    "circuit_name": "LED Circuit",
    "components":   ["battery", "resistor", "led"],
    "connections":  ["battery -> resistor -> led"],
    "confidence":   "high",
    "description":  "Basic LED circuit",
}


# ── _validate_llm_circuit ──────────────────────────────────────────────────────

def test_valid_payload_is_accepted():
    result = _validate_llm_circuit(dict(VALID_PAYLOAD))

    assert result["circuit_name"] == "LED Circuit"
    assert result["components"] == ["battery", "resistor", "led"]
    assert result["connections"] == ["battery -> resistor -> led"]
    assert result["source"] == "llm"


def test_whitespace_is_trimmed():
    result = _validate_llm_circuit({
        "circuit_name": "  LED  ",
        "components":   [" battery ", "led "],
        "connections":  [" battery -> led "],
    })

    assert result["circuit_name"] == "LED"
    assert result["components"] == ["battery", "led"]
    assert result["connections"] == ["battery -> led"]


def test_unknown_confidence_is_normalized():
    result = _validate_llm_circuit({**VALID_PAYLOAD, "confidence": "certain"})

    assert result["confidence"] == "medium"


def test_missing_description_defaults_to_empty_string():
    payload = dict(VALID_PAYLOAD)
    payload.pop("description")

    assert _validate_llm_circuit(payload)["description"] == ""


@pytest.mark.parametrize("payload", [
    None,
    [],
    "not json",
    42,
])
def test_non_object_payload_rejected(payload):
    with pytest.raises(ValueError):
        _validate_llm_circuit(payload)


@pytest.mark.parametrize("name", [None, "", "   ", 7, ["LED"]])
def test_missing_or_invalid_name_rejected(name):
    with pytest.raises(ValueError):
        _validate_llm_circuit({**VALID_PAYLOAD, "circuit_name": name})


@pytest.mark.parametrize("components", [None, "battery,led", [], [""], ["battery", 3], {"led": True}])
def test_invalid_components_rejected(components):
    with pytest.raises(ValueError):
        _validate_llm_circuit({**VALID_PAYLOAD, "components": components})


@pytest.mark.parametrize("connections", [None, "battery -> led", [], [" "], ["battery -> led", 3], {"a": "b"}])
def test_invalid_connections_rejected(connections):
    with pytest.raises(ValueError):
        _validate_llm_circuit({**VALID_PAYLOAD, "connections": connections})


# ── generate_circuit fallback behaviour ────────────────────────────────────────

def test_malformed_llm_output_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr(gen, "generate_with_llm", lambda prompt: {"circuit_name": "broken"})

    result = generate_circuit("make me a LED circuit")

    assert result["source"] == "rule-based"
    assert "led" in result["components"]


def test_llm_exception_falls_back_to_rules(monkeypatch):
    def boom(prompt):
        raise RuntimeError("GROQ_API_KEY not set in environment")

    monkeypatch.setattr(gen, "generate_with_llm", boom)

    result = generate_circuit("make me a LED circuit")

    assert result["source"] == "rule-based"
    assert result["circuit_name"] == "LED Circuit"


def test_valid_llm_output_is_returned(monkeypatch):
    monkeypatch.setattr(gen, "generate_with_llm", lambda prompt: dict(VALID_PAYLOAD))

    result = generate_circuit("make me a LED circuit")

    assert result["source"] == "llm"
    assert result["circuit_name"] == "LED Circuit"


def test_invalid_input_still_short_circuits():
    result = generate_circuit("  ")

    assert result["error_code"] == "INVALID_INPUT"
    assert result["components"] == []
    assert result["connections"] == []
