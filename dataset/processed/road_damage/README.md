# RDD2022 — Processed Road Damage Dataset (YOLO Format)

## 1. Overview

This directory stores the standardized, preprocessed road damage detection dataset formatted for modern object detection architectures (Ultralytics YOLOv8 / YOLOv11).

All raw Pascal VOC XML bounding boxes have been validated, normalized, and deterministically split into training, validation, and testing sets with fixed random seed (`seed=42`).

---

## 2. Directory Structure

```
dataset/processed/road_damage/
├── dataset.yaml                   # YOLO configuration mapping image paths & class IDs
├── manifest.json                  # Preprocessing statistics, split counts & class instances
├── road_damage_summary.csv        # Segment-level damage metrics (severity score, box counts)
├── README.md                      # This documentation
├── images/
│   ├── train/                     # 70% of annotated training frames
│   ├── val/                       # 15% validation frames
│   └── test/                      # 15% held-out test frames
└── labels/
    ├── train/                     # Normalized YOLO .txt label files
    ├── val/
    └── test/
```

---

## 3. Label Format Specification

Each `.txt` label file in `labels/{split}/` contains one line per detected road damage instance:

$$\langle\text{class\_id}\rangle \quad \langle x_{\text{center}}\rangle \quad \langle y_{\text{center}}\rangle \quad \langle w\rangle \quad \langle h\rangle$$

- Coordinates are normalized in $[0, 1]$ relative to image dimensions.
- Bounding box coordinates adhere to standard YOLO conventions.

### Class ID Mapping

| Class ID | Class Code | Description |
|---|---|---|
| `0` | **D00** | Longitudinal Crack |
| `1` | **D10** | Transverse Crack |
| `2` | **D20** | Alligator Crack |
| `3` | **D40** | Pothole |

---

## 4. Road Damage Severity Index Formula

For spatial route analysis, segment-level pavement degradation is scored as:

$$\text{Damage Severity Score} = 3.0 \cdot N_{\text{D40}} + 2.0 \cdot N_{\text{D20}} + 1.0 \cdot N_{\text{D10}} + 1.0 \cdot N_{\text{D00}}$$

where:
- Potholes ($D40$) carry the highest penalty ($3.0$) due to vehicle deceleration and puncture risk.
- Alligator fatigue cracks ($D20$) carry a moderate penalty ($2.0$) due to road surface roughness.
- Longitudinal and transverse cracks ($D00, D10$) carry a baseline penalty ($1.0$).

---

## 5. Preprocessing Execution

To regenerate the processed splits reproducibly:
```bash
# Dry run verification
python ml/preprocess_rdd2022.py --dry-run

# Full execution
python ml/preprocess_rdd2022.py --seed 42
```
