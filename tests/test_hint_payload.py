"""Tests for hint payload normalisation.

The hint endpoint is called with whatever the client sends, so malformed
fields (None, bare strings, ints, non-dict rows) must not raise.
"""

import pytest

from hint import hint_module
from hint.hint_module import (
    generate_hint,
    _hint_with_rules,
    _sanitize_payload,
    _summarize_circuit,
)


@pytest.fixture(autouse=True)
def offline_llm(monkeypatch):
    """Force the deterministic rule-based path; no network in tests."""
    def _unavailable(payload):
        raise RuntimeError("LLM disabled in tests")

    monkeypatch.setattr(hint_module, "_hint_with_llm", _unavailable)


class TestSanitizePayload:

    def test_none_payload_is_normalised(self):
        clean = _sanitize_payload(None)

        assert clean["inputs"] == []
        assert clean["outputs"] == []
        assert clean["truth_table"] == []
        assert clean["gates"] == []
        assert clean["wires"] == []
        assert clean["last_result"] == {}
        assert clean["problem_title"] == ""
        assert clean["problem_description"] == ""

    def test_string_lists_are_coerced_and_blank_entries_dropped(self):
        clean = _sanitize_payload({"inputs": ["A", 1, None, "  "], "outputs": "Y"})

        assert clean["inputs"] == ["A", "1"]
        assert clean["outputs"] == ["Y"]

    def test_non_list_containers_are_wrapped(self):
        clean = _sanitize_payload({"inputs": 42, "outputs": ("S", "C")})

        assert clean["inputs"] == ["42"]
        assert clean["outputs"] == ["S", "C"]

    def test_non_dict_gate_and_wire_entries_are_dropped(self):
        clean = _sanitize_payload({
            "gates": [{"id": 1, "type": "INPUT"}, "junk", 7],
            "wires": {"fromId": 1, "toId": 2},
            "truth_table": [{"A": 0}, "row"],
        })

        assert clean["gates"] == [{"id": 1, "type": "INPUT"}]
        assert clean["wires"] == [{"fromId": 1, "toId": 2}]
        assert clean["truth_table"] == [{"A": 0}]

    def test_last_result_must_be_a_dict(self):
        clean = _sanitize_payload({"last_result": '{"passed": false}'})

        assert clean["last_result"] == {}

    def test_text_fields_are_stringified(self):
        clean = _sanitize_payload({
            "problem_title": 123,
            "problem_description": None,
        })

        assert clean["problem_title"] == "123"
        assert clean["problem_description"] == ""


class TestGenerateHintPayloads:

    def test_none_payload_returns_a_hint(self):
        result = generate_hint(None)

        assert isinstance(result["hint"], str) and result["hint"]
        assert result["source"] == "rule-based"
        assert "INPUT" in result["hint"]

    def test_scalar_inputs_do_not_crash(self):
        result = generate_hint({
            "inputs": "A",
            "outputs": None,
            "gates": "not-a-list",
            "wires": 42,
        })

        assert isinstance(result["hint"], str) and result["hint"]

    def test_non_string_io_names_do_not_crash(self):
        result = generate_hint({
            "inputs": [1, 2],
            "outputs": [{"name": "Y"}],
            "gates": [{"id": 1, "type": "INPUT", "label": None}],
            "wires": [],
        })

        assert isinstance(result["hint"], str) and result["hint"]

    def test_non_dict_last_result_does_not_crash(self):
        result = generate_hint({
            "problem_title": "Half Adder",
            "inputs": ["A", "B"],
            "outputs": ["S", "C"],
            "gates": [{"id": 1, "type": "INPUT", "label": "A"}],
            "wires": [],
            "last_result": "passed=false",
        })

        assert isinstance(result["hint"], str) and result["hint"]

    def test_identify_with_malformed_payload_does_not_crash(self):
        result = generate_hint({
            "request_type": "identify",
            "problem_title": None,
            "gates": "bad",
        })

        assert isinstance(result["hint"], str) and result["hint"]

    def test_empty_problem_prompts_for_setup(self):
        hint_text = _hint_with_rules({"gates": [], "wires": []})

        assert "INPUT" in hint_text
        assert "0 INPUT" not in hint_text


class TestSummarizeCircuit:

    def test_wires_with_unlabelled_gates_use_fallbacks(self):
        gates = [
            {"id": 1, "type": "INPUT"},
            {"id": 2, "type": "OUTPUT", "label": ""},
        ]
        wires = [{"fromId": 1, "toId": 2}]

        summary = _summarize_circuit(gates, wires)

        assert "- gate1 -> gate2" in summary
        assert "None ->" not in summary

    def test_wires_pointing_at_missing_gates_are_skipped(self):
        gates = [{"id": 1, "type": "INPUT", "label": "A"}]
        wires = [{"fromId": 1, "toId": 99}]

        summary = _summarize_circuit(gates, wires)

        assert "(none)" in summary
