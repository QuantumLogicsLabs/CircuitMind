"""Regression tests for port-label matching in rule-based hints."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hint.hint_module import _hint_with_rules


def _gates(labels_types):
    return [
        {"id": i + 1, "type": gate_type, "label": label}
        for i, (label, gate_type) in enumerate(labels_types)
    ]


def test_mismatched_labels_are_flagged():
    hint = _hint_with_rules({
        "inputs": ["A", "B"],
        "outputs": ["S", "C"],
        "gates": _gates([
            ("X", "INPUT"), ("Y", "INPUT"),
            ("XOR1", "XOR"),
            ("P", "OUTPUT"), ("Q", "OUTPUT"),
        ]),
        "wires": [],
    })

    assert "labels" in hint
    assert "A" in hint and "S" in hint
    assert "X" in hint and "P" in hint


def test_matching_labels_reach_the_generic_hint():
    gates = _gates([
        ("A", "INPUT"), ("B", "INPUT"),
        ("XOR1", "XOR"), ("S", "OUTPUT"), ("C", "OUTPUT"),
    ])
    hint = _hint_with_rules({
        "inputs": ["A", "B"],
        "outputs": ["S", "C"],
        "gates": gates,
        "wires": [
            {"id": 1, "fromId": 1, "toId": 3, "toIndex": 0},
            {"id": 2, "fromId": 2, "toId": 3, "toIndex": 1},
            {"id": 3, "fromId": 3, "toId": 4, "toIndex": 0},
            {"id": 4, "fromId": 4, "toId": 5, "toIndex": 0},
        ],
    })

    assert "counts look reasonable" in hint


def test_labels_compare_case_insensitively():
    hint = _hint_with_rules({
        "inputs": ["a", "b"],
        "outputs": ["s", "c"],
        "gates": _gates([
            ("A", "INPUT"), ("B", "INPUT"),
            ("XOR1", "XOR"), ("S", "OUTPUT"), ("C", "OUTPUT"),
        ]),
        "wires": [],
    })

    assert "labels don't match" not in hint
