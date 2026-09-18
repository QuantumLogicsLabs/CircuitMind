"""
CircuitMind - Diagnose Module
diagnose/diagnose_module.py

Takes a circuit JSON as input, checks for common electrical issues,
and returns a structured result with warnings and errors.
"""

from typing import Any

from utils.component_resolver import (
    POWER_SOURCES,
    NEEDS_CURRENT_LIMIT,
    CURRENT_LIMITERS,
    LOAD_COMPONENTS,
    KNOWN_COMPONENTS,
    _normalize,
    _fuzzy_match,
)

# ── Constants ──────────────────────────────────────────────────────────────────


POSITIVE_KEYWORDS   = {"+", "pos", "positive", "anode", "vcc", "v+", "plus"}
GROUND_KEYWORDS     = {"ground", "gnd", "0v", "v-", "negative", "common"}
WIRE_LABELS         = {"wire", "node", "net", "junction", "point", "trace"}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _parse_connections(connections: list) -> list:
    parsed = []
    for conn in connections:
        if "->" in conn:
            nodes = [n.strip().lower() for n in conn.split("->")]
        elif "--" in conn:
            nodes = [n.strip().lower() for n in conn.split("--")]
        else:
            nodes = [conn.strip().lower()]
        parsed.append(nodes)
    return parsed


# ── Individual Checks ──────────────────────────────────────────────────────────

def check_power_source(components: list) -> str | None:
    if not any(c in POWER_SOURCES for c in components):
        return "Error: No power source found. Add a battery or power supply."
    return None


def check_current_limiting(components: list) -> list:
    warnings = []
    has_limiter = any(c in CURRENT_LIMITERS for c in components)
    for comp in NEEDS_CURRENT_LIMIT:
        if comp in components and not has_limiter:
            warnings.append(
                f"Warning: '{comp}' detected without a current-limiting component. "
                "Add a resistor to prevent burnout."
            )
    return warnings


def check_empty_connections(connections: list) -> str | None:
    if not connections:
        return "Error: No connections defined. Components are not linked together."
    return None


def check_short_circuit(connections: list) -> list:
    """BFS from each power source — flags paths that reach ground without a load."""
    errors = []

    def _is_power(node: str) -> bool:
        return _normalize(node) in POWER_SOURCES

    def _is_ground(node: str) -> bool:
        n = _normalize(node)
        return n in GROUND_KEYWORDS or n.startswith("gnd") or n.startswith("ground")

    def _is_load(node: str) -> bool:
        """Return True only for components that act as electrical loads."""
        return _normalize(node) in LOAD_COMPONENTS

    graph: dict = {}
    for path in _parse_connections(connections):
        for i in range(len(path) - 1):
            n1 = _normalize(path[i])
            n2 = _normalize(path[i + 1])
            graph.setdefault(n1, []).append(n2)
            graph.setdefault(n2, []).append(n1)

    for start_node in list(graph.keys()):
        if not _is_power(start_node):
            continue
        queue   = [(start_node, [start_node], False)]
        visited: set = set()
        while queue:
            current, path_so_far, passed_load = queue.pop(0)
            
            state = (current, passed_load)
            if state in visited:
                continue
            visited.add(state)
            
            for neighbor in graph.get(current, []):
                if neighbor in path_so_far:
                    continue
                
                if _is_ground(neighbor):
                    if not passed_load:
                        short_path = " -> ".join(path_so_far + [neighbor])
                        errors.append(
                            f"Error: Short circuit detected — power reaches ground with no load. "
                            f"Path: [{short_path}]"
                        )
                    continue
                queue.append((neighbor, path_so_far + [neighbor], passed_load or _is_load(neighbor)))

    return errors


def check_floating_components(components: list, connections: list) -> list:
    warnings     = []
    all_conn_text = " ".join(connections).lower()
    for comp in components:
        if comp in POWER_SOURCES:
            continue
        if _normalize(comp) in GROUND_KEYWORDS or "ground" in comp.lower() or "gnd" in comp.lower():
            continue
        if comp not in all_conn_text and comp.replace("_", " ") not in all_conn_text:
            warnings.append(
                f"Warning: '{comp}' is not found in any connection. "
                "It may be floating (disconnected)."
            )
    return warnings

def check_capacitor_polarity(components: list, connections: list) -> str | None:
    if "capacitor" not in components:
        return None

    capacitor_polarity = {
        "positive": False,
        "negative": False,
    }

    for path in _parse_connections(connections):
        for node in path:
            n = _normalize(node)

            # Only inspect capacitor nodes
            if "capacitor" not in n:
                continue

            if any(keyword in n for keyword in POSITIVE_KEYWORDS):
                capacitor_polarity["positive"] = True

            if (
                "-" in n
                or "negative" in n
                or "neg" in n
            ):
                capacitor_polarity["negative"] = True

    if not (
        capacitor_polarity["positive"]
        and capacitor_polarity["negative"]
    ):
        return (
            "Warning: Capacitor detected but polarity not specified. "
            "Ensure correct orientation for polarised capacitors."
        )

    return None


def check_ground_present(components: list, connections: list) -> str | None:
    all_text = " ".join(components + connections).lower()
    has_ground = any(kw in all_text for kw in GROUND_KEYWORDS)
    has_power  = any(c in POWER_SOURCES for c in components)
    if has_power and not has_ground:
        return "Info: No ground reference found. Consider adding a ground connection for a complete circuit."
    return None


# ── Main Entry Point ───────────────────────────────────────────────────────────

def diagnose_circuit(circuit: dict) -> dict:
    circuit_name = circuit.get("circuit_name", "Unnamed Circuit")
    components = circuit.get("components", [])
    connections = circuit.get("connections", [])

    issues = []

    # 1. Check for Power Source
    normalized_comps = [_normalize(c) for c in components]
    has_power = any(c in POWER_SOURCES for c in normalized_comps)
    if not has_power:
        issues.append({
            "severity": "error",
            "code": "NO_POWER_SOURCE",
            "message": "No power source found. Add a battery or power supply.",
            "suggestion": "Add a 'battery' or 'power_supply' component to the circuit."
        })

    # 2. Check for Floating Components
    floating_warnings = check_floating_components(components, connections)
    for warning_msg in floating_warnings:
        issues.append({
            "severity": "warning",
            "code": "FLOATING_COMPONENT",
            "message": warning_msg,
            "suggestion": "Ensure all terminals of this component are properly connected in the circuit paths."
        })

    # Backward compatibility: extract plain text strings for legacy frontends
    legacy_issues = [f"{i['severity'].capitalize()}: {i['message']}" for i in issues]

    # Calculate summary counts
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    info_count = sum(1 for i in issues if i["severity"] == "info")

    return {
        "circuit_name": circuit_name,
        "passed": error_count == 0,
        "issues": issues,
        "legacy_issues": legacy_issues,
        "summary": {
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
        }
    }