"""
CircuitMind - Component name normalization tests
tests/test_component_normalize.py

_normalize() replaced spaces and hyphens one at a time, so repeated
separators survived as doubled underscores ("DC--Motor" -> "dc__motor").
Those keys then missed COMPONENT_DB and fell through to looser substring
matching, resolving a DC motor to a plain "motor" and "solar  panel" to
nothing at all.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.component_resolver import _fuzzy_match, _normalize, is_logic_circuit


class TestNormalizeCollapsesSeparators:

    def test_double_hyphen(self):
        assert _normalize("DC--Motor") == "dc_motor"

    def test_double_space(self):
        assert _normalize("solar  panel") == "solar_panel"

    def test_mixed_separators(self):
        assert _normalize("555 -  timer") == "555_timer"

    def test_padding_is_ignored(self):
        assert _normalize("  LED  ") == "led"

    def test_canonical_names_are_unchanged(self):
        assert _normalize("npn_transistor") == "npn_transistor"


class TestMessyNamesResolve:

    def test_hyphenated_motor_resolves_to_dc_motor(self):
        assert _fuzzy_match(_normalize("DC--Motor")) == "dc_motor"

    def test_spaced_solar_panel_resolves_to_solar_cell(self):
        assert _fuzzy_match(_normalize("solar  panel")) == "solar_cell"

    def test_logic_circuit_accepts_messy_names(self):
        assert is_logic_circuit(["input_a", "AND  gate", "output"])
