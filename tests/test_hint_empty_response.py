"""A blank LLM completion must not become a blank hint.

Groq occasionally returns an empty message (or no content at all). The hint
module used to strip it and return it as-is; it now treats that as a failed
LLM attempt and falls back to the deterministic rules.
"""

import logging
from types import SimpleNamespace

import pytest

import hint.hint_module as hint

PAYLOAD = {
    "request_type": "hint",
    "problem_title": "Half adder",
    "inputs": ["A", "B"],
    "outputs": ["SUM", "CARRY"],
    "gates": [],
    "wires": [],
}


class FakeCompletions:
    def __init__(self, content):
        self.content = content

    def create(self, **kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeGroq:
    content = "Check the output wiring."

    def __init__(self, api_key):
        self.chat = SimpleNamespace(completions=FakeCompletions(self.content))


@pytest.fixture(autouse=True)
def stub_groq(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(hint, "Groq", FakeGroq, raising=False)
    monkeypatch.setattr(hint, "GROQ_AVAILABLE", True)
    monkeypatch.setattr(FakeGroq, "content", "Check the output wiring.")
    yield


@pytest.mark.parametrize("content", ["", "   ", "\n\t", None])
def test_blank_llm_output_falls_back_to_rules(content, caplog):
    FakeGroq.content = content

    with caplog.at_level(logging.WARNING):
        result = hint.generate_hint(PAYLOAD)

    assert result["source"] == "rule-based"
    assert result["hint"].strip()
    assert "empty hint" in caplog.text


def test_non_string_completion_falls_back_to_rules():
    FakeGroq.content = ["not", "text"]

    result = hint.generate_hint(PAYLOAD)

    assert result["source"] == "rule-based"
    assert result["hint"].strip()


def test_valid_llm_output_is_trimmed_and_used():
    FakeGroq.content = "  Compare the XOR and AND outputs.  "

    result = hint.generate_hint(PAYLOAD)

    assert result["source"] == "llm"
    assert result["hint"] == "Compare the XOR and AND outputs."


def test_helper_raises_for_a_blank_completion():
    FakeGroq.content = "  "

    with pytest.raises(RuntimeError, match="empty hint"):
        hint._hint_with_llm(PAYLOAD)
