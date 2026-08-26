"""
CircuitMind - Export Module
export/export_module.py

Converts circuit JSON into:
  - SPICE netlist  (export_format="spice")
  - SVG diagram    (export_format="svg")
  - Gate JSON      (export_format="gate_json")
"""

import json
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Component maps ─────────────────────────────────────────────────────────────

COMPONENT_MAP = {
    # ── Existing entries (unchanged) ──────────────────────────────────────────
    "battery":       "V",
    "resistor":      "R",
    "led":           "D",
    "capacitor":     "C",
    "switch":        "S",
    "motor":         "M",
    "inductor":      "L",
    "transistor":    "Q",
    # ── Added: power sources ──────────────────────────────────────────────────
    "power_supply":  "V",  # voltage source, same symbol as battery
    "solar_cell":    "V",  # modelled as a voltage source in SPICE
    # ── Added: diodes ─────────────────────────────────────────────────────────
    "diode":         "D",  # standard signal diode
    "zener_diode":   "D",  # 5.1 V zener
    "photodiode":    "D",  # common photodiode
    # ── Added: transistors / FETs ─────────────────────────────────────────────
    "npn_transistor": "Q", # same as generic transistor
    "pnp_transistor": "Q", # common PNP
    "mosfet":        "M",  # MOSFET symbol is M in SPICE
    # ── Added: passive ────────────────────────────────────────────────────────
    "potentiometer": "R",  # variable resistor → resistor symbol
    "thermistor":    "R",  # modelled as resistor
    "ldr":           "R",  # modelled as resistor
    "fuse":          "R",  # modelled as a tiny resistor in SPICE
    # ── Added: output / actuators ─────────────────────────────────────────────
    "dc_motor":      "M",  # same as motor
    "buzzer":        "X",  # no native SPICE symbol; use subcircuit
    "speaker":       "X",  # same as buzzer
    "relay":         "X",  # subcircuit, no native element
    # ── Added: ICs / subcircuits ──────────────────────────────────────────────
    "op_amp":            "X",  # subcircuit model
    "555_timer":         "X",  # subcircuit model
    "arduino":           "X",  # subcircuit
    "microcontroller":   "X",  # subcircuit
    "charge_controller": "X",  # subcircuit
    # ── Added: sensors / input ────────────────────────────────────────────────
    "button":        "S",  # same as switch
    "sensor":        "X",  # generic subcircuit
    # ── Added: display / misc ─────────────────────────────────────────────────
    "display":       "X",  # subcircuit
    "lcd":           "X",  # subcircuit
    "transformer":   "X",  # subcircuit
}

COMPONENT_VALUES = {
    # ── Existing entries (unchanged) ──────────────────────────────────────────
    "battery":       "9V",
    "resistor":      "330ohm",
    "led":           "LED",
    "capacitor":     "100uF",
    "switch":        "SW",
    "motor":         "MOTOR",
    "inductor":      "1mH",
    "transistor":    "2N2222",
    # ── Added: power sources ──────────────────────────────────────────────────
    "power_supply":  "12V",
    "solar_cell":    "5V",
    # ── Added: diodes ─────────────────────────────────────────────────────────
    "diode":         "1N4148",
    "zener_diode":   "1N4733A",
    "photodiode":    "BPW34",
    # ── Added: transistors / FETs ─────────────────────────────────────────────
    "npn_transistor": "2N2222",
    "pnp_transistor": "2N2907",
    "mosfet":        "IRF540N",
    # ── Added: passive ────────────────────────────────────────────────────────
    "potentiometer": "10kohm",
    "thermistor":    "10kohm",
    "ldr":           "10kohm",
    "fuse":          "0.01ohm",
    # ── Added: output / actuators ─────────────────────────────────────────────
    "dc_motor":      "MOTOR",
    "buzzer":        "BUZZER",
    "speaker":       "SPEAKER",
    "relay":         "RELAY",
    # ── Added: ICs / subcircuits ──────────────────────────────────────────────
    "op_amp":            "LM741",
    "555_timer":         "NE555",
    "arduino":           "ARDUINO",
    "microcontroller":   "MCU",
    "charge_controller": "CC",
    # ── Added: sensors / input ────────────────────────────────────────────────
    "button":        "SW",
    "sensor":        "SENSOR",
    # ── Added: display / misc ─────────────────────────────────────────────────
    "display":       "DISPLAY",
    "lcd":           "LCD",
    "transformer":   "XFMR",
}

