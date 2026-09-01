"""
CircuitMind - Unified Test Suite
tests/test_all_modules.py

Run with: pytest tests/
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate.generate import generate_circuit
from explain.explain_module import explain_circuit
from diagnose.diagnose_module import diagnose_circuit
from export.export_module import export_module
from hint.hint_module import generate_hint, _hint_with_rules


# ── Fixtures ───────────────────────────────────────────────────────────────────

LED_CIRCUIT = {
    "circuit_name": "LED Circuit",
    "components":   ["battery", "resistor", "led"],
    "connections":  ["battery -> resistor -> led"],
}

BAD_CIRCUIT = {
    "circuit_name": "Bad Circuit",
    "components":   ["battery", "led"],
    "connections":  ["battery -> led"],
}

SHORT_CIRCUIT = {
    "circuit_name": "Short",
    "components":   ["battery", "ground"],
    "connections":  ["battery -> ground"],
}


# ── Generate ───────────────────────────────────────────────────────────────────

class TestGenerate:
    def test_led_prompt(self):
        result = generate_circuit("make me a LED circuit")
        assert "components" in result
        assert "led" in result["components"]

    def test_motor_prompt(self):
        result = generate_circuit("I want a motor circuit")
        assert "motor" in " ".join(result.get("components", [])).lower() or result.get("source") == "rule-based"

    def test_empty_input(self):
        result = generate_circuit("")
        assert "error" in result
        assert result["error_code"] == "INVALID_INPUT"

    def test_too_short_input(self):
        result = generate_circuit("ab")
        assert "error" in result

    def test_too_long_input(self):
        result = generate_circuit("a" * 1001)
        assert "error" in result

    def test_always_returns_dict(self):
        for prompt in ["led", "motor", "unknown xyz circuit", "", "ab"]:
            result = generate_circuit(prompt)
            assert isinstance(result, dict)

    def test_half_adder_is_not_a_subtractor(self):
        from generate.generate import generate_with_rules
        result = generate_with_rules("make a half adder circuit")
        assert result["circuit_name"] == "Half Adder Circuit"
        assert "sum_output" in result["components"]
        assert "diff_output" not in result["components"]

    def test_half_subtractor_still_matches(self):
        from generate.generate import generate_with_rules
        result = generate_with_rules("half subtractor")
        assert result["circuit_name"] == "Half Subtractor Circuit"

    def test_demultiplexer_not_shadowed_by_multiplexer(self):
        from generate.generate import generate_with_rules
        for prompt in ["1 to 2 demultiplexer", "demux", "demultiplexer"]:
            result = generate_with_rules(prompt)
            assert result["circuit_name"] == "1-to-2 Demultiplexer"

    def test_rc_keyword_does_not_collide_with_circuit_or_search(self):
        from generate.generate import generate_with_rules
        for prompt in ["can you search for a circuit", "mystery circuit", "quantum circuit", "search"]:
            result = generate_with_rules(prompt)
            assert result["circuit_name"] == "Unknown"

    def test_led_keyword_does_not_collide_with_suffixes(self):
        from generate.generate import generate_with_rules
        assert generate_with_rules("voice controlled switch")["circuit_name"] == "Unknown"
        assert generate_with_rules("microcontroller enabled motor")["circuit_name"] == "Motor Circuit"
        assert generate_with_rules("a well scheduled timer")["circuit_name"] == "555 Timer Circuit"

    def test_plural_and_inflection_support(self):
        from generate.generate import generate_with_rules
        assert generate_with_rules("make a circuit with 3 leds")["circuit_name"] == "LED Circuit"
        assert generate_with_rules("two motors")["circuit_name"] == "Motor Circuit"
        assert generate_with_rules("cooling fans")["circuit_name"] == "Fan Circuit"
        assert generate_with_rules("two buzzers")["circuit_name"] == "Buzzer Circuit"
        assert generate_with_rules("analog filters")["circuit_name"] == "RC Filter Circuit"
        assert generate_with_rules("demultiplexers")["circuit_name"] == "1-to-2 Demultiplexer"
        assert generate_with_rules("multiplexers")["circuit_name"] == "2-to-1 Multiplexer"

    def test_555_timer_ic_variants(self):
        from generate.generate import generate_with_rules
        assert generate_with_rules("555 timer")["circuit_name"] == "555 Timer Circuit"
        assert generate_with_rules("ne555 circuit")["circuit_name"] == "555 Timer Circuit"
        assert generate_with_rules("lm555 timer")["circuit_name"] == "555 Timer Circuit"
        assert generate_with_rules("555-timer")["circuit_name"] == "555 Timer Circuit"
        assert generate_with_rules("555_timer")["circuit_name"] == "555 Timer Circuit"


# ── Explain ────────────────────────────────────────────────────────────────────

class TestExplain:
    def test_led_circuit_explanation(self):
        result = explain_circuit(LED_CIRCUIT)
        assert "explanation" in result
        assert "battery" in result["explanation"].lower()

    def test_component_details_present(self):
        result = explain_circuit(LED_CIRCUIT)
        assert "component_details" in result
        names = [d["name"] for d in result["component_details"]]
        assert "battery" in names
        assert "led" in names

    def test_warning_for_missing_power(self):
        no_power = {"components": ["resistor", "led"], "connections": ["resistor -> led"]}
        result = explain_circuit(no_power)
        assert len(result.get("warnings", [])) > 0

    def test_no_warnings_for_valid_circuit(self):
        result = explain_circuit(LED_CIRCUIT)
        assert result.get("warnings", []) == []

    def test_empty_circuit(self):
        result = explain_circuit({"components": [], "connections": []})
        assert "explanation" in result


# ── Diagnose ───────────────────────────────────────────────────────────────────

class TestDiagnose:
    def test_valid_circuit_passes(self):
        result = diagnose_circuit(LED_CIRCUIT)
        assert result["passed"] is True
        assert len(result["issues"]) == 1
        assert "Info:" in result["issues"][0]

    def test_missing_resistor_flagged(self):
        result = diagnose_circuit(BAD_CIRCUIT)
        assert result["passed"] is False
        assert any("current-limiting" in i for i in result["issues"])

    def test_short_circuit_detected(self):
        result = diagnose_circuit(SHORT_CIRCUIT)
        assert result["passed"] is False
        assert any("short circuit" in i.lower() for i in result["issues"])

    def test_no_power_source_flagged(self):
        no_power = {"components": ["resistor", "led"], "connections": ["resistor -> led"]}
        result = diagnose_circuit(no_power)
        assert any("power source" in i.lower() for i in result["issues"])

    def test_result_always_has_passed_and_issues(self):
        result = diagnose_circuit(LED_CIRCUIT)
        assert "passed" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)
    
    def test_switch_short_detected(self):
        circuit = {
          "components": ["battery", "switch", "ground"],
          "connections": ["battery -> switch -> ground"]
        }

        result = diagnose_circuit(circuit)

        assert any("short circuit" in i.lower() for i in result["issues"])

    def test_capacitor_without_polarity_warning(self):
        circuit = {
          "components": ["battery", "capacitor"],
          "connections": [
             "battery -> capacitor",
             "capacitor -> ground",
            ],
        }

        result = diagnose_circuit(circuit)

        assert any("polarity" in i.lower() for i in result["issues"])


    def test_led_polarity_does_not_count_for_capacitor(self):
        circuit = {
          "components": ["battery", "capacitor", "led"],
          "connections": [
             "battery -> led+",
             "led -> capacitor",
             "capacitor -> ground",
           ],
        }

        result = diagnose_circuit(circuit)

        assert any("polarity" in i.lower() for i in result["issues"])


# ── Export ─────────────────────────────────────────────────────────────────────

class TestExport:
    def _json(self, circuit: dict) -> str:
        return json.dumps(circuit)

    def test_spice_export(self):
        result = export_module(self._json(LED_CIRCUIT), export_format="spice")
        assert result["status"] == "success"
        assert "spice_netlist" in result
        assert ".end" in result["spice_netlist"]

    def test_spice_subcircuit_export(self):
        solar_circuit = {
            "circuit_name": "Solar Circuit",
            "components":   ["solar_cell", "diode", "charge_controller", "battery"],
            "connections":  ["solar_cell -> diode -> charge_controller -> battery"],
        }
        result = export_module(self._json(solar_circuit), export_format="spice")
        assert result["status"] == "success"
        netlist = result["spice_netlist"]
        assert "X1 2 3 CC" in netlist
        assert ".subckt CC 2 3" in netlist
        assert "Rdummy 2 3 10Meg" in netlist
        assert ".ends CC" in netlist
        assert ".end" in netlist

    def test_gate_json_export(self):
        result = export_module(self._json(LED_CIRCUIT), export_format="gate_json")
        assert result["status"] == "success"
        assert "gate_json" in result
        assert "gates" in result["gate_json"]

    def test_half_adder_gate_json_is_spread_out(self):
        circuit = {
            "circuit_name": "Half Adder Circuit",
            "components": ["input_a", "input_b", "xor", "and", "sum_output", "carry_output"],
            "connections": [
                "input_a -> xor -> sum_output",
                "input_b -> xor",
                "input_a -> and -> carry_output",
                "input_b -> and",
            ],
        }
        result = export_module(self._json(circuit), export_format="gate_json")
        gates = result["gate_json"]["gates"]
        ys = {g["y"] for g in gates}
        input_xs = {g["x"] for g in gates if g["type"] == "INPUT"}
        output_xs = {g["x"] for g in gates if g["type"] == "OUTPUT"}
        assert len(ys) > 1
        assert len(input_xs) == 1
        assert len(output_xs) == 1
        assert max(output_xs) > max(input_xs)
        labels = {g["label"] for g in gates}
        assert "SUM" in labels
        assert "CARRY" in labels

    def test_empty_input(self):
        result = export_module("")
        assert result["status"] == "error"

    def test_invalid_json(self):
        result = export_module("not json at all")
        assert result["status"] == "error"

    def test_missing_fields(self):
        result = export_module('{"circuit_name": "X"}', export_format="spice")
        assert result["status"] == "error"

    def test_invalid_format(self):
        result = export_module(self._json(LED_CIRCUIT), export_format="pdf")
        assert result["status"] == "error"

    def test_no_circuit_name_uses_default(self):
        no_name = {"components": ["battery", "resistor"], "connections": ["battery -> resistor"]}
        result = export_module(json.dumps(no_name), export_format="spice")
        assert result["status"] == "success"
        assert result["circuit_name"] == "CircuitMind_Generated_Circuit"


# ── Hint ───────────────────────────────────────────────────────────────────────
# generate_hint() prefers the LLM when GROQ_API_KEY is configured (as it is
# here), so content-specific assertions target the deterministic rule-based
# fallback (_hint_with_rules) directly rather than depending on environment
# state or burning real API calls.

class TestHint:
    def test_generate_hint_always_returns_hint_and_source(self):
        result = generate_hint({
            "problem_title": "Half Adder",
            "inputs": ["A", "B"],
            "outputs": ["S", "C"],
            "gates": [],
            "wires": [],
        })
        assert isinstance(result.get("hint"), str) and result["hint"]
        assert result["source"] in ("llm", "rule-based")

    def test_generate_hint_with_last_result_does_not_crash(self):
        result = generate_hint({
            "problem_title": "Half Adder",
            "inputs": ["A", "B"],
            "outputs": ["S", "C"],
            "gates": [{"id": 1, "type": "INPUT", "label": "A"}],
            "wires": [],
            "last_result": {"passed": False, "failing_rows": [{"row": 1}]},
        })
        assert isinstance(result["hint"], str)

    def test_rules_empty_canvas_prompts_to_start(self):
        hint_text = _hint_with_rules({
            "inputs": ["A", "B"],
            "outputs": ["S", "C"],
            "gates": [],
            "wires": [],
        })
        assert "INPUT" in hint_text

    def test_rules_missing_io_count_flagged(self):
        gates = [{"id": 1, "type": "INPUT", "label": "A"}]
        hint_text = _hint_with_rules({
            "inputs": ["A", "B"],
            "outputs": ["S", "C"],
            "gates": gates,
            "wires": [],
        })
        assert "1 INPUT" in hint_text

    def test_rules_floating_gate_flagged(self):
        gates = [
            {"id": 1, "type": "INPUT", "label": "A"},
            {"id": 2, "type": "INPUT", "label": "B"},
            {"id": 3, "type": "XOR", "label": "XOR1"},
            {"id": 4, "type": "OUTPUT", "label": "S"},
            {"id": 5, "type": "OUTPUT", "label": "C"},
        ]
        wires = [
            {"id": 1, "fromId": 1, "toId": 3, "toIndex": 0},
            {"id": 2, "fromId": 2, "toId": 3, "toIndex": 1},
            {"id": 3, "fromId": 3, "toId": 4, "toIndex": 0},
            # gate 5 (OUTPUT "C") is never wired
        ]
        hint_text = _hint_with_rules({
            "inputs": ["A", "B"],
            "outputs": ["S", "C"],
            "gates": gates,
            "wires": wires,
        })
        assert "C" in hint_text

    def test_identify_half_adder_from_problem(self):
        result = generate_hint({
            "request_type": "identify",
            "problem_title": "Half Adder",
            "inputs": ["A", "B"],
            "outputs": ["S", "C"],
            "gates": [],
            "wires": [],
        })

        assert result["circuit_name"] == "Half Adder"
        assert result["hint"] == "You have created a Half Adder circuit."
        assert result["source"] == "rule-based"

    def test_identify_half_adder_from_gate_structure(self):
        result = generate_hint({
            "request_type": "identify",
            "problem_title": "",
            "inputs": ["A", "B"],
            "outputs": ["S", "C"],
            "gates": [
                {"id": 1, "type": "INPUT", "label": "A"},
                {"id": 2, "type": "INPUT", "label": "B"},
                {"id": 3, "type": "XOR", "label": "XOR1"},
                {"id": 4, "type": "AND", "label": "AND1"},
                {"id": 5, "type": "OUTPUT", "label": "S"},
                {"id": 6, "type": "OUTPUT", "label": "C"},
            ],
            "wires": [],
        })

        assert result["circuit_name"] == "Half Adder"


# ── Integration ────────────────────────────────────────────────────────────────

class TestIntegration:
    def test_generate_then_diagnose(self):
        circuit = generate_circuit("make me a LED circuit")
        assert "components" in circuit
        result = diagnose_circuit(circuit)
        assert "passed" in result

    def test_generate_then_explain(self):
        circuit = generate_circuit("make me a LED circuit")
        result = explain_circuit(circuit)
        assert "explanation" in result

    def test_generate_then_export(self):
        circuit = generate_circuit("make me a LED circuit")
        result = export_module(json.dumps(circuit), export_format="spice")
        assert result["status"] == "success"
