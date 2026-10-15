"""
Automated test suite for Eco-Friendly Routes vehicle emissions ML model,
pipeline preprocessing, inference service, and FastAPI endpoints.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import pandas as pd
import numpy as np

from ml.pipeline import build_emissions_pipeline, NUMERIC_FEATURES, CATEGORICAL_FEATURES
from ml.evaluate import compute_regression_metrics
from ml.features import standardize_vehicle_input, calculate_baseline_emissions
from ml.predict import EmissionsPredictor, emissions_predictor
from backend.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestEmissionsPipelineAndFeatures:
    """Verifies pipeline assembly, input standardizers, and evaluation metrics."""

    def test_feature_standardization_defaults(self):
        # When given minimal input, standardizer provides safe defaults
        df = standardize_vehicle_input({"vehicle_type": "mid-size"})
        assert list(df.columns) == [
            "Make", "Vehicle Class", "Engine Size(L)", "Cylinders",
            "Transmission", "Fuel Type", "Fuel Consumption Comb (L/100 km)"
        ]
        assert df["Make"].iloc[0] == "HONDA"
        assert df["Vehicle Class"].iloc[0] == "MID-SIZE"
        assert df["Engine Size(L)"].iloc[0] == 2.4
        assert df["Cylinders"].iloc[0] == 4
        assert df["Fuel Type"].iloc[0] == "X"

    def test_fuel_type_alias_mapping(self):
        df_gas = standardize_vehicle_input({"fuel_type": "gasoline"})
        assert df_gas["Fuel Type"].iloc[0] == "X"

        df_diesel = standardize_vehicle_input({"fuel_type": "diesel"})
        assert df_diesel["Fuel Type"].iloc[0] == "D"

        df_prem = standardize_vehicle_input({"fuel_type": "premium"})
        assert df_prem["Fuel Type"].iloc[0] == "Z"

    def test_combined_fuel_consumption_from_city_hwy(self):
        # 0.55 * 10.0 + 0.45 * 8.0 = 5.5 + 3.6 = 9.1
        df = standardize_vehicle_input({
            "fuel_consumption_city": 10.0,
            "fuel_consumption_hwy": 8.0
        })
        assert df["Fuel Consumption Comb (L/100 km)"].iloc[0] == 9.1

    def test_pipeline_construction_and_steps(self):
        pipe = build_emissions_pipeline()
        assert "preprocessor" in pipe.named_steps
        preprocessor = pipe.named_steps["preprocessor"]
        assert "num" in [t[0] for t in preprocessor.transformers]
        assert "cat" in [t[0] for t in preprocessor.transformers]

    def test_compute_regression_metrics(self):
        y_true = np.array([100.0, 200.0, 300.0])
        y_pred = np.array([105.0, 195.0, 302.0])
        metrics = compute_regression_metrics(y_true, y_pred)

        assert "mae" in metrics
        assert "rmse" in metrics
        assert "r2_score" in metrics
        assert metrics["mae"] > 0
        assert metrics["r2_score"] > 0.95


class TestEmissionsPredictor:
    """Verifies the core ML predictor and route emission estimates."""

    def test_model_loaded(self):
        assert emissions_predictor.is_ready() is True

    def test_predict_gasoline_car(self):
        res = emissions_predictor.predict({
            "make": "HONDA",
            "vehicle_class": "MID-SIZE",
            "engine_size_l": 2.4,
            "cylinders": 4,
            "fuel_type": "gasoline",
            "fuel_consumption_comb": 8.5
        }, distance_km=20.0)

        assert res["predicted_co2_g_per_km"] > 150.0
        assert res["predicted_co2_g_per_km"] < 250.0
        assert res["distance_km"] == 20.0
        assert res["trip_co2_grams"] == round(res["predicted_co2_g_per_km"] * 20.0, 2)
        assert res["model_name"] == "RandomForestRegressor"

    def test_predict_ev_returns_zero_tailpipe(self):
        res = emissions_predictor.predict({"fuel_type": "ev"}, distance_km=50.0)
        assert res["predicted_co2_g_per_km"] == 0.0
        assert res["trip_co2_grams"] == 0.0
        assert "Zero-Emission" in res["model_name"]

    def test_negative_distance_raises_value_error(self):
        with pytest.raises(ValueError):
            emissions_predictor.predict({"vehicle_type": "mid-size"}, distance_km=-5.0)


class TestEmissionsFastAPIEndpoints:
    """Tests integration with FastAPI backend routes."""

    def test_health_check_shows_model_loaded(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True

    def test_predict_endpoint_success(self, client):
        payload = {
            "make": "TOYOTA",
            "vehicle_class": "COMPACT",
            "engine_size_l": 1.8,
            "cylinders": 4,
            "fuel_type": "gasoline",
            "fuel_consumption_comb": 7.2,
            "distance_km": 10.0
        }
        resp = client.post("/api/v1/emissions/predict", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "predicted_co2_g_per_km" in data
        assert data["predicted_co2_g_per_km"] > 100.0
        assert data["distance_km"] == 10.0
        assert data["trip_co2_grams"] > 0
        assert data["model_name"] == "RandomForestRegressor"
        assert "limitations_note" in data

    def test_predict_endpoint_ev(self, client):
        resp = client.post("/api/v1/emissions/predict", json={
            "fuel_type": "ev",
            "distance_km": 25.0
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["predicted_co2_g_per_km"] == 0.0
        assert data["trip_co2_grams"] == 0.0

    def test_predict_endpoint_negative_distance_validation_error(self, client):
        resp = client.post("/api/v1/emissions/predict", json={
            "vehicle_type": "mid-size",
            "distance_km": -10.0
        })
        assert resp.status_code == 422

    def test_metadata_endpoint(self, client):
        resp = client.get("/api/v1/emissions/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert data["model_name"] == "RandomForestRegressor"
        assert "test_metrics" in data
        assert data["test_metrics"]["r2_score"] > 0.99
        assert data["test_metrics"]["mae"] < 5.0
