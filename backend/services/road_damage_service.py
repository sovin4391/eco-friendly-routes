"""
Module C: Road Condition & Damage Detection Service.

Responsibilities:
- Encapsulates road damage detection models (RDD2022 trained YOLO models).
- Analyzes pavement images for potholes (D40) and surface cracking (D00, D10, D20).
- Provides genuine inference when model weights are available.
- Graceful degradation: NEVER fabricates detections when model is unavailable.
- Enforces strict isolation: does not arbitrarily modify emissions or route scores.
"""

import io
from pathlib import Path
from typing import Optional, List, Dict, Any

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_WEIGHTS_PATH = PROJECT_ROOT / "models" / "road_damage" / "best.pt"

DAMAGE_CLASSES = {
    0: {"code": "D00", "name": "Longitudinal Crack", "severity_weight": 1.0},
    1: {"code": "D10", "name": "Transverse Crack", "severity_weight": 1.0},
    2: {"code": "D20", "name": "Alligator Crack", "severity_weight": 2.0},
    3: {"code": "D40", "name": "Pothole", "severity_weight": 3.0},
}


class RoadDamageService:
    def __init__(self, weights_path: Path = MODEL_WEIGHTS_PATH):
        self.weights_path = weights_path
        self.model = None
        self.model_loaded: bool = False
        self._load_model_if_available()

    def _load_model_if_available(self) -> bool:
        """Attempts to load Ultralytics YOLO model from saved weights."""
        if self.weights_path.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(self.weights_path))
                self.model_loaded = True
                print(f"[RoadDamageService] Successfully loaded detector: {self.weights_path}")
                return True
            except Exception as e:
                print(f"[RoadDamageService] Warning: Failed to load model from {self.weights_path}: {e}")
                self.model = None
                self.model_loaded = False
                return False
        else:
            self.model = None
            self.model_loaded = False
            return False

    def is_available(self) -> bool:
        """Returns True if the road damage vision model is initialized and weights are loaded."""
        if not self.model_loaded and self.weights_path.exists():
            self._load_model_if_available()
        return self.model_loaded

    def get_supported_classes(self) -> List[Dict[str, Any]]:
        """Returns the list of detectable road damage categories and their severity weights."""
        return [
            {"id": k, "code": v["code"], "name": v["name"], "severity_weight": v["severity_weight"]}
            for k, v in DAMAGE_CLASSES.items()
        ]

    def detect_damage(self, image_bytes: bytes, conf_threshold: float = 0.25) -> Dict[str, Any]:
        """
        Runs road damage inference on uploaded image bytes.
        Returns authentic detections with bounding boxes, confidence, and pavement quality metrics.
        Raises RuntimeError if model is not available.
        """
        if not self.is_available():
            raise RuntimeError(
                "Road damage detection model is not loaded. "
                "Please train or download a verified model artifact under models/road_damage/best.pt."
            )

        # 1. Validate and open image
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()  # Check integrity
            # Re-open after verify
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Uploaded file is not a valid, readable image: {e}")

        img_w, img_h = image.size

        # 2. Run inference
        results = self.model.predict(
            source=image,
            conf=conf_threshold,
            device="cpu",
            verbose=False
        )

        detections = []
        damage_counts = {"D00": 0, "D10": 0, "D20": 0, "D40": 0}
        total_severity = 0.0

        if results and len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None:
                for b in boxes:
                    cls_id = int(b.cls[0].item())
                    conf = round(float(b.conf[0].item()), 3)
                    xyxy = b.xyxy[0].tolist()  # [xmin, ymin, xmax, ymax] in pixels

                    # Normalized coordinates [0, 1]
                    xmin_norm = max(0.0, min(1.0, xyxy[0] / img_w))
                    ymin_norm = max(0.0, min(1.0, xyxy[1] / img_h))
                    xmax_norm = max(0.0, min(1.0, xyxy[2] / img_w))
                    ymax_norm = max(0.0, min(1.0, xyxy[3] / img_h))

                    cls_info = DAMAGE_CLASSES.get(cls_id, {"code": f"C{cls_id}", "name": "Unknown Damage", "severity_weight": 1.0})
                    code = cls_info["code"]
                    damage_counts[code] = damage_counts.get(code, 0) + 1
                    total_severity += cls_info["severity_weight"]

                    detections.append({
                        "class_id": cls_id,
                        "class_code": code,
                        "class_name": cls_info["name"],
                        "confidence": conf,
                        "bbox_pixels": [round(x, 1) for x in xyxy],
                        "bbox_normalized": [round(ymin_norm, 4), round(xmin_norm, 4), round(ymax_norm, 4), round(xmax_norm, 4)],
                    })

        # Determine surface quality classification
        if total_severity == 0.0:
            pavement_status = "Good / Undamaged"
        elif total_severity < 3.0:
            pavement_status = "Minor Surface Wear"
        elif total_severity < 6.0:
            pavement_status = "Moderate Degradation"
        else:
            pavement_status = "Severe Pavement Distress"

        return {
            "is_model_loaded": True,
            "image_dimensions": {"width": img_w, "height": img_h},
            "detections": detections,
            "total_detections": len(detections),
            "damage_counts": damage_counts,
            "damage_severity_score": round(total_severity, 2),
            "pavement_status": pavement_status,
            "confidence_threshold": conf_threshold,
            "model_architecture": "Ultralytics YOLOv8 (RDD2022 India)",
        }

    def get_segment_damage_index(
        self,
        segment_id: str,
        coordinates: Optional[List[List[float]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves verified pavement damage and roughness metrics for a specific route segment.
        Returns None if no verified road condition survey data exists for this segment.
        """
        # Strict rule: Never assume damage belongs to an arbitrary route without verified coordinates.
        return None


road_damage_service = RoadDamageService()
