"""Export must reject circuits with no components.

Previously an empty components list produced a "successful" export: a
title-only SPICE netlist, a blank SVG, or a gate graph with zero gates.
"""

import json
import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module

EMPTY_CIRCUIT = {"circuit_name": "Empty", "components": [], "connections": []}


@pytest.mark.parametrize("fmt", ["spice", "svg", "gate_json"])
def test_empty_components_is_rejected_for_every_format(fmt):
    result = export_module(json.dumps(EMPTY_CIRCUIT), export_format=fmt)

    assert result["status"] == "error"
    assert "no components" in result["message"].lower()


def test_missing_fields_message_is_unchanged():
    result = export_module(json.dumps({"circuit_name": "X"}), export_format="spice")

    assert result["status"] == "error"
    assert "Missing required fields" in result["message"]


def test_ground_only_circuit_still_reaches_the_generator():
    circuit = {"circuit_name": "GND", "components": ["ground"], "connections": []}
    result = export_module(json.dumps(circuit), export_format="spice")

    # Non-empty component list: the ground-only decision stays with the
    # format-specific generator rather than this guard.
    assert result["status"] == "success"


def test_normal_circuit_still_exports():
    circuit = {
        "circuit_name": "LED",
        "components": ["battery", "resistor", "led"],
        "connections": ["battery -> resistor -> led"],
    }
    result = export_module(json.dumps(circuit), export_format="spice")

    assert result["status"] == "success"
    assert "V1" in result["spice_netlist"]
