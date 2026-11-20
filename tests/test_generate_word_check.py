"""Prompts made only of punctuation must be rejected politely."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_circuit, validate_input


@pytest.mark.parametrize("prompt", ["???", "!!!", "...", "    @@@    ", "…—–"])
def test_punctuation_only_prompts_are_rejected(prompt):
    result = generate_circuit(prompt)
    assert result["error_code"] == "INVALID_INPUT"
    assert "letters or digits" in result["error"]


def test_validate_input_raises_for_symbols():
    with pytest.raises(ValueError, match="letters or digits"):
        validate_input("****")


def test_part_numbers_and_words_still_pass():
    assert validate_input("555") == "555"
    assert validate_input("make me an LED") == "make me an LED"


def test_555_prompt_still_builds_the_timer_circuit():
    result = generate_circuit("555")
    assert result["circuit_name"] == "555 Timer Circuit"
