# CircuitMind API

**Developer:** Alia  
**Module:** REST API Server — connects all 4 CircuitMind modules

---

## What It Does

This FastAPI server connects all 5 modules (Generate, Explain, Diagnose, Export, Hint) into a single running service. Any frontend, tool, or script can send requests to this API and get circuit results back.

---

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check — confirms API is running |
| GET | `/health` | Liveness probe — always returns `{"status": "ok"}` |
| POST | `/generate` | Convert natural language prompt to circuit JSON |
| POST | `/explain` | Explain a circuit in plain English |
| POST | `/diagnose` | Check circuit for electrical issues |
| POST | `/export` | Export circuit to SPICE netlist, SVG or gate JSON |
| POST | `/hint` | Digital-logic circuit-builder hint (truth table + student's current gate graph → one non-spoiler hint) |
| POST | `/generate-and-explain` | Generate + explain + diagnose in one request |

### Authentication

Authentication is optional. If the server is started with `CIRCUITMIND_API_KEY`
set, every `POST` endpoint requires that key in the `X-API-Key` header:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $CIRCUITMIND_API_KEY" \
  -d '{"prompt": "555 timer circuit"}'
```

A missing or wrong key returns `401` with `{"detail": "Invalid or missing API key"}`.
When the variable is unset the API is open (development mode).

### Rate limits

Limits are per client IP, enforced with `slowapi`:

| Endpoint | Limit |
|---|---|
| `/generate` | 5/minute |
| `/generate-and-explain` | 3/minute |
| `/explain`, `/diagnose`, `/export`, `/hint` | 10/minute |

Exceeding a limit returns `429 Too Many Requests`. Set `RATE_LIMIT_REDIS_URL`
to a Redis instance (for example Upstash) so limits hold across multiple
serverless instances; otherwise the limiter uses in-process memory.

### CORS

Allowed origins come from the comma-separated `ALLOWED_ORIGINS` environment
variable (Streamlit and localhost dev ports by default). `GET` and `POST` are
allowed.

### Error responses

| Status | Meaning |
|---|---|
| `401` | `CIRCUITMIND_API_KEY` is set and the `X-API-Key` header is missing or wrong |
| `422` | Request body failed validation (empty/overlong prompt, unsupported `export_format`, missing circuit fields, …) |
| `429` | Rate limit exceeded |
| `500` | Unhandled server error — body is `{"error": "Internal server error. Please try again."}` |

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add API key
```bash
cp .env.example .env
```
Open `.env` and add your Groq API key. Get a free key at [console.groq.com](https://console.groq.com).

```
GROQ_API_KEY=your_key_here
```

### 3. Run the server
```bash
uvicorn api.app:app --reload
```

### 4. Open interactive docs
```
http://localhost:8000/docs
```

---

## Example Requests

### Generate a circuit
```json
POST /generate
{
  "prompt": "make me a LED circuit"
}
```

Response:
```json
{
  "circuit_name": "LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"],
  "confidence": "high",
  "source": "llm"
}
```

### Explain a circuit
```json
POST /explain
{
  "circuit_json": {
    "circuit_name": "LED Circuit",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"]
  }
}
```

### Diagnose a circuit
```json
POST /diagnose
{
  "circuit_json": {
    "circuit_name": "Bad Circuit",
    "components": ["battery", "led"],
    "connections": ["battery -> led"]
  }
}
```

### Export to SPICE
```json
POST /export
{
  "circuit_json": {
    "circuit_name": "LED Circuit",
    "components": ["battery", "resistor", "led"],
    "connections": ["battery -> resistor -> led"]
  },
  "export_format": "spice"
}
```

### All in one
```json
POST /generate-and-explain
{
  "prompt": "555 timer circuit"
}
```

### Get a hint for a digital-logic problem
```json
POST /hint
{
  "problem_title": "Half Adder",
  "problem_description": "Two 1-bit inputs A and B, outputs Sum (S) and Carry (C).",
  "inputs": ["A", "B"],
  "outputs": ["S", "C"],
  "truth_table": [
    {"A": 0, "B": 0, "S": 0, "C": 0},
    {"A": 0, "B": 1, "S": 1, "C": 0},
    {"A": 1, "B": 0, "S": 1, "C": 0},
    {"A": 1, "B": 1, "S": 0, "C": 1}
  ],
  "gates": [{"id": 1, "type": "INPUT", "label": "A"}, {"id": 2, "type": "INPUT", "label": "B"}],
  "wires": [],
  "last_result": null
}
```

Response:
```json
{
  "hint": "It looks like you've just started ... consider using a gate that produces an output of 1 when the two inputs are different.",
  "source": "llm"
}
```

`gates`/`wires` use the same shape as the logic-gate simulator's export format (`export_format=gate_json`): `{id, type, label, ...}` gates and `{fromId, toId, toIndex}` wires. `last_result` is optional context from the caller's own validator, e.g. `{"passed": false, "failing_rows": [...]}`.

---

## Files

| File | Purpose |
|---|---|
| `app.py` | Main FastAPI server code |
| `README.md` | This file |
