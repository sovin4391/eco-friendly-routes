"""
FastAPI route handlers for vehicle emissions prediction and model metadata.
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from backend.models.schemas import EmissionsPredictionRequest, EmissionsPredictionResponse
from backend.core.config import settings
from ml.predict import emissions_predictor

router = APIRouter(prefix="/emissions", tags=["Vehicle Emissions"])


@router.post("/predict", response_model=EmissionsPredictionResponse)
async def predict_emissions(request: EmissionsPredictionRequest):
    """
    Predicts vehicle direct tailpipe CO2 emission rate (g/km) using the trained
    Natural Resources Canada Random Forest regression pipeline.
    
    If route distance (km) is provided, also calculates total trip baseline CO2 (grams):
    `trip_co2_grams = predicted_rate_g_per_km * distance_km`.
    
    EVs / Electric vehicles return 0.0 g/km direct tailpipe emissions.
    Unvalidated congestion multipliers are not claimed or applied.
    """
    if request.distance_km is not None and request.distance_km < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Distance must be a non-negative number.",
        )

    try:
        input_data = request.model_dump()
        result = emissions_predictor.predict(
            vehicle_data=input_data,
            distance_km=request.distance_km,
        )
        return EmissionsPredictionResponse(**result)
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re),
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Emissions prediction failed: {str(e)}",
        )


@router.get("/metadata")
async def get_model_metadata():
    """
    Returns empirical benchmark metrics (MAE, RMSE, R2) and training metadata
    from the validated models/model_metadata.json artifact.
    """
    metadata_path = settings.MODELS_DIR / "model_metadata.json"
    if not metadata_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metadata artifact not found. Please train models first.",
        )

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read model metadata: {str(e)}",
        )
