# Explain Module — CircuitMind

## Overview

The Explain Module is part of the CircuitMind pipeline. It takes a circuit JSON (gates and wires) as input and returns the same JSON with an explanation, component details, flow description, and warnings added to it.

## How It Fits in the Pipeline

```
User Input → Generate Module → Circuit JSON → Explain Module → Explained Circuit JSON
```

## Files

| File | Description |
|------|-------------|
| `explain_module.py` | Core module — all logic lives here |
| `test_cases.py` | Runs 5 test cases and saves results to JSON |
| `test_results.json` | Output from running test_cases.py |

## Input Format

The module accepts the standard CircuitMind circuit JSON format:

```json
{
  "gates": [
    { "id": 0, "type": "XNOR",   "x": 460, "y": 180, "inputs": 2, "hasOutput": true,  "output": null, "inputValues": [], "label": null },
    { "id": 1, "type": "OUTPUT", "x": 760, "y": 140, "inputs": 1, "hasOutput": false, "output": null, "inputValues": [], "label": "Z" },
    { "id": 2, "type": "INPUT",  "x": 80,  "y": 100, "inputs": 0, "hasOutput": true,  "output": null, "inputValues": [false], "label": "A" },
    { "id": 3, "type": "INPUT",  "x": 80,  "y": 320, "inputs": 0, "hasOutput": true,  "output": null, "inputValues": [false], "label": "B" }
  ],
  "wires": [
    { "id": 0, "fromId": 0, "toId": 1, "toIndex": 0 },
    { "id": 1, "fromId": 2, "toId": 0, "toIndex": 0 },
    { "id": 2, "fromId": 3, "toId": 0, "toIndex": 1 }
  ],
  "gateIdCounter": 4,
  "wireIdCounter": 3,
  "inputCounter": 2,
  "outputCounter": 1
}
```

## Output Format

The module returns the original circuit JSON with these fields added:

```json
{
  "gates": [ ... ],
  "wires": [ ... ],
  "explanation": "This circuit uses inputs A, B, an XNOR gate, and output Z. Signal flows from A into XNOR...",
  "component_details": [
    { "id": 0, "label": "XNOR",   "type": "XNOR",   "role": "logic gate", "description": "outputs true when both inputs are the same" },
    { "id": 1, "label": "Z",      "type": "OUTPUT",  "role": "output",     "description": "receives and displays the final output signal" },
    { "id": 2, "label": "A",      "type": "INPUT",   "role": "input",      "description": "provides an input signal to the circuit" },
    { "id": 3, "label": "B",      "type": "INPUT",   "role": "input",      "description": "provides an input signal to the circuit" }
  ],
  "flow_description": "Signal flows from A into XNOR. Signal flows from B into XNOR. Signal flows from XNOR into Z. The result appears at output Z.",
  "warnings": []
}
```

## Usage

```python
from explain_module import explain_circuit

circuit = {
    "gates": [...],
    "wires": [...]
}

result = explain_circuit(circuit)
print(result["explanation"])
```

For multiple circuits at once:

```python
from explain_module import explain_circuits_batch

results = explain_circuits_batch([circuit1, circuit2])
```

## Supported Gate Types

| Gate | Role | Description |
|------|------|-------------|
| INPUT | input | Provides an input signal to the circuit |
| OUTPUT | output | Receives and displays the final output signal |
| AND | logic gate | Outputs true only when all inputs are true |
| OR | logic gate | Outputs true when at least one input is true |
| NOT | logic gate | Inverts the input signal |
| NAND | logic gate | Outputs false only when all inputs are true |
| NOR | logic gate | Outputs false when at least one input is true |
| XOR | logic gate | Outputs true when inputs are different |
| XNOR | logic gate | Outputs true when both inputs are the same |
| BUFFER | logic gate | Passes the input signal through unchanged |
| MUX | multiplexer | Selects one of several inputs based on a selector |
| DEMUX | demultiplexer | Routes a single input to one of several outputs |
| DFLIP | flip-flop | Stores a single bit of data on a clock edge |
| TFLIP | flip-flop | Toggles its output on each clock pulse |
| CLOCK | clock | Generates a periodic signal to drive sequential logic |

Unknown gate types are handled gracefully — they are included with a warning instead of crashing.

## Warnings

The module automatically checks for common circuit issues:

| Warning | Condition |
|---------|-----------|
| No input source | No INPUT or CLOCK gate in the circuit |
| No output | No OUTPUT gate in the circuit |
| Disconnected gate | A gate has no wires connected to it |
| Unknown gate type | Gate type not found in the knowledge base |

## Running the Tests

```bash
python test_cases.py
```

This runs 5 test cases and saves the results to `test_results.json` in the same folder.

## Notes

- Gate type names are case-insensitive — `"xnor"`, `"XNOR"` both work
- The original circuit JSON is preserved in full in the output — only new fields are added
- The module has no external dependencies beyond the Python standard library
