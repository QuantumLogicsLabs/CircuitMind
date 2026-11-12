"""
CircuitMind - Diagnose connection parsing tests
tests/test_diagnose_arrows.py

The export module writes connections with a unicode arrow. The diagnose parser
only understood "->" and "--", so exported circuits looked like a set of
unconnected single nodes: floating warnings appeared and short circuits were
missed.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import (
    _parse_connections,
    check_short_circuit,
    diagnose_circuit,
)


def _codes(result):
    return {issue["code"] for issue in result["issues"]}


# ── _parse_connections ────────────────────────────────────────────────────────

def test_unicode_arrow_is_split():
    assert _parse_connections(["battery \u2192 resistor \u2192 led"]) == [["battery", "resistor", "led"]]


def test_ascii_arrow_still_splits():
    assert _parse_connections(["battery -> led"]) == [["battery", "led"]]


def test_double_dash_still_splits():
    assert _parse_connections(["battery -- led"]) == [["battery", "led"]]


def test_single_node_is_preserved():
    assert _parse_connections(["battery"]) == [["battery"]]


def test_surrounding_whitespace_is_removed():
    assert _parse_connections([" battery  \u2192  led "]) == [["battery", "led"]]


# ── Checks fed by exported connections ───────────────────────────────────────

def test_unicode_short_circuit_is_detected():
    errors = check_short_circuit(["battery \u2192 ground"])

    assert len(errors) == 1
    assert "short circuit" in errors[0].lower()


def test_unicode_chain_does_not_report_floating_components():
    result = diagnose_circuit({
        "circuit_name": "LED",
        "components": ["battery", "resistor", "led"],
        "connections": ["battery \u2192 resistor \u2192 led"],
    })

    assert "FLOATING_COMPONENT" not in _codes(result)


def test_unicode_chain_still_flags_disconnected_component():
    result = diagnose_circuit({
        "components": ["battery", "resistor", "led", "capacitor"],
        "connections": ["battery \u2192 resistor \u2192 led"],
    })

    assert "FLOATING_COMPONENT" in _codes(result)


def test_unicode_polarity_terminals_satisfy_capacitor_check():
    result = diagnose_circuit({
        "components": ["battery", "capacitor"],
        "connections": ["battery \u2192 capacitor+", "capacitor- \u2192 ground"],
    })

    assert "CAPACITOR_POLARITY" not in _codes(result)
