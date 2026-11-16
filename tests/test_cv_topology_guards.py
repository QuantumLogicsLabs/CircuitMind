"""Detector results with unknown class ids or broken boxes must not crash extraction."""

import pytest

from cv_module.topology_extraction import (
    CircuitTopologyExtractor,
    _class_name_for_box,
    _components_from_boxes,
)


class Tensor:
    def __init__(self, values):
        self.values = list(values)

    def __getitem__(self, index):
        return self.values[index]

    def tolist(self):
        return list(self.values)


class Box:
    def __init__(self, cls=0, xywhn=(0.5, 0.5, 0.1, 0.1), xyxy=(0, 0, 10, 10), broken=False):
        self.cls = Tensor([cls] if cls is not None else [])
        self._broken = broken
        if not broken:
            self.xywhn = Tensor([Tensor(xywhn)])
            self.xyxy = Tensor([Tensor(xyxy)])


class Results:
    def __init__(self, boxes, names):
        self.boxes = boxes
        self.names = names


def test_unknown_class_id_is_skipped():
    results = Results([Box(cls=0), Box(cls=99)], ["battery", "resistor"])
    components, _ = CircuitTopologyExtractor().extract_topology(results)
    assert [c.type for c in components] == ["battery"]


def test_box_without_class_is_skipped():
    results = Results([Box(cls=None), Box(cls=1)], ["battery", "resistor"])
    components, _ = CircuitTopologyExtractor().extract_topology(results)
    assert [c.type for c in components] == ["resistor"]


def test_malformed_geometry_is_skipped():
    results = Results([Box(cls=0, xywhn=()), Box(cls=1)], ["battery", "resistor"])
    components, _ = CircuitTopologyExtractor().extract_topology(results)
    assert [c.type for c in components] == ["resistor"]


def test_valid_detections_keep_original_index_in_id():
    results = Results([Box(cls=99), Box(cls=0)], ["battery", "resistor"])
    components, _ = CircuitTopologyExtractor().extract_topology(results)
    assert [c.id for c in components] == ["battery_2"]


def test_names_mapping_supports_dicts():
    results = Results([Box(cls=3)], {3: "led"})
    components, _ = CircuitTopologyExtractor().extract_topology(results)
    assert [c.type for c in components] == ["led"]


def test_no_boxes_returns_empty_topology():
    components, connections = CircuitTopologyExtractor().extract_topology(Results([], {}))
    assert components == []
    assert connections == []


def test_class_name_helper_returns_none_for_missing_attributes():
    assert _class_name_for_box(["a"], object()) is None


def test_components_from_boxes_guards_each_box():
    boxes = [Box(cls=0), Box(cls=99), Box(cls=1, broken=True), Box(cls=2, xyxy=(5, 5))]
    components = _components_from_boxes(boxes, ["battery", "resistor", "led"])
    assert [c["id"] for c in components] == ["BATTERY_1"]
    assert components[0]["terminals"][0]["pin"] == "positive"


def test_components_from_boxes_empty_when_all_invalid():
    assert _components_from_boxes([Box(cls=99), Box(cls=None)], ["battery"]) == []
