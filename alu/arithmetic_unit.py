"""4-bit ALU arithmetic unit: addition and subtraction."""
from alu.logic_unit import simulate_graph, to_gate_json


def arithmetic_unit(a: int, b: int, subtract: int = 0, width: int = 4):
    """Return (result, carry_out). SUB=0 adds; SUB=1 subtracts using 2's complement."""
    if width < 1:
        raise ValueError("width must be >= 1")
    if subtract not in (0, 1):
        raise ValueError("subtract must be 0 or 1")

    mask = (1 << width) - 1
    a &= mask
    b &= mask
    adjusted_b = b ^ (mask if subtract else 0)
    total = a + adjusted_b + subtract
    return total & mask, (total >> width) & 1


def build_arithmetic_unit_graph(width: int = 4) -> dict:
    """Build a ripple-carry adder/subtractor using basic logic gates."""
    if width < 1:
        raise ValueError("width must be >= 1")

    gates, wires = [], []

    def gate(gid, gtype):
        gates.append({"id": gid, "type": gtype})

    def wire(src, dst):
        wires.append({"from": src, "to": dst})

    for i in range(width):
        gate(f"A{i}", "INPUT")
        gate(f"B{i}", "INPUT")
    gate("SUB", "INPUT")

    # Initial carry is SUB: 0 for addition, 1 for subtraction.
    gate("C0", "AND")
    wire("SUB", "C0")
    wire("SUB", "C0")

    for i in range(width):
        # B XOR SUB: invert B during subtraction.
        gate(f"BX{i}", "XOR")
        wire(f"B{i}", f"BX{i}")
        wire("SUB", f"BX{i}")

        # Propagate = A XOR adjusted B; Sum = Propagate XOR Carry.
        gate(f"P{i}", "XOR")
        wire(f"A{i}", f"P{i}")
        wire(f"BX{i}", f"P{i}")

        gate(f"S{i}", "XOR")
        wire(f"P{i}", f"S{i}")
        wire(f"C{i}", f"S{i}")

        gate(f"SUM{i}", "OUTPUT")
        wire(f"S{i}", f"SUM{i}")

        # Carry = (A AND adjusted B) OR (Propagate AND Carry).
        gate(f"G{i}", "AND")
        wire(f"A{i}", f"G{i}")
        wire(f"BX{i}", f"G{i}")

        gate(f"PC{i}", "AND")
        wire(f"P{i}", f"PC{i}")
        wire(f"C{i}", f"PC{i}")

        gate(f"C{i+1}", "OR")
        wire(f"G{i}", f"C{i+1}")
        wire(f"PC{i}", f"C{i+1}")

    gate("COUT", "OUTPUT")
    wire(f"C{width}", "COUT")

    return {
        "circuit_name": f"{width}-bit ALU Arithmetic Unit",
        "gates": gates,
        "wires": wires,
    }


def simulate_arithmetic_graph(graph: dict, inputs: dict) -> dict:
    """Simulate the graph and return its output pins."""
    return simulate_graph(graph, inputs)


def arithmetic_gate_json(width: int = 4) -> dict:
    """Export the arithmetic graph using the project's gate_json schema."""
    return to_gate_json(build_arithmetic_unit_graph(width))
