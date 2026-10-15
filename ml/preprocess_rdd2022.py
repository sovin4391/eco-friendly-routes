"""
RDD2022 Dataset Preprocessing and Train/Val/Test Splitter.

Converts official Pascal VOC XML annotations to standardized YOLO format:
- Bounding box normalization [x_center, y_center, width, height] in [0, 1].
- Bounding box boundary validation and clipping.
- Deterministic reproducible splitting (70% Train, 15% Val, 15% Test) with fixed random seed.
- Generation of YOLO dataset.yaml and metadata manifest.json.
- Preservation of raw data: output stored strictly in dataset/processed/road_damage/.
- Dry-run mode for pre-split validation.
"""

import argparse
import json
import os
import random
import shutil
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR = PROJECT_ROOT / "dataset" / "raw" / "rdd2022"
DEFAULT_PROCESSED_DIR = PROJECT_ROOT / "dataset" / "processed" / "road_damage"

CLASS_MAP = {
    "D00": 0,  # Longitudinal Crack
    "D10": 1,  # Transverse Crack
    "D20": 2,  # Alligator Crack
    "D40": 3,  # Pothole
}

CLASS_DESCRIPTIONS = {
    0: "D00: Longitudinal Crack",
    1: "D10: Transverse Crack",
    2: "D20: Alligator Crack",
    3: "D40: Pothole",
}


