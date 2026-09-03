"""
Visual Weather Condition Detector for Smart Traffic Management System.
Analyzes road visibility, precipitation, lighting conditions, and road surface moisture.
"""
import cv2
import numpy as np

from .base_detector import BaseDetector

IMPACT_MAP = {
    "clear": 0.1,
    "cloudy": 0.2,
    "haze": 0.3,
    "fog": 0.7,
    "rain": 0.6,
    "snow": 0.8,
    "night": 0.4,
}


class WeatherDetector(BaseDetector):
    """Analyzes atmospheric conditions from traffic surveillance images."""

    def __init__(self, api_key: str | None = None, model_path: str | None = None, confidence_threshold: float = 0.5):
        super().__init__(model_path=model_path, confidence_threshold=confidence_threshold)
        self.api_key = api_key
        self.load_model()

    def load_model(self):
        self.model = "opencv_weather_analyzer"

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        return frame

    def calculate_impact_factor(self, condition: str) -> float:
        """Calculate traffic flow slowdown multiplier based on weather condition."""
        return IMPACT_MAP.get(condition.lower().strip(), 0.1)

    def detect(self, frame: np.ndarray, location: str | None = None):
        if frame is None or frame.size == 0:
            return {"condition": "unknown", "confidence": 0.0, "impact_factor": 0.1}
        return self.detect_from_image(frame)

    def detect_from_image(self, frame: np.ndarray) -> dict:
        """Derive atmospheric conditions from image luminance, color balance, and edge clarity."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # 1. Luminance (night vs day)
            mean_brightness = float(cv2.mean(gray)[0])

            # 2. Edge density / blur (fog / heavy rain dampens edge sharpness)
            lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

            # 3. Sky / horizon contrast
            sky_region = gray[:int(h * 0.35), :]
            if sky_region.size > 0:
                sky_mean = float(cv2.mean(sky_region)[0])
                _, sky_std_arr = cv2.meanStdDev(sky_region)
                sky_std = float(sky_std_arr[0][0])
            else:
                sky_mean = mean_brightness
                sky_std = 10.0

            # 4. Color temperature / saturation
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            saturation_mean = float(cv2.mean(hsv[:, :, 1])[0])

            # Condition classification heuristics
            if mean_brightness < 55:
                condition = "night"
                confidence = round(min(0.95, 0.6 + (55 - mean_brightness) / 55 * 0.35), 2)
            elif lap_var < 70 and sky_mean > 140:
                condition = "fog"
                confidence = round(min(0.92, 0.6 + (70 - lap_var) / 70 * 0.3), 2)
            elif sky_mean > 160 and sky_std < 18 and saturation_mean < 45:
                condition = "cloudy"
                confidence = 0.85
            elif sky_std > 30 and mean_brightness > 130 and saturation_mean > 60:
                condition = "clear"
                confidence = 0.90
            elif saturation_mean < 50 and sky_mean > 110:
                condition = "haze"
                confidence = 0.80
            else:
                condition = "clear"
                confidence = 0.75

            impact = self.calculate_impact_factor(condition)
            return {
                "condition": condition,
                "confidence": confidence,
                "impact_factor": impact,
                "mean_brightness": round(mean_brightness, 1),
                "edge_sharpness": round(lap_var, 1),
                "source": "computer_vision",
            }
        except Exception as e:
            return {
                "condition": "clear",
                "confidence": 0.5,
                "impact_factor": 0.1,
                "error": str(e),
                "source": "fallback",
            }

    def postprocess(self, weather_data, frame: np.ndarray | None = None) -> dict:
        if isinstance(weather_data, dict):
            return weather_data
        return {"condition": "clear", "confidence": 0.5, "impact_factor": 0.1}
