"""
Smart Traffic Management System — FastAPI Application
Entry point for the production-ready API server.
"""
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.middleware.error_handlers import register_error_handlers
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.routers import auth, detection, health, insights, optimization, reports
from app.services import detector_service
from app.utils.logging import get_logger, setup_logging

# Ensure project root is on the path for detector imports
ROOT_DIR = Path(__file__).resolve().parent.parent
for p in [str(ROOT_DIR), str(ROOT_DIR.parent)]:
    if p not in sys.path:
        sys.path.insert(0, p)


_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    - Startup: initialize logging, database, load detectors/models
    - Shutdown: close database connections, cleanup
    """
    global _start_time
    _start_time = time.time()

    # ---- Startup ----
    setup_logging()
    logger = get_logger("main")
    settings = get_settings()

    logger.info("=" * 60)
    logger.info("  %s v%s", settings.app_name, settings.app_version)
    logger.info("  Environment: %s", settings.environment)
    logger.info("  Database: %s", "PostgreSQL" if settings.db_driver != "sqlite" else "SQLite (dev)")
    logger.info("=" * 60)

    # Initialize database (create tables if they don't exist)
    await init_db()
    logger.info("Database initialized")

    # Seed bootstrap admin if configured
    await _bootstrap_admin_if_configured(logger)

    # Initialize detectors (heavy — loads ML models)
    detector_service.initialize_all()

    logger.info("API server ready on http://%s:%d", settings.api_host, settings.api_port)

    yield  # Application is running

    # ---- Shutdown ----
    logger.info("Shutting down %s", settings.app_name)
    await close_db()
    logger.info("Database connections closed")


async def _bootstrap_admin_if_configured(logger):
    """
    Create a bootstrap admin user ONLY if explicitly configured via environment variables.
    Never seeds hardcoded demo admin credentials in production.
    """
    settings = get_settings()
    admin_email = settings.bootstrap_admin_email
    admin_password = settings.bootstrap_admin_password

    if not admin_email or not admin_password:
        if settings.is_production:
            logger.info("No bootstrap administrator configured. Standard production startup.")
        return

    from app.database import get_db_context
    from app.repositories import user_repository
    from app.services.auth_service import hash_password

    if settings.is_production and (len(admin_password) < 12 or admin_password in ("demo123", "password", "admin123", "secret")):
        raise ValueError("CRITICAL SECURITY ERROR: BOOTSTRAP_ADMIN_PASSWORD must be at least 12 characters and secure in production.")

    async with get_db_context() as db:
        existing = await user_repository.get_user_by_email(db, admin_email)
        if existing is None:
            await user_repository.create_user(
                db,
                name="System Administrator",
                email=admin_email,
                password_hash=hash_password(admin_password),
                role="admin",
            )
            logger.info("Initialized bootstrap administrator: %s", admin_email)


def get_uptime() -> float:
    """Return server uptime in seconds."""
    return time.time() - _start_time


def create_app() -> FastAPI:
    """
    FastAPI application factory.
    Creates and configures the app with routers, middleware, and error handlers.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI-powered traffic management API for Indian road conditions",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ---- Error Handlers (must be registered before middleware) ----
    register_error_handlers(app)

    # ---- Middleware (order matters: first added = outermost) ----

    # Request ID (outermost — runs first, so all downstream has the ID)
    app.add_middleware(RequestIDMiddleware)

    # Rate limiter
    app.add_middleware(RateLimiterMiddleware)

    # CORS
    allowed_origins = settings.cors_origin_list
    if not settings.is_production:
        allowed_origins.extend([
            "http://localhost:3000",
            "http://localhost:8001",
            "http://localhost:5173",  # Vite default
        ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ---- Security Headers Middleware ----
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:*; "
            "frame-ancestors 'none';"
        )
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # ---- Routers (all versioned under /api/v1/) ----
    api_prefix = "/api/v1"

    app.include_router(health.router, prefix="/api")  # Health stays unversioned
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(detection.router, prefix=api_prefix)
    app.include_router(optimization.router, prefix=api_prefix)
    app.include_router(insights.router, prefix=api_prefix)
    app.include_router(reports.router, prefix=api_prefix)

    # ---- Backward-compatible unversioned routes ----
    # Keep old /api/auth/* and /api/detect/* routes working for existing clients
    app.include_router(auth.router, prefix="/api", include_in_schema=False)
    app.include_router(detection.router, prefix="/api", include_in_schema=False)
    app.include_router(optimization.router, prefix="/api", include_in_schema=False)
    app.include_router(insights.router, prefix="/api", include_in_schema=False)

    # ---- Root redirect ----
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/api/docs",
            "health": "/api/health",
            "api_prefix": "/api/v1",
            "portal": "/portal/govt-dashboard.html",
        }

    # ---- Serve Frontend Static Files ----
    # Mount the frontend directory so the portal is accessible at /portal/
    frontend_dir = ROOT_DIR.parent / "frontend" / "bootstrap"
    if frontend_dir.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/portal", StaticFiles(directory=str(frontend_dir), html=True), name="portal")

    return app


# Create the app instance (used by uvicorn: "app.main:app")
app = create_app()


# ---- CLI entry point ----
if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Run the STMS API server")
    parser.add_argument("--port", type=int, default=None, help="Port (default: from .env or 8001)")
    parser.add_argument("--host", type=str, default=None, help="Host (default: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    settings = get_settings()
    port = args.port or settings.api_port
    host = args.host or settings.api_host

    print(f"\n{'=' * 60}")
    print(f"  {settings.app_name} v{settings.app_version}")
    print(f"  API:  http://{host}:{port}")
    print(f"  Docs: http://localhost:{port}/api/docs")
    print(f"{'=' * 60}\n")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=args.reload,
    )
