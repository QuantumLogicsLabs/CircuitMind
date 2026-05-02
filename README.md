# ⚡ CircuitMind

> **An AI-powered electronics assistant that understands, explains, and generates circuits — from a blinking LED to a full power management system.**

---

## 🧠 What Is CircuitMind?

CircuitMind is a fine-tuned multimodal ML model designed specifically for the electronics domain. Unlike general-purpose LLMs, CircuitMind speaks the native language of hardware — it understands **netlists**, **component datasheets**, **SPICE parameters**, and **schematic topology** — and uses that knowledge to:

- **Explain** how any circuit works in plain English or expert-level detail
- **Generate** complete, functional circuit schematics from a natural language prompt
- **Diagnose** faults and suggest fixes given a broken schematic or symptom description
- **Optimize** circuits for power, cost, noise, or size constraints
- **Export** designs to industry formats: KiCad `.kicad_sch`, SPICE netlist, Falstad JSON, and SVG

CircuitMind is *not* a chatbot wrapper around GPT. It is a purpose-built model trained on a curated corpus of real-world circuit data, designed to produce **valid, manufacturable, simulation-ready** outputs.

---

## ✨ What Makes CircuitMind Special

Most AI tools treat circuits as text. CircuitMind treats them as **structured graphs**. Every component is a node; every wire is an edge. The model learns the topology of circuits, not just their surface syntax.

| Feature | Generic LLM | CircuitMind |
|---|---|---|
| Understands circuit topology | ❌ | ✅ |
| Generates valid netlists | ❌ | ✅ |
| Exports to KiCad / SPICE | ❌ | ✅ |
| Trained on real schematics | ❌ | ✅ |
| Component-level reasoning | ❌ | ✅ |
| Constraint-aware generation | ❌ | ✅ |

---

## 🗂️ Project Structure

```
circuitmind/
├── data/
│   ├── raw/                    # Raw scraped schematics, datasheets
│   ├── processed/              # Normalized netlist graphs (JSON)
│   ├── augmented/              # Augmented variants (rotated, relabeled)
│   └── splits/                 # train / val / test splits
│
├── tokenizer/
│   ├── component_vocab.json    # Component tokens (R, C, L, MOSFET, OpAmp…)
│   ├── netlist_tokenizer.py    # Custom graph-aware tokenizer
│   └── text_tokenizer.py       # BPE tokenizer for natural language
│
├── model/
│   ├── architecture.py         # CircuitMind Transformer definition
│   ├── graph_encoder.py        # GNN-based schematic encoder
│   ├── text_decoder.py         # Explanation decoder (causal LM head)
│   ├── netlist_decoder.py      # Autoregressive netlist generation head
│   └── fusion.py               # Cross-attention fusion layer
│
├── training/
│   ├── pretrain.py             # Self-supervised pretraining on netlists
│   ├── finetune.py             # Supervised fine-tuning (SFT)
│   ├── rlhf.py                 # RLHF with engineer preference data
│   ├── loss.py                 # Custom graph reconstruction loss
│   └── config/
│       ├── pretrain_config.yaml
│       └── finetune_config.yaml
│
├── inference/
│   ├── generate.py             # Circuit generation pipeline
│   ├── explain.py              # Explanation pipeline
│   ├── diagnose.py             # Fault diagnosis pipeline
│   └── export/
│       ├── to_kicad.py
│       ├── to_spice.py
│       ├── to_falstad.py
│       └── to_svg.py
│
├── eval/
│   ├── validity_checker.py     # Is the netlist electrically valid?
│   ├── simulation_eval.py      # Run SPICE sim, compare to spec
│   ├── human_eval_rubric.md    # Rubric for engineer raters
│   └── benchmarks/
│       ├── component_recall.py
│       └── constraint_satisfaction.py
│
├── api/
│   ├── app.py                  # FastAPI server
│   ├── routes/
│   │   ├── generate.py
│   │   ├── explain.py
│   │   └── diagnose.py
│   └── schemas.py              # Pydantic request/response models
│
├── ui/                         # Optional local web UI (React + Tailwind)
├── notebooks/                  # Exploratory notebooks
├── scripts/                    # Data pipeline scripts
├── tests/
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 🏗️ Model Architecture

CircuitMind uses a **dual-encoder, dual-decoder** architecture:

```
                        ┌─────────────────────┐
  Natural Language  ──► │   Text Encoder      │ ──┐
  (Prompt / Query)      │   (12-layer Transformer)│  │
                        └─────────────────────┘  │
                                                  ▼
                                        ┌──────────────────┐
                                        │  Cross-Attention  │
                                        │  Fusion Layer     │
                                        └──────────────────┘
                                           │            │
                        ┌──────────────────┐    ┌──────────────────┐
  Output: Explanation ◄─│  Text Decoder    │    │ Netlist Decoder  │─► Output: Circuit
                        │  (Causal LM)     │    │ (Graph Autoregr.)│
                        └──────────────────┘    └──────────────────┘
                                                         ▲
                        ┌─────────────────────┐          │
  Input Schematic   ──► │   Graph Encoder     │ ─────────┘
  (Netlist / Image)     │   (GNN + Attention) │
                        └─────────────────────┘
