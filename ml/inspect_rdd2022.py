"""
RDD2022 Dataset Inspection and Quality Audit Tool.

Inspects raw RDD2022 road damage images and Pascal VOC XML annotations.
Audits:
- Total train and test image counts
- Annotation XML file counts and parsing integrity
- Class distribution across standard categories (D00, D10, D20, D40)
- Image dimensions and channels
- Bounding box statistics
- Image-annotation correspondence (orphans, missing files)
- Corrupted or invalid files
Outputs machine-readable JSON report: dataset/raw/rdd2022/inspection_report.json
"""

import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Any, List

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "dataset" / "raw" / "rdd2022"

KNOWN_CLASSES = {
    "D00": "Longitudinal Crack",
    "D10": "Transverse Crack",
    "D20": "Alligator Crack",
    "D40": "Pothole",
}


def find_dataset_subdirs(base_dir: Path) -> Dict[str, Path]:
    """Finds train annotations, train images, and test images directories."""
    # Look under base_dir/India or directly under base_dir
    candidates = [base_dir / "India", base_dir]
    for c in candidates:
        xml_dir = c / "train" / "annotations" / "xmls"
        train_img_dir = c / "train" / "images"
        test_img_dir = c / "test" / "images"
        if xml_dir.exists() and train_img_dir.exists():
            return {
                "xmls": xml_dir,
                "train_images": train_img_dir,
                "test_images": test_img_dir if test_img_dir.exists() else None,
                "root": c,
            }
    return {}


