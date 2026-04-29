import json

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
    components  = ", ".join(data["components"])
    connections = ", ".join(c.replace("->", "→") for c in data["connections"])

   
    output = {
        "status": "success",
        "circuit_name": name,
        "components": components,
        "connections": connections
    }

    # Save to file in case needed 
    if save_to_file:
        with open("circuit_output.json", "w") as f:
            json.dump(output, f, indent=4)
        with open("circuit_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Circuit Name : {name}\nComponents   : {components}\nConnections  : {connections}")

    return output


# Tests
if __name__ == "__main__":

    valid = '''{"circuit_name": "LED Circuit", "components": ["battery", "resistor", "led"], "connections": ["battery -> resistor -> led"]}'''

    print(export_module(valid, save_to_file=True))
    print(export_module(""))
    print(export_module("not json"))
