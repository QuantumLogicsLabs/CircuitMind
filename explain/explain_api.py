"""
CircuitMind AI — Explain Module FastAPI Endpoint
=================================================
Author  : Mustehsan Kazmi
Endpoint: POST /explain

This file exposes the Explain Module as a FastAPI router.
The Team Captain integrates it into the master FastAPI app like this:

    # In the master app (team captain's file)
    from explain_api import router as explain_router
    app.include_router(explain_router)

That's it — no other changes needed from your side.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
import traceback

from explain_module import explain_circuit   # your core module

router = APIRouter(prefix="/explain", tags=["Explain Module"])


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class ComponentModel(BaseModel):
    id:    str
    type:  str                       # AND, OR, NOT, RESISTOR, LED, etc.
    value: Optional[str] = None      # e.g. "220ohm", "5V"
    label: Optional[str] = None

class ConnectionModel(BaseModel):
    from_:  str = Field(..., alias="from")
    to:     str
    wire_id: str

    class Config:
        populate_by_name = True

class CircuitJSON(BaseModel):
    components:  list[ComponentModel]
    connections: list[ConnectionModel]
    metadata:    Optional[dict] = None

class ExplainRequest(BaseModel):
    circuit:         CircuitJSON
    level:           Literal["beginner", "intermediate", "expert"] = "beginner"
    return_analysis: bool = False

class ExplainResponse(BaseModel):
    level:       str
    explanation: str
    analysis:    Optional[dict] = None


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=ExplainResponse)
async def explain_endpoint(request: ExplainRequest):
    """
    Accepts a CircuitMind JSON and returns a plain-English explanation.

    - **level**: "beginner" | "intermediate" | "expert"
    - **return_analysis**: set to true to also get the intermediate analysis object

    The circuit JSON must follow the standard CircuitMind schema
    (components list + connections list).
    """
    try:
        # Convert Pydantic model → plain dict for the explain module
        circuit_dict = request.circuit.model_dump(by_alias=True)

        result = explain_circuit(
            circuit_json    = circuit_dict,
            level           = request.level,
            return_analysis = request.return_analysis,
        )
        return ExplainResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Explain Module error: {str(e)}\n{traceback.format_exc()}"
        )


@router.get("/health")
async def health_check():
    """Quick health check — lets the team captain verify the module is alive."""
    return {"module": "explain", "status": "ok"}
