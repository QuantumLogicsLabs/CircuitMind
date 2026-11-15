"""
CircuitMind - gate JSON classification and layout tests
tests/test_export_gate_layout.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import (
    LAYER_X_GAP,
    ORIGIN_X,
    ORIGIN_Y,
    _classify_component,
    _layout_gates,
    generate_gate_json,
)


def test_gate_type_matching_prefers_longer_names():
    assert _classify_component("XNOR1", 1, 5)[0] == "XNOR"
    assert _classify_component("XOR1", 1, 5)[0] == "XOR"
    assert _classify_component("NAND1", 1, 5)[0] == "NAND"
    assert _classify_component("NOR1", 1, 5)[0] == "NOR"
    assert _classify_component("AND1", 1, 5)[0] == "AND"
    assert _classify_component("OR1", 1, 5)[0] == "OR"


def test_not_gate_has_one_input():
    gate_type, inputs, has_output = _classify_component("NOT1", 1, 5)
    assert (gate_type, inputs, has_output) == ("NOT", 1, True)


def test_input_and_output_classification():
    assert _classify_component("INPUT_A", 0, 5)[0] == "INPUT"
    assert _classify_component("in_clock", 0, 5)[0] == "INPUT"
    assert _classify_component("sum_output", 4, 5)[0] == "OUTPUT"
    assert _classify_component("led", 2, 5)[0] == "OUTPUT"


def test_layout_places_outputs_after_logic_and_respects_gaps():
    gates = [
        {"id": 0, "type": "INPUT", "x": 0, "y": 0},
        {"id": 1, "type": "AND", "x": 0, "y": 0},
        {"id": 2, "type": "OUTPUT", "x": 0, "y": 0},
        {"id": 3, "type": "XOR", "x": 0, "y": 0},
    ]
    wires = [
        {"id": 0, "fromId": 0, "toId": 1, "toIndex": 0},
        {"id": 1, "fromId": 1, "toId": 2, "toIndex": 0},
    ]
    _layout_gates(gates, wires)
    by_id = {g["id"]: g for g in gates}

    assert by_id[0]["x"] == ORIGIN_X
    assert by_id[1]["x"] == ORIGIN_X + LAYER_X_GAP
    assert by_id[2]["x"] == ORIGIN_X + 2 * LAYER_X_GAP
    assert by_id[3]["x"] == ORIGIN_X  # disconnected gate stays in the first free column
    assert by_id[0]["y"] == ORIGIN_Y
    assert by_id[3]["y"] == ORIGIN_Y + 130


def test_gate_json_wires_target_pins_in_order():
    circuit = generate_gate_json(
        "Half Adder",
        ["input_a", "input_b", "xor", "and", "sum_output", "carry_output"],
        [
            "input_a -> xor -> sum_output",
            "input_b -> xor",
            "input_a -> and -> carry_output",
            "input_b -> and",
        ],
    )
    wires = circuit["wires"]
    ids = {g["id"] for g in circuit["gates"]}

    assert [w["id"] for w in wires] == list(range(len(wires)))
    assert all(w["fromId"] in ids and w["toId"] in ids for w in wires)

    xor = next(g["id"] for g in circuit["gates"] if g["label"] == "XOR")
    xor_inputs = {w["toIndex"] for w in wires if w["toId"] == xor}
    assert xor_inputs == {0, 1}


def test_gate_json_uses_friendly_output_labels():
    circuit = generate_gate_json(
        "Half Adder",
        ["input_a", "input_b", "xor", "and", "sum_output", "carry_output"],
        ["input_a -> xor -> sum_output"],
    )
    labels = {g["label"] for g in circuit["gates"]}
    assert {"A", "B", "SUM", "CARRY"} <= labels
    assert circuit["inputCounter"] == 2
    assert circuit["outputCounter"] == 2
