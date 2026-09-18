"""
CircuitMind - utils Module
utils/component_resolver.py

Shared component definitions and helper functions used by
both the Explain and Diagnose modules.
"""

COMPONENT_DB: dict[str, dict] = {
    # Power
    "battery":       {"role": "power source",      "description": "provides electrical energy to the circuit"},
    "power_supply":  {"role": "power source",       "description": "supplies regulated DC voltage to the circuit"},
    "solar_cell":    {"role": "power source",       "description": "converts sunlight into electrical energy"},

    # Passive
    "resistor":      {"role": "current limiter",    "description": "limits and controls the flow of current"},
    "capacitor":     {"role": "energy storage",     "description": "stores and releases electrical energy"},
    "inductor":      {"role": "energy storage",     "description": "stores energy in a magnetic field and opposes current change"},
    "potentiometer": {"role": "variable resistor",  "description": "provides adjustable resistance"},

    # Diodes
    "diode":         {"role": "one-way valve",      "description": "allows current to flow in only one direction"},
    "led":           {"role": "light emitter",      "description": "emits light when current flows through it"},
    "zener_diode":   {"role": "voltage regulator",  "description": "maintains a stable reference voltage"},

    # Transistors
    "transistor":        {"role": "switch/amplifier",  "description": "amplifies signals or acts as an electronic switch"},
    "npn_transistor":    {"role": "NPN switch",         "description": "switches on when base is driven high"},
    "pnp_transistor":    {"role": "PNP switch",         "description": "switches on when base is driven low"},
    "mosfet":            {"role": "FET switch",         "description": "voltage-controlled switch with very low gate current"},

    # ICs
    "op_amp":            {"role": "amplifier",          "description": "amplifies the difference between two input voltages"},
    "555_timer":         {"role": "timer IC",            "description": "generates timing pulses and oscillations"},
    "arduino":           {"role": "microcontroller",    "description": "runs code to control other components"},
    "microcontroller":   {"role": "microcontroller",    "description": "processes data and controls the circuit"},
    "charge_controller": {"role": "charge regulator",    "description": "regulates charging voltage and current to protect the battery"},

    # Output devices
    "buzzer":    {"role": "audio output",    "description": "produces sound when current flows through it"},
    "motor":     {"role": "mechanical output","description": "converts electrical energy into rotational motion"},
    "dc_motor":  {"role": "mechanical output","description": "converts electrical energy into rotational motion"},
    "speaker":   {"role": "audio output",    "description": "converts electrical signals into sound waves"},
    "relay":     {"role": "electromagnetic switch","description": "uses a small current to control a larger circuit"},
    "display":   {"role": "visual output",   "description": "shows numerical or graphical information"},
    "lcd":       {"role": "visual output",   "description": "displays text or graphics using liquid crystals"},

    # Sensors
    "ldr":          {"role": "light sensor",     "description": "changes resistance based on light intensity"},
    "thermistor":   {"role": "temperature sensor","description": "changes resistance based on temperature"},
    "photodiode":   {"role": "light sensor",      "description": "generates current proportional to light intensity"},
    "button":       {"role": "input switch",      "description": "opens or closes a circuit when pressed"},
    "switch":       {"role": "circuit switch",    "description": "manually opens or closes a circuit"},
    "sensor":       {"role": "sensor",            "description": "detects physical quantities and converts them to electrical signals"},

    # Other
    "ground":       {"role": "reference",         "description": "provides the zero-voltage reference point"},
    "fuse":         {"role": "protection",        "description": "breaks the circuit if current exceeds a safe level"},
    "transformer":  {"role": "voltage converter", "description": "steps voltage up or down using electromagnetic induction"},

    # Digital Logic Gates (Task B3)
    "and":     {"role": "logic gate",  "description": "outputs HIGH only when all inputs are HIGH"},
    "or":      {"role": "logic gate",  "description": "outputs HIGH when at least one input is HIGH"},
    "not":     {"role": "logic gate",  "description": "inverts the input signal (HIGH->LOW, LOW->HIGH)"},
    "nand":    {"role": "logic gate",  "description": "outputs LOW only when all inputs are HIGH (inverted AND)"},
    "nor":     {"role": "logic gate",  "description": "outputs LOW when any input is HIGH (inverted OR)"},
    "xor":     {"role": "logic gate",  "description": "outputs HIGH when an odd number of inputs are HIGH"},
    "xnor":    {"role": "logic gate",  "description": "outputs HIGH when inputs are the same (inverted XOR)"},
    "buffer":  {"role": "logic gate",  "description": "passes the input signal through unchanged (used for signal buffering)"},

    # Logic I/O (Task B3)
    "input_a":       {"role": "input signal",  "description": "provides a digital input signal (A)"},
    "input_b":       {"role": "input signal",  "description": "provides a digital input signal (B)"},
    "input_c":       {"role": "input signal",  "description": "provides a digital input signal (C)"},
    "sum_output":    {"role": "output signal", "description": "carries the sum result of an arithmetic operation"},
    "carry_output":  {"role": "output signal", "description": "carries the carry result of an arithmetic operation"},
}

