"""
CircuitMind - Gate JSON connection parsing tests
tests/test_export_arrows.py

generate_gate_json() split connections on "->" only. Circuits pasted back with
the unicode arrow used by the export previews ("input_a → and") produced a
single node per connection and therefore zero wires.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from export.export_module import export_module, generate_gate_json

COMPONENTS = ["input_a", "input_b", "and", "output"]


def _gate_json(connections):
    return generate_gate_json("Arrow Test", COMPONENTS, connections)


class TestArrowStyles:

    def test_ascii_arrow_still_creates_wires(self):
        data = _gate_json(["input_a -> and", "input_b -> and", "and -> output"])

        assert len(data["wires"]) == 3

    def test_unicode_arrow_creates_wires(self):
        data = _gate_json(["input_a → and", "input_b → and", "and → output"])

        assert len(data["wires"]) == 3
        assert data["wireIdCounter"] == 3

    def test_em_dash_and_double_dash_are_accepted(self):
        data = _gate_json(["input_a — and", "input_b -- and", "and — output"])

        assert len(data["wires"]) == 3

    def test_unknown_nodes_are_ignored(self):
        data = _gate_json(["input_a → and", "missing → output"])

        assert len(data["wires"]) == 1


class TestExportEntryPoint:

    def test_gate_json_export_with_unicode_arrows(self):
        payload = json.dumps({
            "circuit_name": "Half Adder",
            "components":   COMPONENTS,
            "connections":  ["input_a → and", "input_b → and", "and → output"],
        })

        result = export_module(payload, export_format="gate_json")

        assert result["status"] == "success"
        assert len(result["gate_json"]["wires"]) == 3
