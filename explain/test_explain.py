"""
CircuitMind AI — Explain Module TEST SCRIPT
===========================================
Author : Mustehsan Kazmi

PURPOSE: Test your explain_module.py RIGHT NOW without waiting for Shayan
         (CV Module) or Haseeb (Text-to-Circuit Generator).

         Uses hardcoded mock circuit JSON payloads that match the standard
         CircuitMind schema exactly.

HOW TO RUN:
    1. Set your API key first:
          export GROQ_API_KEY="gsk_xxxxxxxxxxxx"     (get free key at console.groq.com)
       OR
          export OPENAI_API_KEY="sk-xxxxxxxxxxxx"

    2. Run:
          python test_explain.py

    3. When Shayan/Haseeb's modules are ready, the hardcoded JSON below
       gets replaced with live data — zero changes needed to explain_module.py.
"""

import json
from explain_module import explain_circuit

# ─────────────────────────────────────────────────────────────────────────────
# MOCK CIRCUIT JSONs  (hardcoded — for testing only)
# Replace these with live output from Haseeb's module when it's ready.
# ─────────────────────────────────────────────────────────────────────────────

MOCK_LED_CIRCUIT = {
    "components": [
        {"id": "C1", "type": "BATTERY",   "value": "9V",    "label": "Power Supply"},
        {"id": "C2", "type": "RESISTOR",  "value": "220ohm","label": "Current Limiter"},
        {"id": "C3", "type": "LED",       "value": None,    "label": "Output LED"},
    ],
    "connections": [
        {"from": "C1", "to": "C2", "wire_id": "W1"},
        {"from": "C2", "to": "C3", "wire_id": "W2"},
        {"from": "C3", "to": "C1", "wire_id": "W3"},
    ],
    "metadata": {
        "circuit_name": "Basic LED Circuit",
        "source": "mock_test"
    }
}

MOCK_LOGIC_GATE_CIRCUIT = {
    "components": [
        {"id": "G1", "type": "AND",  "value": None, "label": "AND Gate 1"},
        {"id": "G2", "type": "NOT",  "value": None, "label": "Inverter"},
        {"id": "G3", "type": "OR",   "value": None, "label": "OR Gate"},
        {"id": "IN1","type": "INPUT","value": None, "label": "Input A"},
        {"id": "IN2","type": "INPUT","value": None, "label": "Input B"},
        {"id": "IN3","type": "INPUT","value": None, "label": "Input C"},
        {"id": "OUT","type": "OUTPUT","value":None, "label": "Final Output"},
    ],
    "connections": [
        {"from": "IN1", "to": "G1",  "wire_id": "W1"},
        {"from": "IN2", "to": "G1",  "wire_id": "W2"},
        {"from": "G1",  "to": "G2",  "wire_id": "W3"},
        {"from": "G2",  "to": "G3",  "wire_id": "W4"},
        {"from": "IN3", "to": "G3",  "wire_id": "W5"},
        {"from": "G3",  "to": "OUT", "wire_id": "W6"},
    ],
    "metadata": {
        "circuit_name": "AND-NOT-OR Logic Chain",
        "source": "mock_test"
    }
}

MOCK_VOLTAGE_DIVIDER = {
    "components": [
        {"id": "C1", "type": "BATTERY",  "value": "12V",   "label": "VCC"},
        {"id": "C2", "type": "RESISTOR", "value": "10kohm","label": "R1"},
        {"id": "C3", "type": "RESISTOR", "value": "10kohm","label": "R2"},
        {"id": "C4", "type": "GROUND",   "value": None,    "label": "GND"},
    ],
    "connections": [
        {"from": "C1", "to": "C2",  "wire_id": "W1"},
        {"from": "C2", "to": "C3",  "wire_id": "W2"},
        {"from": "C3", "to": "C4",  "wire_id": "W3"},
    ],
    "metadata": {
        "circuit_name": "Voltage Divider",
        "source": "mock_test"
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# TEST RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_test(name: str, circuit_json: dict, level: str):
    print("\n" + "═" * 65)
    print(f"  TEST: {name}")
    print(f"  LEVEL: {level.upper()}")
    print("═" * 65)

    result = explain_circuit(
        circuit_json    = circuit_json,
        level           = level,
        return_analysis = True,       # show intermediate analysis too
    )

    print("\n── [Agent 1 Analysis] " + "─" * 43)
    print(json.dumps(result.get("analysis", {}), indent=2))

    print("\n── [Agent 2 Explanation] " + "─" * 40)
    print(result["explanation"])


if __name__ == "__main__":
    print("\n🔬 CircuitMind — Explain Module Test Suite")
    print("   Author: Mustehsan Kazmi\n")

    # Test 1: Simple LED circuit — beginner level
    run_test(
        name="Basic LED Circuit",
        circuit_json=MOCK_LED_CIRCUIT,
        level="beginner"
    )

    # Test 2: Logic gate circuit — expert level
    run_test(
        name="AND-NOT-OR Logic Chain",
        circuit_json=MOCK_LOGIC_GATE_CIRCUIT,
        level="expert"
    )

    # Test 3: Voltage divider — intermediate level
    run_test(
        name="Voltage Divider",
        circuit_json=MOCK_VOLTAGE_DIVIDER,
        level="intermediate"
    )

    print("\n\n✅ All tests completed.")
