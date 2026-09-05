"""
Base Detector Module for Smart Traffic Management System.
"""
from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BaseDetector(ABC):
    """Abstract base class for all STMS detectors."""

    def __init__(self, model_path: str | None = None, confidence_threshold: float = 0.5):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None

    @abstractmethod
    def load_model(self):
        """Load model weights into memory."""
        pass

    @abstractmethod
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess raw input frame before inference."""
        pass

    @abstractmethod
    def detect(self, frame: np.ndarray) -> Any:
        """Run inference on the preprocessed frame."""
        pass

    @abstractmethod
    def postprocess(self, detections: Any, frame: np.ndarray | None = None) -> Any:
        """Convert raw detections to structured detection output."""
        pass
