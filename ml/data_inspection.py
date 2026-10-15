"""
Reusable Dataset Inspection and Validation Tool for Eco-Friendly Routes.
Performs systematic audits on tabular datasets:
- Column names, data types, and row counts
- Missing value counts and percentages
- Exact and subset duplicate detection
- Target variable (CO2) physical validation (non-negativity, distribution)
- Generates machine-readable (JSON) and human-readable (Markdown) audit reports.

Usage:
    python ml/data_inspection.py
    python ml/data_inspection.py --file dataset/raw/emissions/routes_data.csv
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np


class DatasetInspector:
    """Systematic auditor for route and vehicle emissions datasets."""

    CANDIDATE_TARGET_NAMES = [
        "co2", "co2_emissions", "co2_grams", "emissions", "carbon",
        "co2_emissions_g_km", "co2_g_km", "co2_tailpipe_g_km",
        "co2_emissions(g/km)", "co2_emissions_total", "emission_co2"
    ]

    CANDIDATE_DISTANCE_NAMES = ["distance", "distance_km", "trip_distance", "length_km"]
    CANDIDATE_DURATION_NAMES = ["duration", "duration_min", "travel_time_min", "trip_duration", "time_min"]
    CANDIDATE_VEHICLE_NAMES = ["vehicle_type", "vehicle_class", "vehicle", "make_model", "car_type"]
    CANDIDATE_FUEL_NAMES = ["fuel_type", "fuel", "powertrain", "engine_type"]
    CANDIDATE_CONGESTION_NAMES = ["traffic_density", "congestion", "congestion_level", "traffic_factor", "density"]

    def __init__(self, raw_dir: str = "dataset/raw/emissions"):
        self.raw_dir = Path(raw_dir)

    def find_raw_files(self) -> List[Path]:
        """Locates all CSV and Parquet files in the raw emissions directory."""
        if not self.raw_dir.exists():
            return []
        files = list(self.raw_dir.glob("*.csv")) + list(self.raw_dir.glob("*.parquet"))
        return sorted(files)

    def identify_target_column(self, columns: List[str], specified_target: Optional[str] = None) -> Optional[str]:
        """Identifies the candidate CO2 emission target variable column."""
        if specified_target and specified_target in columns:
            return specified_target

        col_lower_map = {c.lower().strip().replace(" ", "_"): c for c in columns}
        for candidate in self.CANDIDATE_TARGET_NAMES:
            if candidate in col_lower_map:
                return col_lower_map[candidate]

        # Substring search if exact match not found
        for clean_name, orig_name in col_lower_map.items():
            if "co2" in clean_name or "emission" in clean_name:
                return orig_name
        return None

    def inspect_dataframe(self, df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
        """Performs comprehensive quality inspection on a pandas DataFrame."""
        row_count, col_count = df.shape

        # 1. Column Inventory & Data Types
        columns_info = {}
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            null_count = int(df[col].isnull().sum())
            null_pct = round((null_count / row_count) * 100, 2) if row_count > 0 else 0.0
            unique_count = int(df[col].nunique(dropna=True))

            columns_info[col] = {
                "dtype": dtype_str,
                "null_count": null_count,
                "null_percentage": null_pct,
                "unique_values": unique_count,
            }

        # 2. Duplicate Check
        exact_duplicates = int(df.duplicated().sum())
        duplicate_pct = round((exact_duplicates / row_count) * 100, 2) if row_count > 0 else 0.0

        # 3. Target Variable Validation
        target_name = self.identify_target_column(list(df.columns), target_col)
        target_audit: Dict[str, Any] = {
            "target_column": target_name,
            "target_found": target_name is not None,
            "validation_passed": False,
            "issues": [],
            "warnings": [],
            "stats": {}
        }

        if target_name:
            target_series = df[target_name]
            # Verify numeric
            if not pd.api.types.is_numeric_dtype(target_series):
                target_audit["issues"].append(
                    f"Target column '{target_name}' is non-numeric ({target_series.dtype}). Must be float or integer."
                )
            else:
                valid_num = target_series.dropna()
                negative_count = int((valid_num < 0).sum())
                zero_count = int((valid_num == 0).sum())

                if negative_count > 0:
                    target_audit["issues"].append(
                        f"Found {negative_count} negative emission values. Negative CO2 emissions are physically invalid."
                    )

                if len(valid_num) > 0:
                    min_val = float(valid_num.min())
                    max_val = float(valid_num.max())
                    q25 = float(valid_num.quantile(0.25))
                    q75 = float(valid_num.quantile(0.75))

                    target_audit["stats"] = {
                        "min": min_val,
                        "max": max_val,
                        "mean": float(round(valid_num.mean(), 2)),
                        "median": float(round(valid_num.median(), 2)),
                        "std": float(round(valid_num.std(), 2)),
                        "q25": float(round(q25, 2)),
                        "q75": float(round(q75, 2)),
                        "iqr": float(round(q75 - q25, 2)),
                        "zero_count": zero_count,
                    }

                    # Flag suspicious ranges for review (Safeguard 5)
                    if zero_count > 0:
                        target_audit["warnings"].append(
                            f"Contains {zero_count} zero-emission records. Valid for EVs/bicycles, but review if ICE vehicles are present."
                        )

                    if max_val > 0 and max_val < 5.0:
                        target_audit["warnings"].append(
                            f"Maximum value ({max_val}) is very low. Target may be measured in kilograms (kg) rather than grams (g). Review unit definition."
                        )
                    elif max_val > 50000.0:
                        target_audit["warnings"].append(
                            f"Maximum value ({max_val}) is very high. Review if target is cumulative journey total or long-distance fleet metric."
                        )

                    if negative_count == 0 and len(valid_num) > 0:
                        target_audit["validation_passed"] = True
        else:
            target_audit["issues"].append(
                "No candidate CO2 emission target variable identified. Model training cannot proceed without target."
            )

        # 4. Feature Coverage Mapping
        col_clean = [c.lower().strip().replace(" ", "_") for c in df.columns]
        feature_coverage = {
            "distance_present": any(k in col_clean for k in self.CANDIDATE_DISTANCE_NAMES),
            "duration_present": any(k in col_clean for k in self.CANDIDATE_DURATION_NAMES),
            "vehicle_type_present": any(k in col_clean for k in self.CANDIDATE_VEHICLE_NAMES),
            "fuel_type_present": any(k in col_clean for k in self.CANDIDATE_FUEL_NAMES),
            "congestion_present": any(k in col_clean for k in self.CANDIDATE_CONGESTION_NAMES),
        }

        # 5. Overall Readiness Determination
        # Ready if target passes validation, has >= 50 rows, and contains either distance (trip level)
        # or vehicle characteristics + fuel type (vehicle-level emission rate in g/km)
        overall_ready = (
            target_audit["validation_passed"]
            and row_count >= 50
            and (
                feature_coverage["distance_present"]
                or (feature_coverage["vehicle_type_present"] and feature_coverage["fuel_type_present"])
            )
        )

        return {
            "shape": {"rows": row_count, "columns": col_count},
            "columns": columns_info,
            "duplicates": {
                "count": exact_duplicates,
                "percentage": duplicate_pct,
            },
            "target_audit": target_audit,
            "feature_coverage": feature_coverage,
            "dataset_ready_for_ml": overall_ready,
        }

    def inspect_file(self, file_path: Path, target_col: Optional[str] = None) -> Dict[str, Any]:
        """Loads and audits a specific file from disk."""
        if not file_path.exists():
            return {
                "file_path": str(file_path),
                "error": f"File not found: {file_path}",
                "dataset_ready_for_ml": False,
            }

        file_size_kb = round(file_path.stat().st_size / 1024, 2)
        try:
            if file_path.suffix.lower() == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix.lower() == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                return {
                    "file_path": str(file_path),
                    "error": f"Unsupported file extension: {file_path.suffix}",
                    "dataset_ready_for_ml": False,
                }
        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": f"Failed to parse file: {str(e)}",
                "dataset_ready_for_ml": False,
            }

        result = self.inspect_dataframe(df, target_col)
        result["file_path"] = str(file_path)
        result["file_size_kb"] = file_size_kb
        return result

    def format_markdown_report(self, report: Dict[str, Any]) -> str:
        """Formats inspection results into human-readable Markdown."""
        lines = [
            "# Dataset Quality & Validation Audit Report",
            "",
            f"- **File Audited**: `{report.get('file_path', 'In-memory DataFrame')}`",
            f"- **File Size**: {report.get('file_size_kb', 'N/A')} KB",
            f"- **Total Rows**: {report['shape']['rows']}",
            f"- **Total Columns**: {report['shape']['columns']}",
            f"- **Exact Duplicate Rows**: {report['duplicates']['count']} ({report['duplicates']['percentage']}%)",
            f"- **ML Readiness**: {'[READY FOR PREPROCESSING]' if report.get('dataset_ready_for_ml') else '[NOT READY - ACTION REQUIRED]'}",
            "",
            "## 1. Target Variable Audit",
            "",
        ]

        t_audit = report["target_audit"]
        if t_audit["target_found"]:
            lines.append(f"- **Identified Target Column**: `{t_audit['target_column']}`")
            lines.append(f"- **Validation Status**: {'PASSED' if t_audit['validation_passed'] else 'FAILED'}")
            if t_audit["stats"]:
                lines.append(f"- **Range**: [{t_audit['stats']['min']} to {t_audit['stats']['max']}]")
                lines.append(f"- **Mean (Std)**: {t_audit['stats']['mean']} (± {t_audit['stats']['std']})")
                lines.append(f"- **Median (IQR)**: {t_audit['stats']['median']} (IQR: {t_audit['stats']['iqr']})")
                lines.append(f"- **Zero Values**: {t_audit['stats']['zero_count']}")
        else:
            lines.append("- **Status**: Target emission variable NOT found.")

        if t_audit.get("warnings"):
            lines.append("")
            lines.append("### Flagged Warnings for Review:")
            for warn in t_audit["warnings"]:
                lines.append(f"- :information_source: {warn}")

        if t_audit["issues"]:
            lines.append("")
            lines.append("### Identified Critical Issues:")
            for issue in t_audit["issues"]:
                lines.append(f"- :warning: {issue}")

        lines.append("")
        lines.append("## 2. Feature Coverage Summary")
        lines.append("")
        fc = report["feature_coverage"]
        lines.append(f"- Distance Feature Present: {'Yes' if fc['distance_present'] else 'No'}")
        lines.append(f"- Duration Feature Present: {'Yes' if fc['duration_present'] else 'No'}")
        lines.append(f"- Vehicle Type Feature Present: {'Yes' if fc['vehicle_type_present'] else 'No'}")
        lines.append(f"- Fuel Type Feature Present: {'Yes' if fc['fuel_type_present'] else 'No'}")
        lines.append(f"- Congestion Feature Present: {'Yes' if fc['congestion_present'] else 'No'}")

        lines.append("")
        lines.append("## 3. Column Quality Breakdown")
        lines.append("")
        lines.append("| Column Name | Data Type | Null Count | Null % | Unique Values |")
        lines.append("|---|---|---|---|---|")
        for col_name, info in report["columns"].items():
            lines.append(f"| `{col_name}` | {info['dtype']} | {info['null_count']} | {info['null_percentage']}% | {info['unique_values']} |")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit Eco-Friendly Routes raw emissions dataset.")
    parser.add_argument("--file", type=str, default=None, help="Path to specific raw CSV or Parquet file")
    parser.add_argument("--target", type=str, default=None, help="Explicit target variable column name")
    parser.add_argument("--output", type=str, default="dataset/processed/emissions/inspection_report.json", help="Path to save JSON audit report")
    args = parser.parse_args()

    inspector = DatasetInspector()

    if args.file:
        file_to_inspect = Path(args.file)
    else:
        available_files = inspector.find_raw_files()
        if not available_files:
            print("[DATASET AUDIT] No dataset files found in 'dataset/raw/emissions/'.")
            print("Action Required: Please download/place your Kaggle emissions CSV file into:")
            print("  dataset/raw/emissions/")
            print("Then re-run this script to inspect row counts, schema, and target validity.")
            sys.exit(0)
        file_to_inspect = available_files[0]
        if len(available_files) > 1:
            print(f"[DATASET AUDIT] Multiple raw files found. Auditing primary: {file_to_inspect.name}")

    print(f"[DATASET AUDIT] Starting inspection of: {file_to_inspect}")
    report = inspector.inspect_file(file_to_inspect, target_col=args.target)

    # Save JSON report
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[DATASET AUDIT] JSON report saved to: {out_path}")

    # Print Markdown Summary
    md_summary = inspector.format_markdown_report(report)
    print("\n" + md_summary + "\n")


if __name__ == "__main__":
    main()
