"""
CircuitMind - Topology Extraction
cv_module/topology_extraction.py

Two implementations available:
  1. image_to_circuit_json()      — simple YOLO-only (proximity-based connections)
  2. generate_circuit_netlist()   — YOLO + OpenCV wire-tracing (more accurate)

The API layer calls image_to_circuit_json(); the wire-tracing version is
available for higher-accuracy use cases once best.pt is trained.
"""

import json
import math
import os
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# Dynamic pin/terminal layout per component type.
# Replaces the old hardcoded assumption that every component has
# exactly 3 terminals (input_1, input_2, output).
TERMINAL_SPECS: dict[str, list[str]] = {
    "resistor":    ["terminal_1", "terminal_2"],
    "capacitor":   ["terminal_1", "terminal_2"],
    "inductor":    ["terminal_1", "terminal_2"],
    "switch":      ["terminal_1", "terminal_2"],
    "wire":        ["terminal_1", "terminal_2"],
    "led":         ["anode", "cathode"],
    "diode":       ["anode", "cathode"],
    "battery":     ["positive", "negative"],
    "transistor":  ["base", "collector", "emitter"],
    "ic":          ["pin_1", "pin_2", "pin_3", "pin_4"],
}
DEFAULT_TERMINALS: list[str] = ["terminal_1", "terminal_2"]  # 2-pin fallback


def _terminals_for(comp_type: str) -> list[str]:
    """Look up the correct terminal set for a component type (case-insensitive)."""
    return TERMINAL_SPECS.get(comp_type.lower(), DEFAULT_TERMINALS)


def _terminal_coords(xmin: int, ymin: int, xmax: int, ymax: int,
                      pin_names: list[str]) -> list[dict]:
    """
    Dynamically place N terminal coordinates around a bounding box instead of
    assuming a fixed 3-pin (input_1/input_2/output) layout.

    - 2 pins: one on the left edge, one on the right edge (typical 2-lead part).
    - 3+ pins: distributed evenly down the left edge, remainder on the right edge
      (covers transistors, ICs, etc.).
    """
    n = len(pin_names)
    cy = (ymin + ymax) // 2

    if n == 2:
        coords = [[xmin, cy], [xmax, cy]]
    else:
        left_count  = math.ceil(n / 2)
        right_count = n - left_count
        coords = []
        for k in range(left_count):
            frac = (k + 1) / (left_count + 1)
            coords.append([xmin, int(ymin + frac * (ymax - ymin))])
        for k in range(right_count):
            frac = (k + 1) / (right_count + 1)
            coords.append([xmax, int(ymin + frac * (ymax - ymin))])

    return [{"pin": name, "coord": coord} for name, coord in zip(pin_names, coords)]


@dataclass
class Component:
    id:    str
    type:  str
    x:     float
    y:     float
    value: str | None = None


@dataclass
class Connection:
    from_component: str
    to_component:   str


class CircuitTopologyExtractor:
    """Converts YOLO detection results into components + connections."""

    def __init__(self, connection_threshold: float = 0.25):
        self.connection_threshold = connection_threshold

    def _distance(self, a: Component, b: Component) -> float:
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def extract_topology(self, yolo_results) -> tuple[list[Component], list[Connection]]:
        components:  list[Component]  = []
        connections: list[Connection] = []

        if not yolo_results or not hasattr(yolo_results, "boxes") or len(yolo_results.boxes) == 0:
            return components, connections

        for i, box in enumerate(yolo_results.boxes):
            cls_id = int(box.cls[0])
            label  = yolo_results.names[cls_id]
            xywh   = box.xywhn[0].tolist() if hasattr(box, "xywhn") else [0.5, 0.5, 0.1, 0.1]
            components.append(Component(id=f"{label}_{i + 1}", type=label, x=xywh[0], y=xywh[1]))

        for i, a in enumerate(components):
            for j, b in enumerate(components):
                if i >= j:
                    continue
                if self._distance(a, b) <= self.connection_threshold:
                    connections.append(Connection(from_component=a.id, to_component=b.id))

        return components, connections


