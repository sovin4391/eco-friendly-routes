"""
Unit tests for dataset inspection, validation rules, preprocessing pipeline,
and service boundary contracts.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from ml.data_inspection import DatasetInspector
from ml.preprocess import EmissionsPreprocessor
from backend.services.traffic_service import traffic_service
from backend.services.road_damage_service import road_damage_service


class TestDatasetDirectoryStructure:
    """Verifies that all required Phase 2 dataset folders and marker files exist."""

    EXPECTED_DIRS = [
        "dataset/raw/emissions",
        "dataset/raw/bdd100k",
        "dataset/raw/rdd2022",
        "dataset/processed/emissions",
        "dataset/processed/traffic",
        "dataset/processed/road_damage",
    ]

    @pytest.mark.parametrize("dir_path", EXPECTED_DIRS)
    def test_directory_and_gitkeep_exist(self, dir_path):
        p = Path(dir_path)
        assert p.exists(), f"Expected directory does not exist: {dir_path}"
        assert p.is_dir(), f"Path is not a directory: {dir_path}"
        gitkeep = p / ".gitkeep"
        assert gitkeep.exists(), f"Missing .gitkeep in: {dir_path}"

    def test_dataset_plan_exists(self):
        plan = Path("dataset/DATASET_PLAN.md")
        assert plan.exists(), "dataset/DATASET_PLAN.md must exist."
        assert plan.stat().st_size > 500, "DATASET_PLAN.md content is incomplete."


class TestDatasetInspector:
    """Tests the dataset inspection tool logic."""

    @pytest.fixture
    def inspector(self):
        return DatasetInspector()

    def test_valid_dataframe_audit(self, inspector):
        df = pd.DataFrame({
            "distance_km": [10.5, 20.0, 15.2, 8.0, 12.3] * 20,
            "duration_min": [18, 32, 24, 15, 20] * 20,
            "vehicle_type": ["gasoline", "diesel", "hybrid", "ev", "gasoline"] * 20,
            "co2_emissions": [1400.0, 2100.0, 950.0, 0.0, 1350.0] * 20,
        })

        report = inspector.inspect_dataframe(df)

        assert report["shape"]["rows"] == 100
        assert report["shape"]["columns"] == 4
        assert report["target_audit"]["target_found"] is True
        assert report["target_audit"]["target_column"] == "co2_emissions"
        assert report["target_audit"]["validation_passed"] is True
        assert len(report["target_audit"]["issues"]) == 0
        assert report["dataset_ready_for_ml"] is True

    def test_suspicious_range_warnings(self, inspector):
        # Extremely low CO2 (e.g. 0.05, likely kg instead of g) and zero values
        df = pd.DataFrame({
            "distance_km": [10.0, 20.0, 30.0],
            "co2_emissions": [0.0, 0.12, 0.45],
        })
        report = inspector.inspect_dataframe(df)
        assert len(report["target_audit"]["warnings"]) >= 2
        assert any("zero" in w.lower() for w in report["target_audit"]["warnings"])
        assert any("kilogram" in w.lower() for w in report["target_audit"]["warnings"])

    def test_detects_negative_co2_values(self, inspector):
        df = pd.DataFrame({
            "distance_km": [10.0, 20.0, 30.0],
            "co2_emissions": [150.0, -25.0, 300.0],  # Negative emission is physically invalid
        })

        report = inspector.inspect_dataframe(df)
        assert report["target_audit"]["validation_passed"] is False
        assert any("negative" in issue.lower() for issue in report["target_audit"]["issues"])
        assert report["dataset_ready_for_ml"] is False

    def test_detects_missing_target_column(self, inspector):
        df = pd.DataFrame({
            "distance_km": [10.0, 20.0, 30.0],
            "traffic_density": [0.2, 0.5, 0.8],
        })

        report = inspector.inspect_dataframe(df)
        assert report["target_audit"]["target_found"] is False
        assert report["target_audit"]["validation_passed"] is False
        assert report["dataset_ready_for_ml"] is False

    def test_duplicate_and_null_counting(self, inspector):
        df = pd.DataFrame({
            "feature_a": [1, 2, 2, np.nan, 5],
            "co2": [100.0, 200.0, 200.0, 300.0, 500.0],
        })

        report = inspector.inspect_dataframe(df)
        assert report["duplicates"]["count"] == 1
        assert report["columns"]["feature_a"]["null_count"] == 1
        assert report["columns"]["feature_a"]["null_percentage"] == 20.0


class TestEmissionsPreprocessor:
    """Tests data cleaning, documented imputation, outlier logging, and splits."""

    @pytest.fixture
    def preprocessor(self):
        return EmissionsPreprocessor(random_state=42)

    def test_target_missing_rows_dropped(self, preprocessor):
        df = pd.DataFrame({
            "distance": [10, 20, 30, 40],
            "co2": [100.0, np.nan, 300.0, 400.0],
        })
        train, val, test = preprocessor.process(df, target_col="co2")
        total = len(train) + len(val) + len(test)
        assert total == 3, "Rows with missing target must be dropped from training."
        assert preprocessor.transformation_log["dropped_target_null_rows"] == 1

    def test_missing_predictors_imputed_with_median_and_mode(self, preprocessor):
        df = pd.DataFrame({
            "distance": [10.0, 20.0, np.nan, 40.0, 50.0] * 20,
            "fuel_type": ["gasoline", "diesel", np.nan, "gasoline", "gasoline"] * 20,
            "co2": [100.0, 200.0, 300.0, 400.0, 500.0] * 20,
        })

        train, val, test = preprocessor.process(df, target_col="co2")
        combined = pd.concat([train, val, test])

        # Verify no nulls remain in predictors
        assert combined["distance"].isnull().sum() == 0
        assert combined["fuel_type"].isnull().sum() == 0

        # Verify imputation manifest documents fill values fitted on train
        assert "distance" in preprocessor.transformation_log["imputation"]
        assert preprocessor.transformation_log["imputation"]["distance"]["strategy"] == "train_median"
        assert preprocessor.transformation_log["imputation"]["fuel_type"]["strategy"] == "train_mode"

    def test_no_data_leakage_in_imputation(self, preprocessor):
        """Asserts that imputation values are learned SOLELY from the train set, avoiding test leakage."""
        # Create dataset where train set has median=10, but test set has a huge outlier (1000)
        # 10 rows: 7 train, 1 val, 2 test (deterministic split with seed=42)
        df = pd.DataFrame({
            "distance": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, np.nan, 10.0, 10.0, 1000.0],
            "co2": [100.0] * 10,
        })
        train, val, test = preprocessor.process(df, target_col="co2")
        fitted_median = preprocessor.transformation_log["imputation"]["distance"]["fitted_value"]
        # The fitted median must be 10.0 from train, not influenced by the test split outlier
        assert fitted_median == 10.0, f"Expected train-only fitted median 10.0, got {fitted_median}"

    def test_deterministic_split_ratios(self, preprocessor):
        n = 100
        df = pd.DataFrame({
            "feature": list(range(n)),
            "co2": [float(x * 10) for x in range(n)],
        })

        train, val, test = preprocessor.process(df, target_col="co2")
        assert len(train) == 70
        assert len(val) == 15
        assert len(test) == 15
        assert len(train) + len(val) + len(test) == n

    def test_split_reproducibility(self):
        df = pd.DataFrame({
            "val": list(range(50)),
            "co2": [float(x) for x in range(50)],
        })
        p1 = EmissionsPreprocessor(random_state=42)
        train1, _, _ = p1.process(df, target_col="co2")

        p2 = EmissionsPreprocessor(random_state=42)
        train2, _, _ = p2.process(df, target_col="co2")

        pd.testing.assert_frame_equal(train1, train2)


class TestServiceBoundariesNoFakeData:
    """Verifies that Module B and Module C return None without verified segment matches."""

    def test_traffic_service_returns_none_without_camera_feed(self):
        density = traffic_service.get_segment_traffic_density(
            segment_id="segment_delhi_ring_road",
            coordinates=[[28.61, 77.20], [28.62, 77.21]],
        )
        assert density is None, "TrafficService must return None when no verified camera data is matched."

    def test_road_damage_service_returns_none_without_survey_data(self):
        damage = road_damage_service.get_segment_damage_index(
            segment_id="segment_delhi_ring_road",
            coordinates=[[28.61, 77.20], [28.62, 77.21]],
        )
        assert damage is None, "RoadDamageService must return None when no verified survey data exists."
