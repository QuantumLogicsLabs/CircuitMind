"""
Tests for the CV_CONFIDENCE detection threshold.

The YOLO confidence cutoff used to be hardcoded (implicit 0.25 for plain
inference, 0.25 for predict). Deployments need to tune it per model, so the
threshold is read once from the environment and validated.
"""

import json
import sys
import types

import pytest

import cv_module.topology_extraction as te


class FakeYOLO:
    calls: list = []

    def __init__(self, weights):
        self.weights = weights

    def __call__(self, source, **kwargs):
        FakeYOLO.calls.append({"source": source, **kwargs})
        return [types.SimpleNamespace(boxes=[], names={})]

    def predict(self, **kwargs):
        FakeYOLO.calls.append({"predict": True, **kwargs})
        return [types.SimpleNamespace(boxes=[], names={})]


@pytest.fixture
def fake_yolo(monkeypatch):
    FakeYOLO.calls = []
    monkeypatch.setitem(sys.modules, "ultralytics", types.SimpleNamespace(YOLO=FakeYOLO))
    return FakeYOLO


def test_missing_env_uses_default():
    assert te.resolve_confidence({}) == te.DEFAULT_CONFIDENCE
    assert te.resolve_confidence({"CV_CONFIDENCE": "  "}) == te.DEFAULT_CONFIDENCE


def test_valid_values_are_accepted():
    assert te.resolve_confidence({"CV_CONFIDENCE": "0.5"}) == 0.5
    assert te.resolve_confidence({"CV_CONFIDENCE": "0"}) == 0.0
    assert te.resolve_confidence({"CV_CONFIDENCE": "1"}) == 1.0
    assert te.resolve_confidence({"CV_CONFIDENCE": " 0.4 "}) == 0.4


@pytest.mark.parametrize("raw", ["abc", "-0.1", "1.01", "nan-ish"])
def test_invalid_values_fall_back_to_default(raw):
    assert te.resolve_confidence({"CV_CONFIDENCE": raw}) == te.DEFAULT_CONFIDENCE


def test_threshold_is_passed_to_model_call(fake_yolo, monkeypatch):
    monkeypatch.setattr(te, "CONFIDENCE_THRESHOLD", 0.6)

    te.image_to_circuit_json("circuit.png", model_path="./missing.pt")

    assert fake_yolo.calls[0]["conf"] == 0.6


def test_predict_uses_threshold(fake_yolo, monkeypatch, tmp_path):
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")

    image_path = tmp_path / "circuit.png"
    cv2.imwrite(str(image_path), np.full((32, 32, 3), 255, dtype=np.uint8))
    weights = tmp_path / "weights.pt"
    weights.write_bytes(b"not-a-real-model")

    monkeypatch.setattr(te, "CONFIDENCE_THRESHOLD", 0.7)

    netlist_json = te.generate_circuit_netlist(str(image_path), str(weights))

    assert fake_yolo.calls[0]["predict"] is True
    assert fake_yolo.calls[0]["conf"] == 0.7
    assert json.loads(netlist_json)["components"] == []
