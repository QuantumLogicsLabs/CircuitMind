import json
from export_module import export_module

#1: LED Circuit
led = '''{"circuit_name": "LED Circuit", "components": ["battery", "resistor", "led"], "connections": ["battery -> resistor -> led"]}'''

#2: Motor Circuit
motor = '''{"circuit_name": "Motor Circuit", "components": ["battery", "switch", "motor"], "connections": ["battery -> switch -> motor"]}'''

#3: Fan Circuit
fan = '''{"circuit_name": "Fan Circuit", "components": ["battery", "switch", "capacitor", "motor"], "connections": ["battery -> switch -> capacitor -> motor"]}'''

#4: Empty input
empty = ''

#5: Invalid JSON
invalid = 'not json at all'

# Running of all tests
results = []

for test in [led, motor, fan, empty, invalid]:
    result = export_module(test, save_to_file=False)
    results.append(result)
    print(result)

#Save results to test_results.json
with open("test_results.json", "w") as f:
    json.dump(results, f, indent=4)

print("All tests done - saved to test_results.json")
