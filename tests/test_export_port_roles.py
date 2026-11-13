"""Regression tests for input/output port classification."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module


def _gates(components, connections):
    circuit = {
        "circuit_name": "Logic",
        "components": components,
        "connections": connections,
    }
    result = export_module(json.dumps(circuit), export_format="gate_json")
    assert result["status"] == "success"
    return result["gate_json"]["gates"]


def test_full_adder_control_inputs_are_inputs():
    gates = _gates(
        ["input_a", "input_b", "cin", "xor1", "xor2", "and1",
         "and2", "or", "sum_output", "cout"],
        ["input_a -> xor1 -> xor2 -> sum_output"],
    )
    by_label = {g["label"]: g for g in gates}

    for label in ("A", "B", "CIN"):
        assert by_label[label]["type"] == "INPUT"
    assert by_label["COUT"]["type"] == "OUTPUT"


def test_decoder_outputs_are_outputs():
    gates = _gates(
        ["input_a", "input_b", "not_a", "not_b", "and0", "and1", "and2",
         "and3", "y0", "y1", "y2", "y3"],
        ["input_a -> not_a -> and0 -> y0"],
    )
    by_label = {g["label"]: g for g in gates}

    for label in ("Y0", "Y1", "Y2", "Y3"):
        assert by_label[label]["type"] == "OUTPUT"


def test_full_subtractor_borrow_input_is_input():
    gates = _gates(
        ["input_a", "input_b", "bin", "xor1", "xor2", "not1", "and1",
         "not2", "and2", "or", "diff_output", "borrow_output"],
        ["input_a -> xor1 -> xor2 -> diff_output"],
    )
    by_label = {g["label"]: g for g in gates}

    assert by_label["BIN"]["type"] == "INPUT"
    assert by_label["BORROW"]["type"] == "OUTPUT"
