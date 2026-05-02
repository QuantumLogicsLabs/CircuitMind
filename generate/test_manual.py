import json
from generate import generate_circuit

tests = [
    # Rule-based circuits
    "make me a LED circuit",
    "I want a motor circuit",
    "buzzer circuit banao",
    "make a fan circuit",
    "temperature sensor circuit",
    "solar panel charging circuit",
    "555 timer circuit",
    "rc filter circuit",

    # LLM smart circuits
    "make me a bluetooth speaker circuit",
    "alarm system circuit",

    # Error cases
    "",        # empty
    "ab",      # too short
    "a" * 1001 # too long
]

results = {}

print("=" * 50)
print("CircuitMind Generate Module Tests")
print("=" * 50)

for test in tests:
    display = test if len(test) < 30 else test[:30] + "..."
    print(f"\nInput: '{display}'")
    output=generate_circuit(test)
    print(f"Source: {output.get('source','error')}")
    print(f"Output: {output}")
    results[display]=output

with open("output.json", "w") as f:
    json.dump(results, f, indent=4)

print("\n" + "=" * 50)
print("output.json saved")
print("=" * 50)