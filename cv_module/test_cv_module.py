"""
CV Module Test Suite
Author: SHAYAN HAIDER

Run this to verify your CV module is working correctly
"""

import sys
import os
from pathlib import Path
import json

# ==============================================================================
# PATH SAFETY GUARD
# Ensures Python can locate your internal modules without path errors
# ==============================================================================
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_imports():
    """Test 1: Check if all required packages are installed"""
    print("\n" + "="*70)
    print("TEST 1: Checking Dependencies")
    print("="*70)
    
    required_packages = {
        'torch': 'PyTorch',
        'cv2': 'OpenCV',
        'ultralytics': 'YOLO',
        'numpy': 'NumPy',
        'scipy': 'SciPy',
        'albumentations': 'Albumentations',
        'PIL': 'Pillow',
    }
    
    missing = []
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name}: Installed")
        except ImportError:
            print(f"❌ {name}: Missing")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True


def test_dataset_structure():
    """Test 2: Check if dataset directories exist"""
    print("\n" + "="*70)
    print("TEST 2: Dataset Structure")
    print("="*70)
    
    # Resolves to project_root/cv_module/dataset
    base_dir = project_root / "cv_module" / "dataset"
    
    required_dirs = [
        base_dir / "images" / "train",
        base_dir / "images" / "val",
        base_dir / "images" / "test",
        base_dir / "labels" / "train",
        base_dir / "labels" / "val",
        base_dir / "labels" / "test",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✅ {dir_path.relative_to(project_root) if project_root in dir_path.parents else dir_path}")
        else:
            print(f"❌ {dir_path.name} - Missing")
            all_exist = False
    
    if all_exist:
        print("\n✅ Dataset structure correct!")
    else:
        print("\n⚠️ Run dataset_preparation.py to create structure")
    
    return all_exist


def test_yaml_config():
    """Test 3: Check if YAML config exists"""
    print("\n" + "="*70)
    print("TEST 3: YAML Configuration")
    print("="*70)
    
    yaml_path = project_root / "cv_module" / "dataset" / "circuit_dataset.yaml"
    
    if yaml_path.exists():
        print(f"✅ YAML config found: {yaml_path}")
        try:
            with open(yaml_path, 'r') as f:
                content = f.read()
                print("\nContent preview:")
                print(content[:200] + "...")
            return True
        except Exception as e:
            print(f"❌ Error reading YAML file: {e}")
            return False
    else:
        print(f"❌ YAML config not found at {yaml_path}")
        print("⚠️ Run dataset_preparation.py to generate it")
        return False


def test_topology_extraction():
    """Test 4: Test topology extraction functions"""
    print("\n" + "="*70)
    print("TEST 4: Topology Extraction Module")
    print("="*70)
    
    try:
        # Dynamically falls back gracefully if file hasn't been created yet
        from cv_module.topology_extraction import CircuitTopologyExtractor, Component, Connection
        
        print("✅ Imports successful")
        
        extractor = CircuitTopologyExtractor()
        print(f"✅ Extractor initialized (threshold: {extractor.connection_threshold})")
        
        test_component = Component(
            id="test_resistor_1",
            type="resistor",
            value="220Ω",
            x=0.5,
            y=0.5
        )
        print(f"✅ Component creation works: {test_component.id}")
        
        test_connection = Connection(
            from_component="comp_1",
            to_component="comp_2"
        )
        print(f"✅ Connection creation works")
        
        return True
        
    except ImportError:
        print("❌ Error: topology_extraction.py module file does not exist yet.")
        return False
    except Exception as e:
        print(f"❌ Error during module execution test: {e}")
        return False


def test_model_inference():
    """Test 5: Check if trained model exists and can load"""
    print("\n" + "="*70)
    print("TEST 5: Model Loading")
    print("="*70)
    
    model_path = project_root / "cv_module" / "models" / "best.pt"
    
    if not model_path.exists():
        print(f"⚠️ Model weight checkpoint file not found at {model_path}")
        print("This is expected if you haven't completed training yet on Google Colab.")
        print("After training, download your best.pt and place it inside the models directory.")
        return None
    
    try:
        from ultralytics import YOLO
        
        model = YOLO(str(model_path))
        print(f"✅ Model weights loaded successfully")
        print(f"   Model Object Class Type: {type(model)}")
        return True
        
    except Exception as e:
        print(f"❌ Error parsing model weights file structure: {e}")
        return False


def test_api_imports():
    """Test 6: Check if API module imports correctly"""
    print("\n" + "="*70)
    print("TEST 6: API Module")
    print("="*70)
    
    try:
        from cv_module.cv_api import app
        print("✅ API core instance module located and imported successfully")
        
        # Pull endpoint routes directly from the master app instance
        routes = [route.path for route in app.routes]
        print(f"✅ Active operational endpoints discovered: {len(routes)}")
        for route in routes:
            print(f"   - {route}")
        return True
        
    except ImportError:
        print("❌ Error: cv_api.py core script file is missing or contains broken imports.")
        return False
    except Exception as e:
        print(f"❌ Error structural mapping failed: {e}")
        return False


def generate_test_report():
    """Run all tests and generate report"""
    print("\n" + "🔍 "*25)
    print("CircuitMind AI - CV Module Test Suite")
    print("🔍 "*25)
    
    results = {
        "Dependencies": test_imports(),
        "Dataset Structure": test_dataset_structure(),
        "YAML Config": test_yaml_config(),
        "Topology Extraction": test_topology_extraction(),
        "Model Loading": test_model_inference(),
        "API Module": test_api_imports(),
    }
    
    # Summary Table Output
    print("\n" + "="*70)
    print("📊 TEST SUMMARY REPORT")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️ SKIP"
        
        print(f"{status:12} | {test_name}")
    
    print("="*70)
    print(f"Final Count: {passed} passed, {failed} failed, {skipped} skipped")
    print("="*70)
    
    # Strategic Pipeline Recovery Prompts
    print("\n📋 DIRECTIVE RECOMMENDATIONS:")
    
    if results["Dependencies"] is False:
        print("1. Resolve core package installations instantly via terminal:")
        print("   pip install -r cv_module/requirements_cv.txt")
    
    if results["Dataset Structure"] is False or results["YAML Config"] is False:
        print("2. Setup data parsing structure manually or execute preparation routine:")
        print("   python cv_module/dataset_preparation.py")
    
    if results["Model Loading"] is None:
        print("3. Execute model training iteration (highly recommended via Google Colab runtime):")
        print("   python cv_module/train_yolo.py")
    
    if all(v is True for v in results.values() if v is not None):
        print("🏁 System clearance verified! Shayan's CV processing script matches team schema structures.")


if __name__ == "__main__":
    generate_test_report()