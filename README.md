# CircuitMind

> **An AI-powered electronics assistant that generates, explains, diagnoses, and exports simple circuits from a natural-language prompt.**

---

## What it does

CircuitMind is a FastAPI service (plus a Streamlit UI) that turns a plain-English request like *"make me a LED circuit"* into a structured circuit description, and can then explain it in plain English, check it for common electrical mistakes, and export it to SPICE, SVG, or a logic-gate JSON format.

It is **not** a fine-tuned domain-specific model. Circuit generation is done by an LLM call to Groq's hosted `llama-3.3-70b-versatile`, constrained by a system prompt to a fixed vocabulary of ~30 component types, with a deterministic keyword-matching fallback for when the LLM is unavailable. Explaining and diagnosing are done with a hand-curated component knowledge base and a set of rule-based checks — not machine learning.

---

## ⚙️ How It Actually Works

| Step | Module | Approach |
|---|---|---|
| **Generate** | [`generate/generate.py`](generate/generate.py) | Prompt → Groq LLM (JSON-constrained) → falls back to 8 hardcoded keyword-matched circuit templates (LED, motor, buzzer, fan, temperature sensor, solar charger, 555 timer, RC filter) if the LLM call fails |
| **Explain** | [`explain/explain_module.py`](explain/explain_module.py) | Looks each component up in [`utils/component_resolver.py`](utils/component_resolver.py)'s knowledge base (~30 components with role + description), builds a plain-English explanation, current-flow description, and warnings |
| **Diagnose** | [`diagnose/diagnose_module.py`](diagnose/diagnose_module.py) | Rule-based checks: missing power source, missing current-limiting resistor, no connections defined, BFS-based short-circuit detection, floating (disconnected) components, unspecified capacitor polarity, missing ground reference |
| **Export** | [`export/export_module.py`](export/export_module.py) | Converts circuit JSON to a SPICE netlist, an SVG schematic (via `schemdraw`), or a gate-graph JSON (for a logic-gate simulator front end) |
| **Hint** | [`hint/hint_module.py`](hint/hint_module.py) | Given a digital-logic problem (truth table, I/O ports) and a student's current gate/wire graph from an external circuit builder, returns one short, non-spoiler hint via Groq — falls back to a few deterministic rule-based checks (empty canvas, missing I/O gates, floating gates) if the LLM call fails |

A circuit is represented throughout as a simple JSON object:
```json
{
  "circuit_name": "LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"]
}
```

> **Note:** Generate/Explain/Diagnose/Export are all scoped to *electronics* components (batteries, resistors, LEDs, transistors, ICs — see `utils/component_resolver.py`). Hint is the one exception: it's scoped to *digital-logic gates* (AND/OR/NOT/XOR/…) for an external logic-gate circuit builder, and uses its own gate/wire graph shape rather than the `components`/`connections` format above.

---

## 🗂️ Project Structure

```
CircuitMind/
├── api/
│   ├── app.py                  # FastAPI server (all endpoints)
│   └── requirements.txt        # Slim deps for the Vercel serverless deployment
├── generate/generate.py        # Prompt → circuit JSON (Groq LLM + rule-based fallback)
├── explain/explain_module.py   # Circuit JSON → plain-English explanation
├── diagnose/diagnose_module.py # Circuit JSON → electrical-issue checks
├── export/export_module.py     # Circuit JSON → SPICE / SVG / gate JSON
├── hint/hint_module.py         # Digital-logic problem + student's gate graph → one hint
├── utils/component_resolver.py # Shared component knowledge base + name normalization
├── app_streamlit.py            # Streamlit UI (Generate / Explain / Diagnose / Export / Chatbot tabs)
├── cv_module/                  # Experimental, NOT wired into the API — see note below
├── fpu/                        # 32-bit IEEE-754 FPU (Verilog-2001, standalone)
├── website/                    # Git submodule (separate repo, deployed independently on Vercel)
├── tests/test_all_modules.py   # pytest suite covering all four modules
├── Dockerfile                  # Builds the API and Streamlit containers
├── docker-compose.yml          # Runs API (7860) + Streamlit (8501) together
├── requirements.txt            # Full dependency set (API + Streamlit)
├── vercel.json                 # Deploys api/app.py as a Vercel Python function
└── .env.example
```

