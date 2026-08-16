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

def generate_gate_json(circuit_name: str, components: list, connections: list) -> dict:
    gates  = []
    wires  = []
    input_counter  = 0
    output_counter = 0

    for i, component in enumerate(components):
        comp_lower = component.lower()
        if comp_lower.startswith("input") or comp_lower.startswith("in_") or comp_lower in ("battery", "power_supply", "solar_cell") or (i == 0 and len(components) <= 3):
            gate_type, num_inputs, has_output = "INPUT",  0, True
            input_counter += 1
        elif comp_lower.startswith("output") or comp_lower.endswith("_output") or comp_lower.endswith("_out") or comp_lower in ("cout", "sum", "carry", "led", "lamp", "buzzer") or (i == len(components) - 1 and len(components) <= 3):
            gate_type, num_inputs, has_output = "OUTPUT", 1, False
            output_counter += 1
        else:
            comp_upper = component.upper()
            if "XNOR" in comp_upper: comp_upper = "XNOR"
            elif "XOR" in comp_upper: comp_upper = "XOR"
            elif "NAND" in comp_upper: comp_upper = "NAND"
            elif "NOR" in comp_upper: comp_upper = "NOR"
            elif "AND" in comp_upper: comp_upper = "AND"
            elif "OR" in comp_upper: comp_upper = "OR"
            elif "NOT" in comp_upper: comp_upper = "NOT"
            gate_type = comp_upper
            num_inputs = 1 if comp_upper == "NOT" else 2
            has_output = True

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

    input_gates  = [g for g in gates if g["type"] == "INPUT"]
    output_gates = [g for g in gates if g["type"] == "OUTPUT"]
    logic_gates  = [g for g in gates if g["type"] not in ("INPUT", "OUTPUT")]

    for i, g in enumerate(input_gates):
        g["x"] = 80
        g["y"] = 80 + (i * 120)

    for i, g in enumerate(logic_gates):
        g["x"] = 350 + ((i // 3) * 200)
        g["y"] = 80 + ((i % 3) * 120)

    for i, g in enumerate(output_gates):
        g["x"] = 620 + ((i // 3) * 200)
        g["y"] = 80 + ((i % 3) * 120)

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
