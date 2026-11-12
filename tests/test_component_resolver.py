"""Unit tests for utils/component_resolver.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.component_resolver import COMPONENT_DB, _ALIASES, _fuzzy_match


class TestCanonicalNames:
    def test_every_canonical_name_resolves_to_itself(self):
        for name in COMPONENT_DB:
            assert _fuzzy_match(name) == name

    def test_every_alias_resolves_to_its_canonical_name(self):
        for alias, canonical in _ALIASES.items():
            assert _fuzzy_match(alias) == canonical, alias


class TestWordBoundaries:
    @pytest.mark.parametrize("name", ["candle", "scheduled", "sensorless", "glass"])
    def test_words_containing_gate_names_are_not_gates(self, name):
        assert _fuzzy_match(name) == name

    def test_short_gate_names_do_not_shadow_longer_components(self):
        assert _fuzzy_match("motor") == "motor"
        assert _fuzzy_match("resistor") == "resistor"
        assert _fuzzy_match("sensor") == "sensor"

    def test_compound_names_still_match(self):
        assert _fuzzy_match("solar_cell_module") == "solar_cell"
        assert _fuzzy_match("temperature_sensor") == "sensor"
        assert _fuzzy_match("led_red") == "led"


class TestInputNormalisation:
    def test_plural_forms(self):
        assert _fuzzy_match("leds") == "led"
        assert _fuzzy_match("resistors") == "resistor"
        assert _fuzzy_match("batteries") == "battery"
        assert _fuzzy_match("switches") == "switch"

    def test_case_and_separators(self):
        assert _fuzzy_match("9V Battery") == "battery"
        assert _fuzzy_match("DC-Motor") == "dc_motor"
        assert _fuzzy_match("  LED  ") == "led"

    def test_unknown_names_are_returned_unchanged(self):
        assert _fuzzy_match("gizmo") == "gizmo"
