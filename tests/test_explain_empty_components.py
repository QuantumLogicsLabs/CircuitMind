"""
CircuitMind - Explain output for connection-only payloads
tests/test_explain_empty_components.py

When a payload carried connections but no components, explain_circuit()
produced "No components provided. Cannot generate an explanation. Current
flows from the ..." — it appended a perfectly good flow description to a
sentence claiming no explanation was possible.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from explain.explain_module import explain_circuit


class TestEmptyComponentsWithConnections:

    def test_flow_is_reported_instead_of_a_contradiction(self):
        result = explain_circuit({
            "components": [],
            "connections": ["battery -> resistor"],
        })

        explanation = result["explanation"]
        assert explanation.startswith("No components provided.")
        assert "Current flows from the battery → resistor." in explanation
        assert "Cannot generate an explanation" not in explanation

    def test_flow_description_is_still_exposed(self):
        result = explain_circuit({
            "components": [],
            "connections": ["battery -> led"],
        })

        assert result["flow_description"] == (
            "Current flows from the battery → led. This causes the LED to emit light."
        )

    def test_no_components_and_no_connections_is_unchanged(self):
        result = explain_circuit({"components": [], "connections": []})

        assert result["explanation"] == "No components provided. Cannot generate an explanation."
        assert result["flow_description"] == ""

    def test_normal_circuit_still_appends_flow(self):
        result = explain_circuit({
            "components": ["battery", "resistor", "led"],
            "connections": ["battery -> resistor -> led"],
        })

        assert result["explanation"].startswith("This circuit uses a battery")
        assert result["explanation"].endswith(
            "Current flows from the battery → resistor → led. This causes the LED to emit light."
        )
