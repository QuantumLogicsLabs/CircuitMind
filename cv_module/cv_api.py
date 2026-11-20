"""
CircuitMind - Computer Vision Module API
cv_module/cv_api.py

Exposes the YOLO-based CV pipeline via FastAPI routes.
Mount this router into the main api/app.py for a unified service,
or run standalone for testing.
"""

import os
import importlib.util
import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from cv_module.topology_extraction import image_to_circuit_json

logger = logging.getLogger(__name__)


def engine_available() -> bool:
    """True when the optional ultralytics dependency is installed."""
    return importlib.util.find_spec("ultralytics") is not None

# ── Model path resolution ──────────────────────────────────────────────────────
_MODEL_DIR   = Path(__file__).parent / "models"
MODEL_PATH   = str(_MODEL_DIR / "best.pt")
ACTIVE_MODEL = MODEL_PATH if os.path.exists(MODEL_PATH) else "yolov8n.pt"

# ── Router (attach to main app) ────────────────────────────────────────────────
router = APIRouter(prefix="/cv", tags=["computer-vision"])


@router.get("/status")
async def cv_status():
    """Health check for the CV module."""
    model_ready = os.path.exists(MODEL_PATH)
    engine_ready = engine_available()
    if not engine_ready:
        status = "engine_missing"
    elif model_ready:
        status = "ready"
    else:
        status = "running_on_fallback_weights"
    return {
        "module":           "Computer Vision",
        "status":           status,
        "engine_available": engine_ready,
        "model_path":       MODEL_PATH,
        "model_exists":     model_ready,
        "active_weights":   ACTIVE_MODEL,
        "supported_formats": ["PNG", "JPG", "JPEG"],
        "capabilities": [
            "Component detection (YOLOv8)",
            "Topology extraction",
            "Connection inference via wire tracing",
            "Circuit JSON generation",
        ],
    }


@router.post("/image-to-circuit")
async def image_to_circuit(
    image: UploadFile = File(..., description="Circuit schematic image (PNG/JPG)")
):
    """
    Upload a circuit image and receive structured circuit JSON.
    Uses YOLOv8 for component detection + OpenCV for wire tracing.
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (PNG/JPG/JPEG).")

    if not engine_available():
        raise HTTPException(
            status_code=503,
            detail="CV engine unavailable: install 'ultralytics' to enable image processing.",
        )

    tmp_path = None
    try:
        suffix = Path(image.filename or "upload").suffix or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await image.read())
            tmp_path = tmp.name

        circuit_json = image_to_circuit_json(
            image_path=tmp_path,
            model_path=ACTIVE_MODEL,
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "model_used": "custom" if ACTIVE_MODEL == MODEL_PATH else "fallback_baseline",
                "data": circuit_json,
            },
        )

    except Exception as e:
        logger.error(f"CV processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing image: {e}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/batch-process")
async def batch_process(
    images: list[UploadFile] = File(..., description="Multiple circuit images")
):
    """Process multiple circuit images and return results for each."""
    if not engine_available():
        raise HTTPException(
            status_code=503,
            detail="CV engine unavailable: install 'ultralytics' to enable image processing.",
        )

    results = []
    for image in images:
        tmp_path = None
        try:
            suffix = Path(image.filename or "upload").suffix or ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await image.read())
                tmp_path = tmp.name

            circuit_json = image_to_circuit_json(tmp_path, ACTIVE_MODEL)
            results.append({"filename": image.filename, "success": True, "circuit_data": circuit_json})

        except Exception as e:
            results.append({"filename": image.filename, "success": False, "error": str(e)})

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return {
        "total":      len(results),
        "successful": sum(1 for r in results if r["success"]),
        "failed":     sum(1 for r in results if not r["success"]),
        "results":    results,
    }


# ── Standalone app (for isolated testing) ─────────────────────────────────────
app = FastAPI(title="CircuitMind CV Module", version="1.0.0")
app.include_router(router)
