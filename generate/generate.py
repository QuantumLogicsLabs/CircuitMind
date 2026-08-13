"""
CircuitMind - Generate Module
generate/generate.py

Converts a natural language prompt into a structured circuit JSON.
Strategy: LLM (Groq) first → rule-based fallback if LLM is unavailable.
"""

import json
import os
import logging

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
    # ── Digital Logic Circuits ──────────────────────────────────────────────────
    (["odd parity", "odd_parity"],              "Odd Parity Generator",    ["input_a", "input_b", "input_c", "xor1", "xnor2", "parity_output"], ["input_a -> xor1 -> xnor2 -> parity_output", "input_b -> xor1", "input_c -> xnor2"], "3-bit odd parity generator circuit"),
    (["even parity", "even_parity"],            "Even Parity Generator",   ["input_a", "input_b", "input_c", "xor1", "xor2", "parity_output"], ["input_a -> xor1 -> xor2 -> parity_output", "input_b -> xor1", "input_c -> xor2"], "3-bit even parity generator circuit"),
    (["half", "subtractor"],                   "Half Subtractor Circuit",  ["input_a", "input_b", "xor", "not", "and", "diff_output", "borrow_output"], ["input_a -> xor -> diff_output", "input_b -> xor", "input_a -> not -> and -> borrow_output", "input_b -> and"], "Half subtractor circuit computing difference and borrow"),
    (["full", "subtractor"],                   "Full Subtractor Circuit",  ["input_a", "input_b", "bin", "xor1", "xor2", "not1", "and1", "not2", "and2", "or", "diff_output", "borrow_output"], ["input_a -> xor1 -> xor2 -> diff_output", "input_b -> xor1", "bin -> xor2", "input_a -> not1 -> and1 -> or -> borrow_output", "input_b -> and1", "xor1 -> not2 -> and2 -> or", "bin -> and2"], "Full subtractor circuit with borrow-in"),
    (["half", "adder"],                         "Half Adder Circuit",       ["input_a", "input_b", "xor", "and", "sum_output", "carry_output"], ["input_a -> xor -> sum_output", "input_b -> xor", "input_a -> and -> carry_output", "input_b -> and"], "Half adder circuit computing sum and carry"),
    (["full", "adder"],                         "Full Adder Circuit",       ["input_a", "input_b", "cin", "xor1", "xor2", "and1", "and2", "or", "sum_output", "cout"], ["input_a -> xor1 -> xor2 -> sum_output", "input_b -> xor1", "cin -> xor2", "input_a -> and1 -> or -> cout", "input_b -> and1", "xor1 -> and2 -> or", "cin -> and2"], "Full adder circuit with carry-in"),
    (["multiplexer", "mux"],                    "2-to-1 Multiplexer",      ["input_a", "input_b", "sel", "not", "and1", "and2", "or", "output"], ["input_a -> and1 -> or -> output", "sel -> not -> and1", "input_b -> and2 -> or", "sel -> and2"], "2-to-1 multiplexer circuit"),
    (["demultiplexer", "demux"],                "1-to-2 Demultiplexer",    ["input_din", "sel", "not", "and1", "and2", "output_y0", "output_y1"], ["input_din -> and1 -> output_y0", "sel -> not -> and1", "input_din -> and2 -> output_y1", "sel -> and2"], "1-to-2 demultiplexer circuit"),
    (["decoder"],                               "2-to-4 Decoder",          ["input_a", "input_b", "not_a", "not_b", "and0", "and1", "and2", "and3", "y0", "y1", "y2", "y3"], ["input_a -> not_a -> and0 -> y0", "input_b -> not_b -> and0", "input_a -> and1 -> y1", "input_b -> not_b -> and1", "input_a -> not_a -> and2 -> y2", "input_b -> and2", "input_a -> and3 -> y3", "input_b -> and3"], "2-to-4 line decoder circuit"),
    (["comparator"],                            "1-Bit Comparator",        ["input_a", "input_b", "not_a", "not_b", "xnor", "and_gt", "and_lt", "eq_out", "gt_out", "lt_out"], ["input_a -> xnor -> eq_out", "input_b -> xnor", "input_a -> and_gt -> gt_out", "input_b -> not_b -> and_gt", "input_a -> not_a -> and_lt -> lt_out", "input_b -> and_lt"], "1-bit magnitude comparator"),
    (["xor", "xnor"],                           "XOR / XNOR Circuit",       ["input_a", "input_b", "xor", "output"],                ["input_a -> xor -> output", "input_b -> xor"], "2-input XOR gate circuit"),
    (["logic gate", "logic circuit"],           "Logic Gate Circuit",       ["input_a", "input_b", "and", "or", "output"],          ["input_a -> and -> or -> output", "input_b -> and", "input_b -> or"], "Combinational logic gate circuit"),
    # ── Analog / IC Circuits ─────────────────────────────────────────────────────
    (["led", "light"],                         "LED Circuit",              ["battery", "resistor", "led"],                          ["battery -> resistor -> led"],                        "Basic LED circuit with current-limiting resistor"),
    (["motor"],                                "Motor Circuit",            ["battery", "switch", "dc_motor"],                       ["battery -> switch -> dc_motor"],                     "Basic DC motor circuit with on/off switch"),
    (["buzzer"],                               "Buzzer Circuit",           ["battery", "resistor", "buzzer"],                       ["battery -> resistor -> buzzer"],                     "Buzzer circuit with resistor for sound output"),
    (["fan"],                                  "Fan Circuit",              ["battery", "switch", "capacitor", "dc_motor"],          ["battery -> switch -> capacitor -> dc_motor"],        "Fan circuit with capacitor for smooth startup"),
    (["temperature", "sensor"],                "Temperature Sensor",       ["battery", "thermistor", "resistor", "microcontroller"],["battery -> thermistor -> resistor -> microcontroller"],"Temperature sensing circuit using thermistor"),
    (["solar"],                                "Solar Charging Circuit",   ["solar_cell", "diode", "charge_controller", "battery"],["solar_cell -> diode -> charge_controller -> battery"],"Solar panel battery charging circuit"),
    (["555", "timer"],                         "555 Timer Circuit",        ["battery", "555_timer", "resistor", "capacitor", "led"],["battery -> 555_timer -> resistor -> capacitor -> led"],"555 timer astable multivibrator"),
    (["rc", "filter"],                         "RC Filter Circuit",        ["power_supply", "resistor", "capacitor"],              ["power_supply -> resistor -> capacitor -> ground"],    "RC low-pass filter circuit"),
]

