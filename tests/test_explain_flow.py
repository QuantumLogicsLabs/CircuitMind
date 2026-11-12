"""
CircuitMind - Explain flow parsing tests
tests/test_explain_flow.py

Connections exported by the export module use a unicode arrow, and terminals
are often written with polarity markers ("led+"). Both used to break the flow
description: unicode chains were reported as disconnected nodes and polarity
suffixed loads lost their effect note.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from explain.explain_module import _parse_flow, _split_connection, explain_circuit


# ── _split_connection ─────────────────────────────────────────────────────────

def test_ascii_arrow():
    assert _split_connection("battery -> resistor -> led") == ["battery", "resistor", "led"]


def test_unicode_arrow():
    assert _split_connection("battery \u2192 resistor \u2192 led") == ["battery", "resistor", "led"]


def test_em_and_en_dash():
    assert _split_connection("battery \u2014 resistor") == ["battery", "resistor"]
    assert _split_connection("battery \u2013 resistor") == ["battery", "resistor"]


def test_double_dash():
    assert _split_connection("battery -- led") == ["battery", "led"]


def test_no_arrow_is_a_single_node():
    assert _split_connection("battery") == ["battery"]


def test_whitespace_around_arrows_is_dropped():
    assert _split_connection("  battery   ->   led  ") == ["battery", "led"]


# ── _parse_flow ───────────────────────────────────────────────────────────────

def test_unicode_chain_is_not_reported_as_standalone():
    flow = _parse_flow(["battery \u2192 resistor \u2192 led"])

    assert "stands alone" not in flow
    assert flow.startswith("Current flows from the battery")
    assert "emit light" in flow


def test_polarity_suffix_keeps_led_effect():
    flow = _parse_flow(["battery -> resistor -> led+"])

    assert "This causes the LED to emit light." in flow


def test_uppercase_output_keeps_effect():
    flow = _parse_flow(["battery -> LED"])

    assert "emit light" in flow


def test_motor_effect_through_alias():
    flow = _parse_flow(["battery \u2192 switch \u2192 dc_motor"])

    assert "motor to spin" in flow


def test_buzzer_effect():
    flow = _parse_flow(["battery -> buzzer"])

    assert "buzzer to produce sound" in flow


def test_non_output_gets_no_effect_note():
    flow = _parse_flow(["battery -> resistor"])

    assert "Current flows from the battery" in flow
    assert "This causes" not in flow


def test_single_node_still_reported():
    flow = _parse_flow(["battery"])

    assert flow == "The battery stands alone with no connections."


def test_multiple_connections_are_joined():
    flow = _parse_flow(["battery -> resistor", "resistor -> led"])

    assert flow.count("Current flows") == 2


def test_explain_circuit_exposes_unicode_flow():
    result = explain_circuit({
        "components": ["battery", "resistor", "led"],
        "connections": ["battery \u2192 resistor \u2192 led"],
    })

    assert "stands alone" not in result["flow_description"]
    assert "emit light" in result["flow_description"]
