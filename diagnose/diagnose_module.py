"""
CircuitMind - Diagnose Module
diagnose/diagnose_module.py

Takes a circuit JSON as input, checks for common issues,
and returns warning/error messages if something is wrong.
"""

import json


# ── Rule Definitions ────────────────────────────────────────────────────────

POWER_SOURCES = {"battery", "power supply", "supply", "voltage source", "vcc", "v+"}

CURRENT_LIMITING_COMPONENTS = {"resistor"}

COMPONENTS_NEEDING_CURRENT_LIMIT = {"led", "diode"}

COMPONENTS_NEEDING_POWER = {"led", "motor", "resistor", "capacitor", "transistor",
                             "relay", "op-amp", "inductor"}


# ── Individual Check Functions ───────────────────────────────────────────────

def check_power_source(components: list) -> str | None:
    """Check if circuit has at least one power source."""
    normalized = [c.strip().lower() for c in components]
    for comp in normalized:
        if comp in POWER_SOURCES:
            return None  # power source found — no issue
    return "Error: No power source found. Add a battery or power supply."


def check_led_resistor(components: list) -> str | None:
    """Check if LED is present without a current-limiting resistor."""
    normalized = [c.strip().lower() for c in components]
    has_led       = any(c in COMPONENTS_NEEDING_CURRENT_LIMIT for c in normalized)
    has_resistor  = any(c in CURRENT_LIMITING_COMPONENTS for c in normalized)

    if has_led and not has_resistor:
        return "Warning: LED found without a current-limiting resistor. This may damage the LED."
    return None


def check_empty_connections(connections: list) -> str | None:
    """Check if connections list is empty."""
    if not connections:
        return "Error: No connections defined. Components are not linked together."
    return None


def check_floating_components(components: list, connections: list) -> list:
    """
    Check if any component is not mentioned in any connection.
    A component not in any connection is 'floating' (disconnected).
    """
    warnings = []
    # Flatten all connection strings into one big string for lookup
    all_connections_text = " ".join(connections).lower()

    for component in components:
        comp_lower = component.strip().lower()
        # Skip power sources — they are often implied
        if comp_lower in POWER_SOURCES:
            continue
        if comp_lower not in all_connections_text:
            warnings.append(
                f"Warning: '{component}' is not found in any connection. "
                f"It may be disconnected (floating)."
            )
    return warnings


def check_short_circuit(connections: list) -> str | None:
    """
    Basic short circuit check:
    If battery/supply connects directly to ground with no component in between.
    """
    for connection in connections:
        parts = [p.strip().lower() for p in connection.split("->")]
        if len(parts) == 2:
            if parts[0] in POWER_SOURCES and parts[1] in {"ground", "gnd"}:
                return "Error: Direct connection from power source to ground detected. This is a short circuit."
    return None


def check_motor_no_power(components: list) -> str | None:
    """Check if motor is present but no power source exists."""
    normalized = [c.strip().lower() for c in components]
    has_motor  = "motor" in normalized
    has_power  = any(c in POWER_SOURCES for c in normalized)

    if has_motor and not has_power:
        return "Warning: Motor found but no power source detected."
    return None


def check_capacitor_polarity(components: list, connections: list) -> str | None:
    """
    Warn if capacitor is present but no polarity hint (+/-) is in connections.
    Basic check for electrolytic capacitor misuse.
    """
    normalized = [c.strip().lower() for c in components]
    if "capacitor" in normalized:
        all_text = " ".join(connections).lower()
        if "c1.+" not in all_text and "cap+" not in all_text:
            return (
                "Info: Capacitor detected. Ensure correct polarity "
                "if using an electrolytic capacitor."
            )
    return None


# ── Main Diagnose Function ───────────────────────────────────────────────────

def diagnose_circuit(circuit_json: dict) -> list:
    """
    Main function — runs all checks on the circuit JSON.

    Args:
        circuit_json (dict): Circuit data with keys:
            - circuit_name (str, optional)
            - components   (list of str)
            - connections  (list of str)

    Returns:
        list: A list of warning/error strings.
              Empty list means no issues found.
    """
    components  = circuit_json.get("components", [])
    connections = circuit_json.get("connections", [])
    issues      = []

    # Run all checks
    checks = [
        check_power_source(components),
        check_led_resistor(components),
        check_empty_connections(connections),
        check_short_circuit(connections),
        check_motor_no_power(components),
        check_capacitor_polarity(components, connections),
    ]

    # Add single-result checks
    for result in checks:
        if result is not None:
            issues.append(result)

    # Add floating component warnings (returns a list)
    issues.extend(check_floating_components(components, connections))

    return issues


def run_diagnosis(circuit_json: dict) -> str:
    """
    Wrapper that returns a formatted string output.
    Convenient for printing results.
    """
    name   = circuit_json.get("circuit_name", "Circuit")
    issues = diagnose_circuit(circuit_json)

    print(f"Diagnosing: {name}")
    print("-" * 50)

    if not issues:
        result = "✅ No issues found. Circuit looks valid."
    else:
        result = "\n".join(issues)

    print(result)
    print()
    return result


# ── Test Cases ───────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Test 1 — From task description: LED without resistor
    test1 = {
        "circuit_name": "LED Without Resistor",
        "components": ["battery", "led"],
        "connections": ["battery -> led"]
    }

    # Test 2 — Valid LED circuit
    test2 = {
        "circuit_name": "Valid LED Circuit",
        "components": ["battery", "resistor", "led"],
        "connections": ["battery -> resistor -> led"]
    }

    # Test 3 — No power source
    test3 = {
        "circuit_name": "No Power Source",
        "components": ["resistor", "led"],
        "connections": ["resistor -> led"]
    }

    # Test 4 — Short circuit
    test4 = {
        "circuit_name": "Short Circuit",
        "components": ["battery", "ground"],
        "connections": ["battery -> ground"]
    }

    # Test 5 — No connections at all
    test5 = {
        "circuit_name": "Empty Connections",
        "components": ["battery", "resistor", "led"],
        "connections": []
    }

    # Test 6 — Floating component
    test6 = {
        "circuit_name": "Floating Motor",
        "components": ["battery", "resistor", "led", "motor"],
        "connections": ["battery -> resistor -> led"]
    }

    for test in [test1, test2, test3, test4, test5, test6]:
        run_diagnosis(test)
