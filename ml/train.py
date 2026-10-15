"""
Model training entry point for Eco-Friendly Routes vehicle emissions prediction.

Executes:
1. Loads train/validation/test splits from `dataset/processed/emissions/`.
2. Trains benchmark models (DummyRegressor, LinearRegression, RandomForestRegressor, GradientBoostingRegressor).
3. Evaluates validation MAE, RMSE, and R2 to select the best estimator.
4. Performs final unbiased evaluation of the selected model on the held-out test split.
5. Persists the winning model artifact to `models/emissions_model.joblib` and `models/eco_route_regressor.joblib`.
6. Generates `models/model_metadata.json` containing verified empirical metrics and provenance.

Usage:
    python ml/train.py
    python ml/train.py --processed_dir dataset/processed/emissions --output_dir models
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import joblib

from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

from ml.pipeline import (
    build_emissions_pipeline,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
)
from ml.evaluate import compute_regression_metrics


def train_and_evaluate_models(
    processed_dir: str = "dataset/processed/emissions",
    output_dir: str = "models",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Trains regression candidates, selects the optimal estimator on validation data,
    evaluates on test split, and persists serialized artifacts.
    """
    proc_path = Path(processed_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    train_file = proc_path / "train.csv"
    val_file = proc_path / "val.csv"
    test_file = proc_path / "test.csv"

    for f in [train_file, val_file, test_file]:
        if not f.exists():
            raise FileNotFoundError(
                f"Missing required processed split: {f}. Run 'python ml/preprocess.py' first."
            )

    print(f"[ML Training] Loading splits from: {proc_path}")
    train_df = pd.read_csv(train_file)
    val_df = pd.read_csv(val_file)
    test_df = pd.read_csv(test_file)

    target_col = "CO2 Emissions(g/km)"
    if target_col not in train_df.columns:
        raise ValueError(f"Target column '{target_col}' not found in train.csv columns: {list(train_df.columns)}")

    feature_cols = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]

    X_val = val_df[feature_cols]
    y_val = val_df[target_col]

    X_test = test_df[feature_cols]
    y_test = test_df[target_col]

    print(f"[ML Training] Dataset split sizes: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}")
    print(f"[ML Training] Feature count: {len(feature_cols)} (Numeric: {len(NUMERIC_FEATURES)}, Categorical: {len(CATEGORICAL_FEATURES)})")

    # Define model candidates
    candidates = {
        "DummyRegressor (Mean Baseline)": DummyRegressor(strategy="mean"),
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=100, random_state=random_state),
        "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=100, random_state=random_state),
    }

    benchmark_results: Dict[str, Any] = {}
    fitted_pipelines = {}

    print("\n--- BENCHMARK RESULTS (Validation Set) ---")
    best_name = None
    best_rmse = float("inf")

    for name, regressor in candidates.items():
        pipeline = build_emissions_pipeline(
            model=regressor,
            numeric_features=NUMERIC_FEATURES,
            categorical_features=CATEGORICAL_FEATURES,
        )
        pipeline.fit(X_train, y_train)
        val_preds = pipeline.predict(X_val)
        val_metrics = compute_regression_metrics(y_val, val_preds)

        benchmark_results[name] = {
            "validation_metrics": val_metrics,
            "regressor_class": regressor.__class__.__name__,
        }
        fitted_pipelines[name] = pipeline

        print(
            f"  {name:32s} | MAE: {val_metrics['mae']:6.2f} g/km | "
            f"RMSE: {val_metrics['rmse']:6.2f} g/km | R2: {val_metrics['r2_score']:.4f}"
        )

        # Selection criteria: lowest validation RMSE
        if val_metrics["rmse"] < best_rmse:
            best_rmse = val_metrics["rmse"]
            best_name = name

    print(f"\n[ML Training] Selected Best Model: {best_name} (Val RMSE: {best_rmse:.2f} g/km)")

    # Unbiased evaluation on held-out test split
    best_pipeline = fitted_pipelines[best_name]
    test_preds = best_pipeline.predict(X_test)
    test_metrics = compute_regression_metrics(y_test, test_preds)

    print("\n--- UNBIASED EVALUATION (Held-out Test Set) ---")
    print(
        f"  {best_name:32s} | MAE: {test_metrics['mae']:6.2f} g/km | "
        f"RMSE: {test_metrics['rmse']:6.2f} g/km | R2: {test_metrics['r2_score']:.4f}\n"
    )

    # Persist model artifacts
    model_path = out_path / "emissions_model.joblib"
    eco_model_path = out_path / "eco_route_regressor.joblib"
    metadata_path = out_path / "model_metadata.json"

    joblib.dump(best_pipeline, model_path)
    joblib.dump(best_pipeline, eco_model_path)
    print(f"[ML Training] Model artifact saved to: {model_path} and {eco_model_path}")

    # Build comprehensive metadata document
    metadata = {
        "model_name": best_name,
        "regressor_type": benchmark_results[best_name]["regressor_class"],
        "target_variable": target_col,
        "target_unit": "g CO2 / km",
        "training_dataset": "Natural Resources Canada - Vehicle CO2 Emissions (2014-2022)",
        "features": {
            "numeric": NUMERIC_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
        },
        "dataset_split_samples": {
            "train": len(X_train),
            "validation": len(X_val),
            "test": len(X_test),
        },
        "validation_benchmark": benchmark_results,
        "test_metrics": test_metrics,
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "notes": (
            "Model estimates vehicle-level tailpipe CO2 emission rate (g/km). "
            "Route-level emissions are calculated as (predicted_rate_g_per_km * distance_km). "
            "Congestion multipliers are not asserted as verified scientific factors."
        ),
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[ML Training] Model metadata saved to: {metadata_path}")
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate Eco-Friendly Routes emissions model.")
    parser.add_argument("--processed_dir", type=str, default="dataset/processed/emissions", help="Directory with processed CSV splits")
    parser.add_argument("--output_dir", type=str, default="models", help="Directory to save trained model artifacts")
    parser.add_argument("--seed", type=int, default=42, help="Random state seed")
    args = parser.parse_args()

    train_and_evaluate_models(
        processed_dir=args.processed_dir,
        output_dir=args.output_dir,
        random_state=args.seed,
    )


if __name__ == "__main__":
    main()