def generate_with_rules(prompt: str) -> dict:
    p = prompt.lower()
    for keywords, name, components, connections, description in _RULES:
        if any(kw in p for kw in keywords):
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
ALLOWED_COMPONENTS = {
    "battery", "power_supply", "solar_cell",
    "resistor", "capacitor", "inductor", "potentiometer",
    "diode", "led", "zener_diode",
    "transistor", "npn_transistor", "pnp_transistor", "mosfet",
    "op_amp", "555_timer", "arduino", "microcontroller",
    "buzzer", "motor", "dc_motor", "speaker", "relay",
    "display", "lcd",
    "ldr", "thermistor", "photodiode", "button", "switch", "sensor",
    "ground", "fuse", "transformer",

    # Digital logic components used by rule-based generation/export
    "input_a", "input_b", "input_c", "input_din", "sel",
    "xor", "xnor", "and", "or", "not", "nand", "nor",
    "xor1", "xor2", "and1", "and2", "or1", "not1", "not2",
    "not_a", "not_b",
    "cin", "bin", "cout",
}

def _validate_llm_output(result: dict) -> bool:
    """Validate the structure and component names returned by the LLM."""

    if not isinstance(result, dict):
        return False

    required_keys = {"circuit_name", "components", "connections"}

    if not required_keys.issubset(result):
        return False

    if not isinstance(result["components"], list):
        return False

    if len(result["components"]) == 0:
        return False

    if not isinstance(result["connections"], list):
        return False

    if len(result["connections"]) == 0:
        return False

    if not all(isinstance(conn, str) for conn in result["connections"]):
        return False

    for comp in result["components"]:
        if not isinstance(comp, str):
            return False

        normalized = (
            comp.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if normalized not in ALLOWED_COMPONENTS:
            return False

    return True


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
    )

    raw = completion.choices[0].message.content.strip()

    # Strip accidental markdown fences
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw

    result = json.loads(raw)

    if not _validate_llm_output(result):
       logger.warning("LLM output failed schema validation")
       raise ValueError("LLM output failed schema validation")

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
