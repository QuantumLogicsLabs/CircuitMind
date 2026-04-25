import json
from generate import generate_circuit

result1 = generate_circuit("make me a LED circuit")
result2 = generate_circuit("make me a motor circuit")
result3 = generate_circuit("make me a buzzer circuit")


print("Test 1: LED circuit")
print(generate_circuit("make me a LED circuit"))

print("Test 2: Motor circuit")
print(generate_circuit("make me a motor circuit"))

print("Test 3: Buzzer circuit")
print(generate_circuit("make me a buzzer circuit"))

print("Test 4: Unknown")
print(generate_circuit("make me a robot"))

with open("output.json", "w") as f:
    json.dump({"led_circuit": result1, "motor_circuit": result2, "buzzer_circuit": result3}, f, indent=4)

print("\noutput.json file created successfully!")