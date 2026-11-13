"""Regression tests for XNOR vs XOR rule selection."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules


def test_xnor_prompt_builds_an_xnor_circuit():
    result = generate_with_rules("make me an xnor gate")

    assert result["circuit_name"] == "XNOR Gate Circuit"
    assert "xnor" in result["components"]
    assert "xor" not in result["components"]
    assert any("xnor" in connection for connection in result["connections"])


def test_xor_prompt_still_builds_an_xor_circuit():
    result = generate_with_rules("build an xor gate")

    assert result["circuit_name"] == "XOR Gate Circuit"
    assert "xor" in result["components"]
    assert "xnor" not in result["components"]
