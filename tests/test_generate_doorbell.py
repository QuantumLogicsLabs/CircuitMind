"""Tests for the doorbell rule template."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules
from utils.component_resolver import COMPONENT_DB


EXPECTED_COMPONENTS = ["power_supply", "button", "buzzer", "resistor", "ground"]


def test_doorbell_prompt_matches():
    result = generate_with_rules("build me a doorbell")
    assert result["circuit_name"] == "Doorbell Circuit"
    assert result["components"] == EXPECTED_COMPONENTS


def test_alternate_phrasings_and_plurals_match():
    for prompt in ("door bell", "door chime", "chime circuit", "two doorbells"):
        assert generate_with_rules(prompt)["circuit_name"] == "Doorbell Circuit"


def test_plain_buzzer_prompt_is_unchanged():
    assert generate_with_rules("make a buzzer")["circuit_name"] == "Buzzer Circuit"


def test_connections_only_reference_declared_components():
    result = generate_with_rules("doorbell circuit")
    for connection in result["connections"]:
        for node in connection.split("->"):
            assert node.strip() in result["components"]


def test_template_components_are_known_to_the_explainer():
    for component in EXPECTED_COMPONENTS:
        assert component in COMPONENT_DB
