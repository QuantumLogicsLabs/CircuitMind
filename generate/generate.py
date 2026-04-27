def validate_input(prompt: str) -> str:
    """Check if user input is valid"""
    if not prompt or len(prompt.strip()) == 0:
        raise ValueError("Input cannot be empty")
    if len(prompt.strip()) < 3:
        raise ValueError("Input too short, please describe your circuit")
    if len(prompt) > 300:
        raise ValueError("Input too long, keep it under 300 characters")
    return prompt.strip()


def generate_circuit(user_prompt: str) -> dict:

    try:
        prompt = validate_input(user_prompt).lower()
    except ValueError as e:
        return {
            "error": str(e),
            "components": [],
            "connections": []
        }

    if "led" in prompt or "light" in prompt:
        return {
            "circuit_name": "LED Circuit",
            "components": ["battery", "resistor", "led"],
            "connections": ["battery -> resistor -> led"],
            "confidence": "high",
            "description": "Basic LED circuit with current limiting resistor"
        }

    elif "motor" in prompt:
        return {
            "circuit_name": "Motor Circuit",
            "components": ["battery", "switch", "motor"],
            "connections": ["battery -> switch -> motor"],
            "confidence": "high",
            "description": "Basic DC motor circuit with on/off switch"
        }

    elif "buzzer" in prompt:
        return {
            "circuit_name": "Buzzer Circuit",
            "components": ["battery", "resistor", "buzzer"],
            "connections": ["battery -> resistor -> buzzer"],
            "confidence": "high",
            "description": "Buzzer circuit with resistor for sound output"
        }

    elif "fan" in prompt:
        return {
            "circuit_name": "Fan Circuit",
            "components": ["battery", "switch", "capacitor", "fan"],
            "connections": ["battery -> switch -> capacitor -> fan"],
            "confidence": "high",
            "description": "Fan circuit with capacitor for smooth startup"
        }

    elif "charge" in prompt or "capacitor" in prompt:
        return {
            "circuit_name": "Capacitor Charging Circuit",
            "components": ["battery", "resistor", "capacitor"],
            "connections": ["battery -> resistor -> capacitor"],
            "confidence": "medium",
            "description": "RC circuit for charging a capacitor"
        }

    elif "switch" in prompt or "button" in prompt:
        return {
            "circuit_name": "Switch Circuit",
            "components": ["battery", "switch", "led"],
            "connections": ["battery -> switch -> led"],
            "confidence": "medium",
            "description": "Simple switch controlled LED circuit"
        }

    else:
        return {
            "circuit_name": "Unknown",
            "components": [],
            "connections": [],
            "confidence": "low",
            "description": "Circuit not recognized. Try: led, motor, buzzer, fan, capacitor"
        }