"""Tests for the automatic night-light rule template."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules
from utils.component_resolver import COMPONENT_DB


EXPECTED_COMPONENTS = [
    "power_supply",
    "ldr",
    "resistor",
    "transistor",
    "led",
    "ground",
]


def test_night_light_prompt_matches():
    result = generate_with_rules("make an automatic night light")
    assert result["circuit_name"] == "Automatic Night Light"
    assert result["components"] == EXPECTED_COMPONENTS


def test_phrases_containing_light_prefer_the_night_light_rule():
    for prompt in ("dark detector", "a light activated switch", "ldr circuit"):
        assert generate_with_rules(prompt)["circuit_name"] == "Automatic Night Light"


def test_generic_light_prompt_still_makes_an_led_circuit():
    assert generate_with_rules("make me a light")["circuit_name"] == "LED Circuit"


def test_connections_only_reference_declared_components():
    result = generate_with_rules("night light")
    for connection in result["connections"]:
        for node in connection.split("->"):
            assert node.strip() in result["components"]


def test_template_components_are_known_to_the_explainer():
    for component in EXPECTED_COMPONENTS:
        assert component in COMPONENT_DB
