# CircuitMind AI — Explain Module
**Author:** Mustehsan Kazmi
**Sub-Team:** NLP Module (Generation & Explanation)
**Pipeline Position:** Circuit JSON → **Explain Module** → GNN Diagnosis

---

## What This Module Does

Takes a circuit JSON (components + connections) and generates a plain-English explanation of the circuit at three levels of technical depth:

| Level | Audience | Style |
|---|---|---|
| `beginner` | No electronics background | Simple language, analogies, no equations |
| `intermediate` | Engineering student | Standard terminology, current/voltage flow |
| `expert` | Senior engineer | KVL/KCL equations, fault analysis, design trade-offs |

---

## How It Works (Multi-Agent System)

Instead of fine-tuning a model (which takes days of compute), this module uses a **two-agent prompt chain** on top of a free hosted LLM (Llama 3.1 via Groq):

```
Circuit JSON
     │
     ▼
┌─────────────────────────────────────┐
│  Agent 1 — Circuit Analyzer         │
│  Reads the JSON, extracts:          │
│  - Component roles                  │
│  - Topology type (series/parallel)  │
│  - Circuit purpose                  │
│  - Beginner & expert key points     │
│  Output: structured analysis JSON   │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  Agent 2 — Explanation Writer       │
│  Takes analysis + requested level   │
│  Writes final human-readable text   │
│  Output: explanation string         │
└─────────────────────────────────────┘
```

Two agents are used because splitting "understand the circuit" and "write the explanation" into separate focused calls produces more reliable, higher-quality output than a single prompt trying to do both.

---

## File Structure

```
CircuitMinds-Explain/
│
├── explain_module.py        # Core logic — two-agent system
├── explain_api.py           # FastAPI router — plugs into master pipeline
├── test_explain.py          # Test script with hardcoded mock circuits
├── requirements_explain.txt # Dependencies
└── README.md                # This file
```

---

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements_explain.txt
```

### 2. Get a Free Groq API Key
- Go to [console.groq.com](https://console.groq.com)
- Sign up and create an API key

### 3. Set the API Key

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your_key_here"
```

**Mac/Linux:**
```bash
export GROQ_API_KEY="your_key_here"
```

**Or use a `.env` file (recommended):**
```
GROQ_API_KEY=your_key_here
```
Then add `from dotenv import load_dotenv; load_dotenv()` at the top of `explain_module.py`.

---

## Running the Test Script

```bash
python test_explain.py
```

This runs three mock circuits through the pipeline:
- Basic LED Circuit → beginner level
- AND-NOT-OR Logic Chain → expert level
- Voltage Divider → intermediate level

No upstream modules needed — uses hardcoded JSON payloads.

---

## Using the Module in Code

```python
from explain_module import explain_circuit

circuit_json = {
    "components": [
        {"id": "C1", "type": "BATTERY",  "value": "9V",    "label": "Power Supply"},
        {"id": "C2", "type": "RESISTOR", "value": "220ohm","label": "Current Limiter"},
        {"id": "C3", "type": "LED",      "value": None,    "label": "Output LED"}
    ],
    "connections": [
        {"from": "C1", "to": "C2", "wire_id": "W1"},
        {"from": "C2", "to": "C3", "wire_id": "W2"},
        {"from": "C3", "to": "C1", "wire_id": "W3"}
    ]
}

result = explain_circuit(circuit_json, level="beginner")
print(result["explanation"])
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `circuit_json` | `dict` | required | Standard CircuitMind JSON |
| `level` | `str` | `"beginner"` | `"beginner"` / `"intermediate"` / `"expert"` |
| `return_analysis` | `bool` | `False` | If `True`, also returns Agent 1's analysis object |

### Return Value

```python
{
    "level":       "beginner",
    "explanation": "This circuit lights up an LED using a battery...",
    "analysis":    { ... }   # only present if return_analysis=True
}
```

---

## FastAPI Integration (For Team Captain)

In the master FastAPI app, add these two lines:

```python
from explain_api import router as explain_router
app.include_router(explain_router)
```

This exposes two endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/explain/` | Main explanation endpoint |
| `GET` | `/explain/health` | Health check |

### Example Request Body

```json
{
    "circuit": {
        "components": [
            {"id": "C1", "type": "BATTERY", "value": "9V", "label": "Power Supply"},
            {"id": "C2", "type": "RESISTOR", "value": "220ohm", "label": "R1"},
            {"id": "C3", "type": "LED", "value": null, "label": "LED1"}
        ],
        "connections": [
            {"from": "C1", "to": "C2", "wire_id": "W1"},
            {"from": "C2", "to": "C3", "wire_id": "W2"},
            {"from": "C3", "to": "C1", "wire_id": "W3"}
        ]
    },
    "level": "expert",
    "return_analysis": false
}
```

### Example Response

```json
{
    "level": "expert",
    "explanation": "This series circuit employs a current-limiting resistor...",
    "analysis": null
}
```

---

## Circuit JSON Schema

This module expects the standard CircuitMind project schema:

```json
{
    "components": [
        {
            "id":    "C1",
            "type":  "RESISTOR",
            "value": "220ohm",
            "label": "Current Limiter"
        }
    ],
    "connections": [
        {
            "from":    "C1",
            "to":      "C2",
            "wire_id": "W1"
        }
    ],
    "metadata": {}
}
```

Supported component types include: `BATTERY`, `RESISTOR`, `LED`, `CAPACITOR`, `GROUND`, `INPUT`, `OUTPUT`, `AND`, `OR`, `NOT`, `XOR`, `NAND`, `NOR` and any other type — Agent 1 handles unknown types gracefully.

---

## Pipeline Integration (When Haseeb's Module is Ready)

Currently `test_explain.py` uses hardcoded JSON. When Haseeb's Text-to-Circuit Generator is complete, the swap is straightforward:

**Before (testing):**
```python
circuit_json = MOCK_LED_CIRCUIT   # hardcoded
result = explain_circuit(circuit_json, level="beginner")
```

**After (live pipeline):**
```python
circuit_json = haseeb_module.generate(user_prompt)   # live
result = explain_circuit(circuit_json, level="beginner")
```

Zero changes needed inside `explain_module.py`.

---

## Dependencies

| Package | Purpose |
|---|---|
| `groq` | LLM API client (Llama 3.1 8B) |
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server |
| `pydantic` | Request/response validation |
| `python-dotenv` | Optional — load `.env` file |

---

## Model

**Current model:** `llama-3.1-8b-instant` via Groq API

Free tier is sufficient for development and demo. No GPU required, no training required.
