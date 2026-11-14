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
# Graph nodes are normalized ("v-" -> "v_"), so match against normalized
# ground labels instead of the raw keyword spellings.
_NORMALIZED_GROUND  = {_normalize(kw) for kw in GROUND_KEYWORDS}
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
        # Resolve aliases such as vcc/vdd so supply-rail labels count as power.
        return _fuzzy_match(_normalize(node)) in POWER_SOURCES

    def _is_ground(node: str) -> bool:
        n = _normalize(node)
        return (
            n in _NORMALIZED_GROUND
            or n.startswith("gnd")
            or n.startswith("ground")
        )

    def _is_load(node: str) -> bool:
        """Return True only for components that act as electrical loads."""
        # Resolve aliases such as light/lamp so they count as loads too.
        return _fuzzy_match(_normalize(node)) in LOAD_COMPONENTS

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
    warnings = []
    
    # Build a set of all nodes that appear in connections
    connected_nodes = set()
    for path in _parse_connections(connections):
        for node in path:
            connected_nodes.add(_normalize(node))
    
    for comp in components:
        normalized = _normalize(comp)
        if normalized in POWER_SOURCES:
            continue
        if normalized in GROUND_KEYWORDS or "ground" in normalized or "gnd" in normalized:
            continue
        
        # Check if this component appears in ANY connection node
        is_connected = any(
            normalized == node or normalized in node or node in normalized
            for node in connected_nodes
        )
        
        if not is_connected:
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

_PREFIXES = ("Error: ", "Warning: ", "Info: ")


def _strip_prefix(message: str) -> str:
    for prefix in _PREFIXES:
        if message.startswith(prefix):
            return message[len(prefix):]
    return message


def _make_issue(severity: str, code: str, message: str, suggestion: str) -> dict:
    return {
        "severity":   severity,
        "code":       code,
        "message":    _strip_prefix(message),
        "suggestion": suggestion,
    }


def diagnose_circuit(circuit: dict) -> dict:
    circuit_name = circuit.get("circuit_name", "Unnamed Circuit")
    components = [_fuzzy_match(_normalize(c)) for c in circuit.get("components", [])]
    connections = circuit.get("connections", [])

    issues = []

    if (msg := check_power_source(components)):
        issues.append(_make_issue(
            "error", "NO_POWER_SOURCE", msg,
            "Add a 'battery' or 'power_supply' component to the circuit.",
        ))

    if (msg := check_empty_connections(connections)):
        issues.append(_make_issue(
            "error", "NO_CONNECTIONS", msg,
            "Add at least one connection, e.g. 'battery -> resistor -> led'.",
        ))

    for msg in check_current_limiting(components):
        issues.append(_make_issue(
            "warning", "MISSING_CURRENT_LIMITER", msg,
            "Add a resistor in series with the component.",
        ))

    for msg in check_short_circuit(connections):
        issues.append(_make_issue(
            "error", "SHORT_CIRCUIT", msg,
            "Place a load (resistor, LED, motor, ...) between power and ground.",
        ))

    for msg in check_floating_components(components, connections):
        issues.append(_make_issue(
            "warning", "FLOATING_COMPONENT", msg,
            "Ensure all terminals of this component are properly connected in the circuit paths.",
        ))

    if (msg := check_capacitor_polarity(components, connections)):
        issues.append(_make_issue(
            "warning", "CAPACITOR_POLARITY", msg,
            "Label capacitor terminals (e.g. 'capacitor+' / 'capacitor-') for polarised parts.",
        ))

    if (msg := check_ground_present(components, connections)):
        issues.append(_make_issue(
            "info", "NO_GROUND", msg,
            "Add a ground connection for a complete circuit.",
        ))

    # Backward compatibility: extract plain text strings for legacy frontends
    legacy_issues = [f"{i['severity'].capitalize()}: {i['message']}" for i in issues]

    # Calculate summary counts
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    info_count = sum(1 for i in issues if i["severity"] == "info")

    return {
        "circuit_name": circuit_name,
        # Preserve the pre-refactor contract: warnings fail a diagnosis too.
        "passed": error_count == 0 and warning_count == 0,
        "issues": issues,
        "legacy_issues": legacy_issues,
        "summary": {
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
        }
    }