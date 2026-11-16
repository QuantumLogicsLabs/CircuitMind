"""The Groq model id can be overridden without editing source.

Both LLM paths (circuit generation and hints) hard-coded the same model, so a
deployment could not switch to another Groq model when one was deprecated or
rate-limited. GROQ_MODEL now overrides both; the default stays stable.
"""

from types import SimpleNamespace

import pytest

import generate.generate as gen
import hint.hint_module as hint

GENERATE_JSON = (
    '{"circuit_name": "LED", "components": ["battery", "led"], '
    '"connections": ["battery -> led"], "confidence": "high", '
    '"description": "LED"}'
)


class FakeCompletions:
    def __init__(self, content, calls):
        self.content = content
        self.calls = calls

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content)
                )
            ]
        )


class FakeGroq:
    def __init__(self, api_key):
        self.api_key = api_key
        self.chat = SimpleNamespace(completions=FakeCompletions(CONTENT, CALLS))


CALLS: list = []
CONTENT = ""


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    CALLS.clear()
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setattr(gen, "Groq", FakeGroq, raising=False)
    monkeypatch.setattr(gen, "GROQ_AVAILABLE", True)
    monkeypatch.setattr(hint, "Groq", FakeGroq, raising=False)
    monkeypatch.setattr(hint, "GROQ_AVAILABLE", True)
    yield


def test_both_modules_share_the_same_default():
    assert gen.DEFAULT_LLM_MODEL == hint.DEFAULT_LLM_MODEL
    assert gen._llm_model() == gen.DEFAULT_LLM_MODEL
    assert hint._llm_model() == hint.DEFAULT_LLM_MODEL


@pytest.mark.parametrize("raw", [" mixtral-8x7b-32768 ", "llama3-8b-8192"])
def test_override_is_trimmed_and_applied(monkeypatch, raw):
    monkeypatch.setenv("GROQ_MODEL", raw)

    assert gen._llm_model() == raw.strip()
    assert hint._llm_model() == raw.strip()


@pytest.mark.parametrize("raw", ["", "   "])
def test_blank_override_falls_back_to_default(monkeypatch, raw):
    monkeypatch.setenv("GROQ_MODEL", raw)

    assert gen._llm_model() == gen.DEFAULT_LLM_MODEL
    assert hint._llm_model() == hint.DEFAULT_LLM_MODEL


def test_generate_forwards_the_default_model():
    global CONTENT
    CONTENT = GENERATE_JSON

    result = gen.generate_with_llm("make me an LED circuit")

    assert result["circuit_name"] == "LED"
    assert CALLS[0]["model"] == gen.DEFAULT_LLM_MODEL


def test_generate_forwards_the_overridden_model(monkeypatch):
    global CONTENT
    CONTENT = GENERATE_JSON
    monkeypatch.setenv("GROQ_MODEL", "custom-model")

    gen.generate_with_llm("make me an LED circuit")

    assert CALLS[0]["model"] == "custom-model"


def test_hint_forwards_the_default_model():
    global CONTENT
    CONTENT = "Check the output wiring."

    text = hint._hint_with_llm({"problem_title": "Half adder"})

    assert text == "Check the output wiring."
    assert CALLS[0]["model"] == hint.DEFAULT_LLM_MODEL


def test_hint_forwards_the_overridden_model(monkeypatch):
    global CONTENT
    CONTENT = "Check the output wiring."
    monkeypatch.setenv("GROQ_MODEL", "custom-model")

    hint._hint_with_llm({"problem_title": "Half adder"})

    assert CALLS[0]["model"] == "custom-model"
