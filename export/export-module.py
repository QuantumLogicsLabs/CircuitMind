import json

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


def export_module(json_input, save_to_file=False):

    if not json_input or json_input.strip() == "":
        return {"status": "error", "message": "Input is empty."}

    try:
        data = json.loads(json_input)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON input."}

    if "circuit_name" not in data or "components" not in data or "connections" not in data:
        return {"status": "error", "message": "Missing fields in JSON."}

    name        = data["circuit_name"]
    components  = data["components"]
    connections = data["connections"]

    spice = generate_spice(name, components)

    output = {
        "status": "success",
        "circuit_name": name,
        "components": ", ".join(components),
        "connections": ", ".join(c.replace("->", "→") for c in connections),

    }

    if save_to_file:
        with open("circuit_output.json", "w") as f:
            json.dump(output, f, indent=4)
        with open("circuit_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Circuit Name : {name}\nComponents   : {output['components']}\nConnections  : {output['connections']}")
        with open("circuit_output.sp", "w") as f:
            f.write(spice)

    return output


if __name__ == "__main__":
    valid = '''{"circuit_name": "LED Circuit", "components": ["battery", "resistor", "led"], "connections": ["battery -> resistor -> led"]}'''
    print(export_module(valid, save_to_file=True))
    print(export_module(""))
    print(export_module("not json"))
