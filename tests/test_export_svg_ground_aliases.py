"""Regression tests: ground aliases must not be drawn as components.

generate_svg only skipped the literal "ground", so a circuit that listed
"gnd", "GND", "v-" or "0V" as a component rendered a stray generic box
labelled "Gnd"/"V"/"0v" in the schematic.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from export.export_module import _is_ground_alias, generate_svg


@pytest.mark.parametrize(
    "key", ["ground", "gnd", "0v", "v-", "v_", "negative", "common", "earth", "gnd_1"]
)
def test_ground_aliases_recognised(key):
    assert _is_ground_alias(key)


@pytest.mark.parametrize("key", ["led", "resistor", "battery", "dc_motor", "wire"])
def test_non_ground_components_kept(key):
    assert not _is_ground_alias(key)


def test_svg_skips_gnd_alias():
    svg = generate_svg("Grounded", ["battery", "resistor", "led", "gnd"])
    assert ">Gnd<" not in svg


def test_svg_skips_v_minus_alias():
    svg = generate_svg("Grounded", ["battery", "resistor", "led", "v-"])
    assert ">V<" not in svg
    assert ">V_<" not in svg


def test_svg_still_draws_the_real_components():
    svg = generate_svg("Grounded", ["battery", "resistor", "led", "ground"])
    assert svg.lstrip().startswith("<?xml")
    assert "Battery" in svg
    assert "Resistor" in svg


def test_only_ground_components_raise():
    with pytest.raises(RuntimeError):
        generate_svg("Just Ground", ["ground", "gnd"])