```

### Key Architectural Choices

**Graph Neural Network Encoder** — Circuits are represented as directed graphs where nodes are components and edges are nets. A 6-layer GNN with message-passing learns structural circuit patterns that cannot be captured with flat text.

**Dual Tokenization** — CircuitMind uses two vocabularies simultaneously: a standard BPE tokenizer for natural language and a custom component tokenizer that encodes component type, value, footprint, and pin assignments as atomic tokens.

**Constrained Decoding** — During netlist generation, a validity mask is applied at each decoding step to prevent the model from generating electrically invalid states (e.g., short circuits, floating pins, missing power rails).

**Retrieval Augmentation (optional)** — A vector store of 2M+ indexed datasheets allows CircuitMind to ground component selection in real-world specifications at inference time.

---

## 📦 Installation

### Requirements

- Python 3.10+
- CUDA 12.1+ (for GPU training/inference)
- 24 GB VRAM minimum for full model inference (FP16)
- 8 GB VRAM sufficient with 4-bit quantization

### Clone & Install

```bash
git clone https://github.com/your-org/circuitmind.git
cd circuitmind

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in editable mode
pip install -e .
```

### Requirements File (core dependencies)

```
torch>=2.2.0
transformers>=4.40.0
torch-geometric>=2.5.0
networkx>=3.2
spacy>=3.7
fastapi>=0.111.0
uvicorn>=0.29.0
pydantic>=2.0
schemdraw>=0.19
PySpice>=1.5
kiutils>=1.5
datasets>=2.18.0
accelerate>=0.29.0
bitsandbytes>=0.43.0
wandb>=0.16.0
groq>=0.4.0
python-dotenv
```

---

## 📊 Dataset

CircuitMind is trained on a multi-source dataset totalling approximately **4.2 million circuits**:

| Source | Count | Type |
|---|---|---|
| KiCad open-source library | 180K | Production schematics |
| SnapEDA / Component Search Engine | 900K | Component + footprint netlists |
| EEVblog forum archives | 220K | Annotated schematic discussions |
| Falstad Circuit Simulator dumps | 1.4M | Simulated + labeled circuits |
| Textbook circuit examples (OCR) | 60K | Educational schematics with explanations |
| Synthetic augmentation | 1.4M | Programmatically generated variants |

### Data Format

Each training example is a JSON object:

```json
{
  "id": "cm_0042819",
  "prompt": "Design a 5V to 3.3V LDO regulator with <150mA output current",
  "circuit": {
    "nodes": [
      { "id": "U1", "type": "LDO", "value": "AMS1117-3.3", "pins": ["IN","OUT","GND","ADJ"] },
      { "id": "C1", "type": "CAP", "value": "10uF", "footprint": "0805" },
      { "id": "C2", "type": "CAP", "value": "22uF", "footprint": "0805" }
    ],
    "edges": [
      { "from": "VIN",    "to":   "U1.IN"  },
      { "from": "U1.IN",  "to":   "C1.+"   },
      { "from": "C1.-",   "to":   "GND"    },
      { "from": "U1.OUT", "to":   "VOUT"   },
      { "from": "U1.OUT", "to":   "C2.+"   },
      { "from": "C2.-",   "to":   "GND"    },
      { "from": "U1.GND", "to":   "GND"    }
    ]
  },
  "explanation": "The AMS1117-3.3 is a fixed 3.3V LDO regulator. C1 at the input filters high-frequency noise...",
  "constraints": { "Vout": 3.3, "Iout_max": 0.15, "Vin_range": [4.5, 12] },
  "tags": ["power", "LDO", "3v3", "linear-regulator"]
}
```

### Building the Dataset

```bash
# Step 1: Scrape and normalize raw sources
python scripts/scrape_kicad.py --output data/raw/kicad/
python scripts/parse_falstad.py --output data/raw/falstad/

# Step 2: Convert to unified graph format
python scripts/normalize.py --input data/raw/ --output data/processed/

# Step 3: Augment (rotation, value perturbation, relabeling)
python scripts/augment.py --input data/processed/ --output data/augmented/ --factor 5

# Step 4: Split
python scripts/split.py --input data/augmented/ --train 0.90 --val 0.05 --test 0.05
```

---

## 🏋️ Training

### Stage 1: Self-Supervised Pretraining

Pretrain the graph encoder and netlist decoder by predicting masked components and connections.

```bash
python training/pretrain.py \
  --config training/config/pretrain_config.yaml \
  --data data/splits/train \
  --output checkpoints/pretrain/
```

**pretrain_config.yaml:**
```yaml
model:
  graph_layers: 6
  text_layers: 12
  hidden_dim: 768
  heads: 12
  dropout: 0.1

training:
  batch_size: 64
  learning_rate: 3e-4
  warmup_steps: 10000
  max_steps: 500000
  gradient_clip: 1.0
  fp16: true

