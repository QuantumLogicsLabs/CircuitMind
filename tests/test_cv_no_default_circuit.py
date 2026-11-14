"""Regression tests: CV extraction must not invent a fallback circuit.

An image with no detections used to produce a fake battery/resistor/LED
circuit, which then flowed into diagnose/explain/export as if it were
real. Empty detections should stay empty.
"""

import sys
import types

import cv_module.topology_extraction as topo


class _EmptyResults:
    boxes: list = []
    names: dict = {}


class _FakeYOLO:
    def __init__(self, weights):
        self.weights = weights

    def __call__(self, _image_path):
        return [_EmptyResults()]

    def predict(self, **_kwargs):
        return [_EmptyResults()]


def test_image_to_circuit_json_returns_empty_when_nothing_detected(monkeypatch):
    fake = types.ModuleType("ultralytics")
    fake.YOLO = _FakeYOLO
    monkeypatch.setitem(sys.modules, "ultralytics", fake)

    result = topo.image_to_circuit_json("blank.png")

    assert result["components"] == []
    assert result["connections"] == []
    assert result["detected"] is False


def test_adapt_empty_netlist_returns_empty_schema():
    result = topo.adapt_netlist_to_schema({"components": [], "connections": []})

    assert result["components"] == []
    assert result["connections"] == []
    assert result["detected"] is False


def test_adapt_netlist_keeps_real_components():
    raw = {
        "components": [
            {"id": "BATTERY_1", "type": "battery"},
            {"id": "LED_1", "type": "led"},
        ],
        "connections": [
            {"from": {"component": "BATTERY_1"}, "to": {"component": "LED_1"}},
        ],
    }
    result = topo.adapt_netlist_to_schema(raw)

    assert result["components"] == ["battery", "led"]
    assert result["connections"] == ["BATTERY_1 -> LED_1"]
    assert result["detected"] is True
