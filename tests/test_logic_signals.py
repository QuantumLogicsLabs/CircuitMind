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

from diagnose.diagnose_module import diagnose_circuit
from explain.explain_module import explain_circuit
from generate.generate import _RULES
from utils.component_resolver import (
    COMPONENT_DB,
    _fuzzy_match,
    _normalize,
    is_logic_circuit,
)

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

    def test_logic_circuits_do_not_warn_about_power(self):
        for keywords, name, components, connections, description in _RULES:
            if not is_logic_circuit(components):
                continue

            result = explain_circuit({
                "components":  components,
                "connections": connections,
            })

            assert result["warnings"] == [], name

    def test_analog_circuit_without_power_still_warns(self):
        result = explain_circuit({
            "components":  ["resistor", "led"],
            "connections": ["resistor -> led"],
        })

        assert any("No power source" in w for w in result["warnings"])


class TestLogicCircuitDetection:

    def test_gates_and_signals_are_a_logic_circuit(self):
        assert is_logic_circuit(["input_a", "xor1", "and2", "sum_output"])

    def test_analog_circuit_is_not_a_logic_circuit(self):
        assert not is_logic_circuit(["battery", "resistor", "led"])

    def test_mixed_circuit_is_not_a_logic_circuit(self):
        assert not is_logic_circuit(["xor", "resistor"])

    def test_empty_circuit_is_not_a_logic_circuit(self):
        assert not is_logic_circuit([])


class TestDiagnoseGeneratedCircuits:

    def test_logic_circuits_need_no_power_or_ground(self):
        checked = 0
        for keywords, name, components, connections, description in _RULES:
            if not is_logic_circuit(components):
                continue
            checked += 1

            result = diagnose_circuit({
                "circuit_name": name,
                "components":   components,
                "connections":  connections,
            })

            codes = [issue["code"] for issue in result["issues"]]
            assert "NO_POWER_SOURCE" not in codes, name
            assert "NO_GROUND" not in codes, name
            assert result["passed"] is True, (name, codes)

        assert checked > 0

    def test_analog_circuit_without_power_still_fails(self):
        result = diagnose_circuit({
            "components":  ["resistor", "led"],
            "connections": ["resistor -> led"],
        })

        codes = [issue["code"] for issue in result["issues"]]
        assert "NO_POWER_SOURCE" in codes

