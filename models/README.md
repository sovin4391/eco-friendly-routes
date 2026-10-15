# Models Directory

This directory stores serialized machine learning and computer vision models and pipelines.

## Active Artifacts

### 1. Vehicle Tailpipe Emissions Regressor (`models/emissions_model.joblib`)
- **Architecture**: Scikit-learn Pipeline (`StandardScaler` + `OneHotEncoder` + `RandomForestRegressor`)
- **Metadata**: `models/emissions_model_metadata.json`
- **Trained on**: Natural Resources Canada (NRCan) Vehicle Fuel Consumption & Emissions Dataset
- **Performance**: Test $R^2 = 0.9984$, RMSE $= 2.34$ g/km, MAE $= 1.25$ g/km
- **Inference Service**: `backend/services/emissions_service.py` (`POST /api/v1/emissions/predict`)

### 2. Road Damage Object Detector (`models/road_damage/best.pt`)
- **Active Model**: 5-Epoch YOLOv8n (`models/road_damage/5epoch_run/best.pt`, promoted)
- **Architecture**: Ultralytics YOLOv8n (nano detector, CPU-optimized, $512 \times 512$ resolution)
- **Metadata**: `models/road_damage/training_metrics.json`, `models/road_damage/class_mapping.json`
- **Trained on**: RDD2022 (Crowdsourced Road Damage Dataset 2022, India subset, full 5,392 train images)
- **Test Set Metrics (Held-Out)**:
  - mAP@0.5: `0.1301` (+317% relative improvement over baseline)
  - mAP@0.5:0.95: `0.0540` (+468% relative improvement)
  - Precision: `0.1965`
  - Recall: `0.1639` (+160% relative improvement)
- **Per-Class Breakdown**:
  - `D00` (Longitudinal Crack): mAP@0.5 = `0.0630`
  - `D10` (Transverse Crack): mAP@0.5 = `0.0000` (limited representation, 10 test instances)
  - `D20` (Alligator Crack): mAP@0.5 = `0.3130`
  - `D40` (Pothole): mAP@0.5 = `0.1450`
- **Preserved Baseline**:
  - Location: `models/road_damage/baseline/best.pt` (MD5: `8880c27f9621a520ff88ed11768bb96f`)
  - 3 epochs, fraction=0.1, mAP@0.5 = `0.0312`
- **Inference Service**: `backend/services/road_damage_service.py` (`POST /api/v1/road-damage/detect`)

*Note: Heavy model weights (*.joblib, *.pt) are excluded from git by `.gitignore`.*

