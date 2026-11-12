"""
CircuitMind - Explain Module
explain/explain_module.py

Takes a circuit JSON and returns a human-readable explanation,
component details, current flow description, and any warnings.
"""

from typing import Any

from utils.component_resolver import (
    COMPONENT_DB,
    POWER_SOURCES,
    NEEDS_CURRENT_LIMIT,
    CURRENT_LIMITERS,
    _normalize,
    _fuzzy_match,
)

# ── Explain-specific constants ─────────────────────────────────────────────────

LED_OUTPUTS    = {"led"}
MOTOR_OUTPUTS  = {"motor", "dc_motor"}
BUZZER_OUTPUTS = {"buzzer"}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _parse_flow(connections: list[str]) -> str:
    parts = []
    for conn in connections:
        sep = "->" if "->" in conn else "--"
        nodes = [n.strip() for n in conn.split(sep)]
        
        if len(nodes) == 1:
            parts.append(f"The {nodes[0]} stands alone with no connections.")
        else:
            arrow_chain = " → ".join(nodes)
            parts.append(f"Current flows from the {arrow_chain}.")

            # Add effect note
            last = _normalize(nodes[-1]) if nodes else ""
            if last in LED_OUTPUTS:
                parts[-1] += " This causes the LED to emit light."
            elif last in MOTOR_OUTPUTS:
                parts[-1] += " This causes the motor to spin."
            elif last in BUZZER_OUTPUTS:
                parts[-1] += " This causes the buzzer to produce sound."

    return " ".join(parts)


def _check_warnings(components: list[str], unknown: list[str]) -> list[str]:
    warnings = []
    if not any(c in POWER_SOURCES for c in components):
        warnings.append("No power source detected. The circuit cannot operate without one.")
    has_limiter = any(c in CURRENT_LIMITERS for c in components)
    for comp in NEEDS_CURRENT_LIMIT:
        if comp in components and not has_limiter:
            warnings.append(f"'{comp}' detected without a current-limiting component. Add a resistor to prevent burnout.")
    for u in unknown:
        warnings.append(f"Unknown component '{u}' — not in the knowledge base. Check the component name.")
    return warnings


# ── Main Entry Point ───────────────────────────────────────────────────────────

def _invalid_result(message: str) -> dict[str, Any]:
    """Return a well-formed empty result carrying a validation error."""
    return {
        "explanation":       "",
        "component_details": [],
        "flow_description":  "",
        "warnings":          [],
        "error":             message,
    }


def _as_string_list(value, field: str) -> tuple[list[str] | None, str]:
    """Return (list, "") when value is a list of strings, else (None, error)."""
    if value is None:
        return [], ""
    if not isinstance(value, (list, tuple)):
        return None, f"'{field}' must be a list of strings."
    if not all(isinstance(item, str) for item in value):
        return None, f"Every entry in '{field}' must be a string."
    return list(value), ""


def explain_circuit(circuit_json: dict[str, Any]) -> dict[str, Any]:
    """
    Input:  circuit JSON with 'components' and 'connections' lists
    Output: { explanation, component_details, flow_description, warnings }
            plus 'error' when the input shape is invalid
    """
    if not isinstance(circuit_json, dict):
        return _invalid_result("circuit_json must be a JSON object.")

    raw_components, error = _as_string_list(circuit_json.get("components"), "components")
    if error:
        return _invalid_result(error)

    connections, error = _as_string_list(circuit_json.get("connections"), "connections")
    if error:
        return _invalid_result(error)

    components        = [_fuzzy_match(_normalize(c)) for c in raw_components]
    component_details = []
    unknown_components: list[str] = []

    for comp in components:
        if comp in COMPONENT_DB:
            info = COMPONENT_DB[comp]
            component_details.append({
                "name":        comp,
                "role":        info["role"],
                "description": info["description"],
            })
        else:
            unknown_components.append(comp)
            component_details.append({
                "name":        comp,
                "role":        "unknown",
                "description": "component not in knowledge base",
            })

    if not components:
        explanation = "No components provided. Cannot generate an explanation."
    else:
        parts = []
        for detail in component_details:
            parts.append(f"a {detail['name']} ({detail['role']}) that {detail['description']}")

        if len(parts) == 1:
            explanation = "This circuit uses " + parts[0] + "."
        elif len(parts) == 2:
            explanation = "This circuit uses " + parts[0] + ", and " + parts[1] + "."
        else:
            explanation = "This circuit uses " + ", ".join(parts[:-1]) + ", and " + parts[-1] + "."

    flow_description = _parse_flow(connections) if connections else ""

    if flow_description:
        explanation = explanation.rstrip(".") + ". " + flow_description

    return {
        "explanation":       explanation,
        "component_details": component_details,
        "flow_description":  flow_description,
        "warnings":          _check_warnings(components, unknown_components),
    }


def explain_circuits_batch(circuits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [explain_circuit(c) for c in circuits]