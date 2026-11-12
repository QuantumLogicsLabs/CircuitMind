"""
CircuitMind - SPICE netlist validity tests
tests/test_export_spice.py

SPICE element letters carry an arity: S (switch), Q (BJT) and M (MOSFET)
need four nodes plus a model card, which a two-node circuit cannot supply.
Those components are emitted as subcircuit calls instead, so every line in
the netlist is syntactically valid.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import _spice_subckt_name, export_module, generate_spice


# Two-terminal primitives: <letter><id> <node> <node> <value>
PRIMITIVE_RE = re.compile(r"^[VRCLD]\w* \S+ \S+ \S+$")
# Subcircuit call: X<id> <node> <node> <subckt>
SUBCKT_CALL_RE = re.compile(r"^X\w* \S+ \S+ [A-Za-z_]\w*$")
DIRECTIVE_RE = re.compile(r"^\.(subckt|ends|end)\b")


def _element_lines(netlist):
    return [line for line in netlist.splitlines()[1:] if not DIRECTIVE_RE.match(line)]


def _all_components():
    return [
        "battery", "power_supply", "solar_cell", "resistor", "capacitor", "inductor",
        "potentiometer", "thermistor", "ldr", "fuse", "diode", "led", "zener_diode",
        "photodiode", "switch", "button", "transistor", "npn_transistor",
        "pnp_transistor", "mosfet", "motor", "dc_motor", "buzzer", "speaker", "relay",
        "op_amp", "555_timer", "arduino", "microcontroller", "charge_controller",
        "sensor", "display", "lcd", "transformer",
    ]


# ── Element syntax ────────────────────────────────────────────────────────────

def test_every_element_line_is_syntactically_valid():
    netlist = generate_spice("all", _all_components())

    for line in _element_lines(netlist):
        assert PRIMITIVE_RE.match(line) or SUBCKT_CALL_RE.match(line), line


def test_switch_is_not_emitted_as_bare_s_element():
    netlist = generate_spice("motor", ["battery", "switch", "dc_motor"])

    assert not any(line.startswith("S") for line in _element_lines(netlist))
    assert any("SW" in line for line in _element_lines(netlist))


def test_motor_and_mosfet_are_not_emitted_as_bare_m_elements():
    for component in ("motor", "dc_motor", "mosfet"):
        netlist = generate_spice("c", ["battery", component])
        assert not any(line.startswith("M") for line in _element_lines(netlist)), component


def test_transistor_is_not_emitted_as_bare_q_element():
    netlist = generate_spice("amp", ["battery", "resistor", "transistor", "led"])

    assert not any(line.startswith("Q") for line in _element_lines(netlist))


# ── Subcircuit definitions ───────────────────────────────────────────────────

def test_every_subcircuit_call_has_a_definition():
    netlist = generate_spice("all", _all_components())
    calls = {line.split()[3] for line in _element_lines(netlist) if line.startswith("X")}
    defined = set(re.findall(r"^\.subckt (\S+) IN OUT$", netlist, re.MULTILINE))

    assert calls
    assert calls == defined


def test_subcircuit_names_are_unique_and_legal():
    netlist = generate_spice("all", _all_components())
    names = re.findall(r"^\.subckt (\S+) IN OUT$", netlist, re.MULTILINE)

    assert len(names) == len(set(names))
    for name in names:
        assert name[0].isalpha(), name
        assert re.fullmatch(r"[A-Za-z0-9_]+", name), name


def test_numeric_model_names_are_prefixed():
    assert _spice_subckt_name("2N2222") == "X_2N2222"
    assert _spice_subckt_name("MOTOR") == "MOTOR"
    assert _spice_subckt_name("10k ohm") == "X_10k_ohm"
    assert _spice_subckt_name("") == "SUBCKT"


def test_netlist_ends_with_end_directive():
    netlist = generate_spice("c", ["battery", "led"])

    assert netlist.splitlines()[-1] == ".end"


def test_ground_is_not_emitted_as_a_component():
    netlist = generate_spice("c", ["battery", "ground", "led"])

    assert "ground" not in netlist.lower()


def test_primitive_value_is_kept():
    netlist = generate_spice("c", ["battery", "resistor", "led"])

    assert "V1 1 0 9V" in netlist
    assert "R1 1 2 330ohm" in netlist
    assert "D1 2 0 LED" in netlist


def test_export_module_returns_the_fixed_netlist():
    result = export_module(
        '{"circuit_name": "Motor", "components": ["battery", "switch", "dc_motor"], "connections": []}',
        export_format="spice",
    )

    assert result["status"] == "success"
    assert "M1" not in result["spice_netlist"]
    assert ".subckt MOTOR IN OUT" in result["spice_netlist"]
