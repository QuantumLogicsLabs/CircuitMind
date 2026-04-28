import json

def export_module(json_input):
    data = json.loads(json_input)
    
    circuit_name = data["circuit_name"]
    components   = data["components"]
    connections  = data["connections"]
    
    print("Data has loaded successfully")
    print("Circuit Name:", circuit_name)
    print("Components:", components)
    print("Connections:", connections)

json_input = '''
{
  "circuit_name": "LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"]
}
'''

export_module(json_input)
