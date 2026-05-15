
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import json

# Sab 4 modules import karo
from generate.generate import generate_circuit
from explain.explain_module import explain_circuit
from diagnose.diagnose_module import diagnose_circuit
from export.export_module import export_module

# FastAPI app banao
app = FastAPI(
    title="CircuitMind API",
    description="AI-powered circuit generator, explainer, and diagnostics tool",
    version="1.0.0"
)

# ── Input formats ──────────────────────────────────────────────
class GenerateRequest(BaseModel):
    prompt: str                          # e.g. "make me a LED circuit"

class CircuitRequest(BaseModel):
    circuit_json: dict                   # circuit JSON object

class ExportRequest(BaseModel):
    circuit_json: dict
    export_format: Optional[str] = "spice"   # "spice" or "svg"

# ── Endpoints ──────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "CircuitMind API is live!",
        "endpoints": {
            "generate":            "POST /generate",
            "explain":             "POST /explain",
            "diagnose":            "POST /diagnose",
            "export":              "POST /export",
            "generate_and_explain": "POST /generate-and-explain"
        }
    }

@app.post("/generate")
def generate(req: GenerateRequest):
    """
    Input:  { "prompt": "make me a LED circuit" }
    Output: circuit JSON
    """
    result = generate_circuit(req.prompt)
    return result

@app.post("/explain")
def explain(req: CircuitRequest):
    """
    Input:  { "circuit_json": { "components": [...], "connections": [...] } }
    Output: explanation text + component details + warnings
    """
    result = explain_circuit(req.circuit_json)
    return result

@app.post("/diagnose")
def diagnose(req: CircuitRequest):
    """
    Input:  { "circuit_json": { "components": [...], "connections": [...] } }
    Output: issues list + passed (true/false)
    """
    result = diagnose_circuit(req.circuit_json)
    return result

@app.post("/export")
def export(req: ExportRequest):
    """
    Input:  { "circuit_json": {...}, "export_format": "spice" }
    Output: spice_netlist ya svg_file
    """
    json_str = json.dumps(req.circuit_json)
    result = export_module(json_str, export_format=req.export_format)
    return result

@app.post("/generate-and-explain")
def generate_and_explain(req: GenerateRequest):
    """
    Input:  { "prompt": "LED circuit banao" }
    Output: circuit + explanation + diagnosis
    """
    circuit = generate_circuit(req.prompt)
    if "error" in circuit:
        return circuit
    return {
        "circuit":     circuit,
        "explanation": explain_circuit(circuit),
        "diagnosis":   diagnose_circuit(circuit)
    }
