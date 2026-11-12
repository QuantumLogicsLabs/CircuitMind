"""
CircuitMind - Issue rendering tests
tests/test_issue_format.py

The Diagnose tab called str.startswith() on every finding, but diagnose
returns structured issue dicts, so the tab crashed whenever a circuit had
findings. issue_rows() normalises both shapes for rendering.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import diagnose_circuit
from utils.issue_format import issue_rows


def test_structured_issue_becomes_a_row():
    rows = issue_rows([{
        "severity": "error",
        "code": "NO_POWER_SOURCE",
        "message": "No power source found.",
        "suggestion": "Add a battery.",
    }])

    assert rows == [{
        "severity": "error",
        "code": "NO_POWER_SOURCE",
        "text": "No power source found. Add a battery.",
    }]


def test_warning_severity_is_preserved():
    rows = issue_rows([{"severity": "warning", "message": "Floating gate."}])

    assert rows[0]["severity"] == "warning"
    assert rows[0]["text"] == "Floating gate."


def test_unknown_severity_falls_back_to_info():
    rows = issue_rows([{"severity": "critical", "message": "?"}])

    assert rows[0]["severity"] == "info"


def test_missing_message_has_placeholder_text():
    rows = issue_rows([{"severity": "info"}])

    assert rows[0]["text"] == "Unspecified issue."


def test_legacy_strings_keep_their_prefix_severity():
    rows = issue_rows([
        "Error: No power source found.",
        "Warning: LED without resistor.",
        "Info: No ground reference found.",
    ])

    assert [row["severity"] for row in rows] == ["error", "warning", "info"]
    assert rows[0]["text"] == "No power source found."
    assert rows[0]["code"] is None


def test_unprefixed_legacy_string_is_info():
    rows = issue_rows(["Something happened."])

    assert rows[0] == {"severity": "info", "code": None, "text": "Something happened."}


def test_mixed_shapes_keep_order():
    rows = issue_rows([
        {"severity": "error", "message": "first"},
        "Warning: second",
    ])

    assert [row["text"] for row in rows] == ["first", "second"]


def test_none_and_empty_return_no_rows():
    assert issue_rows(None) == []
    assert issue_rows([]) == []


def test_non_issue_entries_are_skipped():
    rows = issue_rows([None, 42, {"message": "kept"}])

    assert [row["text"] for row in rows] == ["kept"]


def test_input_is_not_mutated():
    issues = [{"severity": "error", "message": "boom", "suggestion": "fix"}]
    issue_rows(issues)

    assert issues == [{"severity": "error", "message": "boom", "suggestion": "fix"}]


def test_real_diagnosis_renders_without_raising():
    result = diagnose_circuit({
        "components": ["battery", "led"],
        "connections": ["battery -> led"],
    })

    rows = issue_rows(result["issues"])

    assert rows
    assert all(row["severity"] in {"error", "warning", "info"} for row in rows)
