"""Structural tests for the SPICE netlist generator.

These pin the netlist layout (title, element lines, designator counters,
ground handling, subcircuit blocks) that downstream consumers rely on.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import COMPONENT_MAP, COMPONENT_VALUES, generate_spice


def _element_lines(netlist: str) -> list[str]:
    return [
        line for line in netlist.splitlines()
        if line and not line.startswith(".") and line != netlist.splitlines()[0]
    ]


def test_netlist_starts_with_title_and_ends_with_end():
    netlist = generate_spice("LED Circuit", ["battery", "resistor", "led"])
    lines = netlist.splitlines()

    assert lines[0] == "LED Circuit"
    assert lines[-1] == ".end"
    assert netlist.endswith(".end")


def test_three_component_chain_nodes():
    netlist = generate_spice("LED", ["battery", "resistor", "led"])

    assert _element_lines(netlist) == [
        "V1 1 0 9V",
        "R1 1 2 330ohm",
        "D1 2 0 LED",
    ]


def test_designators_increment_per_symbol_type():
    netlist = generate_spice("Two resistors", ["battery", "resistor", "resistor", "led"])

    assert _element_lines(netlist) == [
        "V1 1 0 9V",
        "R1 1 2 330ohm",
        "R2 2 3 330ohm",
        "D1 3 0 LED",
    ]


def test_ground_components_are_omitted():
    netlist = generate_spice("Grounded", ["battery", "ground", "gnd", "led"])

    assert "ground" not in netlist.lower().split("grounded")[1]
    assert _element_lines(netlist) == ["V1 1 0 9V", "D1 1 0 LED"]


def test_unknown_components_use_subcircuit_symbol():
    netlist = generate_spice("Mystery", ["battery", "widget"])

    assert "X1 1 0 ?" in netlist


def test_every_element_has_symbol_value_pair():
    components = ["battery", "resistor", "capacitor", "inductor", "led", "motor"]
    netlist = generate_spice("Mixed", components)

    for component, line in zip(components, _element_lines(netlist)):
        symbol = COMPONENT_MAP[component]
        value = COMPONENT_VALUES[component]
        parts = line.split()
        assert parts[0].startswith(symbol)
        assert parts[-1] == value


def test_subcircuit_block_is_emitted_for_unknown_value():
    netlist = generate_spice("Buzzer", ["battery", "buzzer"])

    assert "X1 1 0 BUZZER" in netlist
    assert ".subckt BUZZER 1 0" in netlist
    assert "Rdummy 1 0 10Meg" in netlist
    assert ".ends BUZZER" in netlist


def test_single_component_still_produces_valid_netlist():
    netlist = generate_spice("One", ["battery"])

    assert _element_lines(netlist) == ["V1 1 0 9V"]
    assert netlist.splitlines()[-1] == ".end"
