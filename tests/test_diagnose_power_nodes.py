"""Regression tests for alias-aware short-circuit detection."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose.diagnose_module import diagnose_circuit


def _codes(result):
    return [issue["code"] for issue in result["issues"]]


def test_vcc_to_ground_without_load_is_a_short():
    result = diagnose_circuit({
        "circuit_name": "Rail short",
        "components": ["power_supply", "led"],
        "connections": ["vcc -> gnd"],
    })

    assert "SHORT_CIRCUIT" in _codes(result)


def test_vcc_through_load_is_not_a_short():
    result = diagnose_circuit({
        "circuit_name": "Safe rail",
        "components": ["power_supply", "resistor", "ground"],
        "connections": ["vcc -> resistor -> gnd"],
    })

    assert "SHORT_CIRCUIT" not in _codes(result)
