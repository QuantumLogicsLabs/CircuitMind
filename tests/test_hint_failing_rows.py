"""Regression tests: rule-based hints should use the last submit result.

With a graded attempt present, the fallback ignored last_result entirely and
always returned the generic "walk the truth table" advice.
"""

from hint.hint_module import _hint_with_rules


def _payload(last_result=None):
    return {
        "gates": [
            {"id": "g1", "type": "INPUT", "label": "A"},
            {"id": "g2", "type": "INPUT", "label": "B"},
            {"id": "g3", "type": "AND", "label": "AND1"},
            {"id": "g4", "type": "OUTPUT", "label": "Y"},
        ],
        "wires": [
            {"fromId": "g1", "toId": "g3"},
            {"fromId": "g2", "toId": "g3"},
            {"fromId": "g3", "toId": "g4"},
        ],
        "inputs": ["A", "B"],
        "outputs": ["Y"],
        "last_result": last_result or {},
    }


def test_single_failing_row_is_quoted():
    hint = _hint_with_rules(
        _payload(
            {
                "passed": False,
                "failing_rows": [
                    {"row": 3, "inputs": {"A": 1, "B": 0}, "expected": 0, "actual": 1}
                ],
            }
        )
    )
    assert "1 truth-table row" in hint
    assert '"row": 3' in hint
    assert '"expected": 0' in hint


def test_multiple_failing_rows_report_the_count():
    hint = _hint_with_rules(
        _payload({"passed": False, "failing_rows": [{"row": 1}, {"row": 2}, {"row": 4}]})
    )
    assert "3 truth-table rows" in hint


def test_no_failing_rows_keeps_generic_hint():
    hint = _hint_with_rules(_payload({}))
    assert "walk through the truth table row by row" in hint


def test_empty_last_result_keeps_generic_hint():
    hint = _hint_with_rules(_payload(None))
    assert "walk through the truth table row by row" in hint


def test_non_serialisable_row_does_not_crash():
    hint = _hint_with_rules(_payload({"failing_rows": [{"row": object()}]}))
    assert "1 truth-table row" in hint


def test_floating_gate_takes_priority_over_failing_rows():
    payload = _payload({"failing_rows": [{"row": 1}]})
    payload["gates"].append({"id": "g9", "type": "OR", "label": "OR1"})
    hint = _hint_with_rules(payload)
    assert "floating gate" in hint or "isn't connected" in hint
