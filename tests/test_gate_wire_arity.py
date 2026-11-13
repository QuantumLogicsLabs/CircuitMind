"""Regression tests for gate input-pin bounds in gate JSON."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module


def _gate_json(components, connections):
    circuit = {
        "circuit_name": "Arity",
        "components": components,
        "connections": connections,
    }
    result = export_module(json.dumps(circuit), export_format="gate_json")
    assert result["status"] == "success"
    return result["gate_json"]


def test_extra_wires_are_dropped_and_pins_stay_in_range():
    data = _gate_json(
        ["input_a", "input_b", "input_c", "and", "output_y"],
        ["input_a -> and", "input_b -> and", "input_c -> and"],
    )

    gates = {g["label"]: g for g in data["gates"]}
    and_gate = gates["AND"]

    assert and_gate["inputs"] == 2
    and_wires = [w for w in data["wires"] if w["toId"] == and_gate["id"]]
    assert len(and_wires) == 2
    assert sorted(w["toIndex"] for w in and_wires) == [0, 1]

    for wire in data["wires"]:
        target = next(g for g in data["gates"] if g["id"] == wire["toId"])
        assert wire["toIndex"] < target["inputs"]


def test_input_gates_never_receive_wires():
    data = _gate_json(
        ["input_a", "input_b", "xor", "output_y"],
        ["input_a -> xor -> output_y", "input_b -> xor", "xor -> input_a"],
    )

    for wire in data["wires"]:
        target = next(g for g in data["gates"] if g["id"] == wire["toId"])
        assert target["type"] != "INPUT"
