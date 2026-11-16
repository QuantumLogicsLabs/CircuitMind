"""Decoder outputs (y0, y1, ...) must export as OUTPUT nodes, not gate types."""

from export.export_module import _classify_component, generate_gate_json


def _gates_by_label(result):
    return {g["label"]: g for g in result["gates"]}


def test_decoder_outputs_classified_as_output():
    for name in ("y0", "y1", "y2", "y3", "y10"):
        gate_type, inputs, has_output = _classify_component(name, 2, 10)
        assert gate_type == "OUTPUT", name
        assert inputs == 1
        assert has_output is False


def test_decoder_outputs_are_case_insensitive():
    assert _classify_component("Y2", 2, 10)[0] == "OUTPUT"


def test_non_numeric_y_names_are_not_outputs():
    assert _classify_component("y", 2, 10)[0] != "OUTPUT"
    assert _classify_component("ymux", 2, 10)[0] != "OUTPUT"


def test_existing_output_names_still_work():
    assert _classify_component("output_y0", 2, 10)[0] == "OUTPUT"
    assert _classify_component("led", 2, 10)[0] == "OUTPUT"


def test_decoder_gate_json_counts_outputs():
    result = generate_gate_json(
        "decoder",
        ["in_a", "in_b", "decoder", "y0", "y1", "y2", "y3"],
        ["in_a -> decoder", "in_b -> decoder", "decoder -> y0"],
    )
    gates = _gates_by_label(result)
    for label in ("Y0", "Y1", "Y2", "Y3"):
        assert gates[label]["type"] == "OUTPUT"
    assert result["outputCounter"] == 4
    assert result["inputCounter"] == 2


def test_decoder_outputs_share_last_column():
    result = generate_gate_json(
        "decoder",
        ["in_a", "in_b", "decoder", "y0", "y1", "y2", "y3"],
        ["in_a -> decoder", "in_b -> decoder"],
    )
    gates = _gates_by_label(result)
    xs = {gates[label]["x"] for label in ("Y0", "Y1", "Y2", "Y3")}
    assert len(xs) == 1
    assert gates["IN_A"]["x"] < gates["DECODER"]["x"] < xs.pop()
