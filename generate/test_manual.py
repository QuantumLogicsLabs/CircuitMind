import json
from generate import generate_circuit

tests = [
    "make me a LED circuit",
    "I want a motor circuit",
    "buzzer circuit banao",
    "make a fan circuit",
    "temperature sensor circuit",
    "solar panel charging circuit",
    "",
]

results = {}

for test in tests:
    print(f"\nInput: '{test}'")
    output = generate_circuit(test)
    print(f"Output: {output}")
    results[test if test else "empty_input"] = output

with open("output.json", "w") as f:
    json.dump(results, f, indent=4)

print("\noutput.json saved successfully.")