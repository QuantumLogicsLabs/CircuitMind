"""
Tests for the OUTPUT-used-as-source hint.

An OUTPUT gate must only display results. When a student wires one into
another gate the circuit cannot match the truth table, so the rule-based
hint should name that gate instead of giving generic advice.
"""

from hint.hint_module import _find_output_used_as_source, _hint_with_rules


def _wire(from_id, to_id):
    return {"fromId": from_id, "toId": to_id}


def test_output_driving_another_gate_is_detected():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "AND", "label": "G1"},
        {"id": 3, "type": "OUTPUT", "label": "Y"},
    ]
    found = _find_output_used_as_source(gates, [_wire(1, 2), _wire(3, 2)])
    assert found is gates[2]


def test_normal_input_to_output_flow_is_not_flagged():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "AND", "label": "G1"},
        {"id": 3, "type": "OUTPUT", "label": "Y"},
    ]
    assert _find_output_used_as_source(gates, [_wire(1, 2), _wire(2, 3)]) is None


def test_no_wires_is_not_flagged():
    gates = [{"id": 1, "type": "OUTPUT", "label": "Y"}]
    assert _find_output_used_as_source(gates, []) is None


def test_hint_with_rules_names_the_reversed_output():
    payload = {
        "inputs": ["A"],
        "outputs": ["Y"],
        "gates": [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "AND", "label": "G1"},
            {"id": 3, "type": "OUTPUT", "label": "Y"},
        ],
        "wires": [_wire(1, 2), _wire(3, 2), _wire(2, 3)],
    }
    hint = _hint_with_rules(payload)
    assert "'Y'" in hint
    assert "OUTPUT" in hint


def test_hint_with_rules_keeps_generic_advice_for_correct_flow():
    payload = {
        "inputs": ["A", "B"],
        "outputs": ["Y"],
        "gates": [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "INPUT", "label": "B"},
            {"id": 3, "type": "AND", "label": "G1"},
            {"id": 4, "type": "OUTPUT", "label": "Y"},
        ],
        "wires": [_wire(1, 3), _wire(2, 3), _wire(3, 4)],
    }
    assert "truth table" in _hint_with_rules(payload)
