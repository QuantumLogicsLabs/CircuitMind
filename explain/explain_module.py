from typing import Any


GATE_INFO = {
    "AND":    {"role": "logic gate",   "description": "outputs true only when all inputs are true"},
    "OR":     {"role": "logic gate",   "description": "outputs true when at least one input is true"},
    "NOT":    {"role": "logic gate",   "description": "inverts the input signal"},
    "NAND":   {"role": "logic gate",   "description": "outputs false only when all inputs are true"},
    "NOR":    {"role": "logic gate",   "description": "outputs false when at least one input is true"},
    "XOR":    {"role": "logic gate",   "description": "outputs true when inputs are different"},
    "XNOR":   {"role": "logic gate",   "description": "outputs true when both inputs are the same"},
    "BUFFER": {"role": "logic gate",   "description": "passes the input signal through unchanged"},
    "INPUT":  {"role": "input",        "description": "provides an input signal to the circuit"},
    "OUTPUT": {"role": "output",       "description": "receives and displays the final output signal"},
    "MUX":    {"role": "multiplexer",  "description": "selects one of several input signals based on a selector"},
    "DEMUX":  {"role": "demultiplexer","description": "routes a single input to one of several outputs"},
    "DFLIP":  {"role": "flip-flop",    "description": "stores a single bit of data on a clock edge"},
    "TFLIP":  {"role": "flip-flop",    "description": "toggles its output on each clock pulse"},
    "CLOCK":  {"role": "clock",        "description": "generates a periodic signal to drive sequential logic"},
}

NEEDS_INPUT_LIMIT = {"OUTPUT"}
POWER_GATES       = {"INPUT", "CLOCK"}


def _normalize(name: str) -> str:
    return name.strip().upper()


def _article(word: str) -> str:
    return "an" if word and word[0].lower() in "aeiou" else "a"


def _build_flow_description(gates: list[dict], wires: list[dict]) -> str:
    id_to_gate = {g["id"]: g for g in gates}
    flow_sentences = []

    for wire in wires:
        from_gate = id_to_gate.get(wire["fromId"])
        to_gate   = id_to_gate.get(wire["toId"])
        if not from_gate or not to_gate:
            continue

        from_label = from_gate.get("label") or from_gate["type"]
        to_label   = to_gate.get("label")   or to_gate["type"]

        sentence = f"Signal flows from {from_label} into {to_label}."

        if to_gate["type"] == "OUTPUT":
            sentence += f" The result appears at output {to_label}."
        elif to_gate["type"] in {"AND", "NAND"}:
            sentence += f" This feeds into an AND condition."
        elif to_gate["type"] in {"OR", "NOR"}:
            sentence += f" This feeds into an OR condition."
        elif to_gate["type"] == "NOT":
            sentence += f" The signal will be inverted."
        elif to_gate["type"] in {"XOR", "XNOR"}:
            sentence += f" This feeds into an equality check."

        flow_sentences.append(sentence)

    return " ".join(flow_sentences)


def _check_warnings(gates: list[dict], wires: list[dict], unknown: list[str]) -> list[str]:
    warnings = []
    gate_types = [g["type"] for g in gates]

    if not any(t in POWER_GATES for t in gate_types):
        warnings.append("No INPUT or CLOCK gate detected. The circuit has no signal source.")

    if "OUTPUT" not in gate_types:
        warnings.append("No OUTPUT gate detected. The circuit has no observable result.")

    connected_ids = {w["toId"] for w in wires} | {w["fromId"] for w in wires}
    for gate in gates:
        if gate["id"] not in connected_ids:
            label = gate.get("label") or gate["type"]
            warnings.append(f"Gate '{label}' (id {gate['id']}) is not connected to anything.")

    for u in unknown:
        warnings.append(f"Gate type '{u}' is not in the knowledge base. Description may be incomplete.")

    return warnings


