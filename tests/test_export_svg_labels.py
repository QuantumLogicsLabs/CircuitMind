"""Regression tests for schematic display labels.

generate_svg used str.title() on the component key, rendering "LED" as
"Led" and "dc_motor" as "Dc Motor" in the exported schematic.
"""

import pytest

from export.export_module import _display_label, generate_svg


@pytest.mark.parametrize(
    "key,expected",
    [
        ("led", "LED"),
        ("rgb_led", "RGB LED"),
        ("ir_led", "IR LED"),
        ("ldr", "LDR"),
        ("lcd", "LCD"),
        ("dc_motor", "DC Motor"),
        ("555_timer", "555 Timer"),
        ("op_amp", "Op-Amp"),
        ("resistor", "Resistor"),
        ("zener_diode", "Zener Diode"),
        ("solar_cell", "Solar Cell"),
    ],
)
def test_display_label_casing(key, expected):
    assert _display_label(key) == expected


def test_generate_svg_uses_acronym_labels():
    svg = generate_svg("LED Circuit", ["battery", "resistor", "led"])
    assert "LED" in svg
    assert ">Led<" not in svg


def test_generate_svg_dc_motor_label():
    svg = generate_svg("Motor Circuit", ["battery", "switch", "dc_motor"])
    assert "DC Motor" in svg
    assert "Dc Motor" not in svg