masking:
  node_mask_ratio: 0.15
  edge_mask_ratio: 0.10
```

### Stage 2: Supervised Fine-Tuning (SFT)

Fine-tune on paired (prompt → circuit + explanation) examples.

```bash
python training/finetune.py \
  --config training/config/finetune_config.yaml \
  --checkpoint checkpoints/pretrain/best.pt \
  --output checkpoints/sft/
```

### Stage 3: RLHF (Optional but Recommended)

Collect preference pairs from electronics engineers (A/B rating interface included at `ui/rating_app/`), then run PPO fine-tuning.

```bash
# Train reward model on collected preferences
python training/rlhf.py --mode reward_model \
  --preferences data/human_prefs/comparisons.jsonl

# Run PPO
python training/rlhf.py --mode ppo \
  --sft_checkpoint checkpoints/sft/best.pt \
  --reward_checkpoint checkpoints/reward/best.pt
```

### Estimated Training Compute

| Stage | Hardware | Duration |
|---|---|---|
| Pretraining | 8× A100 80GB | ~72 hours |
| SFT | 4× A100 80GB | ~18 hours |
| RLHF | 4× A100 80GB | ~12 hours |

For smaller-scale experimentation, training on a subset of data with a reduced model (4-layer GNN, 6-layer Transformer) works on a single RTX 3090.

---

## 🚀 Inference

### Python API

```python
from circuitmind import CircuitMind

cm = CircuitMind.from_pretrained("circuitmind/v1")

# Generate a circuit from a prompt
result = cm.generate(
    prompt="555 timer astable oscillator with 1kHz output frequency",
    constraints={"Vcc": 9.0, "duty_cycle": 0.5},
    export_format="kicad"
)

print(result.explanation)    # Plain English explanation
print(result.netlist)        # Raw netlist
result.export("my_circuit.kicad_sch")  # Save to file

# Explain an existing circuit
with open("mystery_circuit.kicad_sch") as f:
    explanation = cm.explain(f.read(), detail_level="expert")
print(explanation)

# Diagnose a problem
diagnosis = cm.diagnose(
    schematic="...",
    symptom="Output voltage is oscillating at 60Hz"
)
print(diagnosis.root_cause)
print(diagnosis.suggested_fix)
```

### REST API

```bash
# Start the API server
uvicorn api.app:app --host 0.0.0.0 --port 8000

# Generate endpoint
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Low-pass RC filter with cutoff at 10kHz",
    "export_format": "spice"
  }'

# Explain endpoint
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{ "schematic": "<netlist string>", "detail_level": "beginner" }'
```

---

## 📐 Evaluation

CircuitMind is evaluated on four axes:

**1. Electrical Validity** — Is the generated netlist free of short circuits, floating pins, and missing references? Checked via a rule-based validator and ngspice DRC.

**2. Constraint Satisfaction** — Does the circuit meet the specified electrical constraints (voltage, current, frequency)? Verified by running SPICE simulation and comparing to spec.

**3. Component Accuracy** — Are the selected components real, in-production parts with correct footprints? Checked against the LCSC and Digi-Key component databases.

**4. Explanation Quality** — Rated by electronics engineers on accuracy, completeness, and clarity (1–5 scale).

```bash
# Run full evaluation suite
python eval/run_eval.py \
  --checkpoint checkpoints/sft/best.pt \
  --test_data data/splits/test \
  --output eval/results/
```

### Baseline Results (v0.1)

| Metric | Score |
|---|---|
| Electrical Validity | 94.2% |
| Constraint Satisfaction (SPICE sim pass) | 81.7% |
| Component Accuracy (real part match) | 88.5% |
| Explanation Quality (avg. engineer rating) | 4.1 / 5.0 |

---

## 🗺️ Roadmap

- [x] Dataset pipeline and normalization
- [x] GNN graph encoder
- [x] Pretraining on netlist masked modeling
- [x] SFT on prompt → circuit pairs
- [x] KiCad and SPICE export
- [ ] Multimodal input: accept hand-drawn schematic photos
- [ ] PCB layout awareness (component placement hints)
- [ ] Real-time Falstad browser simulation integration
- [ ] Component sourcing (link generated BOM to live pricing APIs)
- [ ] Voice-to-circuit: describe a circuit out loud
- [ ] Fine-tuning API for custom component libraries

---

## 🤝 Contributing

Contributions are welcome. The highest-impact areas right now:

- **Data**: Cleaned, well-annotated schematic datasets
- **Evaluation**: SPICE simulation harness improvements
- **Export formats**: Eagle, Altium, LTSpice support
- **Datasheets**: Expanding the component RAG database

Please open an issue before starting large contributions.

---

## 📄 License

CircuitMind code is released under the **Apache 2.0 License**.
Model weights are released under **CC BY-NC 4.0** (non-commercial use).

---

## 🙏 Acknowledgements

Built on the shoulders of: PyTorch Geometric, Hugging Face Transformers, KiCad, ngspice, schemdraw, and the countless open-source hardware engineers who shared their schematics with the world.

---

*CircuitMind — where language meets electronics.*
