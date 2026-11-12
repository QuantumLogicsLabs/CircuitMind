"""
CircuitMind - Explain input validation tests
tests/test_explain_validation.py

explain_circuit() assumed a dict with list-of-string fields. A None payload,
a dict-valued connection, or components containing non-strings raised
AttributeError/TypeError instead of returning a usable explanation result.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from explain.explain_module import explain_circuit, explain_circuits_batch

LED_CIRCUIT = {
    "components":  ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
}


class TestInvalidPayloads:

    def test_non_dict_payload_returns_error(self):
        result = explain_circuit(None)

        assert "error" in result
        assert result["explanation"] == ""
        assert result["component_details"] == []
        assert result["flow_description"] == ""
        assert result["warnings"] == []

    def test_string_components_are_rejected(self):
        result = explain_circuit({"components": "led", "connections": []})

        assert "components" in result["error"]

    def test_non_string_component_is_rejected(self):
        result = explain_circuit({"components": ["led", 42], "connections": []})

        assert "components" in result["error"]

    def test_non_string_connection_is_rejected(self):
        result = explain_circuit({
            "components":  ["battery", "led"],
            "connections": [{"from": "battery", "to": "led"}],
        })

        assert "connections" in result["error"]

    def test_non_list_connections_are_rejected(self):
        result = explain_circuit({"components": ["led"], "connections": "led"})

        assert "connections" in result["error"]

    def test_none_fields_are_treated_as_empty(self):
        result = explain_circuit({"components": None, "connections": None})

        assert "error" not in result
        assert "No components provided" in result["explanation"]

    def test_missing_fields_are_treated_as_empty(self):
        result = explain_circuit({})

        assert "error" not in result

    def test_batch_propagates_errors_per_item(self):
        results = explain_circuits_batch([LED_CIRCUIT, None])

        assert "error" not in results[0]
        assert "error" in results[1]


class TestValidPayloads:

    def test_valid_circuit_is_explained(self):
        result = explain_circuit(LED_CIRCUIT)

        assert "error" not in result
        assert "led" in result["explanation"].lower()
        assert result["flow_description"]
        assert isinstance(result["warnings"], list)
