"""
CircuitMind - export format argument tests
tests/test_export_format.py

export_module() compared export_format against VALID_FORMATS verbatim, so
"SPICE" or " spice " from an API client was rejected as an invalid format.
The argument is now trimmed and lower-cased, and the error message lists the
formats in a stable, sorted order instead of set iteration order.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module

CIRCUIT = {
    "circuit_name": "LED",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
}
CIRCUIT_JSON = json.dumps(CIRCUIT)


class TestFormatIsNormalised:

    def test_uppercase_spice_is_accepted(self):
        result = export_module(CIRCUIT_JSON, "SPICE")

        assert result["status"] == "success"
        assert result["format"] == "spice"
        assert "R1" in result["spice_netlist"]

    def test_padded_mixed_case_gate_json_is_accepted(self):
        result = export_module(CIRCUIT_JSON, " Gate_JSON ")

        assert result["status"] == "success"
        assert result["format"] == "gate_json"
        assert len(result["gate_json"]["gates"]) == 3

    def test_default_format_still_works(self):
        result = export_module(CIRCUIT_JSON)

        assert result["status"] == "success"
        assert result["format"] == "spice"


class TestInvalidFormatMessage:

    def test_unknown_format_lists_sorted_options(self):
        result = export_module(CIRCUIT_JSON, "pdf")

        assert result["status"] == "error"
        assert result["message"] == "Invalid format. Use one of: gate_json, spice, svg."

    def test_none_format_is_an_error_not_a_crash(self):
        result = export_module(CIRCUIT_JSON, None)

        assert result["status"] == "error"
        assert "Invalid format" in result["message"]
