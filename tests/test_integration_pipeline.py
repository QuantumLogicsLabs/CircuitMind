"""
CircuitMind - cross-module pipeline tests
tests/test_integration_pipeline.py

Each module has unit coverage; these tests exercise the hand-off between
generate -> explain/diagnose/export/hint so schema drift is caught.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hint.hint_module as hint_module
from diagnose.diagnose_module import diagnose_circuit
from explain.explain_module import explain_circuit
from export.export_module import export_module
from generate.generate import generate_with_rules


def test_led_circuit_survives_explain_and_diagnose():
    circuit = generate_with_rules("make me a led circuit")

    explained = explain_circuit(circuit)
    assert explained["explanation"]
    assert {d["name"] for d in explained["component_details"]} == set(circuit["components"])

    diagnosed = diagnose_circuit(circuit)
    assert isinstance(diagnosed["passed"], bool)
    assert isinstance(diagnosed["issues"], list)


def test_generated_half_adder_exports_gate_json():
    circuit = generate_with_rules("make a half adder circuit")

    exported = export_module(json.dumps(circuit), export_format="gate_json")
    assert exported["status"] == "success"

    gates = exported["gate_json"]["gates"]
    assert len(gates) == len(circuit["components"])
    ids = {g["id"] for g in gates}
    for wire in exported["gate_json"]["wires"]:
        assert wire["fromId"] in ids
        assert wire["toId"] in ids


def test_generated_half_adder_exports_spice():
    circuit = generate_with_rules("make a half adder circuit")

    exported = export_module(json.dumps(circuit), export_format="spice")
    assert exported["status"] == "success"
    assert exported["spice_netlist"].splitlines()[-1] == ".end"


def test_hint_accepts_a_generated_problem(monkeypatch):
    monkeypatch.setattr(
        hint_module, "_hint_with_llm",
        lambda payload: (_ for _ in ()).throw(RuntimeError("offline")),
    )

    result = hint_module.generate_hint({
        "problem_title": "Half Adder",
        "inputs": ["A", "B"],
        "outputs": ["S", "C"],
        "gates": [],
        "wires": [],
    })

    assert result["source"] == "rule-based"
    assert result["hint"]


def test_identify_request_bypasses_the_generated_circuit_modules():
    result = hint_module.generate_hint({
        "request_type": "identify",
        "problem_title": "Half Adder",
        "inputs": ["A", "B"],
        "outputs": ["S", "C"],
        "gates": [],
        "wires": [],
    })
    assert result["circuit_name"] == "Half Adder"
    assert result["source"] == "rule-based"
