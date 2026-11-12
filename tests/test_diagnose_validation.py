"""
CircuitMind - Diagnose input validation tests
tests/test_diagnose_validation.py

diagnose_circuit() assumed a dict of list-of-string fields: a None payload, a
string connection, or a non-string component raised AttributeError/TypeError
instead of returning a diagnosis result.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import diagnose_circuit

LED_CIRCUIT = {
    "circuit_name": "LED",
    "components":   ["battery", "resistor", "led", "ground"],
    "connections":  ["battery -> resistor -> led", "led -> ground"],
}


class TestInvalidPayloads:

    def test_non_dict_payload_returns_error(self):
        result = diagnose_circuit(None)

        assert result["passed"] is False
        assert result["issues"] == []
        assert result["legacy_issues"] == []
        assert result["summary"] == {"errors": 0, "warnings": 0, "info": 0}
        assert "error" in result

    def test_string_payload_returns_error(self):
        assert "error" in diagnose_circuit("battery -> led")

    def test_non_string_component_is_rejected(self):
        result = diagnose_circuit({"components": ["battery", 1], "connections": []})

        assert "components" in result["error"]

    def test_non_string_connection_is_rejected(self):
        result = diagnose_circuit({"components": ["battery"], "connections": [None]})

        assert "connections" in result["error"]

    def test_non_list_components_are_rejected(self):
        result = diagnose_circuit({"components": "battery", "connections": []})

        assert "components" in result["error"]

    def test_none_fields_are_treated_as_empty(self):
        result = diagnose_circuit({"components": None, "connections": None})

        assert "error" not in result
        codes = [issue["code"] for issue in result["issues"]]
        assert "NO_POWER_SOURCE" in codes
        assert "NO_CONNECTIONS" in codes

    def test_missing_fields_are_treated_as_empty(self):
        result = diagnose_circuit({})

        assert "error" not in result
        assert result["circuit_name"] == "Unnamed Circuit"

    def test_non_string_circuit_name_is_coerced(self):
        result = diagnose_circuit({
            "circuit_name": 123,
            "components":   LED_CIRCUIT["components"],
            "connections":  LED_CIRCUIT["connections"],
        })

        assert result["circuit_name"] == "123"


class TestValidPayloads:

    def test_valid_circuit_is_diagnosed(self):
        result = diagnose_circuit(LED_CIRCUIT)

        assert "error" not in result
        assert result["issues"] == []
        assert result["passed"] is True
