"""
CircuitMind - SPICE title sanitisation tests
tests/test_export_spice_title.py

The circuit name is copied verbatim into the first line of the netlist. A
name containing a newline could inject extra SPICE lines (including an early
.end), so the title must stay on one line.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import generate_spice, export_module, _spice_title


def test_newline_in_name_does_not_inject_netlist_lines():
    netlist = generate_spice("Evil\nR99 1 0 1k\n.end", ["battery", "resistor"])
    lines = netlist.splitlines()

    assert lines[0] == "Evil R99 1 0 1k .end"
    assert "R99 1 0 1k" not in lines[1:]
    assert lines.count(".end") == 1


def test_whitespace_is_collapsed():
    assert _spice_title("  My\t Circuit \n") == "My Circuit"


def test_blank_name_falls_back_to_default():
    assert _spice_title("   ") == "CircuitMind_Generated_Circuit"
    assert _spice_title(None) == "CircuitMind_Generated_Circuit"


def test_non_string_name_is_coerced():
    netlist = generate_spice(42, ["battery"])
    assert netlist.splitlines()[0] == "42"


def test_export_module_sanitises_title():
    result = export_module(
        '{"circuit_name": "A\\nB", "components": ["battery", "resistor"], '
        '"connections": ["battery -> resistor"]}'
    )
    assert result["status"] == "success"
    assert result["spice_netlist"].splitlines()[0] == "A B"
