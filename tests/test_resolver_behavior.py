"""
CircuitMind - component resolver behaviour tests
tests/test_resolver_behavior.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.component_resolver import _fuzzy_match, _normalize


def test_normalize_lowercases_and_joins_separators():
    assert _normalize("  Light-Emitting Diode ") == "light_emitting_diode"
    assert _normalize("NPN Transistor") == "npn_transistor"


def test_exact_component_names_resolve():
    assert _fuzzy_match("battery") == "battery"
    assert _fuzzy_match("resistor") == "resistor"


def test_aliases_resolve_to_canonical_names():
    assert _fuzzy_match("vcc") == "power_supply"
    assert _fuzzy_match("ne555") == "555_timer"
    assert _fuzzy_match("opamp") == "op_amp"
    assert _fuzzy_match("photoresistor") == "ldr"


def test_compound_names_use_the_longest_component_match():
    assert _fuzzy_match("indicator_led") == "led"
    assert _fuzzy_match("battery_holder") == "battery"
    assert _fuzzy_match("thermistor_sensor") == "thermistor"


def test_unknown_name_is_returned_unchanged():
    assert _fuzzy_match("mystery_widget") == "mystery_widget"
