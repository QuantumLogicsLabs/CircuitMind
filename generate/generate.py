import json
import os

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def validate_input(prompt: str) -> str:
    """Validate user input before processing"""
    if not prompt or len(prompt.strip()) == 0:
        raise ValueError("Input cannot be empty. Try make me a LED circuit")
    if len(prompt.strip()) < 3:
        raise ValueError("Input too short. Try make me a LED circuit")
    if len(prompt) > 1000:
        raise ValueError("Input too long. Keep it under 1000 characters")
    return prompt.strip()


def generate_with_rules(prompt: str) -> dict:
    """Rule-based fallback when LLM is unavailable"""
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
    elif "temperature" in prompt or "sensor" in prompt:
        return {
            "circuit_name": "Temperature Sensor Circuit",
            "components": ["battery", "thermistor", "resistor", "microcontroller"],
            "connections": ["battery -> thermistor -> resistor -> microcontroller"],
            "confidence": "high",
            "description": "Temperature sensing circuit using thermistor",
            "source": "rule-based"
        }
    elif "solar" in prompt:
        return {
            "circuit_name": "Solar Charging Circuit",
            "components": ["solar panel", "diode", "charge controller", "battery"],
            "connections": ["solar panel -> diode -> charge controller -> battery"],
            "confidence": "high",
            "description": "Solar panel battery charging circuit",
            "source": "rule-based"
        }
    elif "555" in prompt or "timer" in prompt:
        return {
            "circuit_name": "555 Timer Circuit",
            "components": ["battery", "555-timer", "resistor", "capacitor", "led"],
            "connections": ["battery -> 555-timer -> resistor -> capacitor -> led"],
            "confidence": "high",
            "description": "555 timer astable multivibrator circuit",
            "source": "rule-based"
        }
    elif "rc" in prompt or "filter" in prompt:
        return {
            "circuit_name": "RC Filter Circuit",
            "components": ["resistor", "capacitor"],
            "connections": ["input -> resistor -> capacitor -> ground"],
            "confidence": "high",
            "description": "RC low pass filter circuit",
            "source": "rule-based"
        }
    else:
        return {
            "circuit_name": "Unknown",
            "components": [],
            "connections": [],
            "confidence": "low",
            "description": "Circuit not recognized. Try: led, motor, buzzer, fan, temperature, solar, 555 timer, rc filter",
            "source": "rule-based"
        }


def generate_with_llm(prompt: str) -> dict:
    """
    Use Groq AI to generate circuit JSON
    Setup: Set GROQ_API_KEY in .env file
    Get free key from: https://console.groq.com
    """

    if not GROQ_AVAILABLE:
        raise ValueError("Groq not installed. Run: pip install groq")

    api_key=os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    client=Groq(api_key=api_key)

    chat_completion=client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """You are a circuit generator AI.
                Convert user requests into circuit JSON.
                Reply ONLY with valid JSON, no explanation, no markdown, no code blocks."""
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

    raw=chat_completion.choices[0].message.content

    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        result = json.loads(raw)
        result["source"] = "llm"
        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}")


def generate_circuit(user_prompt: str) -> dict:
    """
    Main function - LLM first, rule-based fallback if LLM fails
    Input:  User text like 'make LED circuit'
    Output: Circuit JSON dict
    """

    #1 Validate input
    try:
        clean_prompt=validate_input(user_prompt)
    except ValueError as e:
        return {
            "error": str(e),
            "error_code": "INVALID_INPUT",
            "components": [],
            "connections": []
        }

    #2 Try LLM first
    try:
        print("Asking Groq AI...")
        result=generate_with_llm(clean_prompt)
        return result

    #3 Clean fallback, no crash
    except Exception as e:
        print(f"LLM failed ({e}), using rule-based fallback...")
        return generate_with_rules(clean_prompt)