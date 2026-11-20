"""
Tests for utils/circuit_state.py.

Reusing a generated circuit writes the same JSON text into the Explain,
Diagnose and Export text areas, which are keyed "explain", "diag" and
"export_area" respectively.
"""

import json

from utils.circuit_state import circuit_text, reuse_values

CIRCUIT = {
    "circuit_name": "LED Circuit",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
}


def test_circuit_text_is_indented_json():
    text = circuit_text(CIRCUIT)
    assert "\n" in text
    assert json.loads(text) == CIRCUIT


def test_reuse_values_targets_all_three_tabs():
    values = reuse_values(CIRCUIT)
    assert set(values) == {"explain", "diag", "export_area"}


def test_reuse_values_are_identical_and_parse_back():
    values = reuse_values(CIRCUIT)
    assert len(set(values.values())) == 1
    assert json.loads(values["diag"])["circuit_name"] == "LED Circuit"
