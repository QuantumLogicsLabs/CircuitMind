"""Regression tests for the 4-to-2 encoder rule.

"make an encoder" used to return the Unknown fallback while the sibling
"decoder" prompt had a rule.
"""

import pytest

from generate.generate import generate_with_rules


@pytest.mark.parametrize(
    "prompt",
    [
        "make an encoder",
        "build a 4-to-2 encoder",
        "I need encoder circuit",
    ],
)
def test_encoder_prompts_match(prompt):
    result = generate_with_rules(prompt)
    assert result["circuit_name"] == "4-to-2 Encoder"
    assert result["confidence"] == "high"


def test_encoder_outputs_are_two_bits():
    result = generate_with_rules("make an encoder")
    assert "output_a1" in result["components"]
    assert "output_a0" in result["components"]
    assert len([c for c in result["components"] if c.startswith("input_d")]) == 4


def test_encoder_rule_has_connections():
    result = generate_with_rules("make an encoder")
    assert result["connections"]


def test_decoder_prompt_is_unaffected():
    assert generate_with_rules("make a decoder")["circuit_name"] == "2-to-4 Decoder"
