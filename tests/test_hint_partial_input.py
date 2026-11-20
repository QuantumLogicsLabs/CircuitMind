"""
Tests for the partially-wired logic gate hint.

A gate that has one input connected but needs two is a common in-progress
state; the rule-based hint should point at it before falling back to the
generic truth-table advice.
"""

from hint.hint_module import _find_partially_wired_gate, _hint_with_rules


def _wire(from_id, to_id):
    return {"fromId": from_id, "toId": to_id}


def test_and_gate_with_one_input_is_detected():
    gates = [{"id": 1, "type": "AND", "label": "G1"}]
    found = _find_partially_wired_gate(gates, [_wire(9, 1)])
    assert found == (gates[0], 1, 2)


def test_single_input_gate_is_not_flagged():
    gates = [{"id": 1, "type": "NOT", "label": "N1"}]
    assert _find_partially_wired_gate(gates, [_wire(9, 1)]) is None


def test_fully_wired_and_gate_is_not_flagged():
    gates = [{"id": 1, "type": "AND", "label": "G1"}]
    wires = [_wire(8, 1), _wire(9, 1)]
    assert _find_partially_wired_gate(gates, wires) is None


def test_gate_with_zero_inputs_is_left_to_floating_check():
    gates = [{"id": 1, "type": "XOR", "label": "X1"}]
    assert _find_partially_wired_gate(gates, [_wire(1, 9)]) is None


def test_non_logic_gate_types_are_ignored():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "OUTPUT", "label": "Y"},
    ]
    assert _find_partially_wired_gate(gates, [_wire(1, 2)]) is None


def test_hint_with_rules_reports_partial_gate():
    payload = {
        "inputs": ["A"],
        "outputs": ["Y"],
        "gates": [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "AND", "label": "G1"},
            {"id": 3, "type": "OUTPUT", "label": "Y"},
        ],
        "wires": [_wire(1, 2), _wire(2, 3)],
    }
    hint = _hint_with_rules(payload)
    assert "G1" in hint
    assert "1 of 2" in hint


def test_hint_with_rules_keeps_generic_advice_when_fully_wired():
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
    hint = _hint_with_rules(payload)
    assert "truth table" in hint
