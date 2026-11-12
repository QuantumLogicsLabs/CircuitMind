"""Payload-type validation tests for export/export_module.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module

LED_CIRCUIT = {
    "circuit_name": "LED Circuit",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"],
}


class TestNonObjectPayloads:
    @pytest.mark.parametrize("payload", ["[]", "42", '"text"', "null", "true"])
    def test_non_object_json_is_rejected(self, payload):
        result = export_module(payload, export_format="spice")
        assert result["status"] == "error"

    def test_non_object_error_mentions_object(self):
        result = export_module("[]", export_format="spice")
        assert "object" in result["message"].lower()


class TestComponentTypes:
    @pytest.mark.parametrize("components", ["battery", None, {"battery": 1}, ["battery", 3]])
    def test_components_must_be_a_list_of_strings(self, components):
        payload = json.dumps({"components": components, "connections": []})
        result = export_module(payload, export_format="spice")
        assert result["status"] == "error"
        assert "components" in result["message"]

    @pytest.mark.parametrize("connections", [None, 5, [3], [["battery"]]])
    def test_connections_must_be_a_list_of_strings(self, connections):
        payload = json.dumps({"components": ["battery"], "connections": connections})
        result = export_module(payload, export_format="spice")
        assert result["status"] == "error"
        assert "connections" in result["message"]


class TestCircuitName:
    def test_non_string_name_falls_back_to_default(self):
        payload = json.dumps({**LED_CIRCUIT, "circuit_name": 7})
        result = export_module(payload, export_format="spice")
        assert result["status"] == "success"
        assert result["circuit_name"] == "CircuitMind_Generated_Circuit"

    def test_blank_name_falls_back_to_default(self):
        payload = json.dumps({**LED_CIRCUIT, "circuit_name": "   "})
        result = export_module(payload, export_format="spice")
        assert result["status"] == "success"
        assert result["circuit_name"] == "CircuitMind_Generated_Circuit"

    def test_valid_name_is_preserved(self):
        result = export_module(json.dumps(LED_CIRCUIT), export_format="spice")
        assert result["status"] == "success"
        assert result["circuit_name"] == "LED Circuit"
