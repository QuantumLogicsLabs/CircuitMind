"""Tests for the rule-based generator's unknown-prompt guidance."""

from generate.generate import generate_with_rules


def test_unknown_prompt_returns_the_empty_template():
    result = generate_with_rules("a quantum flux capacitor machine")
    assert result["circuit_name"] == "Unknown"
    assert result["components"] == []
    assert result["connections"] == []
    assert result["confidence"] == "low"
    assert result["source"] == "rule-based"


def test_unknown_prompt_suggests_the_digital_logic_templates():
    description = generate_with_rules("a quantum flux capacitor machine")["description"]
    for suggestion in ("adder", "subtractor", "parity", "multiplexer", "comparator", "logic gate"):
        assert suggestion in description


def test_unknown_prompt_still_suggests_the_analog_templates():
    description = generate_with_rules("a quantum flux capacitor machine")["description"]
    for suggestion in ("led", "motor", "555 timer", "rc filter"):
        assert suggestion in description
