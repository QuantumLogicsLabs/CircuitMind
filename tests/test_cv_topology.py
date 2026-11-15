"""Tests for CV terminal layout and proximity topology extraction.

The YOLO model is stubbed, so these run without ultralytics or opencv.
"""

import math

from cv_module.topology_extraction import (
    DEFAULT_TERMINALS,
    CircuitTopologyExtractor,
    TERMINAL_SPECS,
    _terminal_coords,
    _terminals_for,
)


class _Tensor:
    """Minimal stand-in for a torch tensor element."""

    def __init__(self, values):
        self._values = values

    def __getitem__(self, index):
        return self._values[index]

    def tolist(self):
        return list(self._values)


class _Box:
    def __init__(self, class_id, cx, cy):
        self.cls = _Tensor([class_id])
        self.xywhn = _Tensor([_Tensor([cx, cy, 0.1, 0.1])])


class _Results:
    def __init__(self, boxes, names):
        self.boxes = boxes
        self.names = names


def test_known_component_terminals_are_type_specific():
    assert _terminals_for("LED") == ["anode", "cathode"]
    assert _terminals_for("Battery") == ["positive", "negative"]
    assert _terminals_for("transistor") == ["base", "collector", "emitter"]


def test_unknown_component_gets_the_two_pin_fallback():
    assert _terminals_for("flux_capacitor") == DEFAULT_TERMINALS


def test_terminal_specs_are_not_lists_of_one():
    assert all(len(pins) >= 2 for pins in TERMINAL_SPECS.values())


def test_two_pin_layout_uses_left_and_right_edges():
    coords = _terminal_coords(10, 20, 50, 60, ["anode", "cathode"])
    assert [t["pin"] for t in coords] == ["anode", "cathode"]
    assert coords[0]["coord"] == [10, 40]
    assert coords[1]["coord"] == [50, 40]


def test_three_pin_layout_splits_left_and_right_edges():
    coords = _terminal_coords(0, 0, 100, 90, ["base", "collector", "emitter"])
    left = [t for t in coords if t["coord"][0] == 0]
    right = [t for t in coords if t["coord"][0] == 100]
    assert len(left) == 2
    assert len(right) == 1
    assert [t["pin"] for t in coords] == ["base", "collector", "emitter"]


def test_all_terminal_coordinates_stay_inside_the_box():
    coords = _terminal_coords(5, 10, 105, 210, ["pin_1", "pin_2", "pin_3", "pin_4"])
    for terminal in coords:
        x, y = terminal["coord"]
        assert 5 <= x <= 105
        assert 10 <= y <= 210


def test_empty_results_produce_no_topology():
    extractor = CircuitTopologyExtractor()
    assert extractor.extract_topology(None) == ([], [])
    assert extractor.extract_topology(_Results([], {0: "resistor"})) == ([], [])


def test_nearby_components_are_connected_once():
    names = {0: "battery", 1: "resistor"}
    results = _Results([_Box(0, 0.10, 0.10), _Box(1, 0.20, 0.10)], names)

    components, connections = CircuitTopologyExtractor(
        connection_threshold=0.25
    ).extract_topology(results)

    assert [c.id for c in components] == ["battery_1", "resistor_2"]
    assert [(c.from_component, c.to_component) for c in connections] == [
        ("battery_1", "resistor_2")
    ]


def test_distant_components_are_not_connected():
    names = {0: "battery", 1: "led"}
    results = _Results([_Box(0, 0.05, 0.05), _Box(1, 0.95, 0.95)], names)

    _, connections = CircuitTopologyExtractor(
        connection_threshold=0.25
    ).extract_topology(results)

    assert connections == []


def test_threshold_compares_normalized_distance():
    names = {0: "a", 1: "b"}
    results = _Results([_Box(0, 0.0, 0.0), _Box(1, 0.3, 0.4)], names)

    _, just_below = CircuitTopologyExtractor(0.51).extract_topology(results)
    _, just_above = CircuitTopologyExtractor(0.49).extract_topology(results)

    assert math.isclose(0.3 ** 2 + 0.4 ** 2, 0.25)
    assert len(just_below) == 1
    assert just_above == []
