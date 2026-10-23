import itertools
from alu.logic_unit import logic_unit, build_logic_unit_graph, simulate_graph

WIDTH = 4


def test_behavioral_known_values():
    assert logic_unit(0b1100, 0b1010, 0b00) == 0b1000   # AND
    assert logic_unit(0b1100, 0b1010, 0b01) == 0b1110   # OR
    assert logic_unit(0b1100, 0b1010, 0b10) == 0b0110   # XOR
    assert logic_unit(0b1100, 0b1010, 0b11) == 0b0011   # NOT A


def test_gate_graph_matches_behavioral_model():
    graph = build_logic_unit_graph(WIDTH)
    for a, b, op in itertools.product(range(16), range(16), range(4)):
        ins = {"S0": op & 1, "S1": op >> 1}
        for i in range(WIDTH):
            ins[f"A{i}"] = (a >> i) & 1
            ins[f"B{i}"] = (b >> i) & 1
        out = simulate_graph(graph, ins)
        result = sum(out[f"Y{i}"] << i for i in range(WIDTH))
        assert result == logic_unit(a, b, op, WIDTH), (a, b, op)
from alu.logic_unit import to_gate_json


def test_gate_json_structure():
    gj = to_gate_json(build_logic_unit_graph(WIDTH))
    ids = [g["id"] for g in gj["gates"]]
    assert len(ids) == len(set(ids))                    # unique ids
    by_id = {g["id"]: g for g in gj["gates"]}
    for w in gj["wires"]:
        assert w["fromId"] in by_id and w["toId"] in by_id
        assert w["toIndex"] < by_id[w["toId"]]["inputs"]  # pin index is valid
    assert gj["inputCounter"] == 2 * WIDTH + 2          # A0-3, B0-3, S0, S1
    assert gj["outputCounter"] == WIDTH
    assert gj["gateIdCounter"] == len(gj["gates"])
    assert gj["wireIdCounter"] == len(gj["wires"])


def test_gate_json_behaves_like_original():
    gj = to_gate_json(build_logic_unit_graph(WIDTH))
    by_id = {g["id"]: g for g in gj["gates"]}
    feeds = {g["id"]: {} for g in gj["gates"]}
    for w in gj["wires"]:
        feeds[w["toId"]][w["toIndex"]] = w["fromId"]

    def run(a, b, op):
        vals = {"S0": op & 1, "S1": op >> 1}
        for i in range(WIDTH):
            vals[f"A{i}"] = (a >> i) & 1
            vals[f"B{i}"] = (b >> i) & 1
        cache = {}

        def ev(gid):
            if gid in cache:
                return cache[gid]
            g = by_id[gid]
            ins = [ev(feeds[gid][k]) for k in range(g["inputs"])]
            t = g["type"]
            r = (vals[g["label"]] if t == "INPUT" else ins[0] if t == "OUTPUT"
                 else 1 - ins[0] if t == "NOT" else int(all(ins)) if t == "AND"
                 else int(any(ins)) if t == "OR" else sum(ins) % 2)
            cache[gid] = r
            return r

        outs = {g["label"]: ev(g["id"]) for g in gj["gates"] if g["type"] == "OUTPUT"}
        return sum(outs[f"Y{i}"] << i for i in range(WIDTH))

    for a, b, op in itertools.product(range(16), range(16), range(4)):
        assert run(a, b, op) == logic_unit(a, b, op, WIDTH), (a, b, op)