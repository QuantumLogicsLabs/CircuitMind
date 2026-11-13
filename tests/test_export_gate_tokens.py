"""Regression tests for gate classification by whole tokens."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import _classify_component


def _type(component):
    gate_type, _, _ = _classify_component(component, 1, 5)
    return gate_type


def test_words_ending_in_or_are_not_or_gates():
    assert _type("resistor") == "RESISTOR"
    assert _type("motor") == "MOTOR"
    assert _type("capacitor") == "CAPACITOR"
    assert _type("transformer") == "TRANSFORMER"


def test_gate_labels_with_suffixes_are_recognised():
    assert _type("and_gt") == "AND"
    assert _type("and1") == "AND"
    assert _type("or1") == "OR"
    assert _type("xor2") == "XOR"
    assert _type("xnor2") == "XNOR"
    assert _type("nand_gate") == "NAND"
    assert _type("not1") == "NOT"


def test_not_gate_has_one_input():
    _, inputs, has_output = _classify_component("not1", 1, 5)

    assert inputs == 1
    assert has_output is True


def test_logic_gates_keep_two_inputs():
    _, inputs, _ = _classify_component("xor2", 1, 5)

    assert inputs == 2
