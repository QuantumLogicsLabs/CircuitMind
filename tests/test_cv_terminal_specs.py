"""
CircuitMind - CV terminal spec tests
tests/test_cv_terminal_specs.py

dataset_preparation.py trains the detector on class names such as ic_chip,
power_source and ground. Those names must resolve to sensible terminal sets,
otherwise the netlist gives them the generic 2-pin fallback.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cv_module.topology_extraction import (
    DEFAULT_TERMINALS,
    TERMINAL_SPECS,
    _terminal_coords,
    _terminals_for,
)

DATASET_CLASSES = [
    "resistor",
    "capacitor",
    "inductor",
    "diode",
    "transistor",
    "ic_chip",
    "ground",
    "power_source",
]


def test_every_training_class_has_a_specific_terminal_set():
    for class_name in DATASET_CLASSES:
        assert class_name in TERMINAL_SPECS, f"{class_name} falls back to 2 pins"


def test_ic_chip_gets_four_pins():
    terminals = _terminals_for("ic_chip")
    assert len(terminals) == 4
    assert terminals[0] == "pin_1"


def test_power_source_has_polarity():
    assert _terminals_for("power_source") == ["positive", "negative"]


def test_ground_has_one_terminal():
    assert _terminals_for("ground") == ["terminal_1"]
    assert len(_terminal_coords(0, 0, 10, 10, _terminals_for("ground"))) == 1


def test_lookup_is_case_insensitive():
    assert _terminals_for("IC_CHIP") == _terminals_for("ic_chip")


def test_unknown_component_falls_back_to_default():
    assert _terminals_for("flux_capacitor") == DEFAULT_TERMINALS


def test_fallback_list_is_not_shared():
    terminals = _terminals_for("unknown")
    terminals.append("mutated")
    assert _terminals_for("unknown") == DEFAULT_TERMINALS
