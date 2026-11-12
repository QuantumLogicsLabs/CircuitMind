"""
CircuitMind - LLM reply parsing tests
tests/test_generate_json_extraction.py

Groq does not always return bare JSON: replies often start with a sentence,
wrap the object in a markdown fence, or add trailing commentary. The old
parser only handled a leading fence and used lstrip("json"), which mangles
payloads; extraction now finds the first decodable object.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import generate.generate as gen
from generate.generate import _parse_llm_json, generate_with_llm


CIRCUIT = '{"circuit_name": "LED Circuit", "components": ["battery", "led"], "connections": ["battery -> led"]}'


# ── _parse_llm_json ───────────────────────────────────────────────────────────

def test_plain_json():
    assert _parse_llm_json(CIRCUIT)["circuit_name"] == "LED Circuit"


def test_json_fence_with_language():
    assert _parse_llm_json(f"```json\n{CIRCUIT}\n```")["components"] == ["battery", "led"]


def test_json_fence_without_language():
    assert _parse_llm_json(f"```\n{CIRCUIT}\n```")["components"] == ["battery", "led"]


def test_uppercase_fence_language():
    assert _parse_llm_json(f"```JSON\n{CIRCUIT}\n```")["circuit_name"] == "LED Circuit"


def test_prose_before_fence():
    raw = f"Here is the circuit you asked for:\n```json\n{CIRCUIT}\n```"
    assert _parse_llm_json(raw)["circuit_name"] == "LED Circuit"


def test_prose_after_fence():
    raw = f"```json\n{CIRCUIT}\n```\nLet me know if you want changes!"
    assert _parse_llm_json(raw)["circuit_name"] == "LED Circuit"


def test_prose_without_fence():
    assert _parse_llm_json(f"Sure: {CIRCUIT} Enjoy!")["components"] == ["battery", "led"]


def test_prose_braces_are_skipped():
    raw = f'Use {{name: value}} pairs like this:\n{CIRCUIT}'
    assert _parse_llm_json(raw)["circuit_name"] == "LED Circuit"


def test_nested_objects_and_braces_in_strings():
    raw = '{"circuit_name": "Mux {A,B}", "components": ["and"], "connections": [], "meta": {"n": 1}}'
    result = _parse_llm_json(raw)

    assert result["circuit_name"] == "Mux {A,B}"
    assert result["meta"] == {"n": 1}


def test_trailing_text_with_brace_does_not_extend_payload():
    raw = '{"a": 1} (closing note: }'
    assert _parse_llm_json(raw) == {"a": 1}


@pytest.mark.parametrize("raw", ["", "no json here", "[1, 2, 3]", "```json\nnot json\n```"])
def test_unparseable_replies_raise(raw):
    with pytest.raises(ValueError):
        _parse_llm_json(raw)


# ── generate_with_llm ────────────────────────────────────────────────────────

class _FakeClient:
    content = ""

    def __init__(self, api_key):
        outer = self

        class _Completions:
            def create(self, **kwargs):
                message = type("Msg", (), {"content": outer.content})
                choice = type("Choice", (), {"message": message})
                return type("Completion", (), {"choices": [choice]})

        self.chat = type("Chat", (), {"completions": _Completions()})


def test_generate_with_llm_parses_a_chatty_reply(monkeypatch):
    _FakeClient.content = f"Sure! Here you go:\n```json\n{CIRCUIT}\n```\nHope that helps."
    monkeypatch.setattr(gen, "Groq", _FakeClient, raising=False)
    monkeypatch.setattr(gen, "GROQ_AVAILABLE", True)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    result = generate_with_llm("make me a LED circuit")

    assert result["circuit_name"] == "LED Circuit"
    assert result["source"] == "llm"


def test_generate_with_llm_without_key_raises(monkeypatch):
    monkeypatch.setattr(gen, "GROQ_AVAILABLE", True)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(RuntimeError):
        generate_with_llm("make me a LED circuit")
