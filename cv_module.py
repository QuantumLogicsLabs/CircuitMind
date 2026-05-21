import os
import json
import cv2
import math
import numpy as np
from ultralytics import YOLO

def generate_circuit_netlist(image_path, model_path):
    """
    CircuitMind AI - Computer Vision Module Engine
    ---------------------------------------------
    Takes a circuit image, runs custom YOLOv8 component detection, 
    and returns a structured pin-mapped JSON netlist.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model weights file not found at: {model_path}")
        
    model = YOLO(model_path)
    results = model.predict(source=image_path, conf=0.25, verbose=False)
    
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not open or read image: {image_path}")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    components = []
    connections = []
    boxes = results[0].boxes
    
    if len(boxes) == 0:
        return json.dumps({"metadata": {"total_components": 0, "total_connections": 0}, "components": [], "connections": []}, indent=2)
        
    for idx, box in enumerate(boxes):
        xyxy = box.xyxy[0].tolist()
        xmin, ymin, xmax, ymax = map(int, xyxy)
        cls_id = int(box.cls[0])
        comp_type = model.names[cls_id]
        comp_id = f"{comp_type.upper()}_{idx+1}"
        
        cx = (xmin + xmax) // 2
        cy = (ymin + ymax) // 2
        
        terminals = [
            {"pin": "input_1", "coord": [xmin, int(ymin + 0.3 * (ymax - ymin))]},
            {"pin": "input_2", "coord": [xmin, int(ymin + 0.7 * (ymax - ymin))]},
            {"pin": "output", "coord": [xmax, cy]}
        ]
        
        components.append({
            "id": comp_id,
            "type": comp_type,
            "center": [cx, cy],
            "terminals": terminals
        })

    used_pairs = set()
    for i, comp_a in enumerate(components):
        for term_a in comp_a["terminals"]:
            coord_a = term_a["coord"]
            for j, comp_b in enumerate(components):
                if i == j: continue
                for term_b in comp_b["terminals"]:
                    coord_b = term_b["coord"]
                    
                    pin_key = tuple(sorted([f"{comp_a['id']}-{term_a['pin']}", f"{comp_b['id']}-{term_b['pin']}"]))
                    if pin_key in used_pairs: continue
                        
                    dist = math.hypot(coord_b[0] - coord_a[0], coord_b[1] - coord_a[1])
                    if dist < 400:
                        mask = np.zeros_like(binary)
                        cv2.line(mask, tuple(coord_a), tuple(coord_b), 255, thickness=5)
                        intersect = cv2.bitwise_and(binary, mask)
                        if np.sum(intersect > 0) > 20:
                            connections.append({
                                "from": {"component": comp_a["id"], "pin": term_a["pin"]},
                                "to": {"component": comp_b["id"], "pin": term_b["pin"]},
                                "distance": round(dist, 1)
                            })
                            used_pairs.add(pin_key)

    output_payload = {
        "metadata": {
            "total_components": len(components),
            "total_connections": len(connections),
            "engine_status": "Production-Ready"
        },
        "components": [
            {
                "id": c["id"],
                "type": c["type"],
                "position": [round(float(c["center"][0]), 1), round(float(c["center"][1]), 1)]
            } for c in components
        ],
        "connections": connections
    }
    return json.dumps(output_payload, indent=2)
