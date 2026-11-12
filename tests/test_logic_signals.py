"""
CircuitMind - Generator signal name coverage tests
tests/test_logic_signals.py

The rule-based generator emits signal names such as cin, cout, sel, y0 and
diff_output, but only a few of them were in COMPONENT_DB. explain_circuit()
therefore warned "Unknown component 'cin'" on circuits the app generated
itself. On the way, the trailing "or" in borrow_output made the resolver map
that output to the OR gate.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from explain.explain_module import explain_circuit
from generate.generate import _RULES
from utils.component_resolver import COMPONENT_DB, _fuzzy_match, _normalize

GENERATED_SIGNALS = [
    "cin", "cout", "sel", "bin", "input_din",
    "diff_output", "borrow_output", "parity_output",
    "eq_out", "gt_out", "lt_out", "output",
    "output_y0", "output_y1", "y0", "y1", "y2", "y3",
]


class TestSignalNames:

    def test_generated_signal_names_are_known(self):
        for name in GENERATED_SIGNALS:
            assert name in COMPONENT_DB, name

    def test_signals_resolve_to_themselves(self):
        for name in GENERATED_SIGNALS:
            assert _fuzzy_match(_normalize(name)) == name, name

    def test_borrow_output_is_not_mistaken_for_an_or_gate(self):
        assert _fuzzy_match(_normalize("borrow_output")) == "borrow_output"

    def test_carry_and_borrow_outputs_are_output_signals(self):
        for name in ["cout", "diff_output", "borrow_output", "parity_output"]:
            assert COMPONENT_DB[name]["role"] == "output signal"


class TestExplainGeneratedCircuits:

    def test_no_generated_circuit_reports_an_unknown_component(self):
        for keywords, name, components, connections, description in _RULES:
            result = explain_circuit({
                "components":  components,
                "connections": connections,
            })

            unknown = [w for w in result["warnings"] if "Unknown component" in w]
            assert not unknown, (name, unknown)
