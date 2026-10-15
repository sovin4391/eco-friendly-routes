"""
Road Damage Model Trainer for Eco-Friendly Routes.

Trains a lightweight object detection model (YOLOv8n) on the preprocessed
RDD2022 road damage dataset (D00, D10, D20, D40) with CPU compatibility.
Evaluates on held-out test split, saving weights and authentic metrics under
models/road_damage/.
"""

import argparse
import json
import os
import shutil
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_YAML = PROJECT_ROOT / "dataset" / "processed" / "road_damage" / "dataset.yaml"
MODELS_DIR = PROJECT_ROOT / "models" / "road_damage"


def train_road_damage_model(
    data_yaml: Path = DEFAULT_DATA_YAML,
    model_name: str = "yolov8n.pt",
    epochs: int = 20,
    batch_size: int = 8,
    img_size: int = 512,
    device: str = "cpu",
    seed: int = 42,
    fraction: float = 1.0,
    warmup_epochs: int = 1,
    run_name: str = "train_rdd2022_corrected",
    output_dir: Optional[Path] = None,
    promote: bool = True,
):
    print("\n" + "="*70)
    print("      RDD2022 ROAD DAMAGE OBJECT DETECTOR TRAINING (YOLOv8)      ")
    print("="*70)
    print(f"Dataset YAML     : {data_yaml}")
    print(f"Base Model       : {model_name}")
    print(f"Epochs           : {epochs}")
    print(f"Batch Size       : {batch_size}")
    print(f"Image Size       : {img_size}")
    print(f"Compute Device   : {device}")
    print(f"Dataset Fraction : {fraction}")
    print(f"Warmup Epochs    : {warmup_epochs}")
    print(f"Random Seed      : {seed}")
    print(f"Run Name         : {run_name}")

    if output_dir is None:
        output_dir = MODELS_DIR / "corrected_run"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Run Output Dir   : {output_dir}")

    if not data_yaml.exists():
        raise FileNotFoundError(f"Dataset YAML not found at: {data_yaml}. Run ml/preprocess_rdd2022.py first.")

    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise ImportError(
            f"Ultralytics is required for road damage model training: {e}. "
            "Please install via: pip install ultralytics torch torchvision"
        )

    # 1. Initialize detector from pretrained weights
    print(f"\nLoading pretrained base architecture {model_name}...")
    model = YOLO(model_name)

    # 2. Execute Training
    t_start = time.time()
    print("\nStarting model training...")
    run_project_dir = PROJECT_ROOT / "runs" / "road_damage"
    run_project_dir.mkdir(parents=True, exist_ok=True)

    train_args = {
        "data": str(data_yaml.resolve().as_posix()),
        "epochs": epochs,
        "batch": batch_size,
        "imgsz": img_size,
        "device": device,
        "seed": seed,
        "workers": 0,
        "warmup_epochs": warmup_epochs,
        "project": str(run_project_dir),
        "name": run_name,
        "exist_ok": True,
        "verbose": True,
        "save": True,
        "save_period": 1,
        "patience": 50,
    }
    if fraction < 1.0:
        train_args["fraction"] = fraction

    try:
        results = model.train(**train_args)
    except Exception as e:
        print(f"\n[ERROR] Training interrupted or failed: {e}")
        raise e

    training_duration = time.time() - t_start
    print(f"\nTraining completed in {training_duration / 60:.2f} minutes.")

    # 3. Locate best and last checkpoints from training run
    run_dir = Path(results.save_dir)
    best_pt = run_dir / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = run_dir / "weights" / "last.pt"

    if not best_pt.exists():
        raise FileNotFoundError(f"No checkpoint found in {run_dir / 'weights'}")

    # Copy checkpoints to the run's isolated output directory
    shutil.copy2(best_pt, output_dir / "best.pt")
    if (run_dir / "weights" / "last.pt").exists():
        shutil.copy2(run_dir / "weights" / "last.pt", output_dir / "last.pt")
    if (run_dir / "results.csv").exists():
        shutil.copy2(run_dir / "results.csv", output_dir / "results.csv")

    # 4. Evaluate on validation split and held-out test split using the newly trained best weights
    print("\nEvaluating trained checkpoint on validation set...")
    eval_model = YOLO(str(best_pt))
    val_results = eval_model.val(
        data=str(data_yaml.resolve().as_posix()),
        split="val",
        imgsz=img_size,
        device=device,
        verbose=True,
    )

    val_map50 = round(float(val_results.box.map50), 4)
    val_map50_95 = round(float(val_results.box.map), 4)
    val_precision = round(float(val_results.box.mp), 4)
    val_recall = round(float(val_results.box.mr), 4)

    print("\nEvaluating trained checkpoint on held-out test set...")
    test_results = eval_model.val(
        data=str(data_yaml.resolve().as_posix()),
        split="test",
        imgsz=img_size,
        device=device,
        verbose=True,
    )

    # Extract test metrics
    test_map50 = round(float(test_results.box.map50), 4)
    test_map50_95 = round(float(test_results.box.map), 4)
    test_precision = round(float(test_results.box.mp), 4)
    test_recall = round(float(test_results.box.mr), 4)

    per_class_map50 = {
        f"Class_{i}": round(float(test_results.box.maps[i]), 4) if len(test_results.box.maps) > i else None
        for i in range(len(test_results.box.maps))
    }

    # Extract confusion matrix
    cm_matrix = test_results.confusion_matrix.matrix.tolist()

    metrics_data = {
        "model_architecture": model_name,
        "epochs_trained": epochs,
        "image_size": img_size,
        "batch_size": batch_size,
        "compute_device": device,
        "dataset_fraction": fraction,
        "warmup_epochs": warmup_epochs,
        "random_seed": seed,
        "training_duration_seconds": round(training_duration, 1),
        "validation_metrics": {
            "mAP50": val_map50,
            "mAP50_95": val_map50_95,
            "precision": val_precision,
            "recall": val_recall,
        },
        "test_metrics": {
            "mAP50": test_map50,
            "mAP50_95": test_map50_95,
            "precision": test_precision,
            "recall": test_recall,
        },
        "per_class_mAP50": per_class_map50,
        "classes": {
            "0": "D00: Longitudinal Crack",
            "1": "D10: Transverse Crack",
            "2": "D20: Alligator Crack",
            "3": "D40: Pothole",
        },
        "confusion_matrix": cm_matrix,
    }

    metrics_file = output_dir / "training_metrics.json"
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Saved run evaluation metrics to: {metrics_file}")

    class_mapping_file = output_dir / "class_mapping.json"
    with open(class_mapping_file, "w", encoding="utf-8") as f:
        json.dump({
            "classes": metrics_data["classes"],
            "model_type": "yolov8_detector",
            "weights_file": "best.pt",
        }, f, indent=2)

    # 5. Generate representative prediction samples
    pred_dir = output_dir / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)
    test_img_dir = PROJECT_ROOT / "dataset" / "processed" / "road_damage" / "images" / "test"
    sample_images = list(test_img_dir.glob("*.jpg"))[:5]
    if sample_images:
        print(f"\nGenerating representative test predictions ({len(sample_images)} samples)...")
        eval_model.predict(
            source=[str(p) for p in sample_images],
            imgsz=img_size,
            device=device,
            save=True,
            project=str(pred_dir),
            name="samples",
            exist_ok=True,
            conf=0.20,
        )

    # 6. Baseline comparison & Conditional Promotion
    baseline_metrics_file = MODELS_DIR / "baseline" / "training_metrics.json"
    baseline_map50 = 0.0312
    if baseline_metrics_file.exists():
        with open(baseline_metrics_file, "r") as f:
            b_data = json.load(f)
            baseline_map50 = b_data.get("test_metrics", {}).get("mAP50", 0.0312)

    print("\n" + "="*70)
    print("                EVALUATION COMPARISON VS BASELINE")
    print("="*70)
    print(f"Baseline Test mAP@0.5  : {baseline_map50:.4f}")
    print(f"New Run  Test mAP@0.5  : {test_map50:.4f}")
    print(f"New Run  Test Recall   : {test_recall:.4f}")
    print(f"New Run  Test Precision: {test_precision:.4f}")

    if promote:
        if test_map50 > baseline_map50:
            active_pt = MODELS_DIR / "best.pt"
            shutil.copy2(best_pt, active_pt)
            shutil.copy2(metrics_file, MODELS_DIR / "training_metrics.json")
            shutil.copy2(class_mapping_file, MODELS_DIR / "class_mapping.json")
            print(f"\n[PROMOTED] New checkpoint outperformed baseline! Updated active model at: {active_pt}")
        else:
            print(f"\n[RETAINED BASELINE] New checkpoint mAP@0.5 ({test_map50:.4f}) did not exceed baseline ({baseline_map50:.4f}). Baseline remains active.")
    print("="*70 + "\n")

    return metrics_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train road damage detector on RDD2022.")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs (default=5).")
    parser.add_argument("--batch", type=int, default=8, help="Batch size (8 for CPU).")
    parser.add_argument("--imgsz", type=int, default=512, help="Image resolution.")
    parser.add_argument("--device", type=str, default="cpu", help="Compute device (cpu or 0).")
    parser.add_argument("--fraction", type=float, default=1.0, help="Fraction of training images to use (0.0 to 1.0).")
    parser.add_argument("--warmup-epochs", type=int, default=1, help="Warmup epochs (default=1).")
    parser.add_argument("--run-name", type=str, default="train_rdd2022_5epoch", help="Name for training run.")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to save run model and metrics.")
    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else (MODELS_DIR / "5epoch_run")

    train_road_damage_model(
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.imgsz,
        device=args.device,
        fraction=args.fraction,
        warmup_epochs=args.warmup_epochs,
        run_name=args.run_name,
        output_dir=out_dir,
    )