def image_to_circuit_json(image_path: str, model_path: str = "./cv_module/models/best.pt") -> dict:
    """
    YOLO-only implementation (proximity-based connections).
    Falls back to yolov8n.pt baseline if custom model not found.
    """
    from ultralytics import YOLO

    active_model = model_path if os.path.exists(model_path) else "yolov8n.pt"
    if active_model != model_path:
        logger.warning("Custom model not found; using YOLOv8n baseline weights.")

    model   = YOLO(active_model)
    results = model(image_path)[0]

    extractor             = CircuitTopologyExtractor()
    components, conns     = extractor.extract_topology(results)

    # Report what was actually detected. Inventing a battery/resistor/LED
    # circuit for an empty image hides detection failures from every
    # downstream consumer (diagnose, explain, export).
    return {
        "circuit_name": "Detected_Circuit",
        "components":   [c.type for c in components],
        "connections":  [f"{c.from_component} -> {c.to_component}" for c in conns],
        "detected":     bool(components),
    }


def generate_circuit_netlist(image_path: str, model_path: str) -> str:
    """
    YOLO + OpenCV wire-tracing implementation.
    Returns a JSON string with pin-level connection data.
    Requires: ultralytics, opencv-python, numpy
    """
    import cv2
    import numpy as np
    from ultralytics import YOLO

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model weights not found: {model_path}")

    model   = YOLO(model_path)
    results = model.predict(source=image_path, conf=0.25, verbose=False)

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray   = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    components:  list[dict] = []
    connections: list[dict] = []
    boxes = results[0].boxes

    if len(boxes) == 0:
        empty_netlist = {
            "metadata": {"total_components": 0, "total_connections": 0},
            "components": [],
            "connections": [],
        }
        return json.dumps(adapt_netlist_to_schema(empty_netlist), indent=2)

    for idx, box in enumerate(boxes):
        xmin, ymin, xmax, ymax = map(int, box.xyxy[0].tolist())
        comp_type = model.names[int(box.cls[0])]
        cx, cy    = (xmin + xmax) // 2, (ymin + ymax) // 2
        pin_names = _terminals_for(comp_type)
        components.append({
            "id":     f"{comp_type.upper()}_{idx + 1}",
            "type":   comp_type,
            "center": [cx, cy],
            "terminals": _terminal_coords(xmin, ymin, xmax, ymax, pin_names),
        })

    used_pairs: set = set()
    for i, ca in enumerate(components):
        for term_a in ca["terminals"]:
            for j, cb in enumerate(components):
                if i == j:
                    continue
                for term_b in cb["terminals"]:
                    key = tuple(sorted([f"{ca['id']}-{term_a['pin']}", f"{cb['id']}-{term_b['pin']}"]))
                    if key in used_pairs:
                        continue
                    dist = math.hypot(term_b["coord"][0] - term_a["coord"][0],
                                      term_b["coord"][1] - term_a["coord"][1])
                    if dist < 400:
                        mask      = np.zeros_like(binary)
                        cv2.line(mask, tuple(term_a["coord"]), tuple(term_b["coord"]), 255, thickness=5)
                        intersect = cv2.bitwise_and(binary, mask)
                        if np.sum(intersect > 0) > 20:
                            connections.append({
                                "from":     {"component": ca["id"], "pin": term_a["pin"]},
                                "to":       {"component": cb["id"], "pin": term_b["pin"]},
                                "distance": round(dist, 1),
                            })
                            used_pairs.add(key)

    raw_netlist = {
        "metadata": {
            "total_components": len(components),
            "total_connections": len(connections),
            "engine_status": "production",
        },
        "components": [
            {"id": c["id"], "type": c["type"],
             "position": [round(float(c["center"][0]), 1), round(float(c["center"][1]), 1)]}
            for c in components
        ],
        "connections": connections,
    }

    return json.dumps(adapt_netlist_to_schema(raw_netlist), indent=2)


def adapt_netlist_to_schema(raw_netlist: dict) -> dict:
    """
    Adapter: converts the deeply nested, pin-level netlist produced by the
    wire-tracing engine into the simple schema expected by diagnose,
    explain, and export: {"components": [...], "connections": [...]}.


    Pin-level detail isn't discarded — it's kept under "netlist_detail"
    for any future higher-accuracy consumer that wants it.
    """
    components = raw_netlist.get("components", [])
    id_to_type = {c["id"]: c["type"] for c in components}

    seen_pairs: set = set()
    simple_connections: list[str] = []
    for conn in raw_netlist.get("connections", []):
        from_id = conn["from"]["component"]
        to_id   = conn["to"]["component"]
        pair_key = tuple(sorted([from_id, to_id]))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        simple_connections.append(f"{from_id} -> {to_id}")

    return {
        "circuit_name": "Detected_Circuit",
        "components":   [c["type"] for c in components],
        "connections":  simple_connections,
        "detected":     bool(components),
        "netlist_detail": raw_netlist,  # full pin-level data preserved for advanced use
    }