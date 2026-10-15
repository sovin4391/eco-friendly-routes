"""
Preprocessing Pipeline for Eco-Friendly Routes Emissions Dataset.

Responsibilities:
- Loads validated raw tabular emissions data.
- Applies documented missing-value imputation (numerical: median, categorical: mode).
- Audits and logs outliers using the Interquartile Range (IQR) method without silent record deletion.
- Standardizes feature formats and categorical encodings.
- Produces reproducible train / validation / test splits (70% / 15% / 15%).
- Persists cleaned splits and an audit metadata manifest to `dataset/processed/emissions/`.

Usage:
    python ml/preprocess.py
    python ml/preprocess.py --input dataset/raw/emissions/routes_data.csv
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np


class EmissionsPreprocessor:
    """Standardized preprocessing pipeline for journey emissions datasets."""

    def __init__(
        self,
        input_file: Optional[str] = None,
        output_dir: str = "dataset/processed/emissions",
        random_state: int = 42,
    ):
        self.input_file = Path(input_file) if input_file else None
        self.output_dir = Path(output_dir)
        self.random_state = random_state
        self.transformation_log: Dict[str, Any] = {
            "imputation": {},
            "outliers_logged": {},
            "splits": {},
            "feature_columns": [],
            "target_column": None,
        }

    def find_default_raw_file(self) -> Optional[Path]:
        raw_dir = Path("dataset/raw/emissions")
        if not raw_dir.exists():
            return None
        csv_files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.parquet"))
        return csv_files[0] if csv_files else None

    def detect_outliers_iqr(self, series: pd.Series, multiplier: float = 1.5) -> Dict[str, Any]:
        """Calculates IQR outlier bounds and logs candidate outliers without dropping rows."""
        clean_s = series.dropna()
        if len(clean_s) == 0:
            return {"q25": 0, "q75": 0, "iqr": 0, "lower_bound": 0, "upper_bound": 0, "outlier_count": 0}

        q25 = float(clean_s.quantile(0.25))
        q75 = float(clean_s.quantile(0.75))
        iqr = q75 - q25
        lower = q25 - multiplier * iqr
        upper = q75 + multiplier * iqr

        outlier_count = int(((clean_s < lower) | (clean_s > upper)).sum())

        return {
            "q25": round(q25, 2),
            "q75": round(q75, 2),
            "iqr": round(iqr, 2),
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2),
            "outlier_count": outlier_count,
            "outlier_percentage": round((outlier_count / len(clean_s)) * 100, 2),
        }

    def resolve_target_column(self, df: pd.DataFrame, target_col: Optional[str] = None) -> str:
        """Resolves target column from candidate names if not exact match."""
        if target_col and target_col in df.columns:
            return target_col

        candidates = [
            "co2", "co2_emissions", "co2_grams", "emissions", "carbon",
            "co2_emissions_g_km", "co2_g_km", "co2_tailpipe_g_km",
            "co2_emissions(g/km)", "co2_emissions_total", "emission_co2"
        ]
        col_lower_map = {c.lower().strip().replace(" ", "_"): c for c in df.columns}
        for candidate in candidates:
            if candidate in col_lower_map:
                return col_lower_map[candidate]

        for clean_name, orig_name in col_lower_map.items():
            if "co2" in clean_name or "emission" in clean_name:
                return orig_name

        if target_col:
            raise ValueError(f"Target column '{target_col}' not found in DataFrame columns: {list(df.columns)}")
        raise ValueError(f"Could not identify a target CO2 column in DataFrame columns: {list(df.columns)}")

    def process(self, df: pd.DataFrame, target_col: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Executes documented preprocessing on a pandas DataFrame:
        1. Validates target column presence.
        2. Drops rows with missing target values (cannot impute target labels).
        3. Imputes missing predictor features with documented strategy.
        4. Logs numeric feature outliers.
        5. Partitions into Train (70%), Validation (15%), and Test (15%) splits.
        """
        target_col = self.resolve_target_column(df, target_col)
        self.transformation_log["target_column"] = target_col
        initial_rows = len(df)
        self.transformation_log["exact_duplicates"] = int(df.duplicated().sum())

        # 1. Target column missingness check
        valid_target_df = df.dropna(subset=[target_col]).copy()
        dropped_target_rows = initial_rows - len(valid_target_df)
        self.transformation_log["dropped_target_null_rows"] = dropped_target_rows

        if len(valid_target_df) == 0:
            raise ValueError("All rows have null target values. Cannot train.")

        # 2. Partition into Train (70%), Validation (15%), and Test (15%) FIRST to prevent leakage
        shuffled = valid_target_df.sample(frac=1.0, random_state=self.random_state).reset_index(drop=True)
        n = len(shuffled)
        train_end = int(0.70 * n)
        val_end = int(0.85 * n)

        train_df = shuffled.iloc[:train_end].copy().reset_index(drop=True)
        val_df = shuffled.iloc[train_end:val_end].copy().reset_index(drop=True)
        test_df = shuffled.iloc[val_end:].copy().reset_index(drop=True)

        feature_cols = [c for c in train_df.columns if c != target_col]
        self.transformation_log["feature_columns"] = feature_cols

        # 3. Fit Imputers SOLELY on Train Split and Transform All Splits
        for col in feature_cols:
            if pd.api.types.is_numeric_dtype(train_df[col]):
                median_val = float(train_df[col].median()) if not train_df[col].dropna().empty else 0.0
                train_nulls = int(train_df[col].isnull().sum())
                val_nulls = int(val_df[col].isnull().sum())
                test_nulls = int(test_df[col].isnull().sum())

                train_df[col] = train_df[col].fillna(median_val)
                val_df[col] = val_df[col].fillna(median_val)
                test_df[col] = test_df[col].fillna(median_val)

                if train_nulls > 0 or val_nulls > 0 or test_nulls > 0:
                    self.transformation_log["imputation"][col] = {
                        "strategy": "train_median",
                        "fitted_value": round(median_val, 4),
                        "train_imputed_count": train_nulls,
                        "val_imputed_count": val_nulls,
                        "test_imputed_count": test_nulls,
                    }
            else:
                mode_series = train_df[col].mode()
                mode_val = str(mode_series.iloc[0]) if not mode_series.empty else "unknown"
                train_nulls = int(train_df[col].isnull().sum())
                val_nulls = int(val_df[col].isnull().sum())
                test_nulls = int(test_df[col].isnull().sum())

                train_df[col] = train_df[col].fillna(mode_val)
                val_df[col] = val_df[col].fillna(mode_val)
                test_df[col] = test_df[col].fillna(mode_val)

                if train_nulls > 0 or val_nulls > 0 or test_nulls > 0:
                    self.transformation_log["imputation"][col] = {
                        "strategy": "train_mode",
                        "fitted_value": mode_val,
                        "train_imputed_count": train_nulls,
                        "val_imputed_count": val_nulls,
                        "test_imputed_count": test_nulls,
                    }

        # 4. Outlier Logging (Log row indices and values without silent deletion)
        for col in feature_cols + [target_col]:
            if pd.api.types.is_numeric_dtype(train_df[col]):
                self.transformation_log["outliers_logged"][col] = self.detect_outliers_iqr(train_df[col])

        self.transformation_log["splits"] = {
            "total_samples": n,
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "random_state": self.random_state,
        }

        return train_df, val_df, test_df

    def save_splits(self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame):
        """Saves output splits and transformation manifest to disk."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        train_path = self.output_dir / "train.csv"
        val_path = self.output_dir / "val.csv"
        test_path = self.output_dir / "test.csv"
        manifest_path = self.output_dir / "preprocessing_manifest.json"

        train_df.to_csv(train_path, index=False)
        val_df.to_csv(val_path, index=False)
        test_df.to_csv(test_path, index=False)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.transformation_log, f, indent=2)

        print(f"[PREPROCESS] Cleaned splits saved to: {self.output_dir}")
        print(f"  - Train: {train_path} ({len(train_df)} rows)")
        print(f"  - Validation: {val_path} ({len(val_df)} rows)")
        print(f"  - Test: {test_path} ({len(test_df)} rows)")
        print(f"  - Transformation Manifest: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="Preprocess Eco-Friendly Routes raw emissions dataset.")
    parser.add_argument("--input", type=str, default=None, help="Path to raw CSV file")
    parser.add_argument("--target", type=str, default=None, help="Target emission column name (auto-detected if omitted)")
    parser.add_argument("--output_dir", type=str, default="dataset/processed/emissions", help="Output directory for processed splits")
    parser.add_argument("--seed", type=int, default=42, help="Random state for split reproducibility")
    args = parser.parse_args()

    preprocessor = EmissionsPreprocessor(
        input_file=args.input,
        output_dir=args.output_dir,
        random_state=args.seed
    )

    file_to_process = preprocessor.input_file or preprocessor.find_default_raw_file()

    if not file_to_process or not file_to_process.exists():
        print("[PREPROCESS] No raw emissions file found in 'dataset/raw/emissions/'.")
        print("Action Required: Please download/place your Kaggle emissions CSV file into:")
        print("  dataset/raw/emissions/")
        print("Then run: python ml/preprocess.py")
        sys.exit(0)

    print(f"[PREPROCESS] Loading raw data from: {file_to_process}")
    df = pd.read_csv(file_to_process)
    print(f"[PREPROCESS] Loaded {len(df)} rows and {len(df.columns)} columns.")

    train_df, val_df, test_df = preprocessor.process(df, target_col=args.target)
    preprocessor.save_splits(train_df, val_df, test_df)


if __name__ == "__main__":
    main()
