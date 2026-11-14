"""Regression tests for single-gate rule generation.

Prompts like "make an and gate" used to fall through to the generic
"Unknown" fallback because only compound circuits were covered.
"""

import pytest

from generate.generate import generate_with_rules


@pytest.mark.parametrize(
    "prompt,name,gate",
    [
        ("make an and gate", "AND Gate Circuit", "and"),
        ("build me a NAND gate", "NAND Gate Circuit", "nand"),
        ("make an or gate", "OR Gate Circuit", "or"),
        ("I need a nor gate please", "NOR Gate Circuit", "nor"),
        ("make a not gate", "NOT Gate Circuit", "not"),
        ("show a buffer gate", "Buffer Gate Circuit", "buffer"),
    ],
)
def test_single_gate_prompts_are_recognised(prompt, name, gate):
    result = generate_with_rules(prompt)
    assert result["circuit_name"] == name
    assert gate in result["components"]
    assert result["confidence"] == "high"


def test_nand_does_not_match_and_rule():
    result = generate_with_rules("make a nand gate")
    assert result["circuit_name"] == "NAND Gate Circuit"
    assert "and" not in result["components"]


def test_nor_does_not_match_or_rule():
    result = generate_with_rules("make a nor gate")
    assert result["circuit_name"] == "NOR Gate Circuit"
    assert result["components"].count("or") == 0


def test_not_gate_prompt_matches_inverter_keyword():
    assert generate_with_rules("give me an inverter")["circuit_name"] == "NOT Gate Circuit"


def test_gate_rules_include_source_and_connections():
    result = generate_with_rules("make an and gate")
    assert result["source"] == "rule-based"
    assert result["connections"]


def test_unrelated_prompt_still_falls_back():
    assert generate_with_rules("make me a quantum flux capacitor")["circuit_name"] == "Unknown"
