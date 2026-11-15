# 🖼️ Computer Vision Module - CircuitMind AI

**Author:** SHAYAN HAIDER  
**Module:** Image Input → Circuit JSON Conversion  
**Priority:** 🔴 HIGH (Foundation for entire pipeline)

---

## 📋 Overview

This module transforms real-world circuit images into structured data that the rest of the AI pipeline can process.

**Pipeline:**
```
Input Image (.png/.jpg) 
    ↓
YOLO Object Detection 
    ↓
Topology Extraction 
    ↓
Standard Circuit JSON (for team use)
```

---

## 🎯 Your 3 Main Tasks

### ✅ Task 1: Dataset Collection & Augmentation
**File:** `dataset_preparation.py`

**What to do:**
1. Generate synthetic circuit images using schemdraw
2. Collect real circuit schematics (GitHub, Fritzing, manual drawing)
3. Label images using labelImg or Roboflow
4. Apply augmentations to expand dataset

**Run:**
```bash
cd circuitmind-ai
python cv_module/dataset_preparation.py
```

**Labeling tools:**
```bash
# Option 1: labelImg (local)
pip install labelImg
labelImg cv_module/dataset/images/train

# Option 2: Roboflow (cloud, recommended)
# Upload to roboflow.com for auto-labeling
```

---

### ✅ Task 2: YOLO Training
**File:** `train_yolo.py`

**What to do:**
1. Train YOLOv8/v9 on labeled dataset
2. Monitor training metrics (mAP, precision, recall)
3. Evaluate on test set
4. Export best model

**Run:**
```bash
python cv_module/train_yolo.py
```

**Expected Performance:**
- **mAP@0.5:** >0.80 (good)
- **mAP@0.5:0.95:** >0.60 (acceptable)
- **Precision:** >0.85
- **Recall:** >0.80

**Training outputs:**
```
cv_module/training/runs/circuit_detector/
├── weights/
│   ├── best.pt          ← Use this for inference
│   └── last.pt
├── results.png          ← Training curves
├── confusion_matrix.png
└── val_batch*.jpg       ← Validation predictions
```

---

### ✅ Task 3: Topology Extraction
**File:** `topology_extraction.py`

**What to do:**
1. Convert YOLO bounding boxes to circuit components
2. Detect connections using spatial proximity
3. Generate standard JSON format
4. Test with sample images

**Run:**
```bash
python cv_module/topology_extraction.py
```

---

## 🔗 Team Integration

### For Other Team Members to Use Your Work:

**Method 1: Direct Function Call**
```python
from cv_module.topology_extraction import image_to_circuit_json

# Convert image to circuit JSON
circuit_data = image_to_circuit_json(
    image_path="my_circuit.png",
    model_path="cv_module/models/best.pt"
)

print(circuit_data)
# {
#   "circuit_id": "circuit_abc123",
#   "components": [
#     {"id": "resistor_1", "type": "resistor", "value": "220Ω", ...},
#     {"id": "led_1", "type": "led", "value": "red", ...}
#   ],
#   "connections": [
#     {"from_component": "battery_1", "to_component": "resistor_1", ...}
#   ]
# }
```

**Method 2: API Endpoint** (once API is running)
```python
import requests

with open('circuit.png', 'rb') as f:
    files = {'image': f}
    response = requests.post(
        'http://localhost:8000/api/v1/cv/image-to-circuit',
        files=files
    )
    circuit_data = response.json()['data']
```

---

## 📊 Output Format (Standard Team JSON)

```json
{
  "circuit_id": "circuit_xyz789",
  "components": [
    {
      "id": "resistor_a1b2c3d4",
      "type": "resistor",
      "value": "220Ω",
      "x": 0.35,
      "y": 0.42,
      "terminals": [
        {"x": 0.30, "y": 0.42, "label": "left"},
        {"x": 0.40, "y": 0.42, "label": "right"}
      ],
      "properties": {
        "confidence": 0.94,
        "bbox": {"x1": 120, "y1": 150, "x2": 180, "y2": 170}
      }
    }
  ],
  "connections": [
    {
      "from_component": "battery_xyz",
      "to_component": "resistor_a1b2",
      "from_terminal": "positive",
      "to_terminal": "left"
    }
  ],
  "metadata": {
    "source": "computer_vision",
    "image_dimensions": {"width": 800, "height": 600},
    "total_detections": 5,
    "components_detected": 4,
    "connections_detected": 3
  }
}
```

---

## 🚀 Quick Start (Step-by-Step)