POWER_SOURCES       = {"battery", "power_supply", "solar_cell"}
NEEDS_CURRENT_LIMIT = {"led", "diode", "zener_diode"}
CURRENT_LIMITERS    = {"resistor", "potentiometer", "mosfet", "transistor",
                       "npn_transistor", "pnp_transistor"}

# Components that act as electrical loads.
# These interrupt a direct power-to-ground short circuit because they
# consume or store electrical energy rather than acting as a wire.
LOAD_COMPONENTS = {
    "resistor",
    "potentiometer",
    "capacitor",
    "inductor",
    "led",
    "diode",
    "zener_diode",
    "motor",
    "dc_motor",
    "speaker",
    "buzzer",
    "relay",
    "display",
    "lcd",
    "transformer",
    "op_amp",
    "555_timer",
    "arduino",
    "microcontroller",
    "charge_controller",
}

KNOWN_COMPONENTS = set(COMPONENT_DB.keys())

def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


# Expanded Alias Dictionary (Task B4)
_ALIASES = {
    # Power
    "solar_panel": "solar_cell",
    "9v_battery": "battery",
    "cell": "battery",
    "voltage_source": "power_supply",
    "vcc": "power_supply",
    "power": "power_supply",
    # Passive
    "variable_resistor": "potentiometer",
    "pot": "potentiometer",
    "rheostat": "potentiometer",
    "coil": "inductor",
    "cap": "capacitor",
    # Diodes
    "light_emitting_diode": "led",
    "zener": "zener_diode",
    # Transistors
    "bjt": "transistor",
    "npn": "npn_transistor",
    "pnp": "pnp_transistor",
    "fet": "mosfet",
    "jfet": "mosfet",
    # ICs
    "timer": "555_timer",
    "ne555": "555_timer",
    "opamp": "op_amp",
    "operational_amplifier": "op_amp",
    "mcu": "microcontroller",
    "pic": "microcontroller",
    "esp32": "microcontroller",
    # Output
    "lamp": "led",
    "light": "led",
    "beeper": "buzzer",
    "horn": "buzzer",
    # Sensors
    "photoresistor": "ldr",
    "light_dependent_resistor": "ldr",
    "ntc": "thermistor",
    "temp_sensor": "thermistor",
    "push_button": "button",
    "momentary_switch": "button",
    # Logic gates
    "and_gate": "and",
    "or_gate": "or",
    "not_gate": "not",
    "xor_gate": "xor",
    "nand_gate": "nand",
    "nor_gate": "nor",
    "xnor_gate": "xnor",
    "inverter": "not",
}


def _fuzzy_match(name: str) -> str:
    """Resolve a component name to its canonical COMPONENT_DB key."""
    if name in COMPONENT_DB:
        return name
    if name in _ALIASES:
        return _ALIASES[name]
    # Substring: find canonical names contained within the input
    matches = [canon for canon in COMPONENT_DB if canon in name]
    if matches:
        return max(matches, key=len)  # longest match = most specific
    return name