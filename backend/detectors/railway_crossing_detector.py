"""
Railway Crossing Detector for Smart Traffic Management System.
Detects level crossings, approaching trains, barrier states, and track hazards.
"""
import cv2
import numpy as np

from .base_detector import BaseDetector
from .object_detector import ObjectDetector


class RailwayCrossingDetector(BaseDetector):
    """Detects railway level crossings, track occupancy, and crossing status."""

    def __init__(self, model_path: str | None = None, confidence_threshold: float = 0.4):
        super().__init__(model_path=model_path, confidence_threshold=confidence_threshold)
        self.object_detector = ObjectDetector(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
        )
        self.model = self.object_detector.model

    def load_model(self):
        self.object_detector.load_model()
        self.model = self.object_detector.model

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        return frame

    def detect(self, frame: np.ndarray):
        detections = self.object_detector.detect(frame)
        return detections

    def _rectangles_overlap(self, rect1: list, rect2: list) -> bool:
        """Check if two rectangles [x, y, w, h] overlap."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        return not (x1 + w1 < x2 or x2 + w2 < x1 or y1 + h1 < y2 or y2 + h2 < y1)

    def _check_intersection(self, railway_objects: list, road_objects: list) -> bool:
        if not railway_objects or not road_objects:
            return False

        for rail_obj in railway_objects:
            box = rail_obj.get("box", rail_obj.get("bbox"))
            if not box or len(box) < 4:
                continue
            rail_rect = [box[0], box[1], box[2] - box[0], box[3] - box[1]]

            for road_obj in road_objects:
                rbox = road_obj.get("box", road_obj.get("bbox"))
                if not rbox or len(rbox) < 4:
                    continue
                road_rect = [rbox[0], rbox[1], rbox[2] - rbox[0], rbox[3] - rbox[1]]

                if self._rectangles_overlap(rail_rect, road_rect):
                    return True

        return False

    def _detect_crossing_pattern(self, frame: np.ndarray) -> bool:
        """Hough line transform to spot track rails / barrier crossbars."""
        if frame is None or frame.size == 0:
            return False
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
            if lines is not None and len(lines) >= 4:
                return True
        except Exception:
            pass
        return False

    def postprocess(self, detections, frame: np.ndarray | None = None) -> dict:
        all_detections = self.object_detector.postprocess(detections, frame)

        railway_classes = ("train", "rail", "locomotive")
        road_classes = ("car", "truck", "bus", "motorcycle", "person")

        railway_objects = []
        road_objects = []

        for det in all_detections:
            cls_name = det.get("class", "").lower()
            if any(rc in cls_name for rc in railway_classes):
                railway_objects.append(det)
            elif any(rc in cls_name for rc in road_classes):
                road_objects.append(det)

        has_tracks = self._detect_crossing_pattern(frame) if frame is not None else False
        train_present = len(railway_objects) > 0
        status_value = "closed" if train_present else "open"

        # If train or crossing detected, build structured crossing results
        crossing_results = []
        for obj in railway_objects:
            crossing_results.append({
                "class": "train",
                "confidence": obj.get("confidence", 0.8),
                "bbox": obj.get("bbox", [0, 0, 0, 0]),
                "status": "closed",
            })

        if not crossing_results and has_tracks:
            h, w = frame.shape[:2] if frame is not None else (480, 640)
            crossing_results.append({
                "class": "railway_crossing",
                "confidence": 0.75,
                "bbox": [int(w * 0.1), int(h * 0.3), int(w * 0.9), int(h * 0.7)],
                "status": status_value,
            })

        return {
            "railway_objects": crossing_results,
            "train_present": train_present,
            "status": status_value,
            "road_objects_count": len(road_objects),
            "hazard_detected": self._check_intersection(railway_objects, road_objects),
        }
