"""
Pydantic models for detection and analysis endpoints.
"""
from pydantic import BaseModel
from typing import List, Dict, Optional, Any


class DetectionResult(BaseModel):
    """A single detection with bounding box, class, and confidence."""
    bbox: List[float] = []
    confidence: float = 0.0
    class_name: Optional[str] = None  # 'class' is reserved in Python


class DetectionResponse(BaseModel):
    """Response for object/sign/pothole/railway detection endpoints."""
    success: bool
    message: str
    detections: List[Dict[str, Any]] = []
    count: int = 0
    visualization: Optional[str] = None  # base64-encoded image
    vehicle_count: Optional[int] = None
    pedestrian_count: Optional[int] = None


class WeatherResponse(BaseModel):
    """Response for weather detection endpoint."""
    success: bool
    message: str
    condition: str = "unknown"
    confidence: float = 0.0
    impact_factor: float = 0.0


class OptimizationRequest(BaseModel):
    """Request body for signal optimization."""
    junction_id: Optional[str] = None
    traffic_data: Optional[Dict[str, Any]] = None


class OptimizationResponse(BaseModel):
    """Response for signal optimization endpoint."""
    success: bool
    message: str
    signal_timings: Optional[Dict[str, Any]] = None
    congestion_level: Optional[float] = None


class InsightsRequest(BaseModel):
    """Request body for AI insights generation."""
    prompt: str = ""


class InsightsResponse(BaseModel):
    """Response for AI insights endpoint."""
    success: bool
    message: str
    insights: List[str] = []
