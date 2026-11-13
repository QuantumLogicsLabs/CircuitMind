"""Regression tests for half-adder vs half-subtractor identification."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hint.hint_module import _identify_circuit


def _payload(gate_types):
    return {
        "problem_title": "",
        "problem_description": "",
        "gates": [{"id": i, "type": t, "label": t.lower()} for i, t in enumerate(gate_types)],
        "wires": [],
    }


def test_xor_and_without_not_is_a_half_adder():
    assert _identify_circuit(
        _payload(["INPUT", "INPUT", "XOR", "AND", "OUTPUT", "OUTPUT"])
    ) == "Half Adder"


def test_xor_and_with_not_is_a_half_subtractor():
    assert _identify_circuit(
        _payload(["INPUT", "INPUT", "XOR", "NOT", "AND", "OUTPUT", "OUTPUT"])
    ) == "Half Subtractor"


def test_ambiguous_graph_is_not_named():
    assert _identify_circuit(
        _payload(["INPUT", "INPUT", "XOR", "OUTPUT", "OUTPUT"])
    ) is None