VALID_FORMATS = {"spice", "svg", "gate_json"}


# ── SPICE generator ────────────────────────────────────────────────────────────

def generate_spice(circuit_name: str, components: list) -> str:
    lines    = [circuit_name]
    counters: dict = {}
    
    comps = [c for c in components if c.lower() not in ("ground", "gnd")]
    
    # Track defined subcircuits by subcircuit name: value -> (node1, node2)
    defined_subckts = {}
    
    for i, component in enumerate(comps):
        symbol = COMPONENT_MAP.get(component, "X")
        value  = COMPONENT_VALUES.get(component, "?")
        counters[symbol] = counters.get(symbol, 0) + 1
        name = f"{symbol}{counters[symbol]}"
        
        if i == 0:
            n1, n2 = 1, 0
        elif i == len(comps) - 1:
            n1, n2 = i, 0
        else:
            n1, n2 = i, i + 1
            
        lines.append(f"{name} {n1} {n2} {value}")
        
        if symbol == "X":
            if value not in defined_subckts:
                defined_subckts[value] = (n1, n2)
                
    for subckt_name, (node_a, node_b) in defined_subckts.items():
        lines.append(f".subckt {subckt_name} {node_a} {node_b}")
        lines.append(f"Rdummy {node_a} {node_b} 10Meg")
        lines.append(f".ends {subckt_name}")
        
    lines.append(".end")
    return "\n".join(lines)


# ── SVG generator ──────────────────────────────────────────────────────────────

def generate_svg(circuit_name: str, components: list) -> str:
    """Generate an SVG circuit schematic and return SVG markup string."""
    try:
        import schemdraw
        import schemdraw.elements as elm
    except ImportError:
        raise RuntimeError("schemdraw is not installed. Run: pip install schemdraw")

    SVG_MAP = {
        # Power sources
        "battery":       elm.Battery,
        "power_supply":  elm.SourceV,
        "solar_cell":    elm.SourceV,
        # Passive
        "resistor":      elm.Resistor,
        "capacitor":     elm.Capacitor,
        "inductor":      elm.Inductor,
        "potentiometer": elm.Potentiometer,
        # Diodes
        "diode":         elm.Diode,
        "led":           elm.LED2,
        "zener_diode":   elm.Zener,
        # Switches
        "switch":        elm.Switch,
        "button":        elm.Button,
        # Output devices
        "motor":         elm.Motor,
        "dc_motor":      elm.Motor,
        "buzzer":        elm.Speaker,
        "speaker":       elm.Speaker,
        # Protection
        "fuse":          elm.Fuse,
    }

    def _norm(name: str) -> str:
        return name.strip().lower().replace(" ", "_").replace("-", "_")

    normalized = [_norm(c) for c in components]
    drawable   = [c for c in normalized if c != "ground"]

    if not drawable:
        raise RuntimeError("No drawable components found in the circuit.")

    d = schemdraw.Drawing(show=False)
    d.config(fontsize=12)

    first_elem = None
    for i, comp in enumerate(drawable):
        label    = comp.replace("_", " ").title()
        elem_cls = SVG_MAP.get(comp, elm.RBox)
        elem     = d.add(elem_cls().right().label(label, loc="top"))
        if i == 0:
            first_elem = elem

    # Close the circuit with a return path to form a loop
    if first_elem and len(drawable) > 1:
        d.add(elm.Line().down().length(d.unit * 0.6))
        d.add(elm.Line().left().tox(first_elem.start))
        d.add(elm.Line().up().toy(first_elem.start))

    return d.get_imagedata("svg").decode("utf-8")


