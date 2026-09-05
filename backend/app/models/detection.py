"""
Pydantic models for detection and analysis endpoints.
"""
from typing import Any

from pydantic import BaseModel


class DetectionResult(BaseModel):
    """A single detection with bounding box, class, and confidence."""
    bbox: list[float] = []
    confidence: float = 0.0
    class_name: str | None = None  # 'class' is reserved in Python


class DetectionResponse(BaseModel):
    """Response for object/sign/pothole/railway detection endpoints."""
    success: bool
    message: str
    detections: list[dict[str, Any]] = []
    count: int = 0
    visualization: str | None = None  # base64-encoded image
    vehicle_count: int | None = None
    pedestrian_count: int | None = None


class WeatherResponse(BaseModel):
    """Response for weather detection endpoint."""
    success: bool
    message: str
    condition: str = "unknown"
    confidence: float = 0.0
    impact_factor: float = 0.0


class OptimizationRequest(BaseModel):
    """Request body for signal optimization."""
    junction_id: str | None = None
    traffic_data: dict[str, Any] | None = None


class OptimizationResponse(BaseModel):
    """Response for signal optimization endpoint."""
    success: bool
    message: str
    signal_timings: dict[str, Any] | None = None
    congestion_level: float | None = None


class InsightsRequest(BaseModel):
    """Request body for AI insights generation."""
    prompt: str = ""


class InsightsResponse(BaseModel):
    """Response for AI insights endpoint."""
    success: bool
    message: str
    insights: list[str] = []
