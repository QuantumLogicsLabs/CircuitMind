from alu.arithmetic_unit import (
    arithmetic_unit,
    build_arithmetic_unit_graph,
    simulate_arithmetic_graph,
    arithmetic_gate_json,
)


def test_addition_and_subtraction():
    assert arithmetic_unit(5, 3, 0) == (8, 0)
    assert arithmetic_unit(5, 3, 1) == (2, 1)
    assert arithmetic_unit(15, 1, 0) == (0, 1)
    assert arithmetic_unit(0, 1, 1) == (15, 0)


def test_all_four_bit_values():
    for a in range(16):
        for b in range(16):
            for sub in (0, 1):
                result, carry = arithmetic_unit(a, b, sub)
                expected = a + b if sub == 0 else a - b
                assert result == (expected & 15)
                assert carry == ((a + b) >> 4 if sub == 0 else int(a >= b))


def test_gate_graph_matches_reference():
    graph = build_arithmetic_unit_graph(4)
    for a in range(16):
        for b in range(16):
            for sub in (0, 1):
                inputs = {
                    **{f"A{i}": (a >> i) & 1 for i in range(4)},
                    **{f"B{i}": (b >> i) & 1 for i in range(4)},
                    "SUB": sub,
                }
                outputs = simulate_arithmetic_graph(graph, inputs)
                result = sum(outputs[f"SUM{i}"] << i for i in range(4))
                assert (result, outputs["COUT"]) == arithmetic_unit(a, b, sub)


def test_gate_json_structure():
    data = arithmetic_gate_json(4)
    assert data["gates"]
    assert data["wires"]
    assert data["outputCounter"] == 5
