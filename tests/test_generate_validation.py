"""Tests for generate module input validation."""

import pytest

from generate.generate import generate_circuit, validate_input


def test_surrounding_whitespace_does_not_count_toward_the_length_cap():
    prompt = "  " + "x" * 1000 + "\n"
    assert validate_input(prompt) == "x" * 1000


def test_prompt_over_the_limit_is_rejected():
    with pytest.raises(ValueError, match="too long"):
        validate_input("x" * 1001)


def test_blank_prompt_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        validate_input("   ")


def test_short_prompt_is_rejected():
    with pytest.raises(ValueError, match="too short"):
        validate_input(" ab ")


def test_valid_prompt_is_trimmed():
    assert validate_input("  led circuit  ") == "led circuit"


def test_generate_circuit_reports_invalid_input_as_an_error_result():
    result = generate_circuit("   ")
    assert result["error_code"] == "INVALID_INPUT"
    assert result["components"] == []
    assert result["connections"] == []
