"""
Utility functions for converting NumPy types to native Python types.
Centralizes the conversion logic that was duplicated 5+ times in the monolith.
"""
import numpy as np
from typing import Any


def deep_convert_numpy(obj: Any) -> Any:
    """
    Recursively convert any NumPy types in a nested structure to native Python types.

    Handles: np.ndarray, np.integer, np.floating, np.bool_, and nested dicts/lists.
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: deep_convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [deep_convert_numpy(item) for item in obj]
    else:
        return obj


def clean_detection(detection: dict) -> dict:
    """
    Clean a single detection dict: ensure bbox, class, and confidence
    are present and use native Python types.
    """
    cleaned = deep_convert_numpy(detection)

    # Normalize bbox key
    if "bbox" not in cleaned and "box" in cleaned:
        cleaned["bbox"] = cleaned.pop("box")
    if "bbox" not in cleaned:
        cleaned["bbox"] = [0, 0, 50, 50]

    # Ensure bbox values are proper ints/floats
    if isinstance(cleaned.get("bbox"), (list, tuple)):
        cleaned["bbox"] = [
            int(x) if isinstance(x, (int, float)) else x
            for x in cleaned["bbox"]
        ]

    # Ensure required fields
    if "class" not in cleaned:
        cleaned["class"] = "unknown"
    elif not isinstance(cleaned["class"], str):
        cleaned["class"] = str(cleaned["class"])

    if "confidence" not in cleaned:
        cleaned["confidence"] = 0.5
    else:
        cleaned["confidence"] = float(cleaned["confidence"])

    return cleaned


def clean_detections(detections: list[dict]) -> list[dict]:
    """Clean a list of detection dicts."""
    return [clean_detection(d) for d in detections]
