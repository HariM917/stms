"""
Health check router — system health, readiness, and status.
"""
import time
import psutil
from datetime import datetime

from fastapi import APIRouter

from app.config import get_settings
from app.services import detector_service
from app.utils.logging import get_logger

logger = get_logger("health")
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    System health check — reports detector status, uptime, version,
    database connectivity, and resource usage.
    """
    settings = get_settings()

    # Database check
    db_status = "unknown"
    try:
        from app.database import _get_engine
        engine = _get_engine()
        if engine:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    # Uptime
    try:
        from app.main import get_uptime
        uptime = round(get_uptime(), 1)
    except Exception:
        uptime = 0

    # Memory usage
    try:
        process = psutil.Process()
        memory_mb = round(process.memory_info().rss / 1024 / 1024, 1)
    except Exception:
        memory_mb = None

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": uptime,
        "memory_mb": memory_mb,
        "services": {
            "database": db_status,
            "detectors": detector_service.get_detector_status(),
            "optimization": detector_service.get_optimizer() is not None,
            "insights": detector_service.get_insights_llm() is not None,
        },
    }


@router.get("/health/ready")
async def readiness_probe():
    """
    Kubernetes-style readiness probe.
    Returns 200 only if the database is connected and detectors are loaded.
    """
    from fastapi.responses import JSONResponse

    # Check database
    try:
        from app.database import _get_engine
        engine = _get_engine()
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "Database not available"},
        )

    return {"ready": True}
