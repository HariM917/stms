"""
Pothole and Road Damage Detector for Smart Traffic Management System.
Combines object detection with image contrast enhancement and surface texture analysis.
"""
import cv2
import numpy as np

from .base_detector import BaseDetector
from .object_detector import ObjectDetector


class PotholeDetector(BaseDetector):
    """Detects potholes, cracks, and road surface damage."""

    def __init__(self, model_path: str | None = None, confidence_threshold: float = 0.5):
        super().__init__(model_path=model_path, confidence_threshold=confidence_threshold)
        self.object_detector = ObjectDetector(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
        )
        self.model = self.object_detector.model

    def load_model(self):
        self.object_detector.load_model()
        self.model = self.object_detector.model

    def enhance_contrast(self, frame: np.ndarray) -> np.ndarray:
        """Apply CLAHE contrast enhancement for surface texture separation."""
        if frame is None or frame.size == 0:
            return frame
        try:
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            enhanced_lab = cv2.merge((cl, a, b))
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        except Exception:
            return frame

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        return self.enhance_contrast(frame)

    def detect(self, frame: np.ndarray):
        preprocessed = self.preprocess(frame)
        return self.object_detector.detect(preprocessed)

    def detect_damage_in_region(self, region: np.ndarray) -> bool:
        """Determine if a cropped road patch has high texture variance typical of damage."""
        if region is None or region.size == 0:
            return False
        try:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            mean, std = cv2.meanStdDev(blur)
            return bool(std[0][0] > 30)
        except Exception:
            return False

    def postprocess(self, detections, frame: np.ndarray | None = None) -> list[dict]:
        all_detections = self.object_detector.postprocess(detections, frame)
        if all_detections is None:
            all_detections = []

        pothole_related = ("pothole", "hole", "damage", "crack")
        potholes = []

        for detection in all_detections:
            cls_name = detection.get("class", "").lower()
            if any(rel in cls_name for rel in pothole_related):
                detection["class"] = "pothole"
                detection["severity"] = "High" if detection.get("confidence", 0) > 0.7 else "Medium"
                potholes.append(detection)
            elif cls_name == "road" and frame is not None:
                box = detection.get("box") or detection.get("bbox")
                if isinstance(box, (list, tuple)) and len(box) == 4:
                    x1, y1, x2, y2 = box
                    road_region = frame[y1:y2, x1:x2]
                    if self.detect_damage_in_region(road_region):
                        detection["class"] = "road_damage"
                        detection["severity"] = "Medium"
                        potholes.append(detection)

        # Direct morphological edge detection fallback if frame provided and zero YOLO detections
        if not potholes and frame is not None and frame.size > 0:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (7, 7), 0)
                thresh = cv2.adaptiveThreshold(
                    blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 19, 5
                )
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                h, w = frame.shape[:2]
                road_y_start = int(h * 0.4)  # focus on lower 60% of frame (road)

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if 1200 < area < (w * h * 0.15):
                        x, y, cw, ch = cv2.boundingRect(cnt)
                        if y > road_y_start and 0.3 < (cw / max(ch, 1)) < 3.5:
                            patch = frame[y:y+ch, x:x+cw]
                            if self.detect_damage_in_region(patch):
                                potholes.append({
                                    "class": "pothole",
                                    "confidence": round(min(0.85, 0.5 + (area / (w * h * 0.15)) * 0.35), 2),
                                    "severity": "Medium" if area < 5000 else "High",
                                    "bbox": [x, y, x + cw, y + ch],
                                    "box": [x, y, x + cw, y + ch],
                                })
                                if len(potholes) >= 10:
                                    break
            except Exception:
                pass

        return potholes
