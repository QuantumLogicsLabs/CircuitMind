"""
CircuitMind - Gate JSON wiring tests
tests/test_export_gate_wires.py

Component names are not unique in a circuit (two resistors, two LEDs...).
Wire resolution used to map every occurrence of a name to the first gate with
that label, so a repeated name produced a self-wire and left the other gates
unconnected.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import generate_gate_json


def _pairs(result):
    return [(w["fromId"], w["toId"]) for w in result["wires"]]


def test_repeated_component_name_advances_to_the_next_gate():
    result = generate_gate_json(
        "dup",
        ["battery", "resistor", "resistor", "led"],
        ["battery -> resistor -> resistor -> led"],
    )

    assert _pairs(result) == [(0, 1), (1, 2), (2, 3)]


def test_each_duplicate_gate_gets_a_wire():
    result = generate_gate_json(
        "dup",
        ["battery", "resistor", "resistor", "led"],
        ["battery -> resistor -> resistor -> led"],
    )

    wired = {w["fromId"] for w in result["wires"]} | {w["toId"] for w in result["wires"]}
    assert {1, 2} <= wired


def test_no_self_wire_for_repeated_names():
    result = generate_gate_json(
        "dup",
        ["battery", "resistor", "resistor", "led"],
        ["battery -> resistor -> resistor -> led"],
    )

    assert all(w["fromId"] != w["toId"] for w in result["wires"])


def test_single_occurrence_still_resolves_to_first_gate():
    result = generate_gate_json(
        "single",
        ["battery", "resistor", "led"],
        ["battery -> resistor -> led"],
    )

    assert _pairs(result) == [(0, 1), (1, 2)]


def test_extra_occurrences_reuse_the_last_gate():
    result = generate_gate_json(
        "extra",
        ["battery", "resistor", "led"],
        ["battery -> resistor -> led -> battery -> led"],
    )

    # Only one led exists, so the third and fourth references reuse it.
    assert (0, 2) in _pairs(result)
    assert (2, 0) in _pairs(result)


def test_unknown_names_are_skipped():
    result = generate_gate_json(
        "unknown",
        ["battery", "led"],
        ["battery -> mystery -> led"],
    )

    assert result["wires"] == []


def test_wire_and_gate_counters_match():
    result = generate_gate_json(
        "dup",
        ["battery", "resistor", "resistor", "led"],
        ["battery -> resistor -> resistor -> led"],
    )

    assert result["wireIdCounter"] == len(result["wires"])
    assert result["gateIdCounter"] == len(result["gates"])


def test_target_pin_index_increments_per_wire():
    result = generate_gate_json(
        "fan",
        ["input_a", "input_b", "and", "led"],
        ["input_a -> and", "input_b -> and", "and -> led"],
    )

    and_wires = [w for w in result["wires"] if w["toId"] == 2]
    assert [w["toIndex"] for w in and_wires] == [0, 1]
