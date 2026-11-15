"""Circuit summarization used to build the LLM prompt.

The previous implementation scanned every gate for both endpoints of every
wire (O(gates x wires)). It now indexes gates by id so large graphs stay cheap
while producing identical output.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hint.hint_module import _summarize_circuit


def test_empty_canvas_message():
    assert _summarize_circuit([], []) == "The canvas is empty — no gates placed yet."


def test_gates_only_show_no_wires():
    summary = _summarize_circuit([{"id": 1, "type": "INPUT", "label": "A"}], [])

    assert "- A: type=INPUT" in summary
    assert "(none)" in summary


def test_wires_render_with_labels():
    gates = [
        {"id": 1, "type": "INPUT", "label": "A"},
        {"id": 2, "type": "OUTPUT", "label": "Y"},
    ]
    wires = [{"fromId": 1, "toId": 2}]

    summary = _summarize_circuit(gates, wires)

    assert "- A -> Y" in summary


def test_wire_to_missing_gate_is_skipped():
    gates = [{"id": 1, "type": "INPUT", "label": "A"}]

    summary = _summarize_circuit(gates, [{"fromId": 1, "toId": 99}])

    assert "(none)" in summary


def test_duplicate_ids_use_first_gate():
    gates = [
        {"id": 1, "type": "INPUT", "label": "FIRST"},
        {"id": 1, "type": "INPUT", "label": "SECOND"},
        {"id": 2, "type": "OUTPUT", "label": "Y"},
    ]

    summary = _summarize_circuit(gates, [{"fromId": 1, "toId": 2}])

    assert "- FIRST -> Y" in summary
    assert "- SECOND -> Y" not in summary


def test_large_graph_is_summarized_completely():
    size = 2000
    gates = [{"id": i, "type": "AND", "label": f"G{i}"} for i in range(size)]
    wires = [{"fromId": i, "toId": i + 1} for i in range(size - 1)]

    summary = _summarize_circuit(gates, wires)

    assert summary.count("type=AND") == size
    assert "- G0 -> G1" in summary
    assert f"- G{size - 2} -> G{size - 1}" in summary
