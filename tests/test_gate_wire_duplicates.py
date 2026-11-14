"""Regression tests: duplicate connections must not steal input pins.

A repeated connection (same source and target) used to claim a second
input pin, which pushed a real second input past the gate's pin count and
silently dropped it from the exported gate JSON.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module


def _gate_json(components, connections):
    circuit = {
        "circuit_name": "Dupes",
        "components": components,
        "connections": connections,
    }
    result = export_module(json.dumps(circuit), export_format="gate_json")
    assert result["status"] == "success"
    return result["gate_json"]


def _wires_into(data, label):
    gate = next(g for g in data["gates"] if g["label"] == label)
    return [w for w in data["wires"] if w["toId"] == gate["id"]]


def test_duplicate_input_wire_does_not_consume_a_pin():
    data = _gate_json(
        ["input_a", "input_b", "and", "output_y"],
        ["input_a -> and", "input_b -> and", "input_a -> and"],
    )

    and_wires = _wires_into(data, "AND")
    assert len(and_wires) == 2
    assert sorted(w["toIndex"] for w in and_wires) == [0, 1]

    sources = {w["fromId"] for w in and_wires}
    labels = {g["label"] for g in data["gates"] if g["id"] in sources}
    assert labels == {"A", "B"}


def test_duplicate_chain_connection_is_emitted_once():
    data = _gate_json(
        ["input_a", "input_b", "xor", "output_y"],
        ["input_a -> xor -> output_y", "input_a -> xor -> output_y"],
    )

    assert len(_wires_into(data, "OUTPUT_Y")) == 1
    assert len(_wires_into(data, "XOR")) == 1


def test_reversed_direction_is_not_treated_as_a_duplicate():
    data = _gate_json(
        ["input_a", "input_b", "xor", "and", "output_y"],
        ["input_a -> xor", "input_b -> and", "xor -> and"],
    )

    assert len(_wires_into(data, "AND")) == 2


def test_wire_ids_stay_contiguous_after_dedupe():
    data = _gate_json(
        ["input_a", "input_b", "or", "output_y"],
        ["input_a -> or", "input_a -> or", "input_b -> or", "or -> output_y"],
    )

    assert [w["id"] for w in data["wires"]] == list(range(len(data["wires"])))
    assert data["wireIdCounter"] == len(data["wires"])
