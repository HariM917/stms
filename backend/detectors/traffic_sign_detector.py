"""
Indian Traffic Sign Detector Module for Smart Traffic Management System.
Detects speed limits, pedestrian crossings, speed humps, stop signs, and traffic control signs.
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


INDIAN_TRAFFIC_SIGNS = {
    0: "hump",
    1: "pedestrian_crossing",
    2: "stop",
    3: "speed_limit_20",
    4: "speed_limit_30",
    5: "speed_limit_40",
    6: "speed_limit_50",
    7: "no_entry",
    8: "no_parking",
}


class TrafficSignDetector(BaseDetector):
    """Detects Indian traffic signs and control signals."""

    def __init__(self, model_path: str | None = None, confidence_threshold: float = 0.25):
        if model_path is None:
            root_dir = Path(__file__).resolve().parent.parent
            candidate_paths = [
                root_dir / "models" / "indian_traffic_sign_model.pt",
                root_dir / "ai_models" / "indian_traffic_sign_model.pt",
                root_dir / "ai_models" / "indian_traffic_sign_model.pth",
                root_dir / "yolov8n.pt",
                Path("yolov8n.pt"),
            ]
            for p in candidate_paths:
                if p.exists() and p.stat().st_size > 10_000:
                    model_path = str(p)
                    break
            if model_path is None:
                model_path = str(root_dir / "yolov8n.pt")

        super().__init__(model_path=model_path, confidence_threshold=confidence_threshold)
        self.classes = INDIAN_TRAFFIC_SIGNS
        self._lock = threading.Lock()
        self.load_model()

    def load_model(self):
        if not YOLO_AVAILABLE or YOLO is None:
            print("ultralytics not installed — TrafficSignDetector model cannot be loaded")
            self.model = None
            return

        try:
            p = Path(self.model_path)
            if p.exists() and p.stat().st_size > 10_000:
                self.model = YOLO(str(p))
                print(f"Traffic sign model loaded from {self.model_path}")
            else:
                fallback = Path(__file__).resolve().parent.parent / "yolov8n.pt"
                if fallback.exists():
                    self.model = YOLO(str(fallback))
                    print(f"Loaded general YOLO model as traffic sign fallback from {fallback}")
                else:
                    self.model = None
        except Exception as e:
            print(f"Error loading traffic sign model: {e}")
            self.model = None

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        return frame

    def detect(self, frame: np.ndarray):
        if self.model is None or not callable(self.model):
            return None

        try:
            with self._lock:
                results = self.model(frame, conf=self.confidence_threshold)
            if isinstance(results, list) and len(results) > 0:
                return results[0]
            return results
        except Exception as e:
            print(f"Error during traffic sign detection: {e}")
            return None

    def postprocess(self, results, frame: np.ndarray | None = None) -> list[dict]:
        detections = []
        if results is None:
            return detections

        boxes_obj = getattr(results, "boxes", None)
        if boxes_obj is None or len(boxes_obj) == 0:
            return detections

        try:
            boxes = boxes_obj.cpu().numpy()
            h, w = (frame.shape[:2]) if (frame is not None and hasattr(frame, "shape")) else (None, None)

            for i, box in enumerate(boxes):
                try:
                    xyxy = box.xyxy[0].astype(int)
                    x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                    if w is not None and h is not None:
                        x1 = max(0, min(x1, w - 1))
                        y1 = max(0, min(y1, h - 1))
                        x2 = max(0, min(x2, w))
                        y2 = max(0, min(y2, h))
                    if x2 <= x1 or y2 <= y1:
                        continue

                    conf = float(box.conf[0])
                    class_id = int(box.cls[0])

                    if hasattr(results, "names") and class_id in results.names:
                        class_name = results.names[class_id]
                    elif class_id in self.classes:
                        class_name = self.classes[class_id]
                    else:
                        class_name = f"sign_{class_id}"

                    sign_keywords = ("sign", "stop", "light", "cross", "speed", "entry", "parking", "hump")
                    if any(k in str(class_name).lower() for k in sign_keywords) or class_id in self.classes:
                        detections.append({
                            "class": str(class_name),
                            "confidence": round(conf, 4),
                            "bbox": [x1, y1, x2, y2],
                            "box": [x1, y1, x2, y2],
                        })
                except Exception as e:
                    print(f"Error parsing sign box {i}: {e}")
                    continue
        except Exception as e:
            print(f"Error postprocessing traffic sign results: {e}")

        return detections
