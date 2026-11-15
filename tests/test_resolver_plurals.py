"""
CircuitMind - plural component name tests
tests/test_resolver_plurals.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.component_resolver import _fuzzy_match


def test_plural_component_names_resolve():
    assert _fuzzy_match("leds") == "led"
    assert _fuzzy_match("capacitors") == "capacitor"
    assert _fuzzy_match("diodes") == "diode"
    assert _fuzzy_match("switches") == "switch"
    assert _fuzzy_match("batteries") == "battery"


def test_plural_aliases_resolve():
    assert _fuzzy_match("solar_panels") == "solar_cell"
    assert _fuzzy_match("pots") == "potentiometer"
    assert _fuzzy_match("temp_sensors") == "thermistor"
    assert _fuzzy_match("push_buttons") == "button"


def test_singular_names_are_unchanged():
    assert _fuzzy_match("led") == "led"
    assert _fuzzy_match("battery") == "battery"
    assert _fuzzy_match("solar_panel") == "solar_cell"


def test_unknown_names_pass_through():
    assert _fuzzy_match("quux_device") == "quux_device"
    assert _fuzzy_match("gizmos") == "gizmos"
