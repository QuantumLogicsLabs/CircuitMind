"""Regression tests for labelled capacitor terminal detection."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import diagnose_circuit


def _codes(result):
    return [issue["code"] for issue in result["issues"]]


def test_labelled_terminals_do_not_warn():
    result = diagnose_circuit({
        "circuit_name": "Polarised cap",
        "components": ["battery", "resistor", "capacitor", "ground"],
        "connections": [
            "battery+ -> resistor -> capacitor+",
            "capacitor- -> ground -> battery-",
        ],
    })

    assert "CAPACITOR_POLARITY" not in _codes(result)


def test_unlabelled_capacitor_still_warns():
    result = diagnose_circuit({
        "circuit_name": "Plain cap",
        "components": ["battery", "resistor", "capacitor", "ground"],
        "connections": ["battery -> resistor -> capacitor -> ground"],
    })

    assert "CAPACITOR_POLARITY" in _codes(result)


def test_positive_terminal_only_still_warns():
    result = diagnose_circuit({
        "circuit_name": "Half labelled cap",
        "components": ["battery", "resistor", "capacitor", "ground"],
        "connections": [
            "battery+ -> resistor -> capacitor+",
            "capacitor -> ground -> battery-",
        ],
    })

    assert "CAPACITOR_POLARITY" in _codes(result)
