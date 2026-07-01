"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type safety.
"""
import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central configuration for the STMS backend."""

    # --- Application ---
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    app_name: str = "Smart Traffic Management System"
    app_version: str = "2.0.0"

    # --- Server ---
    api_port: int = Field(default=8001, alias="API_PORT")
    api_host: str = "0.0.0.0"

    # --- CORS ---
    cors_origins: str = Field(
        default="http://localhost:5000,http://127.0.0.1:5000",
        alias="CORS_ORIGIN",
    )

    # --- Database ---
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_database: str = Field(default="stms_db", alias="DB_DATABASE")

    # Database driver: "postgresql" (production) or "sqlite" (local dev)
    db_driver: str = Field(default="sqlite", alias="DB_DRIVER")

    # Connection pool settings (PostgreSQL only)
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # --- Authentication ---
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 8

    # --- Rate Limiting ---
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=900, alias="RATE_LIMIT_WINDOW")  # 15 min

    # --- Paths ---
    root_dir: Path = Path(__file__).resolve().parent.parent

    # --- Detection ---
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    max_detections: int = 100

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def models_dir(self) -> Path:
        """Path to AI model weights directory."""
        return self.root_dir / "ai_models"

    @property
    def snapshots_dir(self) -> Path:
        """Path to detection snapshots directory."""
        return self.root_dir / "snapshots"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def database_url(self) -> str:
        """Synchronous database URL (for Alembic)."""
        if self.db_driver == "sqlite":
            return f"sqlite:///{self.root_dir / 'stms.db'}"
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
        )

    @property
    def database_url_async(self) -> str:
        """Async database URL (for SQLAlchemy async engine)."""
        if self.db_driver == "sqlite":
            return f"sqlite+aiosqlite:///{self.root_dir / 'stms.db'}"
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton. Call this to get the app configuration."""
    return Settings()
