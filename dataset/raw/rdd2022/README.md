# RDD2022 — Raw Road Damage Dataset (India Subset)

## 1. Overview & Provenance

This directory stores the official, raw road damage detection dataset acquired from the **Crowdsensing-based Road Damage Detection Challenge (CRDDC'2022)** published by Seki Lab (The University of Tokyo) and IIT Roorkee.

- **Dataset Title**: *RDD2022 - The multi-national Road Damage Dataset released through CRDDC'2022*
- **Official DOI**: [10.6084/m9.figshare.21431547](https://doi.org/10.6084/m9.figshare.21431547)
- **Official Figshare Publication**: [https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547](https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547)
- **Reference Code Repository**: [https://github.com/sekilab/RoadDamageDetector](https://github.com/sekilab/RoadDamageDetector)
- **License**: **Creative Commons Attribution 4.0 International (CC BY 4.0)**
- **Attribution Citation**:
  ```bibtex
  @article{arya2024rdd2022,
    title={RDD2022: A multi-national image dataset for automatic road damage detection},
    author={Arya, Deeksha and Maeda, Hiroya and Ghosh, Sanjay Kumar and Toshniwal, Durga and Sekimoto, Yoshihide},
    journal={Geoscience Data Journal},
    volume={11},
    number={4},
    pages={846--862},
    year={2024},
    publisher={Wiley Online Library}
  }
  ```

---

## 2. Acquired Files & Verification

| Asset | Source URL | File Size | Description |
|---|---|---|---|
| `RDD2022_India.zip` | `https://ndownloader.figshare.com/files/38030910` (bytes 609341079-1136050223) | **502.31 MB** (526,709,145 bytes) | Contiguous uncompressed zip entry of India camera frames and Pascal VOC XMLs |
| `label_map.pbtxt` | `https://ndownloader.figshare.com/files/38030820` | 127 bytes | Official TensorFlow/VOC label mapping file |
| `Directory_Structure_CRDDC_RDD2022.txt` | `https://ndownloader.figshare.com/files/38030823` | 1,161 bytes | Official challenge directory hierarchy |

---

## 3. Directory Layout

```
dataset/raw/rdd2022/
├── RDD2022_India.zip                  # Raw zip archive (ignored by git)
├── label_map.pbtxt                    # Official label map
├── Directory_Structure_CRDDC_RDD2022.txt
├── inspection_report.json             # Generated quality audit report
├── README.md                          # This documentation
└── India/                             # Extracted asset directory (ignored by git)
    ├── train/
    │   ├── annotations/
    │   │   └── xmls/                  # Pascal VOC XML annotation files (e.g., India_000001.xml)
    │   └── images/                    # Training camera images (e.g., India_000001.jpg)
    └── test/
        └── images/                    # Held-out challenge test images (e.g., India_009891.jpg)
```

---

## 4. Standard Damage Categories

| Class Code | Category Name | Description | Routing Penalty Profile |
|---|---|---|---|
| **D00** | Longitudinal Crack | Pavement surface cracks parallel to traffic flow | Low: minor tyre friction |
| **D10** | Transverse Crack | Cracks perpendicular to traffic flow | Low-Medium: slight bumping |
| **D20** | Alligator Crack | Interconnected fatigue cracking resembling reptile scales | Medium-High: structural breakdown |
| **D40** | Pothole | Bowl-shaped road depressions and cavities | High: severe hazard, braking penalty |

---

## 5. Inspection Protocol

To audit the raw dataset for image corruptions, bounding box bounds, orphan annotations, and class distributions, run:
```bash
python ml/inspect_rdd2022.py
```
This generates `dataset/raw/rdd2022/inspection_report.json`.
