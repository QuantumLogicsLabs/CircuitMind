"""Unit tests for export.export_module.generate_svg."""

import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import generate_svg

SVG_NS = "{http://www.w3.org/2000/svg}"


def _root(svg: str):
    return ET.fromstring(svg)


class TestSvgDocument:
    def test_multi_component_output_is_well_formed_xml(self):
        svg = generate_svg("LED Blinker", ["battery", "resistor", "led"])
        root = _root(svg)
        assert root.tag == f"{SVG_NS}svg"
        assert root.get("viewBox")
        assert root.get("version") == "1.1"

    def test_single_component_output_is_well_formed_xml(self):
        svg = generate_svg("Battery Only", ["battery"])
        root = _root(svg)
        assert root.tag == f"{SVG_NS}svg"
        # Labels are emitted as XML comments by schemdraw's SVG backend.
        assert "<!-- Battery -->" in svg


class TestSvgLabels:
    def test_known_components_are_labelled(self):
        svg = generate_svg("Known", ["battery", "resistor", "led"])
        for label in ("Battery", "Resistor", "Led"):
            assert f"<!-- {label} -->" in svg

    def test_unknown_component_falls_back_to_generic_box(self):
        svg = generate_svg("Unknown", ["flux capacitor"])
        _root(svg)
        assert "<!-- Flux Capacitor -->" in svg

    def test_names_are_case_and_separator_normalized(self):
        svg = generate_svg(
            "Normalized", ["BATTERY", " dc-motor ", "DC Motor", "power_supply"]
        )
        for label in ("Battery", "Dc Motor", "Power Supply"):
            assert f"<!-- {label} -->" in svg

    def test_ground_is_not_drawn(self):
        svg = generate_svg("Grounded", ["battery", "ground", "led"])
        _root(svg)
        assert "<!-- Ground -->" not in svg
        assert "<!-- Battery -->" in svg
        assert "<!-- Led -->" in svg


class TestSvgEmpty:
    @pytest.mark.parametrize(
        "components",
        [
            [],
            ["ground"],
            ["ground", "GROUND", " Ground "],
        ],
    )
    def test_no_drawable_components_raises(self, components):
        with pytest.raises(RuntimeError, match="No drawable components found"):
            generate_svg("Empty", components)