---

## 🔧 FPU (32-bit IEEE-754)

`fpu/` contains a combinational, single-cycle floating-point unit written in Verilog-2001. It is a standalone hardware module and is independent of the Python circuit assistant.

**Scope**

- `fp_add` implements IEEE-754 binary32 addition and subtraction, including subnormals, round-to-nearest-even, and the `invalid` / `overflow` / `underflow` / `inexact` flags.
- `fpu_top` decodes a 2-bit opcode: `00` add, `01` subtract, `10` multiply, `11` divide. Multiply and divide are currently flagged stubs (`stub_active = 1`) that return the canonical qNaN `0x7FC00000`.

**Datapath**

1. Unpack the operands and compare magnitudes using the effective exponent (`1` for subnormals).
2. Align the smaller significand and keep guard, round, and sticky bits.
3. Add or subtract the significands; subtraction compensates for the truncated sticky bit.
4. Normalize (carry, leading-zero shift, subnormal clamp) and round to nearest-even.
5. Assemble the result and exception flags.

**Modules**

| File | Role |
|---|---|
| `fpu/rtl/fp_add.v` | Add/sub wrapper: special cases, operand swap, flag mux |
| `fpu/rtl/fp_compare_mag.v` | Effective-exponent and magnitude comparison |
| `fpu/rtl/fp_align.v` | Significand alignment with guard/round/sticky |
| `fpu/rtl/fp_addsub_core.v` | 28-bit significand add/subtract |
| `fpu/rtl/fp_normalize.v` | Normalization and round-to-nearest-even |
| `fpu/rtl/fpu_control.v` | Opcode decode |
| `fpu/rtl/fpu_top.v` | Integrated top: add/sub plus mul/div sockets |
| `fpu/rtl/stubs/fp_mul_stub.v`, `fpu/rtl/stubs/fp_div_stub.v` | Placeholders for the arithmetic modules |

See [`fpu/README.md`](fpu/README.md) for the port list, the stub contract, and verification details.

**Running the tests**

The testbenches run on the WASM build of Icarus Verilog, so no native Verilog install is needed. Node.js 24+ is required:

```bash
cd fpu
npm ci
npm test
```

The suites read the committed vectors in `fpu/vectors/` and compare both the result bits and the four IEEE exception flags.

**Integration notes**

- `fpu_top` is purely combinational: no clock, reset, or internal state.
- Flags are valid for every operation; stub operations return qNaN with all flags deasserted and `stub_active` high.
- Special cases follow IEEE-754: canonical qNaN output, signaling-NaN and `Inf - Inf` invalid, signed-zero rules, and overflow/underflow reporting.
- The FPU is not wired into the Python API or the circuit export formats; it is a self-contained HDL unit.

---

## 📦 Installation

