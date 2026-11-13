"""Regression tests for empty SPICE netlists."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module


def test_ground_only_circuit_is_rejected():
    circuit = {
        "circuit_name": "Ground only",
        "components": ["ground", "gnd"],
        "connections": ["ground -> gnd"],
    }

    result = export_module(json.dumps(circuit), export_format="spice")

    assert result["status"] == "error"
    assert "non-ground component" in result["message"]


def test_normal_circuit_still_exports():
    circuit = {
        "circuit_name": "LED",
        "components": ["battery", "resistor", "led", "ground"],
        "connections": ["battery -> resistor -> led -> ground"],
    }

    result = export_module(json.dumps(circuit), export_format="spice")

    assert result["status"] == "success"
    assert result["spice_netlist"].splitlines()[-1] == ".end"
    assert "R1" in result["spice_netlist"]
