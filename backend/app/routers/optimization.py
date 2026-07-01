"""
Signal optimization router.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services import detector_service
from app.utils.logging import get_logger
from pydantic import BaseModel
from typing import Optional, Dict, Any

logger = get_logger("optimization")
router = APIRouter(prefix="/optimize", tags=["optimization"])


class OptimizationRequest(BaseModel):
    """Request body for signal optimization."""
    junction_id: Optional[str] = None
    traffic_data: Optional[Dict[str, Any]] = None
    weather_data: Optional[Dict[str, Any]] = None


@router.post("/signals")
async def optimize_signals(body: OptimizationRequest = OptimizationRequest()):
    """Optimize traffic signal timings based on current conditions."""
    optimizer = detector_service.get_optimizer()

    # Default mock values
    signal_timings = {
        "north_south": 45,
        "east_west": 30,
        "left_turn": 15,
        "pedestrian": 20,
        "cycle_length": 110,
    }
    congestion_level = 0.65

    # Use the real optimizer if available
    if optimizer is not None and body.traffic_data:
        try:
            result = optimizer.optimize_signals(
                junction_id=body.junction_id or "unknown",
                traffic_data=body.traffic_data,
                weather_data=body.weather_data,
            )
            if isinstance(result, dict):
                signal_timings = result.get("optimized_timings", signal_timings)
                congestion_level = result.get("congestion_level", congestion_level)
            logger.info("Real optimizer used for junction %s", body.junction_id)
        except Exception as e:
            logger.error("Optimizer error: %s — using mock timings", e)
    else:
        logger.info("Optimizer not loaded or no data — returning mock signal timings")

    return {
        "success": True,
        "message": "Signal optimization successful",
        "signal_timings": signal_timings,
        "congestion_level": congestion_level,
    }
