"""
Signal optimization router.
Provides dynamic, constraint-checked traffic signal timings for operators and administrators.
"""
import math

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.middleware.auth_middleware import require_role
from app.models.db.user import User
from app.services import detector_service
from app.utils.logging import get_logger

logger = get_logger("optimization")
router = APIRouter(prefix="/optimize", tags=["optimization"])


class TrafficDataInput(BaseModel):
    vehicle_count: int = Field(default=0, ge=0, le=10000, description="Total detected vehicles")
    pedestrian_count: int | None = Field(default=0, ge=0, le=5000, description="Total detected pedestrians")


class WeatherDataInput(BaseModel):
    condition: str | None = Field(default="clear", max_length=50)
    confidence: float | None = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float | None) -> float | None:
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError("confidence cannot be NaN or Infinity")
        return v


class OptimizationRequest(BaseModel):
    """Request body for signal optimization with strict schema constraints."""
    junction_id: str = Field(..., min_length=1, max_length=100, description="Unique junction identifier")
    traffic_data: TrafficDataInput = Field(default_factory=TrafficDataInput)
    weather_data: WeatherDataInput | None = None


@router.post("/signals")
async def optimize_signals(
    body: OptimizationRequest,
    user: User = Depends(require_role("operator", "admin")),
):
    """
    Optimize traffic signal timings based on real-time vehicle and pedestrian loads.
    Restricted to control room operators and administrators.
    """
    optimizer = detector_service.get_optimizer()

    if optimizer is None:
        if not detector_service.is_mock_allowed():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Traffic signal optimizer is currently unavailable.",
            )
        # Development mock
        logger.warning("Returning dev mock signal timings for junction %s", body.junction_id)
        return {
            "success": True,
            "message": "Signal optimization successful (dev mock)",
            "signal_timings": {
                "north_south": {"green": 45, "yellow": 5, "red": 60},
                "east_west": {"green": 35, "yellow": 5, "red": 60},
                "pedestrian": {"crossing_time": 20, "clearance_interval": 5},
                "cycle_length": 110,
            },
            "congestion_level": 0.65,
            "mock": True,
        }

    try:
        traffic_dict = body.traffic_data.model_dump()
        weather_dict = body.weather_data.model_dump() if body.weather_data else None

        result = optimizer.optimize_signals(
            junction_id=body.junction_id,
            traffic_data=traffic_dict,
            weather_data=weather_dict,
        )

        logger.info("Signal timings optimized for junction %s by %s", body.junction_id, user.email)
        return {
            "success": True,
            "message": "Signal optimization successful",
            "junction_id": result.get("junction_id", body.junction_id),
            "signal_timings": result.get("optimized_timings"),
            "congestion_level": result.get("congestion_level"),
            "cycle_length": result.get("cycle_length"),
            "is_optimized": True,
        }
    except Exception as e:
        logger.error("Signal optimization failed for junction %s: %s", body.junction_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute signal optimization.",
        ) from e
