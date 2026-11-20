"""Tests for the voltage-divider rule template."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules
from utils.component_resolver import COMPONENT_DB


EXPECTED_COMPONENTS = ["power_supply", "resistor", "potentiometer", "ground"]


def test_voltage_divider_prompt_matches():
    result = generate_with_rules("Build a voltage divider for a 3.3V sensor")
    assert result["circuit_name"] == "Voltage Divider Circuit"
    assert result["components"] == EXPECTED_COMPONENTS
    assert result["source"] == "rule-based"


def test_alternate_phrasings_match():
    for prompt in ("potential divider", "voltage splitter", "two voltage dividers"):
        assert generate_with_rules(prompt)["circuit_name"] == "Voltage Divider Circuit"


def test_connections_only_reference_declared_components():
    result = generate_with_rules("voltage divider")
    for connection in result["connections"]:
        for node in connection.split("->"):
            assert node.strip() in result["components"]


def test_template_components_are_known_to_the_explainer():
    for component in EXPECTED_COMPONENTS:
        assert component in COMPONENT_DB


def test_unrelated_prompts_are_not_hijacked():
    assert generate_with_rules("warp core stabiliser")["circuit_name"] == "Unknown"
    assert generate_with_rules("make me a led circuit")["circuit_name"] != "Voltage Divider Circuit"
