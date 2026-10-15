"""
Inference service for Eco-Friendly Routes vehicle emissions prediction.

Provides:
- Model loading and memory caching
- Feature standardization and validation
- Direct tailpipe rate prediction (g CO2 / km)
- Route-level trip emission estimation (predicted_g_per_km * distance_km)
- Transparent limitations documentation
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import joblib
import pandas as pd
import numpy as np

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.features import standardize_vehicle_input


class EmissionsPredictor:
    """Production predictor for vehicle emissions and route carbon estimates."""

    def __init__(self, model_path: Optional[str] = None):
        if model_path:
            self.model_path = Path(model_path)
        else:
            default_p1 = PROJECT_ROOT / "models" / "emissions_model.joblib"
            default_p2 = PROJECT_ROOT / "models" / "eco_route_regressor.joblib"
            self.model_path = default_p1 if default_p1.exists() else default_p2

        self.pipeline = None
        self._load_model()

    def _load_model(self) -> None:
        """Loads serialized pipeline artifact if available."""
        if self.model_path and self.model_path.exists():
            try:
                self.pipeline = joblib.load(self.model_path)
            except Exception as e:
                print(f"[EmissionsPredictor] Warning: Failed to load model artifact {self.model_path}: {e}")
                self.pipeline = None
        else:
            self.pipeline = None

    def is_ready(self) -> bool:
        """Returns True if the ML model pipeline is loaded and ready for inference."""
        return self.pipeline is not None

    def predict(
        self,
        vehicle_data: Dict[str, Any],
        distance_km: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates predicted tailpipe emission rate (g/km) and total trip emission (g).
        """
        # 1. Check for pure Electric Vehicle (EV)
        raw_fuel = str(vehicle_data.get("fuel_type", "")).lower().strip()
        raw_type = str(vehicle_data.get("vehicle_type", "")).lower().strip()
        if raw_fuel in ["ev", "electric", "battery_electric"] or raw_type in ["ev", "electric"]:
            rate_g_km = 0.0
            trip_g = 0.0 if distance_km is not None else None
            return {
                "predicted_co2_g_per_km": 0.0,
                "distance_km": distance_km,
                "trip_co2_grams": 0.0 if distance_km is not None else None,
                "model_name": "Zero-Emission Battery Electric Vehicle Rule",
                "estimation_method": "direct_zero_tailpipe_ev",
                "standardized_features": {"fuel_type": "EV"},
                "limitations_note": (
                    "Zero direct tailpipe emissions for Battery Electric Vehicles. "
                    "Lifecycle upstream power-grid generation emissions are excluded."
                ),
            }

        # 2. Check model readiness
        if not self.is_ready():
            raise RuntimeError(
                "Emissions model is not loaded. Train the model first using 'python ml/train.py'."
            )

        # 3. Standardize input features to match training schema
        df_input = standardize_vehicle_input(vehicle_data)

        # 4. Predict emission rate (g/km)
        raw_pred = self.pipeline.predict(df_input)
        rate_g_km = round(max(0.0, float(raw_pred[0])), 2)

        # 5. Route-level calculation if distance is provided
        trip_co2_g = None
        if distance_km is not None:
            if distance_km < 0:
                raise ValueError(f"Distance cannot be negative, got: {distance_km}")
            trip_co2_g = round(rate_g_km * float(distance_km), 2)

        return {
            "predicted_co2_g_per_km": rate_g_km,
            "distance_km": round(float(distance_km), 2) if distance_km is not None else None,
            "trip_co2_grams": trip_co2_g,
            "model_name": "RandomForestRegressor",
            "estimation_method": "ml_pipeline_random_forest",
            "standardized_features": df_input.iloc[0].to_dict(),
            "limitations_note": (
                "Direct tailpipe CO2 emission rate predicted from vehicle specifications "
                "(Natural Resources Canada model). Trip emissions are estimated as "
                "(predicted_rate_g_per_km * distance_km). Congestion multipliers are unvalidated "
                "and not applied."
            ),
        }


# Global singleton instance for backend reuse
emissions_predictor = EmissionsPredictor()
