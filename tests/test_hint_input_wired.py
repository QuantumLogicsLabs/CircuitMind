"""Rule-based hint when an INPUT gate has a wire feeding into it.

In a combinational logic graph, INPUT gates are sources. Any wire whose
toId points at an INPUT is a structural mistake worth calling out before the
generic truth-table advice.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hint.hint_module import _hint_with_rules


def _payload(gates, wires):
    return {
        "problem_title": "Half adder",
        "inputs": ["A", "B"],
        "outputs": ["Y"],
        "gates": gates,
        "wires": wires,
    }


def test_single_fed_input_is_reported():
    payload = _payload(
        gates=[
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "INPUT", "label": "B"},
            {"id": 3, "type": "AND", "label": "G1"},
            {"id": 4, "type": "OUTPUT", "label": "Y"},
        ],
        wires=[
            {"fromId": 3, "toId": 1},
            {"fromId": 1, "toId": 3},
            {"fromId": 2, "toId": 3},
            {"fromId": 3, "toId": 4},
        ],
    )

    hint = _hint_with_rules(payload)

    assert "'A' is INPUT gate(s)" in hint
    assert "wired into it" in hint


def test_multiple_fed_inputs_use_plural_wording():
    payload = _payload(
        gates=[
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "INPUT", "label": "B"},
            {"id": 3, "type": "AND", "label": "G1"},
            {"id": 4, "type": "OUTPUT", "label": "Y"},
        ],
        wires=[
            {"fromId": 3, "toId": 1},
            {"fromId": 3, "toId": 2},
            {"fromId": 1, "toId": 3},
            {"fromId": 2, "toId": 3},
            {"fromId": 3, "toId": 4},
        ],
    )

    hint = _hint_with_rules(payload)

    assert "'A, B' are INPUT gate(s)" in hint
    assert "wired into them" in hint


def test_correct_direction_gets_generic_hint():
    payload = _payload(
        gates=[
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "INPUT", "label": "B"},
            {"id": 3, "type": "AND", "label": "G1"},
            {"id": 4, "type": "OUTPUT", "label": "Y"},
        ],
        wires=[
            {"fromId": 1, "toId": 3},
            {"fromId": 2, "toId": 3},
            {"fromId": 3, "toId": 4},
        ],
    )

    hint = _hint_with_rules(payload)

    assert "INPUT gate(s)" not in hint
    assert "walk through the truth table" in hint
