"""Logic signal pins must be recognised by explain.

The rule-based generator emits pin names such as ``parity_output``, ``cout``,
``sel`` and decoder bits (``y0``..``y3``). Without entries in the component
knowledge base, explain reported them as unknown components.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_with_rules
from explain.explain_module import explain_circuit
from utils.component_resolver import COMPONENT_DB

LOGIC_PROMPTS = [
    "half adder",
    "full adder",
    "half subtractor",
    "full subtractor",
    "odd parity",
    "even parity",
    "multiplexer",
    "demultiplexer",
    "decoder",
    "comparator",
    "xor circuit",
    "logic gate circuit",
]


@pytest.mark.parametrize("prompt", LOGIC_PROMPTS)
def test_generated_logic_circuit_has_no_unknown_components(prompt):
    circuit = generate_with_rules(prompt)
    result = explain_circuit(circuit)

    unknown = [d["name"] for d in result["component_details"] if d["role"] == "unknown"]
    assert unknown == []
    assert not any("Unknown component" in w for w in result["warnings"])


@pytest.mark.parametrize(
    "name,role",
    [
        ("parity_output", "output signal"),
        ("diff_output", "output signal"),
        ("borrow_output", "output signal"),
        ("cout", "output signal"),
        ("cin", "input signal"),
        ("bin", "input signal"),
        ("sel", "input signal"),
        ("input_din", "input signal"),
        ("eq_out", "output signal"),
        ("gt_out", "output signal"),
        ("lt_out", "output signal"),
        ("output", "output signal"),
        ("y0", "output signal"),
        ("y3", "output signal"),
    ],
)
def test_logic_pins_are_in_knowledge_base(name, role):
    assert name in COMPONENT_DB
    assert COMPONENT_DB[name]["role"] == role


def test_original_logic_io_entries_are_unchanged():
    assert COMPONENT_DB["input_a"]["role"] == "input signal"
    assert COMPONENT_DB["sum_output"]["role"] == "output signal"
    assert COMPONENT_DB["carry_output"]["role"] == "output signal"
