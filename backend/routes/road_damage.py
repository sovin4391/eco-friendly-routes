"""
Road Damage Detection FastAPI Routes.

Provides endpoints for:
- Checking road damage model availability and supported classes
- Performing authentic object detection inference on uploaded pavement images
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Query, status
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Dict, Any, List

from backend.services.road_damage_service import road_damage_service

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_IMAGES_DIR = PROJECT_ROOT / "dataset" / "processed" / "road_damage" / "images" / "test"

router = APIRouter()

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}


@router.get("/status")
def get_road_damage_status() -> Dict[str, Any]:
    """
    Returns the current operational status of the road damage detection model,
    including weights presence and supported defect categories.
    """
    available = road_damage_service.is_available()
    return {
        "model_loaded": available,
        "service_name": "RDD2022 Road Damage & Pothole Detector",
        "supported_classes": road_damage_service.get_supported_classes(),
        "weights_path": str(road_damage_service.weights_path.name) if available else None,
        "status_message": (
            "Model is active and ready for visual inference."
            if available
            else "Model weights not loaded. Inspection/demo mode only."
        ),
    }


@router.post("/detect")
async def detect_road_damage(
    file: UploadFile = File(..., description="Pavement camera image (JPEG or PNG, max 10MB)"),
    conf_threshold: float = Query(0.25, ge=0.05, le=0.95, description="Confidence threshold [0.05 - 0.95]")
) -> Dict[str, Any]:
    """
    Analyzes an uploaded road surface photo for potholes and cracks using
    the trained RDD2022 detector.
    """
    # 1. Validate content type
    content_type = file.content_type.lower() if file.content_type else ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}'. Please upload a JPEG or PNG image."
        )

    # 2. Read and validate file size
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded image: {e}"
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image size exceeds 10MB limit ({len(contents) / (1024*1024):.2f} MB)."
        )

    # 3. Check model availability
    if not road_damage_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Road damage detection model is currently unavailable. "
                "No trained weights were found under models/road_damage/best.pt."
            )
        )

    # 3. Perform inference
    try:
        result = road_damage_service.detect_damage(contents, conf_threshold=conf_threshold)
        result["filename"] = file.filename
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {ex}"
        )


SAMPLE_IMAGES = [
    {
        "filename": "India_000168.jpg",
        "title": "Alligator Fatigue Cracking",
        "defect_type": "D20: Alligator Crack",
        "description": "Interlocking fatigue fracture network across wheel path",
        "url": "/api/v1/road-damage/samples/India_000168.jpg"
    },
    {
        "filename": "India_000174.jpg",
        "title": "Longitudinal Pavement Fracture",
        "defect_type": "D00 / D20 Mixed Distress",
        "description": "Parallel surface fractures and pavement wear",
        "url": "/api/v1/road-damage/samples/India_000174.jpg"
    },
    {
        "filename": "India_000241.jpg",
        "title": "Surface Wear & Distress",
        "defect_type": "D20: Structural Wear",
        "description": "Progressive alligator cracking under traffic load",
        "url": "/api/v1/road-damage/samples/India_000241.jpg"
    }
]


@router.get("/samples")
def get_sample_images() -> Dict[str, Any]:
    """
    Returns verified sample road test images from the RDD2022 dataset for instant 1-click demonstration.
    """
    return {"samples": SAMPLE_IMAGES}


@router.get("/samples/{filename}")
def get_sample_image_file(filename: str):
    """
    Serves a verified sample road damage image for demonstration.
    """
    # Strict filename whitelist for safety
    allowed_files = {s["filename"] for s in SAMPLE_IMAGES}
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="Sample image not found or unauthorized.")

    file_path = TEST_IMAGES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample file missing from test dataset.")

    return FileResponse(path=file_path, media_type="image/jpeg")
