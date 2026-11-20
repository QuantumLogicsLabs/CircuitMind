"""Tests for the motor speed controller rule template."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules
from utils.component_resolver import COMPONENT_DB


EXPECTED_COMPONENTS = ["power_supply", "potentiometer", "dc_motor", "ground"]


def test_motor_speed_prompt_matches():
    result = generate_with_rules("a motor speed controller for a robot")
    assert result["circuit_name"] == "Motor Speed Controller"
    assert result["components"] == EXPECTED_COMPONENTS


def test_motor_phrases_prefer_the_speed_controller_rule():
    for prompt in ("motor controller", "speed controller", "variable speed motor"):
        assert generate_with_rules(prompt)["circuit_name"] == "Motor Speed Controller"


def test_plain_motor_prompt_is_unchanged():
    assert generate_with_rules("make a motor")["circuit_name"] == "Motor Circuit"


def test_connections_only_reference_declared_components():
    result = generate_with_rules("motor controller")
    for connection in result["connections"]:
        for node in connection.split("->"):
            assert node.strip() in result["components"]


def test_template_components_are_known_to_the_explainer():
    for component in EXPECTED_COMPONENTS:
        assert component in COMPONENT_DB