### Requirements
- Python 3.10+
- A free [Groq API key](https://console.groq.com) (for LLM-backed generation and the Streamlit chatbot tab; both still work in a degraded mode without one)

### Setup
```bash
git clone https://github.com/QuantumLogicsLabs/CircuitMind.git
cd CircuitMind

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# then edit .env and set GROQ_API_KEY
```

### Run the API
```bash
uvicorn api.app:app --reload
# Interactive docs: http://localhost:8000/docs
```

### Run the Streamlit UI
```bash
streamlit run app_streamlit.py
```

### Run both together (Docker Compose)
```bash
docker-compose up --build
# API:       http://localhost:8000
# Streamlit: http://localhost:8501
```

---

## 🚀 REST API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/generate` | Prompt → circuit JSON |
| POST | `/explain` | Circuit JSON → plain-English explanation |
| POST | `/diagnose` | Circuit JSON → electrical-issue report |
| POST | `/export` | Circuit JSON → `spice` / `svg` / `gate_json` |
| POST | `/hint` | Digital-logic problem + student's gate graph → one non-spoiler hint |
| POST | `/generate-and-explain` | Generate + explain + diagnose in one call |

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "make me a LED circuit"}'
```

Full request/response examples are in [`api/README.md`](api/README.md).

Requests are rate-limited per-IP via `slowapi` (5/min on `/generate`, 10/min on `/explain`, `/diagnose`, `/export`, `/hint`, 3/min on `/generate-and-explain`) and, if `CIRCUITMIND_API_KEY` is set, require an `X-API-Key` header.

---

## 🔑 Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | Yes, for LLM generation | Without it, `/generate` falls back to the rule-based templates |
| `CIRCUITMIND_API_KEY` | No | If set, locks the API behind an `X-API-Key` header; unset = open access |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS allow-list (defaults to local Streamlit ports) |
| `RATE_LIMIT_REDIS_URL` | No | Redis connection string so rate limits hold across serverless instances (used on Vercel); falls back to in-memory otherwise |

---

## ☁️ Deployment

**Docker Compose** — the original deployment path. `docker-compose.yml` builds both the API and Streamlit containers from the shared `Dockerfile`/`requirements.txt`.

**Vercel (API only)** — `vercel.json` and `api/requirements.txt` deploy `api/app.py` as a Python serverless function. This works because the API path has no local model weights and does no long-running or stateful work per request — it's a thin FastAPI layer around a Groq API call. Set the four environment variables above on the Vercel project, plus provision a Redis instance (e.g. Upstash via Vercel Storage) for `RATE_LIMIT_REDIS_URL`.

The **Streamlit UI is not deployed on Vercel** — it needs a persistent process and WebSocket connection, which serverless functions don't support. It runs via the existing `Dockerfile` on any container host (Render, Fly.io, Railway, Hugging Face Spaces, etc.) if needed.

The **website/** frontend is a separate submodule/repo, deployed on its own — not part of this deployment.

---

## 🧪 Testing

```bash
pytest tests/
```
Covers all four modules individually (`TestGenerate`, `TestExplain`, `TestDiagnose`, `TestExport`) plus end-to-end integration cases (generate → explain, generate → diagnose, generate → export).

The FPU has its own self-checking simulation suite: `cd fpu && npm ci && npm test`.

---

## ⚠️ Known Limitations

- Generation quality is bounded by the LLM prompt and by 8 hardcoded fallback templates — there's no trained, domain-specific circuit model, no SPICE simulation to validate generated circuits, and no real component/BOM sourcing.
- The component knowledge base (`utils/component_resolver.py`) covers ~30 common component types; anything outside it is treated as "unknown" by Explain/Diagnose.
- **`cv_module/`** (image → circuit JSON via YOLO object detection) is an unfinished, standalone experiment. It requires manually downloading trained YOLO weights, has its own `requirements_cv.txt` (`torch`, `ultralytics`, `opencv-python`), and is **not imported or exposed by `api/app.py`**.
- Rate limiting defaults to in-memory storage, which only holds correctly within a single running process — set `RATE_LIMIT_REDIS_URL` for multi-instance/serverless deployments.
- The FPU (`fpu/`) is verified in simulation only — there is no synthesis or timing sign-off yet — and its multiply/divide paths are stubs until the arithmetic modules land.

```json
{
  "circuit_name": "LED Circuit",
  "components": ["battery", "resistor", "led"],
  "connections": ["battery -> resistor -> led"]
}
```

CircuitMind is **proprietary software** — see [`LICENSE`](LICENSE) for the full terms. It is not open source; contributions and use are governed by that agreement.

---

*CircuitMind — a practical circuit assistant, not a research model.*
