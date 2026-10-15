# Dataset Management & Integration: Eco-Friendly Routes

This directory manages raw and processed data for the three independent machine learning and computer vision modules of **Eco-Friendly Routes**.

---

## 1. Directory Structure

```
dataset/
├── raw/
│   ├── emissions/                 # Place raw tabular CSVs (Kaggle emissions dataset) here
│   │   └── .gitkeep
│   ├── bdd100k/                   # Curated BDD100K sample images and annotation JSONs
│   │   └── .gitkeep
│   └── rdd2022/                   # Curated RDD2022 India subset images and VOC XMLs
│       └── .gitkeep
├── processed/
│   ├── emissions/                 # Cleaned, imputed, and split tabular training datasets
│   │   └── .gitkeep
│   ├── traffic/                   # Extracted traffic density features and benchmarks
│   │   └── .gitkeep
│   └── road_damage/               # Standardized road roughness and damage frequency indexes
│       └── .gitkeep
├── DATASET_PLAN.md                # Comprehensive data plan, licensing, and schema specifications
└── README.md                      # This guide
```

*Note: Raw media, large CSVs, image sets, and model weights are strictly ignored by Git via `.gitignore`.*

---

## 2. Integrated Datasets & Licensing

### Dataset A — Emissions Prediction (Module A)
- **Primary Recommended Dataset**: **CO2 Emission by Vehicles**
  - **Direct Kaggle URL**: [https://www.kaggle.com/datasets/debajyotipodder/co2-emission-by-vehicles](https://www.kaggle.com/datasets/debajyotipodder/co2-emission-by-vehicles)
  - **Source**: Government of Canada (Natural Resources Canada)
  - **Rows**: 7,385 verified records
  - **License**: Open Government Licence - Canada (Permissive public reuse)
  - **Target Variable**: `CO2 Emissions(g/km)` (Empirically measured)
  - **File to Download**: Place `CO2 Emissions_Canada.csv` into `dataset/raw/emissions/`
- **Requested Title Status ("Intelligent Traffic Routing with Eco-Friendly Data")**:
  - *Unverified / Not found as a public Kaggle slug*. Details and secondary alternatives documented in `DATASET_PLAN.md`.

### Dataset B — BDD100K
- **Repository**: [https://github.com/bdd100k/bdd100k](https://github.com/bdd100k/bdd100k)
- **Role**: Computer vision evaluation for vehicle detection and scene traffic density estimation.
- **License**: **BDD License (Berkeley DeepDrive)**.
- **Terms**: Non-commercial academic research only. Redistribution of original images is restricted.
- **Usage Strategy**: Use a curated, small evaluation subset (100–1,000 frames) rather than the full 1.8 TB dataset.

### Dataset C — RDD2022 (Road Damage Dataset 2022)
- **Repository**: [https://github.com/sekilab/RoadDamageDetector](https://github.com/sekilab/RoadDamageDetector)
- **Dataset DOI**: [Figshare: RDD2022 CRDDC'22](https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547)
- **Role**: Computer vision detection of potholes (`D40`) and surface cracking (`D00`, `D10`, `D20`).
- **License**: **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**.
- **Mandatory Attribution**:
  > Arya, D., Maeda, H., Ghosh, S. K., Toshniwal, D., Mraz, A., Kashiyama, T., & Sekimoto, Y. (2022). *Crowdsensing-based Road Damage Detection Challenge (CRDDC'22)*. IEEE BigData.

---

## 3. How to Inspect & Validate Data

Once you download or place a dataset in `dataset/raw/`:

1. **Run the Automated Data Inspector**:
   ```bash
   python ml/data_inspection.py
   ```
   *Reports: row counts, column data types, missing value percentages, duplicate detection, and CO₂ physical value validity.*

2. **Generate Cleaned Preprocessed Data**:
   ```bash
   python ml/preprocess.py
   ```
   *Performs: documented median/mode imputation, IQR outlier logging, categorical encoding, and creates 70/15/15 train/val/test splits in `dataset/processed/emissions/`.*

3. **Run Validation Unit Tests**:
   ```bash
   pytest tests/test_dataset_validation.py
   ```