# ── Gate JSON generator ────────────────────────────────────────────────────────

LAYER_X_GAP = 220
LAYER_Y_GAP = 130
ORIGIN_X = 80
ORIGIN_Y = 80

_FRIENDLY_LABELS = {
    "INPUT_A": "A",
    "INPUT_B": "B",
    "INPUT_C": "C",
    "INPUT_DIN": "D",
    "SUM_OUTPUT": "SUM",
    "CARRY_OUTPUT": "CARRY",
    "DIFF_OUTPUT": "DIFF",
    "BORROW_OUTPUT": "BORROW",
    "PARITY_OUTPUT": "PARITY",
    "EQ_OUT": "EQ",
    "GT_OUT": "GT",
    "LT_OUT": "LT",
    "OUTPUT_Y0": "Y0",
    "OUTPUT_Y1": "Y1",
}


def _classify_component(component: str, index: int, total: int) -> tuple[str, int, bool]:
    comp_lower = component.lower()
    if (
        comp_lower.startswith("input")
        or comp_lower.startswith("in_")
        or comp_lower in ("battery", "power_supply", "solar_cell")
        or (index == 0 and total <= 3)
    ):
        return "INPUT", 0, True
    if (
        comp_lower.startswith("output")
        or comp_lower.endswith("_output")
        or comp_lower.endswith("_out")
        or comp_lower in ("cout", "sum", "carry", "led", "lamp", "buzzer")
        or (index == total - 1 and total <= 3)
    ):
        return "OUTPUT", 1, False

    comp_upper = component.upper()
    if "XNOR" in comp_upper:
        gate_type = "XNOR"
    elif "XOR" in comp_upper:
        gate_type = "XOR"
    elif "NAND" in comp_upper:
        gate_type = "NAND"
    elif "NOR" in comp_upper:
        gate_type = "NOR"
    elif "AND" in comp_upper:
        gate_type = "AND"
    elif "OR" in comp_upper:
        gate_type = "OR"
    elif "NOT" in comp_upper:
        gate_type = "NOT"
    else:
        gate_type = comp_upper
    return gate_type, (1 if gate_type == "NOT" else 2), True


def _layout_gates(gates: list, wires: list) -> None:
    """Place gates in left-to-right columns from the wire graph (not one row)."""
    if not gates:
        return

    ids = [g["id"] for g in gates]
    preds = defaultdict(set)
    succs = defaultdict(set)
    for wire in wires:
        succs[wire["fromId"]].add(wire["toId"])
        preds[wire["toId"]].add(wire["fromId"])

    indegree = {gid: len(preds[gid]) for gid in ids}
    layer = {}
    queue = deque(gid for gid in ids if indegree[gid] == 0)
    for gid in queue:
        layer[gid] = 0

    while queue:
        u = queue.popleft()
        for v in succs[u]:
            layer[v] = max(layer.get(v, 0), layer.get(u, 0) + 1)
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    max_assigned = max(layer.values(), default=0)
    for gid in ids:
        if gid not in layer:
            layer[gid] = max_assigned + 1

    by_id = {g["id"]: g for g in gates}
    logic_layers = [
        layer[g["id"]] for g in gates if g["type"] != "OUTPUT"
    ]
    max_logic = max(logic_layers, default=0)
    out_col = max_logic + 1
    for g in gates:
        if g["type"] == "INPUT":
            layer[g["id"]] = 0
        elif g["type"] == "OUTPUT":
            layer[g["id"]] = out_col

    columns = defaultdict(list)
    for g in gates:
        columns[layer[g["id"]]].append(g)

    max_col_size = max((len(col) for col in columns.values()), default=1)
    total_height = (max_col_size - 1) * LAYER_Y_GAP

    for col_index, col_gates in columns.items():
        col_height = (len(col_gates) - 1) * LAYER_Y_GAP
        y_offset = (total_height - col_height) / 2
        for i, g in enumerate(col_gates):
            by_id[g["id"]]["x"] = ORIGIN_X + col_index * LAYER_X_GAP
            by_id[g["id"]]["y"] = ORIGIN_Y + y_offset + i * LAYER_Y_GAP


