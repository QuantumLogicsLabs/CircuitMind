import json
import schemdraw
import schemdraw.elements as elm
from datetime import datetime, timezone

COMPONENT_MAP = {
    "battery": "V",
    "resistor": "R",
    "led": "D",
    "capacitor": "C",
    "switch": "S",
    "motor": "M"
}

COMPONENT_VALUES = {
    "battery": "9V",
    "resistor": "330ohm",
    "led": "LED",
    "capacitor": "100uF",
    "switch": "SW",
    "motor": "MOTOR"
}

SVG_MAP = {
    "battery": elm.Battery,
    "resistor": elm.Resistor,
    "led": elm.Diode,
    "capacitor": elm.Capacitor,
    "switch": elm.Switch,
}

def generate_spice(circuit_name, components):
    lines = [circuit_name]
    counters = {}
    node = 1
    for component in components:
        symbol = COMPONENT_MAP.get(component, "X")
        value  = COMPONENT_VALUES.get(component, "?")
        counters[symbol] = counters.get(symbol, 0) + 1
        name = f"{symbol}{counters[symbol]}"
        lines.append(f"{name} {node} {node+1} {value}")
        node += 1
    lines.append(".end")
    return "\n".join(lines)

def generate_svg(circuit_name, components, filename="circuit_diagram"):
    with schemdraw.Drawing() as d:
        for component in components:
            element = SVG_MAP.get(component)
            if element:
                d += element().right()
        d.save(f"{filename}.svg")
    return f"{filename}.svg"

def generate_gate_json(circuit_name, components, connections):
    gates = []
    wires = []
    x = 80
    y = 100
    y_gap = 220

    input_counter = 0
    output_counter = 0

    # First component = INPUT, Last = OUTPUT, Middle = regular gate
    for i, component in enumerate(components):
        if i == 0:
            gate_type = "INPUT"
            input_values = [False]
            has_output = True
            num_inputs = 0
            input_counter += 1
            label = component.upper()
        elif i == len(components) - 1:
            gate_type = "OUTPUT"
            input_values = []
            has_output = False
            num_inputs = 1
            output_counter += 1
            label = component.upper()
        else:
            gate_type = component.upper()
            input_values = []
            has_output = True
            num_inputs = 1
            label = component.upper()

        gates.append({
            "id": i,
            "type": gate_type,
            "x": x + (i * 200),
            "y": y,
            "inputs": num_inputs,
            "hasOutput": has_output,
            "output": None,
            "inputValues": input_values,
            "label": label
        })

    # Create wires from connections
    for wire_id, conn in enumerate(connections):
        parts = conn.split("->")
        parts = [p.strip() for p in parts]
        for j in range(len(parts) - 1):
            from_component = parts[j]
            to_component   = parts[j + 1]

            from_id = next((g["id"] for g in gates if g["label"] == from_component.upper()), None)
            to_id   = next((g["id"] for g in gates if g["label"] == to_component.upper()), None)

            if from_id is not None and to_id is not None:
                wires.append({
                    "id": wire_id + j,
                    "fromId": from_id,
                    "toId": to_id,
                    "toIndex": 0
                })

    return {
        "gates": gates,
        "wires": wires,
        "gateIdCounter": len(gates),
        "wireIdCounter": len(wires),
        "inputCounter": input_counter,
        "outputCounter": output_counter,
        "exportedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    }


def export_module(json_input, save_to_file=False, export_format="gate_json"):

    # Check 1: Empty input
    if not json_input or json_input.strip() == "":
        return {"status": "error", "message": "Input is empty."}

    # Check 2: Valid JSON
    try:
        data = json.loads(json_input)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON input."}

# Check 3: Required fields (Updated to make circuit_name optional)
    if "components" not in data or "connections" not in data:
        return {"status": "error", "message": "Missing required fields (components/connections) in JSON."}

    name        = data.get("circuit_name", "CircuitMind_Generated_Circuit")
    components  = data["components"]
    connections = data["connections"]

    if export_format == "spice":
        spice = generate_spice(name, components)
        output = {
            "status": "success",
            "format": "spice",
            "circuit_name": name,
            "components": ", ".join(components),
            "connections": ", ".join(c.replace("->", "→") for c in connections),
            "spice_netlist": spice
        }
        if save_to_file:
            with open("circuit_output.json", "w") as f:
                json.dump(output, f, indent=4)
            with open("circuit_output.txt", "w", encoding="utf-8") as f:
                f.write(f"Circuit Name : {name}\nComponents   : {output['components']}\nConnections  : {output['connections']}")
            with open("circuit_output.sp", "w") as f:
                f.write(spice)

    elif export_format == "svg":
        svg_file = generate_svg(name, components)
        output = {
            "status": "success",
            "format": "svg",
            "circuit_name": name,
            "components": ", ".join(components),
            "svg_file": svg_file
        }

    elif export_format == "gate_json":
        gate_data = generate_gate_json(name, components, connections)
        output = {
            "status": "success",
            "format": "gate_json",
            "circuit_name": name,
            "gate_json": gate_data
        }
        if save_to_file:
            with open("circuit_gate.json", "w") as f:
                json.dump(gate_data, f, indent=4)

    else:
        return {"status": "error", "message": "Invalid format. Use spice, svg or gate_json."}

    return output


if __name__ == "__main__":
    valid = '''{"circuit_name": "LED Circuit", "components": ["battery", "resistor", "led"], "connections": ["battery -> resistor -> led"]}'''

    print("SPICE Test:")
    print(export_module(valid, save_to_file=True, export_format="spice"))

    print("\nSVG Test:")
    print(export_module(valid, save_to_file=True, export_format="svg"))

    print("\nGate JSON Test:")
    print(export_module(valid, save_to_file=True, export_format="gate_json"))

    print("\nEmpty Test:")
    print(export_module(""))

    print("\nInvalid Test:")
    print(export_module("not json"))
