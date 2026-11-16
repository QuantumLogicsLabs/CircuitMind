"""Groq calls must time out so a stalled provider cannot hang the API."""

from types import SimpleNamespace

import pytest

from generate import generate as gen


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

    monkeypatch.setattr(gen, "GROQ_AVAILABLE", True)
    monkeypatch.setattr(gen, "Groq", FakeGroq, raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    return completions


def test_default_timeout(monkeypatch):
    monkeypatch.delenv("GROQ_TIMEOUT", raising=False)
    assert gen._llm_timeout() == gen.DEFAULT_LLM_TIMEOUT


def test_timeout_from_environment(monkeypatch):
    monkeypatch.setenv("GROQ_TIMEOUT", "5")
    assert gen._llm_timeout() == 5.0


def test_invalid_timeout_falls_back(monkeypatch):
    monkeypatch.setenv("GROQ_TIMEOUT", "soon")
    assert gen._llm_timeout() == gen.DEFAULT_LLM_TIMEOUT


@pytest.mark.parametrize("value", ["0", "-3"])
def test_non_positive_timeout_falls_back(monkeypatch, value):
    monkeypatch.setenv("GROQ_TIMEOUT", value)
    assert gen._llm_timeout() == gen.DEFAULT_LLM_TIMEOUT


def test_request_passes_timeout(monkeypatch):
    monkeypatch.setenv("GROQ_TIMEOUT", "7")
    completions = install_fake_groq(
        monkeypatch,
        payload='{"circuit_name": "LED", "components": ["battery"], "connections": []}',
    )
    result = gen.generate_with_llm("a led circuit")
    assert completions.calls[0]["timeout"] == 7.0
    assert result["source"] == "llm"


def test_timeout_error_falls_back_to_rules(monkeypatch):
    install_fake_groq(monkeypatch, error=TimeoutError("provider timed out"))
    result = gen.generate_circuit("a led circuit")
    assert result["source"] == "rule-based"
    assert result["circuit_name"] == "LED Circuit"