def inspect_dataset(raw_dir: Path = RAW_DIR) -> Dict[str, Any]:
    dirs = find_dataset_subdirs(raw_dir)
    if not dirs:
        return {"error": f"No valid RDD2022 dataset directories found under {raw_dir}"}

    xml_dir = dirs["xmls"]
    train_img_dir = dirs["train_images"]
    test_img_dir = dirs["test_images"]

    xml_files = sorted(list(xml_dir.glob("*.xml")))
    train_img_files = sorted(list(train_img_dir.glob("*.jpg")) + list(train_img_dir.glob("*.png")))
    test_img_files = sorted(list(test_img_dir.glob("*.jpg")) + list(test_img_dir.glob("*.png"))) if test_img_dir else []

    xml_stems = {f.stem: f for f in xml_files}
    train_img_stems = {f.stem: f for f in train_img_files}

    class_counts = Counter()
    image_class_counts = defaultdict(int)
    bbox_counts_per_image = []
    dimension_counts = Counter()
    parsing_errors = []
    orphan_xmls = []
    orphan_train_images = []
    invalid_bboxes = []

    # Check image-annotation correspondence
    for stem in xml_stems:
        if stem not in train_img_stems:
            orphan_xmls.append(stem)

    for stem in train_img_stems:
        if stem not in xml_stems:
            orphan_train_images.append(stem)

    # Sample image dimension check & XML parsing
    total_bboxes = 0
    checked_dimensions = 0

    for xml_path in xml_files:
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Read dimensions from XML
            size_elem = root.find("size")
            width = int(size_elem.find("width").text) if size_elem is not None and size_elem.find("width") is not None else None
            height = int(size_elem.find("height").text) if size_elem is not None and size_elem.find("height") is not None else None
            
            if width and height:
                dimension_counts[f"{width}x{height}"] += 1

            objects = root.findall("object")
            bbox_counts_per_image.append(len(objects))
            total_bboxes += len(objects)

            for obj in objects:
                name_elem = obj.find("name")
                if name_elem is None or not name_elem.text:
                    continue
                cls_name = name_elem.text.strip()
                class_counts[cls_name] += 1
                image_class_counts[xml_path.stem] += 1

                bndbox = obj.find("bndbox")
                if bndbox is not None:
                    try:
                        xmin = float(bndbox.find("xmin").text)
                        ymin = float(bndbox.find("ymin").text)
                        xmax = float(bndbox.find("xmax").text)
                        ymax = float(bndbox.find("ymax").text)
                        if xmin >= xmax or ymin >= ymax or xmin < 0 or ymin < 0:
                            invalid_bboxes.append({
                                "file": xml_path.name,
                                "bbox": [xmin, ymin, xmax, ymax],
                                "reason": "non-positive area or negative coordinates"
                            })
                        elif width and height and (xmax > width or ymax > height):
                            # Minor clipping or bounds exceed
                            invalid_bboxes.append({
                                "file": xml_path.name,
                                "bbox": [xmin, ymin, xmax, ymax],
                                "size": [width, height],
                                "reason": "exceeds documented image size"
                            })
                    except Exception as ex:
                        invalid_bboxes.append({"file": xml_path.name, "error": str(ex)})

        except Exception as e:
            parsing_errors.append({"file": xml_path.name, "error": str(e)})

    # Verify a sample of actual images with PIL
    corrupted_images = []
    sample_images = train_img_files[:100]
    for img_path in sample_images:
        try:
            with Image.open(img_path) as im:
                im.verify()
        except Exception as e:
            corrupted_images.append({"file": img_path.name, "error": str(e)})

    # Summary statistics
    avg_bboxes = (total_bboxes / len(xml_files)) if xml_files else 0.0
    zero_box_images = sum(1 for c in bbox_counts_per_image if c == 0)

    report = {
        "status": "COMPLETED",
        "dataset_root": str(dirs["root"]),
        "file_counts": {
            "train_annotations_xml": len(xml_files),
            "train_images": len(train_img_files),
            "test_images": len(test_img_files),
            "total_images": len(train_img_files) + len(test_img_files),
        },
        "image_annotation_correspondence": {
            "matched_pairs": len(train_img_files) - len(orphan_train_images),
            "orphan_xmls_count": len(orphan_xmls),
            "orphan_images_count": len(orphan_train_images),
            "has_perfect_correspondence": len(orphan_xmls) == 0 and len(orphan_train_images) == 0,
        },
        "bounding_boxes": {
            "total_bounding_boxes": total_bboxes,
            "average_boxes_per_image": round(avg_bboxes, 2),
            "images_with_zero_damage_objects": zero_box_images,
            "invalid_or_clipped_boxes_count": len(invalid_bboxes),
        },
        "class_distribution": dict(class_counts),
        "known_class_mapping": KNOWN_CLASSES,
        "image_dimensions_frequency": dict(dimension_counts.most_common(5)),
        "data_quality_issues": {
            "parsing_errors_count": len(parsing_errors),
            "sample_corrupted_images_count": len(corrupted_images),
            "details_parsing_errors": parsing_errors[:5],
            "details_invalid_boxes": invalid_bboxes[:5],
        }
    }

    # Save to JSON
    report_file = RAW_DIR / "inspection_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def print_report(report: Dict[str, Any]) -> None:
    print("\n" + "="*70)
    print("      RDD2022 ROAD DAMAGE DATASET INSPECTION & QUALITY AUDIT      ")
    print("="*70)
    
    if "error" in report:
        print(f"[ERROR] {report['error']}")
        return

    fc = report["file_counts"]
    print("\n[ASSET COUNTS]")
    print(f"  Train XML Annotations : {fc['train_annotations_xml']}")
    print(f"  Train Camera Images   : {fc['train_images']}")
    print(f"  Test Camera Images    : {fc['test_images']}")
    print(f"  Total Images          : {fc['total_images']}")

    corr = report["image_annotation_correspondence"]
    print("\n[CORRESPONDENCE]")
    print(f"  Matched Pairs         : {corr['matched_pairs']}")
    print(f"  Orphan XMLs           : {corr['orphan_xmls_count']}")
    print(f"  Orphan Train Images   : {corr['orphan_images_count']}")
    print(f"  Correspondence Status : {'PERFECT' if corr['has_perfect_correspondence'] else 'PARTIAL'}")

    bb = report["bounding_boxes"]
    print("\n[BOUNDING BOXES & DENSITY]")
    print(f"  Total Bounding Boxes  : {bb['total_bounding_boxes']}")
    print(f"  Average Boxes/Image   : {bb['average_boxes_per_image']}")
    print(f"  Clean (No-Damage) Imgs: {bb['images_with_zero_damage_objects']}")
    print(f"  Invalid Box Geometry  : {bb['invalid_or_clipped_boxes_count']}")

    print("\n[DAMAGE CLASS DISTRIBUTION]")
    cd = report["class_distribution"]
    km = report["known_class_mapping"]
    for code, count in sorted(cd.items(), key=lambda x: x[1], reverse=True):
        desc = km.get(code, "Unknown Category")
        print(f"  {code:6} ({desc:25}) : {count:6} instances")

    dims = report["image_dimensions_frequency"]
    print("\n[TOP IMAGE RESOLUTIONS]")
    for res, count in dims.items():
        print(f"  {res:12} : {count} images")

    print("\n[AUDIT ARTIFACT]")
    print(f"  Report saved to: dataset/raw/rdd2022/inspection_report.json")
    print("="*70 + "\n")


if __name__ == "__main__":
    rep = inspect_dataset()
    print_report(rep)
