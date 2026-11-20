"""
Tests for the dead-end logic gate hint.

A gate that never reaches an OUTPUT wastes its inputs: no matter how it is
configured, it cannot change the truth-table result. The rule-based hint
should point at that gate before generic advice.
"""

from hint.hint_module import _find_gate_without_path_to_output, _hint_with_rules


def _wire(from_id, to_id):
    return {"fromId": from_id, "toId": to_id}


def test_gate_with_direct_path_to_output_is_fine():
    gates = [
        {"id": 1, "type": "AND", "label": "G1"},
        {"id": 2, "type": "OUTPUT", "label": "Y"},
    ]
    assert _find_gate_without_path_to_output(gates, [_wire(1, 2)]) is None


def test_path_through_intermediate_gate_is_fine():
    gates = [
        {"id": 1, "type": "AND", "label": "G1"},
        {"id": 2, "type": "OR", "label": "G2"},
        {"id": 3, "type": "OUTPUT", "label": "Y"},
    ]
    wires = [_wire(1, 2), _wire(2, 3)]
    assert _find_gate_without_path_to_output(gates, wires) is None


def test_dead_end_gate_is_detected():
    gates = [
        {"id": 1, "type": "AND", "label": "G1"},
        {"id": 2, "type": "OR", "label": "G2"},
        {"id": 3, "type": "OUTPUT", "label": "Y"},
        {"id": 4, "type": "NOT", "label": "G3"},
    ]
    wires = [_wire(1, 2), _wire(2, 3), _wire(1, 4)]
    assert _find_gate_without_path_to_output(gates, wires) is gates[3]


def test_cycle_without_output_is_detected():
    gates = [
        {"id": 1, "type": "XOR", "label": "G1"},
        {"id": 2, "type": "XOR", "label": "G2"},
        {"id": 3, "type": "OUTPUT", "label": "Y"},
    ]
    wires = [_wire(1, 2), _wire(2, 1)]
    assert _find_gate_without_path_to_output(gates, wires) is gates[0]


def test_no_outputs_means_no_report():
    gates = [{"id": 1, "type": "AND", "label": "G1"}]
    assert _find_gate_without_path_to_output(gates, []) is None


def test_inputs_and_outputs_themselves_are_skipped():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "OUTPUT", "label": "Y"},
    ]
    assert _find_gate_without_path_to_output(gates, []) is None


def test_hint_with_rules_reports_dead_end_gate():
    payload = {
        "inputs": ["A", "B"],
        "outputs": ["Y"],
        "gates": [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "INPUT", "label": "B"},
            {"id": 3, "type": "AND", "label": "G1"},
            {"id": 4, "type": "AND", "label": "G2"},
            {"id": 5, "type": "OUTPUT", "label": "Y"},
        ],
        "wires": [
            _wire(1, 3), _wire(2, 3),
            _wire(1, 4), _wire(2, 4), _wire(4, 5),
        ],
    }
    hint = _hint_with_rules(payload)
    assert "'G1'" in hint
    assert "OUTPUT" in hint
