"""Regression tests for truth-table truncation in the hint prompt.

_build_user_prompt silently dropped rows beyond the first 16, so the LLM
could not tell whether it was seeing the whole table or a slice of a much
larger one.
"""

from hint.hint_module import _build_user_prompt


def _payload(row_count):
    return {
        "problem_title": "Big Truth Table",
        "problem_description": "A large combinational problem.",
        "inputs": ["A", "B", "C", "D", "E", "F"],
        "outputs": ["Y"],
        "truth_table": [
            {"inputs": {"A": i % 2}, "output": i % 3} for i in range(row_count)
        ],
        "gates": [],
        "wires": [],
    }


def test_large_table_reports_total_and_truncation():
    prompt = _build_user_prompt(_payload(40))
    assert "first 16 of 40 rows" in prompt
    assert "omitted" in prompt


def test_small_table_reports_row_count_only():
    prompt = _build_user_prompt(_payload(3))
    assert "Truth table (JSON, 3 rows)" in prompt
    assert "omitted" not in prompt


def test_exactly_sixteen_rows_is_not_truncated():
    prompt = _build_user_prompt(_payload(16))
    assert "Truth table (JSON, 16 rows)" in prompt
    assert "omitted" not in prompt


def test_seventeen_rows_reports_one_omitted():
    prompt = _build_user_prompt(_payload(17))
    assert "first 16 of 17 rows" in prompt


def test_empty_table_still_renders():
    prompt = _build_user_prompt(_payload(0))
    assert "Truth table (JSON, 0 rows)" in prompt
