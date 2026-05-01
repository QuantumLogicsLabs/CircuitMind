# generate/test_manual.py
# Developer: M-Haseeb
# Day 3 Updated: Testing LLM, fallback, error handling, invalid inputs

import json
from generate import generate_circuit

tests = [
    # Normal circuits - LLM will handle
    "make me a LED circuit",
    "I want a motor circuit",
    "buzzer circuit banao",
    "make a fan circuit",
    "temperature sensor circuit",
    "solar panel charging circuit",

    # These will test LLM smart generation
    "make me a bluetooth speaker circuit",
    "alarm system circuit",

    # Error cases - validation
    "",           # empty input
    "ab",         # too short
    "a" * 301,    # too long
]

results={}

print("=" * 50)
print("Generate Module Tests")
print("=" * 50)

for test in tests:
    display=test if len(test) < 30 else test[:30] + "..."
    print(f"\nInput: '{display}'")
    output=generate_circuit(test)
    print(f"Source: {output.get('source','error')}")
    print(f"Output: {output}")
    results[display]=output

# Save to JSON
with open("output.json", "w") as f:
    json.dump(results, f, indent=4)

print("\n" + "=" * 50)
print("output.json saved")
print("=" * 50)