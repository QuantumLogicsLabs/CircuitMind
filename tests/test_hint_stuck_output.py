"""Rule-based hint for an output stuck at one value.

When a student's failing rows show the same value for an output while the
truth table expects it to vary, the deterministic hint should flag the stuck
signal instead of giving the generic "walk the truth table" advice.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hint.hint_module import _stuck_output_hint, _hint_with_rules


def _failing(*pairs):
    return {
        "passed": False,
        "failing_rows": [
            {"row": index, "inputs": {"A": 0}, "actual": dict(actual), "expected": dict(expected)}
            for index, (actual, expected) in enumerate(pairs)
        ],
    }


def test_no_last_result_returns_no_hint():
    assert _stuck_output_hint(None) is None
    assert _stuck_output_hint({}) is None


def test_single_failing_row_is_not_enough():
    last_result = _failing(({"Y": 0}, {"Y": 1}))

    assert _stuck_output_hint(last_result) is None


def test_constant_actual_against_varying_expected_is_flagged():
    last_result = _failing(({"Y": 0}, {"Y": 0}), ({"Y": 0}, {"Y": 1}))

    hint = _stuck_output_hint(last_result)

    assert hint is not None
    assert "Y is always 0" in hint
    assert "that output" in hint


def test_varying_actual_is_not_flagged():
    last_result = _failing(({"Y": 0}, {"Y": 1}), ({"Y": 1}, {"Y": 0}))

    assert _stuck_output_hint(last_result) is None


def test_constant_expected_is_not_flagged():
    last_result = _failing(({"Y": 0}, {"Y": 0}), ({"Y": 0}, {"Y": 0}))

    assert _stuck_output_hint(last_result) is None


def test_multiple_stuck_outputs_are_listed():
    last_result = _failing(
        ({"S": 0, "C": 1}, {"S": 0, "C": 1}),
        ({"S": 0, "C": 1}, {"S": 1, "C": 0}),
    )

    hint = _stuck_output_hint(last_result)

    assert "C is always 1" in hint
    assert "S is always 0" in hint
    assert "those outputs" in hint


def test_malformed_rows_are_ignored():
    last_result = {
        "failing_rows": [
            "not a row",
            {"actual": {"Y": 0}, "expected": {"Y": 0}},
            {"actual": {"Y": 0}, "expected": {"Y": 1}},
        ]
    }

    assert "Y is always 0" in _stuck_output_hint(last_result)


def test_rule_hint_uses_stuck_output_for_wired_circuit():
    payload = {
        "problem_title": "Buffer",
        "inputs": ["A"],
        "outputs": ["Y"],
        "gates": [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "OUTPUT", "label": "Y"},
        ],
        "wires": [{"fromId": 1, "toId": 2}],
        "last_result": _failing(({"Y": 0}, {"Y": 0}), ({"Y": 0}, {"Y": 1})),
    }

    hint = _hint_with_rules(payload)

    assert "Y is always 0" in hint
    assert "walk through the truth table row by row" not in hint
