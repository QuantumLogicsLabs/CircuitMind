"""
CircuitMind - SVG component resolution tests
tests/test_export_svg.py

generate_svg() had its own private normaliser that only replaced single
spaces and hyphens and never consulted the component resolver, so
"DC--Motor" fell back to a generic box even though "dc_motor" has a motor
symbol, and the "solar  panel" alias never reached the solar_cell symbol.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

pytest.importorskip("schemdraw")

from export.export_module import _svg_key, generate_svg  # noqa: E402


def _shape_signature(components):
    # schemdraw embeds fresh element ids on every call, so compare the drawn
    # geometry (path data starting with a move command), not the raw markup.
    paths = re.findall(r'd="([^"]+)"', generate_svg("T", components))
    return sorted(path for path in paths if path[:1] in ("M", "m"))


class TestSvgKeyResolution:

    @pytest.mark.parametrize("name, expected", [
        ("DC--Motor", "dc_motor"),
        ("solar  panel", "solar_cell"),
        ("  LED  ", "led"),
        ("zener-diode", "zener_diode"),
        ("fluxbox", "fluxbox"),
    ])
    def test_names_resolve_like_the_shared_resolver(self, name, expected):
        assert _svg_key(name) == expected


class TestSvgRendering:

    def test_returns_svg_markup(self):
        svg = generate_svg("LED", ["battery", "resistor", "led"])

        assert svg.lstrip().startswith("<?xml") or svg.lstrip().startswith("<svg")
        assert "Battery" in svg
        assert "Resistor" in svg

    def test_separator_variant_uses_the_same_symbol(self):
        assert _shape_signature(["battery", "DC--Motor"]) == _shape_signature(
            ["battery", "dc_motor"]
        )

    def test_alias_uses_the_same_symbol(self):
        assert _shape_signature(["solar  panel"]) == _shape_signature(["solar_cell"])

    def test_signature_distinguishes_known_from_generic_boxes(self):
        assert _shape_signature(["fluxbox"]) != _shape_signature(["dc_motor"])


class TestGroundHandling:

    def test_ground_alias_is_not_drawn_as_a_component(self):
        svg = generate_svg("Grounded", ["battery", "led", "GND"])

        assert "Gnd" not in svg
        assert _shape_signature(["battery", "led", "GND"]) == _shape_signature(
            ["battery", "led"]
        )

    def test_ground_only_circuit_is_not_drawable(self):
        with pytest.raises(RuntimeError):
            generate_svg("Ground only", ["ground", "gnd"])
