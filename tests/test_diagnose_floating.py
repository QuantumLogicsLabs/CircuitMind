"""
CircuitMind - Floating component matching tests
tests/test_diagnose_floating.py

check_floating_components() treated a connection node as covering a component
when either string contained the other. That made short gate names look wired:
"or" was reported as connected as soon as a "motor" node existed, because
"or" is a substring of "motor".
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import check_floating_components, diagnose_circuit


class TestFloatingMatching:

    def test_short_name_is_not_covered_by_longer_node(self):
        warnings = check_floating_components(
            ["battery", "switch", "motor", "or"],
            ["battery -> switch -> motor"],
        )

        assert any("'or'" in warning for warning in warnings)

    def test_named_gate_is_connected(self):
        warnings = check_floating_components(["battery", "or"], ["battery -> or"])

        assert not any("'or'" in warning for warning in warnings)

    def test_polarity_suffix_does_not_break_matching(self):
        warnings = check_floating_components(
            ["battery", "led"],
            ["battery -> led+"],
        )

        assert not any("'led'" in warning for warning in warnings)

    def test_numbered_node_label_does_not_break_matching(self):
        warnings = check_floating_components(
            ["battery", "resistor"],
            ["battery -> resistor_1"],
        )

        assert not any("'resistor'" in warning for warning in warnings)

    def test_numbered_component_matches_plain_node(self):
        warnings = check_floating_components(
            ["battery", "resistor_1"],
            ["battery -> resistor"],
        )

        assert not any("'resistor_1'" in warning for warning in warnings)

    def test_missing_component_is_still_reported(self):
        warnings = check_floating_components(
            ["battery", "led"],
            ["battery -> resistor"],
        )

        assert any("'led'" in warning for warning in warnings)


class TestDiagnoseIntegration:

    def test_floating_gate_appears_in_structured_issues(self):
        result = diagnose_circuit({
            "circuit_name": "OR check",
            "components":   ["battery", "switch", "motor", "or"],
            "connections":  ["battery -> switch -> motor"],
        })

        floating = [issue for issue in result["issues"] if issue["code"] == "FLOATING_COMPONENT"]
        assert any("'or'" in issue["message"] for issue in floating)

    def test_connected_gate_is_not_flagged(self):
        result = diagnose_circuit({
            "circuit_name": "Wired OR",
            "components":   ["battery", "or"],
            "connections":  ["battery -> or"],
        })

        assert not any(issue["code"] == "FLOATING_COMPONENT" for issue in result["issues"])
