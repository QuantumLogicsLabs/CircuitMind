"""
CircuitMind - Diagnose finding order and duplicate tests
tests/test_diagnose_findings.py

check_current_limiting() used to iterate the NEEDS_CURRENT_LIMIT set, so the
warning order changed between interpreter runs (and duplicated components were
reported repeatedly). The order now follows the circuit's component list.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import check_current_limiting


class TestCurrentLimitWarningOrder:

    def test_warnings_follow_component_order(self):
        warnings = check_current_limiting(["diode", "led"])

        assert len(warnings) == 2
        assert "'diode'" in warnings[0]
        assert "'led'" in warnings[1]

    def test_reversed_order_reverses_warnings(self):
        warnings = check_current_limiting(["led", "diode"])

        assert "'led'" in warnings[0]
        assert "'diode'" in warnings[1]

    def test_duplicate_components_are_reported_once(self):
        warnings = check_current_limiting(["led", "led", "battery"])

        assert len(warnings) == 1
        assert "'led'" in warnings[0]

    def test_a_limiter_silences_every_warning(self):
        assert check_current_limiting(["led", "diode", "resistor"]) == []
