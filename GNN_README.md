# 🧠 GNN Fault Detection Module

Part of the **CircuitMind AI** project — Quantum Logics Labs Internship.

This module takes a circuit JSON as input, converts it into a mathematical
graph, and uses a Graph Convolutional Network (GCN) to classify the circuit
as Valid or detect specific fault types.

---

## 📁 Files

```
gnn/
├── gnn_module.py     # Main GNN model + training + prediction
└── README.md         # This file
```

---

## 🧠 How It Works

```
Circuit JSON
     ↓
Components → One Hot Encoded Vectors (Node Features)
     ↓
Connections → Edge Index (Graph Structure)
     ↓
GCN Layer 1 — each node learns from direct neighbors
     ↓
GCN Layer 2 — each node sees 2 hops away
     ↓
Global Mean Pooling — entire graph compressed to one vector
     ↓
Classifier → Valid / Short Circuit / Floating Component
```

---

## 📥 Input Format

```json
{
  "circuit_name": "LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"],
  "label": 0
}
```

### Labels
| Label | Meaning |
|-------|---------|
| 0 | ✅ Valid Circuit |
| 1 | ❌ Short Circuit |
| 2 | ⚠️ Floating Component |

---

## 📤 Output Format

```python
{
  "prediction": "Valid Circuit",
  "confidence": 99.95
}
```

---

## 🔧 Supported Components

| Component | Vocab Index |
|-----------|-------------|
| battery | 0 |
| power_supply | 1 |
| resistor | 2 |
| capacitor | 3 |
| inductor | 4 |
| led | 5 |
| diode | 6 |
| zener_diode | 7 |
| transistor | 8 |
| npn_transistor | 9 |
| pnp_transistor | 10 |
| mosfet | 11 |
| op_amp | 12 |
| motor | 13 |
| switch | 14 |
| ground | 15 |

---

## 🏗️ Model Architecture

```
Input: One Hot Encoded Node Features (16 dimensions)
     ↓
GCNConv Layer 1: 16 → 32 (ReLU + Dropout 0.3)
     ↓
GCNConv Layer 2: 32 → 32 (ReLU)
     ↓
Global Mean Pooling: graph → single vector
     ↓
Linear Classifier: 32 → 3
     ↓
Output: [Valid, Short Circuit, Floating Component]
```

---

## 📊 Training Results

| Metric | Score |
|--------|-------|
| Training Accuracy | 100% |
| Test Accuracy | 100% |
| Epochs | 50 |
| Dataset Size | 600 circuits |
| Optimizer | Adam (lr=0.01) |
| Loss Function | CrossEntropyLoss |

### Dataset Breakdown
| Type | Count |
|------|-------|
| Valid Circuits | 200 |
| Short Circuits | 200 |
| Floating Components | 200 |

---

## 💻 Usage

```python
import torch
from gnn_module import CircuitGNN, predict_circuit

# Device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load model
checkpoint = torch.load('circuit_gnn.pt', map_location=device)
model = CircuitGNN(input_dim=16, hidden_dim=32, output_dim=3)
model.load_state_dict(checkpoint['model_state_dict'])
model = model.to(device)

# Predict
result = predict_circuit({
    "circuit_name": "My Circuit",
    "components":   ["battery", "resistor", "led"],
    "connections":  ["battery -> resistor -> led"]
}, model, device)

print(result)
# {"prediction": "Valid Circuit", "confidence": 99.95}
```

---

## 🔗 Pipeline Integration

This module sits in the middle of the CircuitMind AI pipeline:

```
CV Module (Shayan)     →  Circuit JSON
NLP Module (Haseeb)    →  Circuit JSON
                               ↓
                    GNN Module (Ubaidullah)
                               ↓
                    Valid / Short / Floating
                               ↓
                    Export Module (Eman)
```

---

## 👤 Author
Ubaidullah — GNN Fault Detection
CircuitMind AI — Quantum Logics Labs Internship