def explain_circuit(circuit_json: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(circuit_json, dict):
        return {**circuit_json, "explanation": "", "component_details": [], "flow_description": "", "warnings": ["Input must be a JSON object."]}

    gates = circuit_json.get("gates", [])
    wires = circuit_json.get("wires", [])

    if not gates:
        return {**circuit_json, "explanation": "", "component_details": [], "flow_description": "", "warnings": ["No gates found in circuit JSON."]}

    component_details = []
    unknown_gates     = []

    for gate in gates:
        gate_type = _normalize(gate.get("type", ""))
        label     = gate.get("label") or gate_type

        if gate_type in GATE_INFO:
            info = GATE_INFO[gate_type]
            component_details.append({"id": gate["id"], "label": label, "type": gate_type, "role": info["role"], "description": info["description"]})
        else:
            unknown_gates.append(gate_type)
            component_details.append({"id": gate["id"], "label": label, "type": gate_type, "role": "unknown", "description": f"a {gate_type} gate (no description available)"})

    inputs  = [g for g in gates if g["type"] == "INPUT"]
    outputs = [g for g in gates if g["type"] == "OUTPUT"]
    logic   = [g for g in gates if g["type"] not in {"INPUT", "OUTPUT"}]

    input_labels  = [g.get("label") or "INPUT" for g in inputs]
    output_labels = [g.get("label") or "OUTPUT" for g in outputs]
    logic_types   = list({g["type"] for g in logic})

    parts = []
    if input_labels:
        parts.append(f"inputs {', '.join(input_labels)}")
    if logic_types:
        gate_parts = [f"{_article(t.lower())} {t} gate" for t in logic_types]
        parts.append(", ".join(gate_parts))
    if output_labels:
        parts.append(f"output {', '.join(output_labels)}")

    if parts:
        explanation = "This circuit uses " + ", ".join(parts) + "."
    else:
        explanation = "This circuit has no identifiable components."

    flow_description = _build_flow_description(gates, wires)
    if flow_description:
        explanation += " " + flow_description

    return {
        **circuit_json,
        "explanation":       explanation,
        "component_details": component_details,
        "flow_description":  flow_description,
        "warnings":          _check_warnings(gates, wires, unknown_gates),
    }


def explain_circuits_batch(circuits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [explain_circuit(c) for c in circuits]


def pretty_print(result: dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print(f"\n📝 EXPLANATION:\n  {result['explanation']}")

    if result.get("flow_description"):
        print(f"\n⚡ FLOW:\n  {result['flow_description']}")

    if result.get("component_details"):
        print("\n🔩 GATES:")
        for c in result["component_details"]:
            print(f"  • [{c['id']}] {c['label']:15s} | {c['role']:20s} | {c['description']}")

    if result.get("warnings"):
        print("\n⚠️  WARNINGS:")
        for w in result["warnings"]:
            print(f"  ! {w}")


def _run_tests() -> None:
    TEST_CASES = [
        {"label": "Basic XNOR Circuit",
         "input": {
             "gates": [
                 {"id": 0, "type": "XNOR", "x": 460, "y": 180, "inputs": 2, "hasOutput": True, "output": None, "inputValues": [], "label": None},
                 {"id": 1, "type": "OUTPUT", "x": 760, "y": 140, "inputs": 1, "hasOutput": False, "output": None, "inputValues": [], "label": "Z"},
                 {"id": 2, "type": "INPUT", "x": 80, "y": 100, "inputs": 0, "hasOutput": True, "output": None, "inputValues": [False], "label": "A"},
                 {"id": 3, "type": "INPUT", "x": 80, "y": 320, "inputs": 0, "hasOutput": True, "output": None, "inputValues": [False], "label": "B"}
             ],
             "wires": [
                 {"id": 0, "fromId": 0, "toId": 1, "toIndex": 0},
                 {"id": 1, "fromId": 2, "toId": 0, "toIndex": 0},
                 {"id": 2, "fromId": 3, "toId": 0, "toIndex": 1}
             ],
             "gateIdCounter": 4, "wireIdCounter": 3, "inputCounter": 2, "outputCounter": 1
         }},

        {"label": "AND Gate Circuit",
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
         }},

        {"label": "Half Adder (XOR + AND)",
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
         }},

        {"label": "No Input Gate (warning expected)",
         "input": {
             "gates": [
                 {"id": 0, "type": "AND",    "x": 300, "y": 160, "inputs": 2, "hasOutput": True,  "output": None, "inputValues": [], "label": None},
                 {"id": 1, "type": "OUTPUT", "x": 560, "y": 160, "inputs": 1, "hasOutput": False, "output": None, "inputValues": [], "label": "Z"}
             ],
             "wires": [
                 {"id": 0, "fromId": 0, "toId": 1, "toIndex": 0}
             ],
             "gateIdCounter": 2, "wireIdCounter": 1, "inputCounter": 0, "outputCounter": 1
         }},

        {"label": "Disconnected Gate (warning expected)",
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
         }},
    ]

    print("\n" + "━" * 60)
    print("  CircuitMind — Explain Module — Test Suite")
    print("━" * 60)

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n[Test {i}] {test['label']}")
        pretty_print(explain_circuit(test["input"]))


if __name__ == "__main__":
    _run_tests()
