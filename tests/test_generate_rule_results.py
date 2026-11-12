"""
CircuitMind - Rule-based generation result isolation tests
tests/test_generate_rule_results.py

generate_with_rules() used to hand back the rule table's own component and
connection lists, so a caller that appended to a result silently changed the
circuit every later request received.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules


class TestRuleResultsAreCopies:

    def test_mutating_a_result_does_not_change_the_next_result(self):
        first = generate_with_rules("make me an led circuit")
        first["components"].append("capacitor")
        first["connections"].clear()

        second = generate_with_rules("make me an led circuit")

        assert "capacitor" not in second["components"]
        assert second["connections"] == ["battery -> resistor -> led"]

    def test_consecutive_results_do_not_share_lists(self):
        first = generate_with_rules("555 timer")
        second = generate_with_rules("555 timer")

        assert first["components"] == second["components"]
        assert first["connections"] == second["connections"]
        assert first["components"] is not second["components"]
        assert first["connections"] is not second["connections"]

    def test_unknown_prompt_returns_fresh_empty_lists(self):
        first = generate_with_rules("quantum flux capacitor")
        first["components"].append("led")

        second = generate_with_rules("quantum flux capacitor")

        assert second["components"] == []
        assert second["connections"] == []
