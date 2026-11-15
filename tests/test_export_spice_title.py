"""SPICE title-line sanitization tests.

SPICE treats the first netlist line as the circuit title, so it must be a
single non-empty line. These tests pin that behaviour for blank, non-string,
and multi-line circuit names.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import (
    generate_spice,
    export_module,
    sanitize_spice_title,
    _DEFAULT_SPICE_TITLE,
)

COMPONENTS = ["battery", "resistor", "led"]


@pytest.mark.parametrize("raw", ["", "   ", "\n\t ", None, 42, ["LED"]])
def test_blank_or_non_string_name_falls_back_to_default(raw):
    assert sanitize_spice_title(raw) == _DEFAULT_SPICE_TITLE


def test_multiline_name_is_collapsed_to_single_line():
    title = sanitize_spice_title("My LED\nCircuit\tWith  Spaces")

    assert title == "My LED Circuit With Spaces"
    assert "\n" not in title and "\t" not in title


def test_normal_name_is_preserved():
    assert sanitize_spice_title("LED Circuit") == "LED Circuit"


def test_generate_spice_first_line_is_sanitized():
    netlist = generate_spice("", COMPONENTS)
    lines = netlist.splitlines()

    assert lines[0] == _DEFAULT_SPICE_TITLE
    assert lines[-1] == ".end"
    assert len(lines) > 2


def test_generate_spice_keeps_valid_title():
    netlist = generate_spice("Blinker\nStage 2", COMPONENTS)

    assert netlist.splitlines()[0] == "Blinker Stage 2"


def test_export_module_spice_export_with_blank_name():
    result = export_module(
        '{"circuit_name": "   ", "components": ["battery", "led"], '
        '"connections": ["battery -> led"]}',
        export_format="spice",
    )

    assert result["status"] == "success"
    assert result["spice_netlist"].splitlines()[0] == _DEFAULT_SPICE_TITLE