def find_raw_subdirs(base_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """Locates train XMLs and images folders."""
    candidates = [base_dir / "India", base_dir]
    for c in candidates:
        xml_dir = c / "train" / "annotations" / "xmls"
        img_dir = c / "train" / "images"
        if xml_dir.exists() and img_dir.exists():
            return xml_dir, img_dir
    return None, None


def parse_voc_xml(xml_path: Path, img_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Parses a single Pascal VOC XML file and returns normalized YOLO bounding boxes.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        size_elem = root.find("size")
        width, height = None, None
        if size_elem is not None:
            w_text = size_elem.find("width")
            h_text = size_elem.find("height")
            if w_text is not None and h_text is not None:
                width = int(w_text.text)
                height = int(h_text.text)

        # Fallback to image dimensions if missing or 0 in XML
        if (not width or not height or width <= 0 or height <= 0) and img_path and img_path.exists():
            with Image.open(img_path) as im:
                width, height = im.size

        if not width or not height or width <= 0 or height <= 0:
            return None

        boxes = []
        class_counts = Counter()

        for obj in root.findall("object"):
            name_elem = obj.find("name")
            if name_elem is None or not name_elem.text:
                continue
            cname = name_elem.text.strip()
            if cname not in CLASS_MAP:
                continue

            cid = CLASS_MAP[cname]
            class_counts[cname] += 1

            bndbox = obj.find("bndbox")
            if bndbox is None:
                continue

            try:
                xmin = float(bndbox.find("xmin").text)
                ymin = float(bndbox.find("ymin").text)
                xmax = float(bndbox.find("xmax").text)
                ymax = float(bndbox.find("ymax").text)
            except (ValueError, TypeError, AttributeError):
                continue

            # Clip to image boundaries
            xmin = max(0.0, min(float(width), xmin))
            xmax = max(0.0, min(float(width), xmax))
            ymin = max(0.0, min(float(height), ymin))
            ymax = max(0.0, min(float(height), ymax))

            bw = xmax - xmin
            bh = ymax - ymin
            if bw <= 1.0 or bh <= 1.0:
                continue

            # Convert to YOLO center format [0, 1]
            x_center = (xmin + xmax) / (2.0 * width)
            y_center = (ymin + ymax) / (2.0 * height)
            w_norm = bw / width
            h_norm = bh / height

            # Double check bounds
            x_center = max(0.0, min(1.0, x_center))
            y_center = max(0.0, min(1.0, y_center))
            w_norm = max(0.0, min(1.0, w_norm))
            h_norm = max(0.0, min(1.0, h_norm))

            boxes.append((cid, x_center, y_center, w_norm, h_norm))

        return {
            "stem": xml_path.stem,
            "width": width,
            "height": height,
            "boxes": boxes,
            "class_counts": dict(class_counts),
        }
    except Exception as e:
        print(f"Warning: Failed to parse XML {xml_path.name}: {e}")
        return None


def stratified_split(
    samples: List[Dict[str, Any]],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Deterministically splits samples across train, val, test,
    ensuring each split contains balanced damage class representation.
    """
    rng = random.Random(seed)
    
    # Bucket by dominant damage class
    buckets = defaultdict(list)
    for s in samples:
        if s["class_counts"]:
            # Pick highest count class
            dominant = max(s["class_counts"].items(), key=lambda x: x[1])[0]
        else:
            dominant = "no_damage"
        buckets[dominant].append(s)

    train_set, val_set, test_set = [], [], []

    for _, group in buckets.items():
        rng.shuffle(group)
        n = len(group)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        
        train_set.extend(group[:n_train])
        val_set.extend(group[n_train:n_train + n_val])
        test_set.extend(group[n_train + n_val:])

    # Shuffle resulting splits
    rng.shuffle(train_set)
    rng.shuffle(val_set)
    rng.shuffle(test_set)

    return train_set, val_set, test_set


def preprocess_dataset(
    raw_dir: Path = DEFAULT_RAW_DIR,
    output_dir: Path = DEFAULT_PROCESSED_DIR,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42,
    dry_run: bool = False
) -> Dict[str, Any]:
    print("\n" + "="*70)
    print("      RDD2022 PREPROCESSING & REPRODUCIBLE DATASET SPLITTING      ")
    print("="*70)
    print(f"Raw Source Path     : {raw_dir}")
    print(f"Processed Dest Path : {output_dir}")
    print(f"Split Ratios        : {train_ratio:.0%} Train / {val_ratio:.0%} Val / {1.0 - train_ratio - val_ratio:.0%} Test")
    print(f"Random Seed         : {seed}")
    print(f"Dry Run Mode        : {'ENABLED (No files will be written)' if dry_run else 'DISABLED (Writing files)'}")

    xml_dir, img_dir = find_raw_subdirs(raw_dir)
    if not xml_dir or not img_dir:
        raise FileNotFoundError(f"Could not locate XML annotations and images under {raw_dir}")

    xml_files = sorted(list(xml_dir.glob("*.xml")))
    print(f"\nDiscovered {len(xml_files)} XML annotation files. Parsing Pascal VOC structures...")

    parsed_samples = []
    skipped_count = 0

    for xml_f in xml_files:
        img_f = img_dir / f"{xml_f.stem}.jpg"
        if not img_f.exists():
            img_f = img_dir / f"{xml_f.stem}.png"
        if not img_f.exists():
            skipped_count += 1
            continue

        sample = parse_voc_xml(xml_f, img_f)
        if sample:
            sample["image_path"] = img_f
            parsed_samples.append(sample)
        else:
            skipped_count += 1

    print(f"Parsed {len(parsed_samples)} valid image-annotation pairs (skipped {skipped_count}).")

    # Perform stratified split
    train_set, val_set, test_set = stratified_split(
        parsed_samples,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        seed=seed
    )

    print(f"\nSplit Distribution:")
    print(f"  Train : {len(train_set):5} samples ({len(train_set)/len(parsed_samples):.1%})")
    print(f"  Val   : {len(val_set):5} samples ({len(val_set)/len(parsed_samples):.1%})")
    print(f"  Test  : {len(test_set):5} samples ({len(test_set)/len(parsed_samples):.1%})")

    # Count damage instances per split
    def count_boxes(sample_list):
        c = Counter()
        for s in sample_list:
            for b in s["boxes"]:
                c[b[0]] += 1
        return c

    train_cls = count_boxes(train_set)
    val_cls = count_boxes(val_set)
    test_cls = count_boxes(test_set)

    print("\nClass instance representation across splits:")
    for cid in range(4):
        cname = [k for k, v in CLASS_MAP.items() if v == cid][0]
        desc = CLASS_DESCRIPTIONS[cid]
        print(f"  {desc:25} -> Train: {train_cls[cid]:5} | Val: {val_cls[cid]:5} | Test: {test_cls[cid]:5}")

    manifest = {
        "status": "DRY_RUN" if dry_run else "COMPLETED",
        "random_seed": seed,
        "split_ratios": {"train": train_ratio, "val": val_ratio, "test": round(1.0 - train_ratio - val_ratio, 2)},
        "counts": {
            "total_samples": len(parsed_samples),
            "train": len(train_set),
            "val": len(val_set),
            "test": len(test_set),
        },
        "classes": {
            "0": "D00 (Longitudinal Crack)",
            "1": "D10 (Transverse Crack)",
            "2": "D20 (Alligator Crack)",
            "3": "D40 (Pothole)",
        },
        "class_instances_per_split": {
            "train": {CLASS_DESCRIPTIONS[cid]: train_cls[cid] for cid in range(4)},
            "val": {CLASS_DESCRIPTIONS[cid]: val_cls[cid] for cid in range(4)},
            "test": {CLASS_DESCRIPTIONS[cid]: test_cls[cid] for cid in range(4)},
        }
    }

    if dry_run:
        print("\nDry run completed. Output files were not written.")
        return manifest

    # Write processed dataset files
    images_dir = output_dir / "images"
    labels_dir = output_dir / "labels"
    for split in ["train", "val", "test"]:
        (images_dir / split).mkdir(parents=True, exist_ok=True)
        (labels_dir / split).mkdir(parents=True, exist_ok=True)

    rows_summary = []

    for split_name, split_samples in [("train", train_set), ("val", val_set), ("test", test_set)]:
        for s in split_samples:
            img_src = s["image_path"]
            img_dst = images_dir / split_name / img_src.name
            lbl_dst = labels_dir / split_name / f"{s['stem']}.txt"

            # Copy image (or link)
            shutil.copy2(img_src, img_dst)

            # Write YOLO text label
            with open(lbl_dst, "w", encoding="utf-8") as f:
                for b in s["boxes"]:
                    cid, xc, yc, w, h = b
                    f.write(f"{cid} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

            # Record in summary
            cc = s["class_counts"]
            total_d = sum(cc.values())
            # Severity index: D40 (pothole) weight 3.0, D20 weight 2.0, D10/D00 weight 1.0
            sev = cc.get("D40", 0) * 3.0 + cc.get("D20", 0) * 2.0 + cc.get("D10", 0) * 1.0 + cc.get("D00", 0) * 1.0
            rows_summary.append({
                "image_id": s["stem"],
                "split": split_name,
                "width": s["width"],
                "height": s["height"],
                "d00_count": cc.get("D00", 0),
                "d10_count": cc.get("D10", 0),
                "d20_count": cc.get("D20", 0),
                "d40_count": cc.get("D40", 0),
                "total_damage_boxes": total_d,
                "damage_severity_score": round(sev, 1),
            })

    # Write summary CSV
    df_summary = pd.DataFrame(rows_summary)
    summary_csv = output_dir / "road_damage_summary.csv"
    df_summary.to_csv(summary_csv, index=False)
    print(f"\nSaved segment damage summary CSV: {summary_csv} ({len(df_summary)} rows)")

    # Write dataset.yaml for YOLO training
    yaml_content = f"""# Ultralytics YOLOv8 Dataset Configuration: RDD2022 Road Damage
path: {output_dir.resolve().as_posix()}
train: images/train
val: images/val
test: images/test

# Classes
names:
  0: D00
  1: D10
  2: D20
  3: D40

# Class descriptions:
# 0: Longitudinal Crack
# 1: Transverse Crack
# 2: Alligator Crack
# 3: Pothole
"""
    yaml_file = output_dir / "dataset.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"Saved YOLO dataset configuration: {yaml_file}")

    # Write manifest JSON
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved preprocessing manifest JSON: {manifest_file}")

    print("\n[SUCCESS] Preprocessing completed successfully!")
    print("="*70 + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess RDD2022 dataset for YOLO training.")
    parser.add_argument("--dry-run", action="store_true", help="Run validation without writing files.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting.")
    args = parser.parse_args()

    preprocess_dataset(seed=args.seed, dry_run=args.dry_run)
