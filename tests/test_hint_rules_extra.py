"""Rule-based hint coverage that complements TestHint in test_all_modules.py.

These tests pin the exact hint text, rule precedence, and prompt-building
behaviour of the deterministic fallback so regressions show up without
needing a Groq API key.
"""

from hint.hint_module import (
    _build_user_prompt,
    _hint_with_rules,
    _identify_circuit,
    _summarize_circuit,
)


def _half_adder_gates():
    return [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "INPUT", "label": "B"},
        {"id": 3, "type": "XOR", "label": "XOR1"},
        {"id": 4, "type": "OUTPUT", "label": "S"},
        {"id": 5, "type": "OUTPUT", "label": "C"},
    ]


def _half_adder_wires():
    return [
        {"id": 1, "fromId": 1, "toId": 3, "toIndex": 0},
        {"id": 2, "fromId": 2, "toId": 3, "toIndex": 1},
        {"id": 3, "fromId": 3, "toId": 4, "toIndex": 0},
        {"id": 4, "fromId": 3, "toId": 5, "toIndex": 0},
    ]


def test_fully_wired_circuit_gets_truth_table_guidance():
    hint = _hint_with_rules({
        "inputs": ["A", "B"],
        "outputs": ["S", "C"],
        "gates": _half_adder_gates(),
        "wires": _half_adder_wires(),
    })
    assert "truth table" in hint.lower()


def test_missing_output_count_takes_precedence_over_floating_rule():
    # The stray AND is both floating and part of an incomplete I/O set; the
    # I/O mismatch is reported first because it blocks every later check.
    hint = _hint_with_rules({
        "inputs": ["A", "B"],
        "outputs": ["S", "C"],
        "gates": [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "INPUT", "label": "B"},
            {"id": 3, "type": "OUTPUT", "label": "S"},
            {"id": 4, "type": "AND", "label": "AND1"},
        ],
        "wires": [],
    })
    assert "2 INPUT and 1 OUTPUT" in hint
    assert "floating" not in hint.lower()


def test_floating_hint_names_every_unconnected_gate():
    hint = _hint_with_rules({
        "inputs": ["A"],
        "outputs": ["Y"],
        "gates": [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "OUTPUT", "label": "Y"},
            {"id": 3, "type": "AND", "label": "AND1"},
            {"id": 4, "type": "NOT", "label": "NOT1"},
        ],
        "wires": [{"id": 1, "fromId": 1, "toId": 2, "toIndex": 0}],
    })
    assert "AND1" in hint and "NOT1" in hint
    assert "isn't connected" in hint


def test_summarize_circuit_lists_wire_endpoints_by_label():
    summary = _summarize_circuit(_half_adder_gates(), _half_adder_wires())
    assert "- A -> XOR1" in summary
    assert "- XOR1 -> S" in summary


def test_summarize_circuit_reports_no_wires():
    summary = _summarize_circuit(_half_adder_gates(), [])
    assert summary.endswith("(none)")


def test_summarize_circuit_ignores_wires_with_unknown_ids():
    summary = _summarize_circuit(
        _half_adder_gates(),
        [{"id": 9, "fromId": 1, "toId": 404}],
    )
    assert summary.endswith("(none)")


def test_summarize_circuit_marks_empty_canvas():
    assert "canvas is empty" in _summarize_circuit([], []).lower()


def test_prompt_reports_failing_row_count():
    prompt = _build_user_prompt({
        "problem_title": "Half Adder",
        "inputs": ["A"],
        "outputs": ["S"],
        "gates": [],
        "wires": [],
        "last_result": {
            "passed": False,
            "failing_rows": [{"row": 1}, {"row": 2}, {"row": 3}],
        },
    })
    assert "3 row(s) failed" in prompt


def test_prompt_notes_a_passing_attempt():
    prompt = _build_user_prompt({
        "problem_title": "Half Adder",
        "inputs": ["A"],
        "outputs": ["S"],
        "gates": [],
        "wires": [],
        "last_result": {"passed": True, "failing_rows": []},
    })
    assert "Last submit attempt passed" in prompt


def test_prompt_includes_submit_error():
    prompt = _build_user_prompt({
        "problem_title": "Half Adder",
        "inputs": ["A"],
        "outputs": ["S"],
        "gates": [],
        "wires": [],
        "last_result": {"error": "Output S is not connected"},
    })
    assert "Output S is not connected" in prompt


def test_prompt_truncates_long_truth_tables():
    rows = [{"row": index} for index in range(20)]
    prompt = _build_user_prompt({
        "problem_title": "Half Adder",
        "inputs": ["A"],
        "outputs": ["S"],
        "truth_table": rows,
        "gates": [],
        "wires": [],
    })
    assert "first 16 rows" in prompt
    assert '"row": 15' in prompt
    assert '"row": 16' not in prompt


def test_identify_matches_common_circuit_keywords():
    cases = {
        "Full Adder": "Full Adder",
        "4-bit multiplexer": "Multiplexer",
        "2-bit comparator": "Comparator",
        "8-to-3 Encoder": "Encoder",
        "Half Subtractor": "Half Subtractor",
    }
    for title, expected in cases.items():
        assert _identify_circuit({"problem_title": title}) == expected


def test_identify_structure_needs_matching_io_counts():
    gates = [
        {"id": 1, "type": "INPUT"},
        {"id": 2, "type": "INPUT"},
        {"id": 3, "type": "INPUT"},
        {"id": 4, "type": "XOR"},
        {"id": 5, "type": "AND"},
        {"id": 6, "type": "OUTPUT"},
        {"id": 7, "type": "OUTPUT"},
    ]
    assert _identify_circuit({"problem_title": "Mystery", "gates": gates}) == "Mystery"
