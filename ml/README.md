# Machine Learning Architecture & Pipelines: Eco-Friendly Routes

This package contains the machine learning pipelines, feature engineering, and data quality tools for **Eco-Friendly Routes**.

---

## 1. Modular Architecture Overview

Eco-Friendly Routes separates predictive modeling into three independent components:

```
+-----------------------------------------------------------------------------------+
| ml/ Package Modules                                                               |
+-----------------------------------------------------------------------------------+
|  MODULE A (Tabular ML)       MODULE B (Computer Vision)    MODULE C (Computer Vision) |
|  ---------------------       --------------------------    -------------------------- |
|  - data_inspection.py        - bdd100k scene analyzer      - rdd2022 damage detector  |
|  - preprocess.py               (optional CV pipeline)        (optional CV pipeline)  |
|  - features.py                                                                       |
|  - pipeline.py                                                                       |
|  - train.py                                                                          |
|  - evaluate.py                                                                       |
+-----------------------------------------------------------------------------------+
```

### Independence Rule
- **Module A** predicts journey-level carbon emissions from tabular journey parameters.
- **Module B** analyzes vehicle counts and local congestion from image feeds.
- **Module C** detects pavement defects (potholes, cracks) from road-surface imagery.
- **Do not combine** image bounding boxes directly into tabular emission training matrices. Only segment-level georeferenced route matches can be aggregated at the decision/recommendation stage.

---

## 2. File Directory & Component Responsibilities

| File | Purpose | Phase |
|---|---|---|
| `data_inspection.py` | Automated dataset quality auditor (row counts, nulls, duplicates, CO₂ physical checks, Markdown/JSON reports). | **Phase 2 (Active)** |
| `preprocess.py` | Documented missing value imputation (median/mode), IQR outlier logging, deterministic 70/15/15 train/val/test split. | **Phase 2 (Active)** |
| `features.py` | Feature transformations extracting distance, speed, elevation gain, and vehicle factors from route queries. | Skeletons |
| `pipeline.py` | Scikit-learn `Pipeline` and `ColumnTransformer` builder combining scalers with regressors. | Skeletons |
| `train.py` | Model training script with hyperparameter configuration and `joblib` model serialization. | Phase 3 Target |
| `evaluate.py` | Regression evaluation metrics (RMSE, MAE, R²) and residual visualization routines. | Phase 3 Target |

---

## 3. Data Inspection & Preprocessing Commands

### Step 1: Audit Raw Dataset
After placing your raw emissions CSV in `dataset/raw/emissions/`:
```bash
python ml/data_inspection.py
```
*Generates `dataset/processed/emissions/inspection_report.json` and prints a markdown table summary of null percentages, duplicates, and CO₂ distribution.*

### Step 2: Generate Cleaned Splits
```bash
python ml/preprocess.py
```
*Produces `train.csv` (70%), `val.csv` (15%), `test.csv` (15%), and `preprocessing_manifest.json` in `dataset/processed/emissions/`.*

### Step 3: Run Validation Tests
```bash
pytest tests/test_dataset_validation.py
```
