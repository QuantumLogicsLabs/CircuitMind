"""
CircuitMind - Gate JSON input arity tests
tests/test_export_gate_arity.py

_classify_component() gave every recognised gate two inputs except NOT, so a
BUFFER — a one-input pass-through gate named in the builder itself — was
exported with two input pins and rendered with a phantom second input.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import _classify_component, generate_gate_json


class TestGateInputArity:

    def test_buffer_has_one_input(self):
        gate_type, inputs, has_output = _classify_component("buffer", 1, 5)

        assert gate_type == "BUFFER"
        assert inputs == 1
        assert has_output is True

    def test_not_still_has_one_input(self):
        gate_type, inputs, _ = _classify_component("not", 1, 5)

        assert gate_type == "NOT"
        assert inputs == 1

    def test_two_input_gates_are_unchanged(self):
        for name, expected in [
            ("and1", "AND"),
            ("or1", "OR"),
            ("nand1", "NAND"),
            ("nor1", "NOR"),
            ("xor1", "XOR"),
            ("xnor1", "XNOR"),
        ]:
            gate_type, inputs, _ = _classify_component(name, 1, 5)
            assert gate_type == expected
            assert inputs == 2

    def test_input_and_output_ports_are_unchanged(self):
        assert _classify_component("input_a", 0, 5) == ("INPUT", 0, True)
        assert _classify_component("output", 4, 5) == ("OUTPUT", 1, False)


class TestBufferInExportedGateJson:

    def test_buffer_gate_exported_with_single_input(self):
        data = generate_gate_json(
            "Buffer",
            ["input_a", "buffer", "output"],
            ["input_a -> buffer", "buffer -> output"],
        )

        buffer_gate = next(g for g in data["gates"] if g["type"] == "BUFFER")
        assert buffer_gate["inputs"] == 1
        assert data["wireIdCounter"] == 2
