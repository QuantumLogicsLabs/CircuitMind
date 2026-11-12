"""
CircuitMind - SPICE component name normalisation tests
tests/test_export_component_names.py

generate_spice() looked components up in COMPONENT_MAP / COMPONENT_VALUES with
the raw string, while the SVG exporter normalised names first. Mixed-case or
spaced names ("Battery", "solar cell") missed the maps and were emitted as
`X1 1 0 ?` with a `.subckt ?` block, which is not valid SPICE.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module, generate_spice


def _netlist(components):
    return generate_spice("Case Test", components).splitlines()


class TestNormalisedLookups:

    def test_mixed_case_components_use_real_symbols(self):
        lines = _netlist(["Battery", "Resistor", "LED"])

        assert "V1 1 0 9V" in lines
        assert "R1 1 2 330ohm" in lines
        assert "D1 2 0 LED" in lines
        assert not any("?" in line for line in lines)

    def test_spaced_component_names_use_real_symbols(self):
        lines = _netlist(["solar cell", "diode", "battery"])

        assert "V1 1 0 5V" in lines
        assert "D1 1 2 1N4148" in lines
        assert "V2 2 0 9V" in lines
        assert not any(line.startswith("X") for line in lines)

    def test_hyphenated_names_use_real_symbols(self):
        lines = _netlist(["battery", "zener-diode"])

        assert "D1 1 0 1N4733A" in lines

    def test_ground_is_stripped_regardless_of_case(self):
        lines = _netlist(["battery", "GND", "Ground"])

        assert lines == ["Case Test", "V1 1 0 9V", ".end"]

    def test_export_module_spice_uses_normalised_names(self):
        payload = json.dumps({
            "circuit_name": "Case Test",
            "components":   ["Battery", "Resistor", "LED"],
            "connections":  ["Battery -> Resistor -> LED"],
        })

        result = export_module(payload, export_format="spice")

        assert result["status"] == "success"
        assert "X1 1 0 ?" not in result["spice_netlist"]
        assert "R1 1 2 330ohm" in result["spice_netlist"]
