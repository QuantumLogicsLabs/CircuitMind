"""
CircuitMind - Generate Module
generate/generate.py

Converts a natural language prompt into a structured circuit JSON.
Strategy: LLM (Groq) first → rule-based fallback if LLM is unavailable.
"""

import json
import os
import logging
import re

logger = logging.getLogger(__name__)

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


# ── Input Validation ───────────────────────────────────────────────────────────

def validate_input(prompt: str) -> str:
    if not prompt or len(prompt.strip()) == 0:
        raise ValueError("Input cannot be empty. Try: 'make me a LED circuit'")
    if len(prompt.strip()) < 3:
        raise ValueError("Input too short. Try: 'make me a LED circuit'")
    if len(prompt) > 1000:
        raise ValueError("Input too long. Keep it under 1000 characters.")
    return prompt.strip()


# ── Rule-Based Fallback ────────────────────────────────────────────────────────

_RULES = [
    (["led", "light"],                         "LED Circuit",              ["battery", "resistor", "led"],                          ["battery -> resistor -> led"],                        "Basic LED circuit with current-limiting resistor"),
    (["motor"],                                "Motor Circuit",            ["battery", "switch", "dc_motor"],                       ["battery -> switch -> dc_motor"],                     "Basic DC motor circuit with on/off switch"),
    (["buzzer"],                               "Buzzer Circuit",           ["battery", "resistor", "buzzer"],                       ["battery -> resistor -> buzzer"],                     "Buzzer circuit with resistor for sound output"),
    (["fan"],                                  "Fan Circuit",              ["battery", "switch", "capacitor", "dc_motor"],          ["battery -> switch -> capacitor -> dc_motor"],        "Fan circuit with capacitor for smooth startup"),
    (["temperature", "sensor"],                "Temperature Sensor",       ["battery", "thermistor", "resistor", "microcontroller"],["battery -> thermistor -> resistor -> microcontroller"],"Temperature sensing circuit using thermistor"),
    (["solar"],                                "Solar Charging Circuit",   ["solar_cell", "diode", "charge_controller", "battery"],["solar_cell -> diode -> charge_controller -> battery"],"Solar panel battery charging circuit"),
    (["555", "timer"],                         "555 Timer Circuit",        ["battery", "555_timer", "resistor", "capacitor", "led"],["battery -> 555_timer -> resistor -> capacitor -> led"],"555 timer astable multivibrator"),
    (["rc", "filter"],                         "RC Filter Circuit",        ["power_supply", "resistor", "capacitor"],              ["power_supply -> resistor -> capacitor -> ground"],    "RC low-pass filter circuit"),
]

def _matches(prompt: str, keywords: list) -> bool:
    """
    Return True only if a keyword appears as a whole word in the prompt.

    Substring matching is too greedy: "rc" would match inside "circuit"
    and "led" would match inside "bleeding". Word-boundary regex prevents
    these false positives.
    """
    return any(
        re.search(rf"\b{re.escape(kw)}\b", prompt) for kw in keywords
    )

def generate_with_rules(prompt: str) -> dict:
    p = prompt.lower()
    for keywords, name, components, connections, description in _RULES:
        if _matches(p, keywords):
            return {
                "circuit_name": name,
                "components":   components,
                "connections":  connections,
                "confidence":   "high",
                "description":  description,
                "source":       "rule-based",
            }
    return {
        "circuit_name": "Unknown",
        "components":   [],
        "connections":  [],
        "confidence":   "low",
        "description":  "Circuit not recognised. Try: led, motor, buzzer, fan, temperature, solar, 555 timer, rc filter.",
        "source":       "rule-based",
    }


# ── LLM Generation ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a circuit generator AI. "
    "Convert user requests into circuit JSON. "
    "Reply ONLY with valid JSON — no explanation, no markdown, no code blocks.\n"
    "IMPORTANT: Use ONLY these exact component names — no prefixes, values, or modifiers:\n"
    "battery, power_supply, solar_cell, resistor, capacitor, inductor, potentiometer, "
    "diode, led, zener_diode, transistor, npn_transistor, pnp_transistor, mosfet, "
    "op_amp, 555_timer, arduino, microcontroller, "
    "buzzer, motor, dc_motor, speaker, relay, display, lcd, "
    "ldr, thermistor, photodiode, button, switch, sensor, "
    "ground, fuse, transformer"
)

_USER_TEMPLATE = (
    'Convert this into a circuit JSON:\n\n"{prompt}"\n\n'
    "Use exactly this format:\n"
    '{{\n'
    '  "circuit_name": "name of circuit",\n'
    '  "components": ["component1", "component2"],\n'
    '  "connections": ["comp1 -> comp2 -> comp3"],\n'
    '  "confidence": "high",\n'
    '  "description": "one line explanation"\n'
    '}}'
)

def generate_with_llm(prompt: str) -> dict:
    if not GROQ_AVAILABLE:
        raise RuntimeError("Groq not installed. Run: pip install groq")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": _USER_TEMPLATE.format(prompt=prompt)},
        ],
        max_tokens=512,
        temperature=0.2,
        response_format={"type": "json_object"},  # enforce valid JSON output
    )

    raw = completion.choices[0].message.content.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    result = json.loads(raw)   # raises JSONDecodeError if invalid
    result["source"] = "llm"
    return result


# ── Public API ────────────────────────────────────────────────────────────────

def generate_circuit(user_prompt: str) -> dict:
    """
    Main entry point.
    Input:  user text e.g. 'make me a LED circuit'
    Output: circuit JSON dict — never raises, always returns.
    """
    try:
        clean_prompt = validate_input(user_prompt)
    except ValueError as e:
        return {"error": str(e), "error_code": "INVALID_INPUT", "components": [], "connections": []}

    try:
        logger.info("Attempting LLM generation via Groq")
        return generate_with_llm(clean_prompt)
    except Exception as e:
        logger.warning(f"LLM unavailable ({e}), falling back to rule-based generation")
        return generate_with_rules(clean_prompt)
