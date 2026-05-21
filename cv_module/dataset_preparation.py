"""
CircuitMind AI - Dataset Preparation Utility
Author: SHAYAN HAIDER (Team Lead)

Automatically generates standard YOLO folder directories and maps 
the data configuration tracking YAML profile.
"""

import os
from pathlib import Path

def setup_yolo_dataset():
    # Define absolute base paths relative to this project framework
    project_root = Path(__file__).resolve().parent.parent
    dataset_base = project_root / "cv_module" / "dataset"
    
    print(f"📦 Initializing Dataset Directory Setup at: {dataset_base}")
    
    # 1. Define the mandatory directory structure YOLO expects
    subdirectories = [
        dataset_base / "images" / "train",
        dataset_base / "images" / "val",
        dataset_base / "images" / "test",
        dataset_base / "labels" / "train",
        dataset_base / "labels" / "val",
        dataset_base / "labels" / "test",
    ]
    
    # Create folders if they don't exist
    for folder in subdirectories:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created/Verified: {folder.relative_to(project_root)}")

    # 2. Define custom circuit component classes for the model
    # Update or add classes here depending on your dataset annotation index
    classes = [
        "resistor",
        "capacitor",
        "inductor",
        "diode",
        "transistor",
        "ic_chip",
        "ground",
        "power_source"
    ]
    
    # 3. Generate the absolute tracking configuration YAML file
    yaml_path = dataset_base / "circuit_dataset.yaml"
    
    yaml_content = f"""# CircuitMind AI - YOLO Dataset Configuration Profile
# Generated dynamically by dataset_preparation.py

# Cloud path contexts (Relative to Colab target workspace execution directory)
path: ./circuit_mind_data/dataset
train: images/train
val: images/val
test: images/test

# Class Name Map Array Lookup
names:
"""
    for index, class_name in enumerate(classes):
        yaml_content += f"  {index}: {class_name}\n"
        
    with open(yaml_path, "w") as yaml_file:
        yaml_file.write(yaml_content.strip())
        
    print(f"\n📝 Successfully generated YOLO tracking configuration at:\n   {yaml_path}")
    print("\n🏁 Setup sequence complete. Populate folders before archiving for cloud execution.")

if __name__ == "__main__":
    setup_yolo_dataset()