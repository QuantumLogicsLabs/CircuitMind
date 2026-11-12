"""
CircuitMind - Hint identification tests
tests/test_hint_identify.py

An identify request must not present the problem title as a circuit name:
"You have created a Problem 3 circuit." is worse than admitting uncertainty.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hint.hint_module as hint_module
from hint.hint_module import _identify_circuit, generate_hint


def _payload(**overrides):
    payload = {
        "request_type": "identify",
        "problem_title": "",
        "problem_description": "",
        "inputs": ["A", "B"],
        "outputs": ["S", "C"],
        "gates": [],
        "wires": [],
    }
    payload.update(overrides)
    return payload


# ── _identify_circuit ─────────────────────────────────────────────────────────

def test_arbitrary_title_is_not_a_circuit_name():
    assert _identify_circuit(_payload(problem_title="Problem 3")) is None


def test_empty_payload_is_not_a_circuit_name():
    assert _identify_circuit({}) is None


def test_known_circuit_from_title():
    assert _identify_circuit(_payload(problem_title="Half Adder")) == "Half Adder"


def test_known_circuit_from_description():
    payload = _payload(problem_description="Build a 2-to-1 multiplexer with a select line")
    assert _identify_circuit(payload) == "Multiplexer"


def test_half_adder_from_gate_signature():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "INPUT", "label": "B"},
        {"id": 3, "type": "XOR", "label": "XOR1"},
        {"id": 4, "type": "AND", "label": "AND1"},
        {"id": 5, "type": "OUTPUT", "label": "S"},
        {"id": 6, "type": "OUTPUT", "label": "C"},
    ]
    assert _identify_circuit(_payload(gates=gates)) == "Half Adder"


def test_gate_signature_needs_matching_io_counts():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 3, "type": "XOR", "label": "XOR1"},
        {"id": 5, "type": "OUTPUT", "label": "S"},
    ]
    assert _identify_circuit(_payload(gates=gates)) is None


# ── generate_hint ─────────────────────────────────────────────────────────────

def test_identify_known_circuit_skips_the_llm(monkeypatch):
    def fail(payload):
        raise AssertionError("LLM should not be called for a known circuit")

    monkeypatch.setattr(hint_module, "_hint_with_llm", fail)

    result = generate_hint(_payload(problem_title="Full Adder"))

    assert result["circuit_name"] == "Full Adder"
    assert result["source"] == "rule-based"


def test_identify_unknown_circuit_asks_the_llm(monkeypatch):
    monkeypatch.setattr(hint_module, "_hint_with_llm", lambda payload: "This looks like a 2-bit comparator.")

    result = generate_hint(_payload(problem_title="Problem 3"))

    assert result["source"] == "llm"
    assert "comparator" in result["hint"]
    assert "circuit_name" not in result


def test_identify_unknown_circuit_without_llm_admits_uncertainty(monkeypatch):
    def boom(payload):
        raise RuntimeError("GROQ_API_KEY not set in environment")

    monkeypatch.setattr(hint_module, "_hint_with_llm", boom)

    result = generate_hint(_payload(problem_title="Problem 3"))

    assert result["source"] == "rule-based"
    assert "can't confidently identify" in result["hint"]
    assert "Problem 3" not in result["hint"]
    assert "circuit_name" not in result
