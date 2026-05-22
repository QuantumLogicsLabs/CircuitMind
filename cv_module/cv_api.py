"""
Computer Vision Module - API Interface
Author: SHAYAN HAIDER (CV Module Lead)
Aligned and Optimized by Team Lead

This FastAPI application exposes the CV pipeline to the team
Other modules can call this to get circuit JSON from images
"""

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cv_module.topology_extraction import image_to_circuit_json

# Initialize the core FastAPI app instance that test_cv_module.py expects!
app = FastAPI(
    title="CircuitMind AI - CV Module Gateway",
    description="FastAPI instance hosting the YOLO schematic object detector",
    version="1.0.0"
)

router = APIRouter()

# Path to trained YOLO model
MODEL_PATH = "./cv_module/models/best.pt"

# Framework safe check: Use baseline weight fallback if best.pt is not yet trained
ACTIVE_MODEL_PATH = MODEL_PATH if os.path.exists(MODEL_PATH) else "yolov8n.pt"


@router.post("/cv/image-to-circuit")
async def image_to_circuit(
    image: UploadFile = File(..., description="Circuit schematic image (PNG/JPG)")
):
    """
    🎯 PRIMARY CV ENDPOINT
    Converts uploaded circuit image to structured JSON
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image (PNG/JPG)")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            contents = await image.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        circuit_json = image_to_circuit_json(
            image_path=tmp_path,
            model_path=ACTIVE_MODEL_PATH
        )
        
        os.unlink(tmp_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Circuit extracted using {'Custom Weights' if ACTIVE_MODEL_PATH == MODEL_PATH else 'Cloud Fallback Baseline'}",
                "data": circuit_json
            }
        )
    
    except Exception as e:
        if 'tmp_path' in locals():
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@router.get("/cv/status")
async def cv_module_status():
    """Check CV module health and model status"""
    model_exists = os.path.exists(MODEL_PATH)
    return {
        "module": "Computer Vision",
        "status": "ready" if model_exists else "running_on_fallback_weights",
        "model_path": MODEL_PATH,
        "model_exists": model_exists,
        "active_weights": ACTIVE_MODEL_PATH,
        "supported_formats": ["PNG", "JPG", "JPEG"],
        "capabilities": [
            "Component detection (YOLO)",
            "Topology extraction",
            "Connection inference",
            "Circuit JSON generation"
        ]
    }


@router.post("/cv/batch-process")
async def batch_process_images(
    images: list[UploadFile] = File(..., description="Multiple circuit images")
):
    """Process multiple circuit images in batch"""
    results = []
    for image in images:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                contents = await image.read()
                tmp_file.write(contents)
                tmp_path = tmp_file.name
            
            circuit_json = image_to_circuit_json(tmp_path, ACTIVE_MODEL_PATH)
            results.append({
                "filename": image.filename,
                "success": True,
                "circuit_data": circuit_json
            })
            os.unlink(tmp_path)
        except Exception as e:
            results.append({
                "filename": image.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total_images": len(images),
        "successful": sum(1 for r in results if r['success']),
        "failed": sum(1 for r in results if not r['success']),
        "results": results
    }

# Register the router routes cleanly into the main app instance
app.include_router(router)