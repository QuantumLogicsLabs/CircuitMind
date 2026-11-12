"""
CircuitMind - Generate prompt validation tests
tests/test_generate_input.py

generate_circuit() only catches ValueError from validate_input(), but the
validator called prompt.strip() first, so a non-string prompt (an int, a list,
a dict) raised AttributeError straight out of the public function.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_circuit, validate_input


class TestNonStringPrompts:

    @pytest.mark.parametrize("prompt", [123, 4.5, ["led"], {"prompt": "led"}, True])
    def test_validate_input_rejects_non_strings(self, prompt):
        with pytest.raises(ValueError):
            validate_input(prompt)

    @pytest.mark.parametrize("prompt", [123, 4.5, ["led"], {"prompt": "led"}])
    def test_generate_circuit_returns_invalid_input(self, prompt):
        result = generate_circuit(prompt)

        assert result["error_code"] == "INVALID_INPUT"
        assert "text" in result["error"]
        assert result["components"] == []
        assert result["connections"] == []


class TestStringPromptsStillWork:

    def test_none_is_reported_as_empty_not_a_type_error(self):
        result = generate_circuit(None)

        assert result["error_code"] == "INVALID_INPUT"
        assert "empty" in result["error"].lower()

    def test_valid_prompt_still_generates(self):
        result = generate_circuit("make me an led circuit")

        assert "error" not in result
        assert result["circuit_name"] == "LED Circuit"
