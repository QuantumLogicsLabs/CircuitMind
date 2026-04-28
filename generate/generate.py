import json
from groq import Groq


def validate_input(prompt: str) -> str:

    if not prompt or len(prompt.strip()) == 0:
        raise ValueError("Input cannot be empty")
    if len(prompt.strip()) < 3:
        raise ValueError("Input too short, please describe your circuit")
    if len(prompt) > 300:
        raise ValueError("Input too long, keep it under 300 characters")
    return prompt.strip()


def generate_with_rules(prompt: str) -> dict:
    """Fallback rule-based generation if LLM fails"""
    prompt = prompt.lower()

    if "led" in prompt or "light" in prompt:
        return {
            "circuit_name": "LED Circuit",
            "components": ["battery", "resistor", "led"],
            "connections": ["battery -> resistor -> led"],
            "confidence": "high",
            "description": "Basic LED circuit with current limiting resistor",
            "source": "rule-based"
        }
    elif "motor" in prompt:
        return {
            "circuit_name": "Motor Circuit",
            "components": ["battery", "switch", "motor"],
            "connections": ["battery -> switch -> motor"],
            "confidence": "high",
            "description": "Basic DC motor circuit with on/off switch",
            "source": "rule-based"
        }
    elif "buzzer" in prompt:
        return {
            "circuit_name": "Buzzer Circuit",
            "components": ["battery", "resistor", "buzzer"],
            "connections": ["battery -> resistor -> buzzer"],
            "confidence": "high",
            "description": "Buzzer circuit with resistor for sound output",
            "source": "rule-based"
        }
    elif "fan" in prompt:
        return {
            "circuit_name": "Fan Circuit",
            "components": ["battery", "switch", "capacitor", "fan"],
            "connections": ["battery -> switch -> capacitor -> fan"],
            "confidence": "high",
            "description": "Fan circuit with capacitor for smooth startup",
            "source": "rule-based"
        }
    else:
        return {
            "circuit_name": "Unknown",
            "components": [],
            "connections": [],
            "confidence": "low",
            "description": "Circuit not recognized",
            "source": "rule-based"
        }


def generate_with_llm(prompt: str) -> dict:
    """Use Groq LLM to generate circuit JSON"""
    client = Groq()

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """You are a circuit generator AI. 
Convert user requests into circuit JSON.
Reply ONLY with valid JSON, nothing else, no explanation."""
            },
            {
                "role": "user",
                "content": f"""Convert this into a circuit JSON:
"{prompt}"

Use exactly this format:
{{
  "circuit_name": "name of circuit",
  "components": ["component1", "component2"],
  "connections": ["comp1 -> comp2 -> comp3"],
  "confidence": "high",
  "description": "one line explanation"
}}"""
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    raw = chat_completion.choices[0].message.content
    result = json.loads(raw)
    result["source"] = "llm"
    return result


def generate_circuit(user_prompt: str) -> dict:

    #1: Validate input
    try:
        clean_prompt = validate_input(user_prompt)
    except ValueError as e:
        return {
            "error": str(e),
            "components": [],
            "connections": []
        }

    #2 Try LLM first
    try:
        print("Asking Groq AI...")
        result = generate_with_llm(clean_prompt)
        return result

    #3 If LLM fails, use rules
    except Exception as e:
        print(f"LLM failed: {e}, using rule-based fallback")
        return generate_with_rules(clean_prompt)