"""Logic Unit of the ALU: AND, OR, XOR, NOT-A selected by S1S0."""
from datetime import datetime, timezone
OPS = {0b00: "AND", 0b01: "OR", 0b10: "XOR", 0b11: "NOT_A"}


def logic_unit(a: int, b: int, op: int, width: int = 4) -> int:
    """Reference (behavioral) model. Used to verify the gate-level design."""
    if op not in OPS:
        raise ValueError("op must be 0-3")
    mask = (1 << width) - 1
    a, b = a & mask, b & mask
    result = {0: a & b, 1: a | b, 2: a ^ b, 3: ~a}[op]
    return result & mask


def build_logic_unit_graph(width: int = 4) -> dict:
    """Build the logic unit as gates + wires."""
    gates, wires = [], []

    def gate(gid, gtype):
        gates.append({"id": gid, "type": gtype})

    def wire(src, dst):
        wires.append({"from": src, "to": dst})

    # Inputs
    for i in range(width):
        gate(f"A{i}", "INPUT")
        gate(f"B{i}", "INPUT")
    gate("S0", "INPUT")
    gate("S1", "INPUT")

    # Shared 2-to-4 decoder: D0=00, D1=01, D2=10, D3=11
    gate("nS0", "NOT"); wire("S0", "nS0")
    gate("nS1", "NOT"); wire("S1", "nS1")
    for name, (x, y) in {"D0": ("nS1", "nS0"), "D1": ("nS1", "S0"),
                         "D2": ("S1", "nS0"), "D3": ("S1", "S0")}.items():
        gate(name, "AND"); wire(x, name); wire(y, name)

    # One slice per bit
    for i in range(width):
        gate(f"and{i}", "AND"); wire(f"A{i}", f"and{i}"); wire(f"B{i}", f"and{i}")
        gate(f"or{i}", "OR");   wire(f"A{i}", f"or{i}");  wire(f"B{i}", f"or{i}")
        gate(f"xor{i}", "XOR"); wire(f"A{i}", f"xor{i}"); wire(f"B{i}", f"xor{i}")
        gate(f"not{i}", "NOT"); wire(f"A{i}", f"not{i}")

        # 4:1 mux = AND each result with its decoder line, then OR them together
        for k, src in enumerate([f"and{i}", f"or{i}", f"xor{i}", f"not{i}"]):
            gate(f"m{k}_{i}", "AND"); wire(src, f"m{k}_{i}"); wire(f"D{k}", f"m{k}_{i}")
        gate(f"or01_{i}", "OR"); wire(f"m0_{i}", f"or01_{i}"); wire(f"m1_{i}", f"or01_{i}")
        gate(f"or23_{i}", "OR"); wire(f"m2_{i}", f"or23_{i}"); wire(f"m3_{i}", f"or23_{i}")
        gate(f"y_or_{i}", "OR"); wire(f"or01_{i}", f"y_or_{i}"); wire(f"or23_{i}", f"y_or_{i}")
        gate(f"Y{i}", "OUTPUT"); wire(f"y_or_{i}", f"Y{i}")

    return {"circuit_name": f"{width}-bit ALU Logic Unit", "gates": gates, "wires": wires}


def simulate_graph(graph: dict, inputs: dict) -> dict:
    """Evaluate the gate graph. `inputs` maps input id -> 0/1."""
    types = {g["id"]: g["type"] for g in graph["gates"]}
    sources = {gid: [] for gid in types}
    for w in graph["wires"]:
        sources[w["to"]].append(w["from"])
    cache = {}

    def val(gid):
        if gid in cache:
            return cache[gid]
        t, ins = types[gid], [val(s) for s in sources[gid]]
        if t == "INPUT":
            r = inputs[gid]
        elif t == "OUTPUT":
            r = ins[0]
        elif t == "NOT":
            r = 1 - ins[0]
        elif t == "AND":
            r = int(all(ins))
        elif t == "OR":
            r = int(any(ins))
        elif t == "XOR":
            r = sum(ins) % 2
        else:
            raise ValueError(f"unknown gate type {t}")
        cache[gid] = r
        return r

    return {gid: val(gid) for gid, t in types.items() if t == "OUTPUT"}
_NUM_INPUTS = {"INPUT": 0, "OUTPUT": 1, "NOT": 1}  # every other gate type has 2 inputs


def to_gate_json(graph: dict) -> dict:
    """Convert build_logic_unit_graph() output into the repo's gate_json format."""
    from export.export_module import _layout_gates  # reuse the repo's auto-layout

    id_map = {g["id"]: i for i, g in enumerate(graph["gates"])}
    gates, input_count, output_count = [], 0, 0

    for g in graph["gates"]:
        gtype = g["type"]
        if gtype == "INPUT":
            input_count += 1
        elif gtype == "OUTPUT":
            output_count += 1
        gates.append({
            "id": id_map[g["id"]],
            "type": gtype,
            "x": 0,
            "y": 0,
            "inputs": _NUM_INPUTS.get(gtype, 2),
            "hasOutput": gtype != "OUTPUT",
            "output": None,
            "inputValues": [False] if gtype == "INPUT" else [],
            "label": g["id"],
        })

    wires, pin_index = [], {}
    for w in graph["wires"]:
        to_id = id_map[w["to"]]
        idx = pin_index.get(to_id, 0)
        wires.append({"id": len(wires), "fromId": id_map[w["from"]],
                      "toId": to_id, "toIndex": idx})
        pin_index[to_id] = idx + 1

    _layout_gates(gates, wires)

    return {
        "gates": gates,
        "wires": wires,
        "gateIdCounter": len(gates),
        "wireIdCounter": len(wires),
        "inputCounter": input_count,
        "outputCounter": output_count,
        "exportedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }