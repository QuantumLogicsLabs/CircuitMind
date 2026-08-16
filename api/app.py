import sys
import os
import logging
import time
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional

# ── RATE LIMITING ───────────────────────────────────────────────
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.extension import _rate_limit_exceeded_handler

# ── LOCAL MODULES ───────────────────────────────────────────────
from generate.generate import generate_circuit
from explain.explain_module import explain_circuit
from diagnose.diagnose_module import diagnose_circuit
from export.export_module import export_module
from hint.hint_module import generate_hint

# ── LOGGING ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("circuitmind")

# ── APP ──────────────────────────────────────────────────────────
app = FastAPI(
    title="CircuitMind API",
    description="AI-powered circuit generator, explainer, and diagnostics tool",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── RATE LIMITER SETUP ──────────────────────────────────────────
# storage_uri points at Redis (e.g. Upstash) in production so limits hold
# across serverless instances; falls back to in-memory when unset (local dev).
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.environ.get("RATE_LIMIT_REDIS_URL"),
)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── API KEY SECURITY ─────────────────────────────────────────────
API_KEY = os.environ.get("CIRCUITMIND_API_KEY")

def verify_api_key(x_api_key: str = Header(default=None)):
    if not API_KEY:
        return  # dev mode (open access)

    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

# ── CORS ─────────────────────────────────────────────────────────
allowed_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── MIDDLEWARE ───────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 1)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response

# ── GLOBAL ERROR HANDLER ─────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error. Please try again."},
    )

# ── RATE LIMIT SHORTCUT ──────────────────────────────────────────
def rl(limit: str):
    return limiter.limit(limit)

# ── REQUEST MODELS ───────────────────────────────────────────────
class GenerateRequest(BaseModel):
    prompt: str

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("prompt cannot be empty")
        if len(v) > 1000:
            raise ValueError("prompt must be under 1000 characters")
        return v.strip()

class CircuitRequest(BaseModel):
    circuit_json: dict

class ExportRequest(BaseModel):
    circuit_json: dict
    export_format: Optional[str] = "spice"

    @field_validator("export_format")
    @classmethod
    def valid_format(cls, v: str) -> str:
        allowed = {"spice", "svg", "gate_json"}
        if v not in allowed:
            raise ValueError(f"export_format must be one of {allowed}")
        return v

class GenerateAndExportRequest(BaseModel):
    prompt: str
    export_format: Optional[str] = "gate_json"

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("prompt cannot be empty")
        if len(v) > 1000:
            raise ValueError("prompt must be under 1000 characters")
        return v.strip()

    @field_validator("export_format")
    @classmethod
    def valid_format(cls, v: str) -> str:
        allowed = {"spice", "svg", "gate_json"}
        if v not in allowed:
            raise ValueError(f"export_format must be one of {allowed}")
        return v

class HintRequest(BaseModel):
    problem_title: str = ""
    problem_description: Optional[str] = ""
    inputs: list[str] = []
    outputs: list[str] = []
    truth_table: list[dict] = []
    gates: list[dict] = []
    wires: list[dict] = []
    last_result: Optional[dict] = None

# ── HEALTH ───────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def root():
    return {
        "status": "running",
        "message": "CircuitMind API is live!",
        "version": "1.0.0",
    }

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

# ── CORE ENDPOINTS ───────────────────────────────────────────────

@app.post("/generate", tags=["core"])
@rl("5/minute")
def generate(
    request: Request,
    req: GenerateRequest,
    _: None = Depends(verify_api_key),
):
    logger.info(f"Generate request: '{req.prompt[:60]}'")

    result = generate_circuit(req.prompt)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    return result


@app.post("/explain", tags=["core"])
@rl("10/minute")
def explain(
    request: Request,
    req: CircuitRequest,
    _: None = Depends(verify_api_key),
):
    logger.info("Explain request received")
    return explain_circuit(req.circuit_json)


@app.post("/diagnose", tags=["core"])
@rl("10/minute")
def diagnose(
    request: Request,
    req: CircuitRequest,
    _: None = Depends(verify_api_key),
):
    logger.info("Diagnose request received")
    return diagnose_circuit(req.circuit_json)


@app.post("/export", tags=["core"])
@rl("10/minute")
def export(
    request: Request,
    req: ExportRequest,
    _: None = Depends(verify_api_key),
):
    logger.info(f"Export request: format={req.export_format}")

    json_str = json.dumps(req.circuit_json)
    result = export_module(json_str, export_format=req.export_format)

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result["message"])

    return result


@app.post("/hint", tags=["core"])
@rl("10/minute")
def hint(
    request: Request,
    req: HintRequest,
    _: None = Depends(verify_api_key),
):
    logger.info(f"Hint request: '{req.problem_title[:60]}'")
    return generate_hint(req.model_dump())


@app.post("/generate-and-explain", tags=["core"])
@rl("3/minute")
def generate_and_explain(
    request: Request,
    req: GenerateRequest,
    _: None = Depends(verify_api_key),
):
    logger.info(f"Generate-and-explain request: '{req.prompt[:60]}'")

    circuit = generate_circuit(req.prompt)
    if "error" in circuit:
        raise HTTPException(status_code=422, detail=circuit["error"])

    return {
        "circuit": circuit,
        "explanation": explain_circuit(circuit),
        "diagnosis": diagnose_circuit(circuit),
    }


@app.post("/generate-and-export", tags=["core"])
@rl("5/minute")
def generate_and_export(
    request: Request,
    req: GenerateAndExportRequest,
    _: None = Depends(verify_api_key),
):
    logger.info(f"Generate-and-export request: '{req.prompt[:60]}', format={req.export_format}")

    circuit = generate_circuit(req.prompt)
    if "error" in circuit:
        raise HTTPException(status_code=422, detail=circuit["error"])

    export_result = export_module(json.dumps(circuit), export_format=req.export_format)
    if export_result.get("status") == "error":
        raise HTTPException(status_code=422, detail=export_result["message"])

    return {
        "circuit": circuit,
        "export": export_result,
    }