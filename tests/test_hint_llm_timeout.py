"""Hint LLM calls must time out so a stalled provider cannot hang the API."""

from types import SimpleNamespace

import pytest

from hint import hint_module as hint


PAYLOAD = {
    "problem_title": "Half Adder",
    "inputs": ["A", "B"],
    "outputs": ["SUM", "CARRY"],
    "truth_table": [{"A": 0, "B": 0, "SUM": 0, "CARRY": 0}],
    "gates": [],
    "wires": [],
}


class FakeCompletions:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        message = SimpleNamespace(content=self.payload)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def install_fake_groq(monkeypatch, payload=None, error=None):
    completions = FakeCompletions(payload, error)

    class FakeGroq:
        def __init__(self, api_key):
            self.api_key = api_key
            self.chat = SimpleNamespace(completions=completions)

    monkeypatch.setattr(hint, "GROQ_AVAILABLE", True)
    monkeypatch.setattr(hint, "Groq", FakeGroq, raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    return completions


def test_default_timeout(monkeypatch):
    monkeypatch.delenv("GROQ_TIMEOUT", raising=False)
    assert hint._llm_timeout() == hint.DEFAULT_LLM_TIMEOUT


def test_timeout_from_environment(monkeypatch):
    monkeypatch.setenv("GROQ_TIMEOUT", "4.5")
    assert hint._llm_timeout() == 4.5


@pytest.mark.parametrize("value", ["", "later", "0", "-1"])
def test_bad_timeout_values_fall_back(monkeypatch, value):
    monkeypatch.setenv("GROQ_TIMEOUT", value)
    assert hint._llm_timeout() == hint.DEFAULT_LLM_TIMEOUT


def test_request_passes_timeout(monkeypatch):
    monkeypatch.setenv("GROQ_TIMEOUT", "9")
    completions = install_fake_groq(monkeypatch, payload="Check your carry logic.")
    text = hint._hint_with_llm(PAYLOAD)
    assert text == "Check your carry logic."
    assert completions.calls[0]["timeout"] == 9.0


def test_timeout_error_falls_back_to_rules(monkeypatch):
    install_fake_groq(monkeypatch, error=TimeoutError("provider timed out"))
    result = hint.generate_hint(PAYLOAD)
    assert result["source"] == "rule-based"
    assert result["hint"]
