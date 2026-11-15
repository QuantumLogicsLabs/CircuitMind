"""Tests for the LLM-to-rules fallback contract in the generate module."""

import generate.generate as generate_module
from generate.generate import generate_circuit


def test_falls_back_to_rules_when_the_llm_raises(monkeypatch):
    def boom(prompt):
        raise RuntimeError("GROQ_API_KEY not set in environment")

    monkeypatch.setattr(generate_module, "generate_with_llm", boom)

    result = generate_circuit("make me a LED circuit")

    assert result["source"] == "rule-based"
    assert result["circuit_name"] == "LED Circuit"
    assert "battery" in result["components"]


def test_returns_the_llm_result_when_available(monkeypatch):
    monkeypatch.setattr(
        generate_module,
        "generate_with_llm",
        lambda prompt: {"circuit_name": "LLM Circuit", "components": [], "connections": [],
                        "description": "", "confidence": "high", "source": "llm"},
    )

    result = generate_circuit("anything at all")

    assert result["source"] == "llm"
    assert result["circuit_name"] == "LLM Circuit"


def test_llm_receives_the_trimmed_prompt(monkeypatch):
    captured = {}

    def fake(prompt):
        captured["prompt"] = prompt
        return {"circuit_name": "X", "components": [], "connections": [],
                "description": "", "confidence": "high", "source": "llm"}

    monkeypatch.setattr(generate_module, "generate_with_llm", fake)

    generate_circuit("  led circuit  ")

    assert captured["prompt"] == "led circuit"


def test_invalid_input_never_reaches_the_llm(monkeypatch):
    def explode(prompt):
        raise AssertionError("LLM must not be called for invalid input")

    monkeypatch.setattr(generate_module, "generate_with_llm", explode)

    result = generate_circuit(" ")

    assert result["error_code"] == "INVALID_INPUT"
