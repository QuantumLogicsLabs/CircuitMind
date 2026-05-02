"""
CircuitMind - Diagnose Module
diagnose/diagnose_module.py

Takes a circuit JSON as input, checks for common issues,
and returns warning/error messages if something is wrong.

Consistent with explain_module.py:
  - Same POWER_SOURCES set
  - Same NEEDS_CURRENT_LIMIT set
  - Same CURRENT_LIMITERS set
  - Component names use underscore (op_amp, power_supply, etc.)
"""

from typing import Any


# ── Constants (mirror explain_module.py exactly) ─────────────────────────────

POWER_SOURCES       = {"battery", "power_supply", "solar_cell"}
NEEDS_CURRENT_LIMIT = {"led", "diode", "zener_diode"}
CURRENT_LIMITERS    = {"resistor", "potentiometer", "mosfet", "transistor",
                       "npn_transistor", "pnp_transistor"}

# Positive terminal keywords — flexible, not fragile
POSITIVE_KEYWORDS   = {"+", "pos", "positive", "anode", "vcc", "v+", "plus"}

# Ground / negative keywords for short circuit detection
GROUND_KEYWORDS     = {"ground", "gnd", "0v", "v-", "negative", "common"}


# ── Normalization Helper ──────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    """Lowercase, strip, replace spaces and hyphens with underscore."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _parse_connections(connections: list) -> list:
    """
    Parse connection strings into lists of nodes.
    Supports '->' and '--' separators.
    """
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


# ── Check 1: Power Source ─────────────────────────────────────────────────────

def check_power_source(components: list) -> str | None:
    if not any(c in POWER_SOURCES for c in components):
        return "Error: No power source found. Add a battery or power supply."
    return None


# ── Check 2: Current Limiting ─────────────────────────────────────────────────

def check_current_limiting(components: list) -> list:
    warnings = []
    has_limiter = any(c in CURRENT_LIMITERS for c in components)
    for comp in NEEDS_CURRENT_LIMIT:
        if comp in components and not has_limiter:
            warnings.append(
                f"Warning: '{comp}' detected without a current-limiting component. "
                f"Add a resistor to prevent burnout."
            )
    return warnings


# ── Check 3: Empty Connections ────────────────────────────────────────────────

def check_empty_connections(connections: list) -> str | None:
    if not connections:
        return "Error: No connections defined. Components are not linked together."
    return None


# ── Check 4: Short Circuit (improved — multi-node path aware) ─────────────────

def check_short_circuit(connections: list) -> list:
    """
    Detects short circuits across paths of ANY length.
    A short circuit = power source reaches ground with no load in between.

    Catches:
      battery -> ground                  (2 nodes)
      battery -> wire -> ground          (3 nodes)
      battery -> n1 -> n2 -> gnd        (4+ nodes)
    """
    errors = []

    def _is_power(node: str) -> bool:
        return _normalize(node) in POWER_SOURCES

    def _is_ground(node: str) -> bool:
        n = _normalize(node)
        return n in GROUND_KEYWORDS or n.startswith("gnd") or n.startswith("ground")

    # Labels that are pure wires/nets — not real load components
    WIRE_LABELS = {"wire", "node", "net", "junction", "point", "trace"}

    def _is_load(node: str) -> bool:
        n = _normalize(node)
        if n in POWER_SOURCES or n in GROUND_KEYWORDS:
            return False
        # Exclude pure wire/net labels (e.g. wire, node1, node2, net_a)
        for label in WIRE_LABELS:
            if n.startswith(label):
                return False
        return True

    # Build graph from connections
    graph: dict = {}
    for path in _parse_connections(connections):
        for i in range(len(path) - 1):
            src, dst = path[i], path[i + 1]
            graph.setdefault(src, []).append(dst)

    # BFS from each power source
    for start_node in list(graph.keys()):
        if not _is_power(start_node):
            continue

        queue   = [(start_node, [start_node], False)]
        visited = set()

        while queue:
            current, path_so_far, passed_load = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for neighbor in graph.get(current, []):
                if _is_ground(neighbor):
                    if not passed_load:
                        short_path = " -> ".join(path_so_far + [neighbor])
                        errors.append(
                            f"Error: Short circuit detected — power reaches ground with no load. "
                            f"Path: [{short_path}]"
                        )
                    continue
                next_passed_load = passed_load or _is_load(neighbor)
                queue.append((neighbor, path_so_far + [neighbor], next_passed_load))

    return errors


