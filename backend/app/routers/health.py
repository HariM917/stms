"""
Health check router — liveness, readiness, and comprehensive status monitoring.
"""
from datetime import datetime, timezone
import psutil
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.services import detector_service
from app.utils.logging import get_logger

logger = get_logger("health")
router = APIRouter(tags=["health"])


@router.get("/health/live")
async def liveness_probe():
    """
    Kubernetes/container liveness probe.
    Returns 200 if the process is alive and responsive.
    """
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/ready")
async def readiness_probe():
    """
    Kubernetes/container readiness probe.
    Returns 200 only if database is connected and ready to serve traffic.
    Returns 503 if not ready.
    """
    # 1. Database connectivity check
    try:
        from app.database import _get_engine
        engine = _get_engine()
        if not engine:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"ready": False, "reason": "Database engine not initialized"},
            )
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning("Readiness probe DB check failed: %s", e)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "reason": "Database connection unavailable"},
        )

    # 2. Detector readiness check in production
    settings = get_settings()
    detector_status = detector_service.get_detector_status()
    if settings.is_production:
        # At least primary detectors should be operational
        if not detector_status.get("object", False):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"ready": False, "reason": "Primary detection models not ready"},
            )

    return {"ready": True, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health")
async def health_check():
    """
    System health check — reports overall status, uptime, version,
    masked database connectivity, and resource usage.
    Returns 503 if system is unhealthy (DB unavailable).
    """
    settings = get_settings()

    # Database check
    db_connected = False
    try:
        from app.database import _get_engine
        engine = _get_engine()
        if engine:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception as e:
        logger.error("Health check database probe error: %s", e)
        db_connected = False

    db_status = "connected" if db_connected else "disconnected"

    # Uptime
    try:
        from app.main import get_uptime
        uptime = round(get_uptime(), 1)
    except Exception:
        uptime = 0.0

    # Memory usage
    try:
        process = psutil.Process()
        memory_mb = round(process.memory_info().rss / 1024 / 1024, 1)
    except Exception:
        memory_mb = None

    detector_status = detector_service.get_detector_status()
    all_detectors_ok = all(detector_status.values()) if detector_status else False

    if not db_connected:
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif not all_detectors_ok:
        overall_status = "degraded"
        http_status = status.HTTP_200_OK
    else:
        overall_status = "ok"
        http_status = status.HTTP_200_OK

    body = {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": uptime,
        "memory_mb": memory_mb,
        "services": {
            "database": db_status,
            "detectors": detector_status,
            "optimization": detector_service.get_optimizer() is not None,
            "insights": detector_service.get_insights_llm() is not None,
        },
    }

    if http_status != status.HTTP_200_OK:
        return JSONResponse(status_code=http_status, content=body)
    return body
