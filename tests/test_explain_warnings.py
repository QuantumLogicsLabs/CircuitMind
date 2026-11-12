"""
CircuitMind - Explain warning order and duplicate tests
tests/test_explain_warnings.py

_check_warnings() iterated the NEEDS_CURRENT_LIMIT set, so the same circuit
produced missing-resistor warnings in a different order under different hash
seeds, and a component listed twice warned twice. Unknown-component warnings
also repeated once per duplicate entry.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from explain.explain_module import explain_circuit


def _warnings(components):
    return explain_circuit({"components": components, "connections": []})["warnings"]


class TestCurrentLimitWarningOrder:

    def test_warnings_follow_circuit_order(self):
        warnings = _warnings(["battery", "diode", "led"])

        assert len(warnings) == 2
        assert "'diode'" in warnings[0]
        assert "'led'" in warnings[1]

    def test_reversed_circuit_reverses_warnings(self):
        warnings = _warnings(["battery", "led", "diode"])

        assert "'led'" in warnings[0]
        assert "'diode'" in warnings[1]

    def test_duplicate_component_warns_once(self):
        warnings = _warnings(["battery", "led", "led"])

        assert len(warnings) == 1
        assert "'led'" in warnings[0]

    def test_a_limiter_silences_every_warning(self):
        assert _warnings(["battery", "led", "diode", "resistor"]) == []


class TestUnknownComponentWarnings:

    def test_duplicate_unknown_component_warns_once(self):
        warnings = _warnings(["battery", "fluxbox", "fluxbox"])

        assert len(warnings) == 1
        assert "fluxbox" in warnings[0]

    def test_distinct_unknown_components_each_warn(self):
        warnings = _warnings(["battery", "mystery_a", "mystery_b"])

        assert len(warnings) == 2
        assert "mystery_a" in warnings[0]
        assert "mystery_b" in warnings[1]