# ── Check 5: Floating Components ──────────────────────────────────────────────

def check_floating_components(components: list, connections: list) -> list:
    warnings     = []
    all_conn_text = " ".join(connections).lower()

    for comp in components:
        if comp in POWER_SOURCES:
            continue
        if comp not in all_conn_text and comp.replace("_", " ") not in all_conn_text:
            warnings.append(
                f"Warning: '{comp}' is not found in any connection. "
                f"It may be floating (disconnected)."
            )
    return warnings


# ── Check 6: Capacitor Polarity (improved — flexible keyword matching) ────────

def check_capacitor_polarity(components: list, connections: list) -> str | None:
    if "capacitor" not in components:
        return None

    all_conn_text = " ".join(connections).lower()
    polarity_specified = any(kw in all_conn_text for kw in POSITIVE_KEYWORDS)

    if not polarity_specified:
        return (
            "Info: Capacitor detected but no polarity indication found in connections. "
            "Ensure correct polarity if using an electrolytic capacitor."
        )
    return None


# ── Main Diagnose Function ────────────────────────────────────────────────────

def diagnose_circuit(circuit_json: dict) -> dict:
    """
    Main function — runs all checks on the circuit JSON.

    Args:
        circuit_json (dict): keys — circuit_name, components, connections

    Returns:
        dict: circuit_name, issues (list), passed (bool)
    """
    if not isinstance(circuit_json, dict):
        return {"circuit_name": "Unknown", "issues": ["Error: Input must be a JSON object."], "passed": False}

    circuit_name = circuit_json.get("circuit_name", "Unnamed Circuit")
    raw_comps    = circuit_json.get("components", [])
    raw_conns    = circuit_json.get("connections", [])

    components  = [_normalize(c) for c in raw_comps]
    connections = raw_conns

    issues = []

    r = check_power_source(components)
    if r: issues.append(r)

    issues.extend(check_current_limiting(components))

    r = check_empty_connections(connections)
    if r: issues.append(r)

    issues.extend(check_short_circuit(connections))
    issues.extend(check_floating_components(components, connections))

    r = check_capacitor_polarity(components, connections)
    if r: issues.append(r)

    return {"circuit_name": circuit_name, "issues": issues, "passed": len(issues) == 0}


def pretty_print(result: dict) -> None:
    print("\n" + "=" * 60)
    print(f"Diagnosing: {result['circuit_name']}")
    print("-" * 60)
    if result["passed"]:
        print("✅ No issues found. Circuit looks valid.")
    else:
        for issue in result["issues"]:
            prefix = "❌" if issue.startswith("Error") else "⚠️ " if issue.startswith("Warning") else "ℹ️ "
            print(f"{prefix} {issue}")


# ── Test Cases ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        {"circuit_name": "LED Without Resistor",     "components": ["battery", "led"],                          "connections": ["battery -> led"]},
        {"circuit_name": "Valid LED Circuit",         "components": ["battery", "resistor", "led"],              "connections": ["battery -> resistor -> led"]},
        {"circuit_name": "No Power Source",           "components": ["resistor", "led"],                         "connections": ["resistor -> led"]},
        {"circuit_name": "Short Circuit (2 nodes)",   "components": ["battery", "ground"],                       "connections": ["battery -> ground"]},
        {"circuit_name": "Short Circuit (3 nodes)",   "components": ["battery", "wire", "ground"],               "connections": ["battery -> wire -> ground"]},
        {"circuit_name": "Short Circuit (4 nodes)",   "components": ["battery", "node1", "node2", "gnd"],        "connections": ["battery -> node1 -> node2 -> gnd"]},
        {"circuit_name": "Empty Connections",         "components": ["battery", "resistor", "led"],              "connections": []},
        {"circuit_name": "Floating Motor",            "components": ["battery", "resistor", "led", "motor"],     "connections": ["battery -> resistor -> led"]},
        {"circuit_name": "Capacitor No Polarity",     "components": ["battery", "resistor", "capacitor"],        "connections": ["battery -> resistor -> capacitor"]},
        {"circuit_name": "Capacitor With Polarity",   "components": ["battery", "resistor", "capacitor"],        "connections": ["battery -> resistor -> capacitor_positive -> gnd"]},
        {"circuit_name": "Op-Amp Circuit",            "components": ["battery", "resistor", "op_amp"],           "connections": ["battery -> resistor -> op_amp"]},
    ]

    for test in tests:
        pretty_print(diagnose_circuit(test))
