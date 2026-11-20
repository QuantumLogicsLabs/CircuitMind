"""Explanations should use readable component names and correct articles."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from explain.explain_module import _article, _display_name, explain_circuit


LED_CIRCUIT = {
    "circuit_name": "LED Circuit",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
}


def test_display_names_are_readable():
    assert _display_name("dc_motor") == "DC motor"
    assert _display_name("op_amp") == "op-amp"
    assert _display_name("555_timer") == "555 timer"
    assert _display_name("battery") == "battery"
    assert _display_name("flux_capacitor") == "flux capacitor"


def test_articles_follow_pronunciation():
    assert _article("led") == "an"
    assert _article("op_amp") == "an"
    assert _article("battery") == "a"
    assert _article("dc_motor") == "a"


def test_explanation_text_is_human_readable():
    result = explain_circuit(LED_CIRCUIT)
    text = result["explanation"]
    assert "an LED" in text
    assert "led" not in text
    assert "Current flows from the battery → resistor → LED." in text


def test_multiword_component_names_have_no_underscores():
    result = explain_circuit(
        {
            "circuit_name": "Motor",
            "components": ["power_supply", "dc_motor"],
            "connections": ["power_supply -> dc_motor"],
        }
    )
    assert "a DC motor" in result["explanation"]
    assert "a power supply" in result["explanation"]
    assert "_" not in result["explanation"]


def test_component_details_keep_canonical_names():
    result = explain_circuit(LED_CIRCUIT)
    names = [detail["name"] for detail in result["component_details"]]
    assert names == ["battery", "resistor", "led"]
