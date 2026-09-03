"""
Detector modules for Smart Traffic Management System.
"""
from .base_detector import BaseDetector
from .object_detector import ObjectDetector
from .pothole_detector import PotholeDetector
from .traffic_sign_detector import TrafficSignDetector
from .railway_crossing_detector import RailwayCrossingDetector
from .weather_detector import WeatherDetector

__all__ = [
    "BaseDetector",
    "ObjectDetector",
    "PotholeDetector",
    "TrafficSignDetector",
    "RailwayCrossingDetector",
    "WeatherDetector",
]
