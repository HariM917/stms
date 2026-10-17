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
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def readiness_probe():
    """
    Kubernetes/container readiness probe.

    Returns 200 only if the database is connected and ready to serve traffic.
    Returns 503 if not ready.
    """

    # 1. Database connectivity check
    try:
        from app.database import _get_engine

        engine = _get_engine()

        if not engine:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "ready": False,
                    "reason": "Database engine not initialized",
                },
            )

        from sqlalchemy import text

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    except Exception as e:
        logger.warning("Readiness probe DB check failed: %s", e)

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ready": False,
                "reason": "Database connection unavailable",
            },
        )

    # 2. Redis check if configured
    settings = get_settings()

    if settings.redis_url and settings.is_production:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(
                settings.redis_url,
                socket_connect_timeout=2.0,
            )

            await r.ping()
            await r.aclose()

        except Exception as e:
            logger.warning(
                "Readiness probe Redis check failed: %s",
                e,
            )

            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "ready": False,
                    "reason": "Redis connection unavailable",
                },
            )

    # 3. Detector readiness check in production
    detector_status = detector_service.get_detector_status()

    if settings.is_production and not detector_status.get("object", False):
        # In production, the primary object detector must be operational.
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ready": False,
                "reason": "Primary detection models not ready",
            },
        )

    return {
        "ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health")
async def health_check():
    """
    System health check.

    Reports:
    - Overall system status
    - Application version
    - Environment
    - Uptime
    - Memory usage
    - Database connectivity
    - Redis connectivity
    - Detector status
    - Optimization service status
    - Insights service status

    Health behavior:
    - Production requires real detectors.
    - Test/development environments may use explicitly enabled mock
      detectors without being marked as degraded.
    - Database failure always makes the system unhealthy.
    - Production Redis failure makes the system unhealthy when Redis
      is configured.
    """

    settings = get_settings()

    # ------------------------------------------------------------------
    # Database check
    # ------------------------------------------------------------------
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
        logger.error(
            "Health check database probe error: %s",
            e,
        )

        db_connected = False

    db_status = "connected" if db_connected else "disconnected"

    # ------------------------------------------------------------------
    # Redis check
    # ------------------------------------------------------------------
    redis_status = "not_configured"

    if settings.redis_url:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(
                settings.redis_url,
                socket_connect_timeout=2.0,
            )

            await r.ping()
            await r.aclose()

            redis_status = "connected"

        except Exception:
            redis_status = "disconnected"

    # ------------------------------------------------------------------
    # Uptime
    # ------------------------------------------------------------------
    try:
        from app.main import get_uptime

        uptime = round(get_uptime(), 1)

    except Exception:
        uptime = 0.0

    # ------------------------------------------------------------------
    # Memory usage
    # ------------------------------------------------------------------
    try:
        process = psutil.Process()
        memory_mb = round(
            process.memory_info().rss / 1024 / 1024,
            1,
        )

    except Exception:
        memory_mb = None

    # ------------------------------------------------------------------
    # Detector status
    # ------------------------------------------------------------------
    detector_status = detector_service.get_detector_status()

    all_detectors_ok = (
        all(detector_status.values())
        if detector_status
        else False
    )

    # ------------------------------------------------------------------
    # Mock detector mode
    #
    # In test/development, mock models are intentionally allowed.
    # They should not make the entire health check degraded.
    #
    # Production NEVER treats mock models as acceptable.
    # ------------------------------------------------------------------
    mock_mode = (
        not settings.is_production
        and settings.allow_mock_models
    )

    # ------------------------------------------------------------------
    # Determine overall system health
    # ------------------------------------------------------------------
    if not db_connected:
        # Database failure is always unhealthy.
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    elif (
        settings.is_production
        and settings.redis_url
        and redis_status != "connected"
    ):
        # Redis is required when configured in production.
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    elif not all_detectors_ok and not mock_mode:
        # Real detectors are required outside explicitly enabled
        # mock mode.
        #
        # This means:
        # - Production + missing real detectors -> degraded
        # - Development + mock mode disabled + missing detectors -> degraded
        overall_status = "degraded"
        http_status = status.HTTP_200_OK

    else:
        # Everything required for the current environment is operational.
        #
        # In test/development with mock mode enabled, mock detectors are
        # considered operational for health purposes.
        overall_status = "ok"
        http_status = status.HTTP_200_OK

    # ------------------------------------------------------------------
    # Response body
    # ------------------------------------------------------------------
    body = {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": uptime,
        "memory_mb": memory_mb,
        "services": {
            "database": db_status,
            "redis": redis_status,
            "detectors": detector_status,
            "optimization": detector_service.get_optimizer() is not None,
            "insights": detector_service.get_insights_llm() is not None,
        },
    }

    # ------------------------------------------------------------------
    # Return appropriate HTTP status
    # ------------------------------------------------------------------
    if http_status != status.HTTP_200_OK:
        return JSONResponse(
            status_code=http_status,
            content=body,
        )

    return body
