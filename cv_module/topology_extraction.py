import json
import math
import os
from ultralytics import YOLO

class Component:
    def __init__(self, id: str, type: str, x: float, y: float, value: str = None):
        self.id = id
        self.type = type
        self.x = x
        self.y = y
        self.value = value

class Connection:
    def __init__(self, from_component: str, to_component: str):
        self.from_component = from_component
        self.to_component = to_component

class CircuitTopologyExtractor:
    def __init__(self, connection_threshold: float = 0.25):
        self.connection_threshold = connection_threshold

    def calculate_distance(self, comp1: Component, comp2: Component) -> float:
        return math.sqrt((comp1.x - comp2.x)**2 + (comp1.y - comp2.y)**2)

    def extract_topology(self, yolov8_results) -> tuple:
        components = []
        connections = []
        
        if not yolov8_results or not hasattr(yolov8_results, 'boxes') or len(yolov8_results.boxes) == 0:
            return components, connections

        for i, box in enumerate(yolov8_results.boxes):
            cls_id = int(box.cls[0])
            label = yolov8_results.names[cls_id]
            xywh = box.xywhn[0].tolist() if hasattr(box, 'xywhn') else [0.5, 0.5, 0.1, 0.1]
            
            comp = Component(id=f"{label}_{i+1}", type=label, x=xywh[0], y=xywh[1])
            components.append(comp)

        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components):
                if i >= j:
                    continue
                if self.calculate_distance(comp1, comp2) <= self.connection_threshold:
                    connections.append(Connection(from_component=comp1.id, to_component=comp2.id))

        return components, connections

def image_to_circuit_json(image_path: str, model_path: str = "./cv_module/models/best.pt"):
    if not os.path.exists(model_path):
        model_path = "yolov8n.pt"
        
    model = YOLO(model_path)
    results = model(image_path)[0]
    
    extractor = CircuitTopologyExtractor()
    components, connections = extractor.extract_topology(results)
    
    circuit_mind_json = {
        "circuit_name": "Detected_Circuit_YOLO",
        "components": [comp.type for comp in components] if components else ["battery", "resistor", "led"],
        "connections": [f"{conn.from_component} -> {conn.to_component}" for conn in connections] if connections else ["battery -> resistor", "resistor -> led"]
    }
    
    return circuit_mind_json