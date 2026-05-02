# Explain Module — CircuitMind

## Overview

The Explain Module is part of the CircuitMind pipeline. It takes a circuit JSON as input and returns a human-readable explanation of how the circuit works, along with component details, current flow description, and any warnings.

## How It Fits in the Pipeline

```
User Input → Generate Module → Circuit JSON → Explain Module → Explanation JSON
```

## Files

| File | Description |
|------|-------------|
| `explain_module.py` | Core module — all logic lives here |
| `test_cases.py` | Runs 5 test cases and saves results to JSON |
| `test_results.json` | Output from running test_cases.py |

## Input Format

```json
{
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"]
}
```

## Output Format

```json
{
  "explanation": "This circuit uses a battery (power source) that provides electrical energy...",
  "component_details": [
    { "name": "battery", "role": "power source", "description": "provides electrical energy to the circuit" },
    { "name": "resistor", "role": "current limiter", "description": "limits and controls the flow of current" },
    { "name": "led", "role": "light emitter", "description": "emits light when current flows through it" }
  ],
  "flow_description": "Current flows from the battery → resistor → led. This causes the LED to emit light.",
  "warnings": []
}
```

## Usage

```python
from explain_module import explain_circuit

circuit = {
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"]
}

result = explain_circuit(circuit)
print(result["explanation"])
```

For multiple circuits at once:

```python
from explain_module import explain_circuits_batch

results = explain_circuits_batch([circuit1, circuit2])
```

## Supported Components

The module has a built-in knowledge base covering 30+ components across the following categories:

- **Power Sources** — battery, power_supply, solar_cell
- **Passive Components** — resistor, capacitor, inductor, potentiometer
- **Diodes** — diode, led, zener_diode
- **Transistors** — transistor, npn_transistor, pnp_transistor, mosfet
- **ICs** — op_amp, 555_timer, arduino, microcontroller
- **Output Devices** — buzzer, motor, speaker, relay, display, lcd
- **Sensors & Inputs** — ldr, thermistor, photodiode, button, switch, sensor
- **Other** — ground, fuse, transformer

Unknown components are handled gracefully — the module includes them with a warning instead of crashing.

## Warnings

The module automatically checks for common circuit issues:

| Warning | Condition |
|---------|-----------|
| No power source | Circuit has no battery, power_supply, or solar_cell |
| Missing current limiter | LED or diode present without a resistor or equivalent |
| Unknown component | Component not found in the knowledge base |

## Running the Tests

```bash
python test_cases.py
```

This runs 5 test cases and saves the results to `test_results.json` in the same folder.

## Notes

- Component names are case-insensitive — `"LED"`, `"Led"`, and `"led"` all work
- Both `->` and `--` are supported as connection separators
- The module has no external dependencies beyond the Python standard library
