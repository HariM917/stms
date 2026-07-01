"""
FastAPI application dependencies.
Shared dependencies injected into route handlers.
"""
from app.config import Settings, get_settings


def get_app_settings() -> Settings:
    """FastAPI dependency for accessing application settings."""
    return get_settings()