def generate_gate_json(circuit_name: str, components: list, connections: list) -> dict:
    gates  = []
    wires  = []
    input_counter  = 0
    output_counter = 0

    for i, component in enumerate(components):
        gate_type, num_inputs, has_output = _classify_component(component, i, len(components))
        if gate_type == "INPUT":
            input_counter += 1
        elif gate_type == "OUTPUT":
            output_counter += 1

        gates.append({
            "id":          i,
            "type":        gate_type,
            "x":           0,
            "y":           0,
            "inputs":      num_inputs,
            "hasOutput":   has_output,
            "output":      None,
            "inputValues": [False] if gate_type == "INPUT" else [],
            "label":       component.upper(),
        })

    wire_id = 0
    target_pin_indices = {}
    for conn in connections:
        parts = [p.strip() for p in conn.split("->")]
        for j in range(len(parts) - 1):
            from_id = next((g["id"] for g in gates if g["label"] == parts[j].upper()), None)
            to_id   = next((g["id"] for g in gates if g["label"] == parts[j + 1].upper()), None)
            if from_id is not None and to_id is not None:
                to_index = target_pin_indices.get(to_id, 0)
                wires.append({"id": wire_id, "fromId": from_id, "toId": to_id, "toIndex": to_index})
                target_pin_indices[to_id] = to_index + 1
                wire_id += 1

    _layout_gates(gates, wires)

    for g in gates:
        g["label"] = _FRIENDLY_LABELS.get(g["label"], g["label"])

    return {
        "gates":           gates,
        "wires":           wires,
        "gateIdCounter":   len(gates),
        "wireIdCounter":   len(wires),
        "inputCounter":    input_counter,
        "outputCounter":   output_counter,
        "exportedAt":      datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }


# ── Main Entry Point ───────────────────────────────────────────────────────────

def export_module(json_input: str, export_format: str = "spice") -> dict:
    """
    Input:  JSON string with 'components' and 'connections'
    Output: dict with export result or error
    """
    if not json_input or not json_input.strip():
        return {"status": "error", "message": "Input is empty."}

    if export_format not in VALID_FORMATS:
        return {"status": "error", "message": f"Invalid format. Use one of: {', '.join(VALID_FORMATS)}."}

    try:
        data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid JSON: {e}"}

    if "components" not in data or "connections" not in data:
        return {"status": "error", "message": "Missing required fields: 'components' and 'connections'."}

    name        = data.get("circuit_name", "CircuitMind_Generated_Circuit")
    components  = data["components"]
    connections = data["connections"]

    logger.info(f"Exporting '{name}' as {export_format}")

    if export_format == "spice":
        spice = generate_spice(name, components)
        return {
            "status":        "success",
            "format":        "spice",
            "circuit_name":  name,
            "components":    ", ".join(components),
            "connections":   ", ".join(c.replace("->", "→") for c in connections),
            "spice_netlist": spice,
        }

    if export_format == "svg":
        try:
            svg_markup = generate_svg(name, components)
        except RuntimeError as e:
            return {"status": "error", "message": str(e)}
        return {
            "status":       "success",
            "format":       "svg",
            "circuit_name": name,
            "components":   ", ".join(components),
            "connections":  ", ".join(c.replace("->", "→") for c in connections),
            "svg_markup":   svg_markup,
        }

    # gate_json
    gate_data = generate_gate_json(name, components, connections)
    return {
        "status":       "success",
        "format":       "gate_json",
        "circuit_name": name,
        "gate_json":    gate_data,
    }