### Day 1: Setup & Data Collection
```bash
# 1. Install dependencies
pip install -r cv_requirements.txt

# 2. Generate synthetic dataset
python cv_module/dataset_preparation.py

# 3. Label images (use Roboflow for speed)
# Upload to roboflow.com → auto-label → download YOLO format
```

### Day 2: Training
```bash
# 4. Train YOLO model
python cv_module/train_yolo.py

# 5. Check results
# Open: cv_module/training/runs/circuit_detector/results.png
```

### Day 3: Integration & Testing
```bash
# 6. Test topology extraction
python cv_module/topology_extraction.py

# 7. Test API endpoint
python -c "from cv_module.cv_api import router; print('API ready!')"
```

---

## 📁 Directory Structure

```
cv_module/
├── dataset_preparation.py    ✅ Task 1: Generate & label data
├── train_yolo.py             ✅ Task 2: Train YOLO model
├── topology_extraction.py    ✅ Task 3: Extract circuit graph
├── cv_api.py                 🔗 API for team integration
│
├── dataset/
│   ├── images/
│   │   ├── train/            ← Training images
│   │   ├── val/              ← Validation images
│   │   └── test/             ← Test images
│   ├── labels/
│   │   ├── train/            ← YOLO annotations (.txt)
│   │   ├── val/
│   │   └── test/
│   └── circuit_dataset.yaml  ← YOLO config
│
├── training/
│   └── runs/
│       └── circuit_detector/
│           ├── weights/
│           │   └── best.pt   ← 🎯 Your trained model
│           └── results.png
│
└── models/
    └── best.pt               ← Final production model
```

---

## 🐛 Troubleshooting

### Issue: Low mAP scores (<0.60)
**Solutions:**
- Collect more labeled data (aim for 500+ images)
- Increase augmentation factor
- Train for more epochs (150-200)
- Try larger model (yolov8s or yolov8m)

### Issue: Poor connection detection
**Solutions:**
- Adjust `connection_threshold` in topology_extraction.py
- Improve wire detection in YOLO training
- Add more wire samples to dataset

### Issue: CUDA out of memory
**Solutions:**
- Reduce batch size in train_yolo.py
- Use smaller model (yolov8n)
- Use CPU instead: `device='cpu'`

---

## 📞 Communication with Team

### What You Provide to Team:
1. **Trained YOLO model** (`best.pt`) → Upload to shared Google Drive
2. **Test circuit JSON samples** → Share in team Slack/Discord
3. **Model performance report** → mAP, precision, recall metrics

### What You Need from Team:
1. **NLP Module (Haseeb):** Sample generated circuit JSONs to test compatibility
2. **GNN Module (Ubaidullah):** Feedback on JSON format requirements
3. **Export Module (Emanalia):** Confirmation that your JSON works with export scripts

---

## 🎯 Success Criteria

- [ ] Dataset: 300+ labeled images across 8 component classes
- [ ] YOLO: mAP@0.5 > 0.80 on test set
- [ ] Topology: Successfully extracts 90%+ components from test images
- [ ] Integration: Other team members can call `image_to_circuit_json()` successfully
- [ ] API: `/cv/image-to-circuit` endpoint returns valid JSON

---

## 📚 Resources

- **YOLOv8 Docs:** https://docs.ultralytics.com
- **Roboflow Labeling:** https://roboflow.com
- **schemdraw Library:** https://schemdraw.readthedocs.io
- **PyTorch Geometric:** https://pytorch-geometric.readthedocs.io

---

## 📝 Daily Progress Tracking

**Day 1:**
- [ ] Setup environment
- [ ] Generate 100 synthetic images
- [ ] Start labeling with Roboflow

**Day 2:**
- [ ] Complete labeling (300+ images)
- [ ] Train YOLO model
- [ ] Evaluate performance

**Day 3:**
- [ ] Test topology extraction
- [ ] Integrate with team API
- [ ] Document and share

---

**Questions? Contact Team Captain or post in project Discord!**

Good luck, Shayan! This is the foundation of our entire pipeline 

## 🧠 Model Weights Setup
To run `cv_module.py`, you need our custom-trained YOLOv8 weights file:
* **Download Link:** [Click Here to Download best.pt](https://drive.google.com/file/d/1fBduzh9M2_mVa7NirI0z9Ti9bsLrcEVS/view?usp=sharing)

**Instructions:** Create a folder named `weights` inside this root directory and place the downloaded `best.pt` file inside it.