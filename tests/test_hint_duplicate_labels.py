"""
Tests for the duplicate INPUT/OUTPUT label hint.

Truth-table columns are matched by port label, so two ports sharing a name
make the circuit ambiguous no matter how well it is wired.
"""

from hint.hint_module import _find_duplicate_port_label, _hint_with_rules


def test_duplicate_input_labels_are_detected():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "INPUT", "label": "A"},
    ]
    assert _find_duplicate_port_label(gates) == ("A", 2)


def test_duplicate_output_labels_are_detected():
    gates = [
        {"id": 1, "type": "OUTPUT", "label": "Y"},
        {"id": 2, "type": "OUTPUT", "label": "Y"},
        {"id": 3, "type": "OUTPUT", "label": "Y"},
    ]
    assert _find_duplicate_port_label(gates) == ("Y", 3)


def test_unique_labels_are_not_flagged():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "INPUT", "label": "B"},
        {"id": 3, "type": "OUTPUT", "label": "Y"},
    ]
    assert _find_duplicate_port_label(gates) is None


def test_label_comparison_ignores_case_and_padding():
    gates = [
        {"id": 1, "type": "INPUT", "label": " A "},
        {"id": 2, "type": "INPUT", "label": "a"},
    ]
    assert _find_duplicate_port_label(gates) == ("A", 2)


def test_logic_gates_with_equal_types_are_ignored():
    gates = [
        {"id": 1, "type": "AND", "label": "G1"},
        {"id": 2, "type": "AND", "label": "G1"},
    ]
    assert _find_duplicate_port_label(gates) is None


def test_hint_with_rules_reports_duplicate_label():
    payload = {
        "inputs": ["A", "B"],
        "outputs": ["Y"],
        "gates": [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "INPUT", "label": "A"},
            {"id": 3, "type": "OUTPUT", "label": "Y"},
        ],
        "wires": [],
    }
    hint = _hint_with_rules(payload)
    assert "'A'" in hint
    assert "unique" in hint
