"""Deterministic rule-based generation.

The test suite only exercised the public generate_circuit() entry point, which
prefers the LLM. These tests pin generate_with_rules() directly: matching,
word boundaries, plural handling and the Unknown fallback.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules


@pytest.mark.parametrize(
    "prompt,circuit_name",
    [
        ("make me a LED circuit", "LED Circuit"),
        ("two LEDs in series", "LED Circuit"),
        ("a light that turns on", "LED Circuit"),
        ("drive a motor", "Motor Circuit"),
        ("buzzer alarm", "Buzzer Circuit"),
        ("cooling fan", "Fan Circuit"),
        ("temperature sensor", "Temperature Sensor"),
        ("solar panel charger", "Solar Charging Circuit"),
        ("555 timer blinker", "555 Timer Circuit"),
        ("rc filter", "RC Filter Circuit"),
        ("MAKE ME A LED CIRCUIT", "LED Circuit"),
    ],
)
def test_prompt_matches_expected_rule(prompt, circuit_name):
    result = generate_with_rules(prompt)

    assert result["circuit_name"] == circuit_name
    assert result["source"] == "rule-based"
    assert result["confidence"] == "high"
    assert result["components"]
    assert result["connections"]


@pytest.mark.parametrize(
    "prompt,circuit_name",
    [
        ("half adder", "Half Adder Circuit"),
        ("full adder with carry in", "Full Adder Circuit"),
        ("half subtractor", "Half Subtractor Circuit"),
        ("full subtractor", "Full Subtractor Circuit"),
        ("odd parity generator", "Odd Parity Generator"),
        ("2-to-1 multiplexer", "2-to-1 Multiplexer"),
        ("decoder", "2-to-4 Decoder"),
        ("magnitude comparator", "1-Bit Comparator"),
    ],
)
def test_logic_prompts_match_their_specific_rule(prompt, circuit_name):
    assert generate_with_rules(prompt)["circuit_name"] == circuit_name


def test_word_boundaries_prevent_false_matches():
    assert generate_with_rules("sled")["circuit_name"] == "Unknown"
    assert generate_with_rules("model train")["circuit_name"] == "Unknown"


def test_unknown_prompt_returns_low_confidence_fallback():
    result = generate_with_rules("make me a flux capacitor")

    assert result["circuit_name"] == "Unknown"
    assert result["components"] == []
    assert result["connections"] == []
    assert result["confidence"] == "low"
    assert "not recognised" in result["description"]


def test_connections_reference_declared_components():
    result = generate_with_rules("make me a LED circuit")
    declared = set(result["components"])

    for connection in result["connections"]:
        for node in connection.split("->"):
            assert node.strip() in declared
