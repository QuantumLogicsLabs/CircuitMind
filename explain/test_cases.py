import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from explain_module import explain_circuit

TEST_CASES = [
    {
        "label": "Basic XNOR Circuit",
        "input": {
            "gates": [
                {"id": 0, "type": "XNOR",   "x": 460, "y": 180, "inputs": 2, "hasOutput": True,  "output": None, "inputValues": [], "label": None},
                {"id": 1, "type": "OUTPUT", "x": 760, "y": 140, "inputs": 1, "hasOutput": False, "output": None, "inputValues": [], "label": "Z"},
                {"id": 2, "type": "INPUT",  "x": 80,  "y": 100, "inputs": 0, "hasOutput": True,  "output": None, "inputValues": [False], "label": "A"},
                {"id": 3, "type": "INPUT",  "x": 80,  "y": 320, "inputs": 0, "hasOutput": True,  "output": None, "inputValues": [False], "label": "B"}
            ],
            "wires": [
                {"id": 0, "fromId": 0, "toId": 1, "toIndex": 0},
                {"id": 1, "fromId": 2, "toId": 0, "toIndex": 0},
                {"id": 2, "fromId": 3, "toId": 0, "toIndex": 1}
            ],
            "gateIdCounter": 4, "wireIdCounter": 3, "inputCounter": 2, "outputCounter": 1
        }
    },
    {
        "label": "AND Gate Circuit",
        "input": {
            "gates": [
                {"id": 0, "type": "INPUT",  "x": 80,  "y": 100, "inputs": 0, "hasOutput": True,  "output": None, "inputValues": [False], "label": "A"},
                {"id": 1, "type": "INPUT",  "x": 80,  "y": 220, "inputs": 0, "hasOutput": True,  "output": None, "inputValues": [False], "label": "B"},
                {"id": 2, "type": "AND",    "x": 300, "y": 160, "inputs": 2, "hasOutput": True,  "output": None, "inputValues": [], "label": None},
                {"id": 3, "type": "OUTPUT", "x": 560, "y": 160, "inputs": 1, "hasOutput": False, "output": None, "inputValues": [], "label": "Z"}
            ],
            "wires": [
                {"id": 0, "fromId": 0, "toId": 2, "toIndex": 0},
                {"id": 1, "fromId": 1, "toId": 2, "toIndex": 1},
                {"id": 2, "fromId": 2, "toId": 3, "toIndex": 0}
            ],
            "gateIdCounter": 4, "wireIdCounter": 3, "inputCounter": 2, "outputCounter": 1
        }
    },
    {
        "label": "Half Adder (XOR + AND)",
        "input": {
            "gates": [
                {"id": 0, "type": "INPUT",  "x": 80,  "y": 100, "inputs": 0, "hasOutput": True,  "output": None, "inputValues": [False], "label": "A"},
                {"id": 1, "type": "INPUT",  "x": 80,  "y": 260, "inputs": 0, "hasOutput": True,  "output": None, "inputValues": [False], "label": "B"},
                {"id": 2, "type": "XOR",    "x": 320, "y": 140, "inputs": 2, "hasOutput": True,  "output": None, "inputValues": [], "label": None},
                {"id": 3, "type": "AND",    "x": 320, "y": 280, "inputs": 2, "hasOutput": True,  "output": None, "inputValues": [], "label": None},
                {"id": 4, "type": "OUTPUT", "x": 560, "y": 140, "inputs": 1, "hasOutput": False, "output": None, "inputValues": [], "label": "SUM"},
                {"id": 5, "type": "OUTPUT", "x": 560, "y": 280, "inputs": 1, "hasOutput": False, "output": None, "inputValues": [], "label": "CARRY"}
            ],
            "wires": [
                {"id": 0, "fromId": 0, "toId": 2, "toIndex": 0},
                {"id": 1, "fromId": 1, "toId": 2, "toIndex": 1},
                {"id": 2, "fromId": 0, "toId": 3, "toIndex": 0},
                {"id": 3, "fromId": 1, "toId": 3, "toIndex": 1},
                {"id": 4, "fromId": 2, "toId": 4, "toIndex": 0},
                {"id": 5, "fromId": 3, "toId": 5, "toIndex": 0}
            ],
            "gateIdCounter": 6, "wireIdCounter": 6, "inputCounter": 2, "outputCounter": 2
        }
    },
    {
        "label": "No Input Gate (warning expected)",
        "input": {
            "gates": [
                {"id": 0, "type": "AND",    "x": 300, "y": 160, "inputs": 2, "hasOutput": True,  "output": None, "inputValues": [], "label": None},
                {"id": 1, "type": "OUTPUT", "x": 560, "y": 160, "inputs": 1, "hasOutput": False, "output": None, "inputValues": [], "label": "Z"}
            ],
            "wires": [
                {"id": 0, "fromId": 0, "toId": 1, "toIndex": 0}
            ],
            "gateIdCounter": 2, "wireIdCounter": 1, "inputCounter": 0, "outputCounter": 1
        }
    },
    {
        "label": "Disconnected Gate (warning expected)",
        "input": {
            "gates": [
                {"id": 0, "type": "INPUT",  "x": 80,  "y": 100, "inputs": 0, "hasOutput": True,  "output": None, "inputValues": [False], "label": "A"},
                {"id": 1, "type": "NOT",    "x": 300, "y": 100, "inputs": 1, "hasOutput": True,  "output": None, "inputValues": [], "label": None},
                {"id": 2, "type": "OUTPUT", "x": 560, "y": 100, "inputs": 1, "hasOutput": False, "output": None, "inputValues": [], "label": "Z"},
                {"id": 3, "type": "AND",    "x": 300, "y": 280, "inputs": 2, "hasOutput": True,  "output": None, "inputValues": [], "label": None}
            ],
            "wires": [
                {"id": 0, "fromId": 0, "toId": 1, "toIndex": 0},
                {"id": 1, "fromId": 1, "toId": 2, "toIndex": 0}
            ],
            "gateIdCounter": 4, "wireIdCounter": 2, "inputCounter": 1, "outputCounter": 1
        }
    },
]

results = []
for test in TEST_CASES:
    output = explain_circuit(test["input"])
    results.append({
        "label":  test["label"],
        "input":  test["input"],
        "output": output
    })

output_path = "test_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"Results saved to {output_path}")
for r in results:
    warnings = r["output"].get("warnings", [])
    print(f"  {r['label']:35s} | warnings: {len(warnings)}")
