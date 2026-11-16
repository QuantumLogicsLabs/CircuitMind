"""Circuit generation asks Groq for JSON output directly.

Free-form completions frequently wrapped the payload in markdown fences,
which cost a parse attempt and occasionally leaked prose. Requesting JSON
mode makes the contract explicit while keeping the fence fallback for
models that do not implement it.
"""

from types import SimpleNamespace

import pytest

import generate.generate as gen

PAYLOAD = (
    '{"circuit_name": "LED Circuit", '
    '"components": ["battery", "resistor", "led"], '
    '"connections": ["battery -> resistor -> led"], '
    '"confidence": "high", "description": "LED"}'
)


class FakeCompletions:
    calls: list = []
    content = PAYLOAD
    error = None

    def create(self, **kwargs):
        FakeCompletions.calls.append(kwargs)
        if FakeCompletions.error is not None:
            raise FakeCompletions.error
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=FakeCompletions.content)
                )
            ]
        )


class FakeGroq:
    def __init__(self, api_key):
        self.chat = SimpleNamespace(completions=FakeCompletions())


@pytest.fixture(autouse=True)
def stub_groq(monkeypatch):
    FakeCompletions.calls = []
    FakeCompletions.content = PAYLOAD
    FakeCompletions.error = None
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(gen, "Groq", FakeGroq, raising=False)
    monkeypatch.setattr(gen, "GROQ_AVAILABLE", True)
    yield


def test_json_mode_is_requested():
    gen.generate_with_llm("make me an LED circuit")

    assert FakeCompletions.calls[0]["response_format"] == {"type": "json_object"}


def test_json_payload_is_parsed_and_tagged():
    result = gen.generate_with_llm("make me an LED circuit")

    assert result["circuit_name"] == "LED Circuit"
    assert result["source"] == "llm"


def test_markdown_fenced_payload_still_parses():
    FakeCompletions.content = f"```json\n{PAYLOAD}\n```"

    result = gen.generate_with_llm("make me an LED circuit")

    assert result["circuit_name"] == "LED Circuit"


def test_provider_rejecting_json_mode_falls_back_to_rules():
    FakeCompletions.error = TypeError("unexpected keyword argument 'response_format'")

    result = gen.generate_circuit("make me a LED circuit")

    assert result["source"] == "rule-based"
    assert result["circuit_name"] == "LED Circuit"
