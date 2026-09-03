"""
Object Detector Module for Smart Traffic Management System.
Uses YOLOv8 for vehicle, pedestrian, and general obstacle detection.
"""
from pathlib import Path
import threading
import numpy as np

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO = None
    YOLO_AVAILABLE = False

from .base_detector import BaseDetector


class ObjectDetector(BaseDetector):
    """YOLOv8 object detector for traffic monitoring."""

    def __init__(self, model_path: str | None = None, confidence_threshold: float = 0.5):
        if model_path is None:
            root_dir = Path(__file__).resolve().parent.parent
            candidate_paths = [
                root_dir / "yolov8n.pt",
                root_dir / "models" / "yolov8n.pt",
                root_dir / "ai_models" / "yolov8n.pt",
                Path("yolov8n.pt"),
            ]
            for p in candidate_paths:
                if p.exists():
                    model_path = str(p)
                    break
            if model_path is None:
                model_path = "yolov8n.pt"

        super().__init__(model_path=model_path, confidence_threshold=confidence_threshold)
        self.classes = None
        self._lock = threading.Lock()
        self.load_model()

    def load_model(self):
        """Load YOLO model weights."""
        if not YOLO_AVAILABLE or YOLO is None:
            print("ultralytics not installed — YOLO model cannot be loaded")
            self.model = None
            return

        try:
            self.model = YOLO(self.model_path)
            print(f"YOLO model loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.model = None

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        return frame

    def detect(self, frame: np.ndarray):
        if self.model is None or not callable(self.model):
            return []

        try:
            with self._lock:
                results = self.model(frame, conf=self.confidence_threshold)
            return results
        except Exception as e:
            print(f"Error during object detection: {e}")
            return []

    def postprocess(self, detections, frame: np.ndarray | None = None) -> list[dict]:
        processed_results = []
        if detections is None or len(detections) == 0:
            return processed_results

        h, w = (frame.shape[:2]) if (frame is not None and hasattr(frame, "shape")) else (None, None)

        for result in detections:
            if not hasattr(result, "boxes") or result.boxes is None:
                continue
            boxes = result.boxes.cpu().numpy()
            for i, box in enumerate(boxes):
                try:
                    xyxy = box.xyxy[0].astype(int)
                    x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                    # Sanitize bounding box bounds
                    if w is not None and h is not None:
                        x1 = max(0, min(x1, w - 1))
                        y1 = max(0, min(y1, h - 1))
                        x2 = max(0, min(x2, w))
                        y2 = max(0, min(y2, h))
                    if x2 <= x1 or y2 <= y1:
                        continue

                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    cls_name = result.names[cls] if hasattr(result, "names") and cls in result.names else str(cls)

                    processed_results.append({
                        "class": str(cls_name),
                        "confidence": round(conf, 4),
                        "bbox": [x1, y1, x2, y2],
                        "box": [x1, y1, x2, y2],
                    })
                except Exception as e:
                    print(f"Error parsing box {i}: {e}")
                    continue

        return processed_results
