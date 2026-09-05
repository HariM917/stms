"""
Application configuration loaded from environment variables.
Uses pydantic-settings for validation and type safety.
"""
import urllib.parse
from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

KNOWN_INSECURE_SECRETS = {
    "change-me-in-production",
    "secret",
    "secretkey",
    "password",
    "admin",
    "123456",
    "default",
}


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
    db_password: str = Field(default="", alias="DB_PASSWORD", repr=False)
    db_database: str = Field(default="stms_db", alias="DB_DATABASE")

    # Database driver: "postgresql" (production) or "sqlite" (local dev)
    db_driver: str = Field(default="sqlite", alias="DB_DRIVER")

    # Connection pool settings (PostgreSQL only)
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=3600, alias="DB_POOL_RECYCLE")
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # --- Authentication ---
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET", repr=False)
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 8

    # Bootstrap Admin (Optional: only create if explicitly set)
    bootstrap_admin_email: str | None = Field(default=None, alias="BOOTSTRAP_ADMIN_EMAIL")
    bootstrap_admin_password: str | None = Field(default=None, alias="BOOTSTRAP_ADMIN_PASSWORD", repr=False)

    # --- Rate Limiting & Redis ---
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=900, alias="RATE_LIMIT_WINDOW")  # 15 min
    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    # --- Upload Limits ---
    max_upload_size_bytes: int = Field(default=10 * 1024 * 1024, alias="MAX_UPLOAD_SIZE_BYTES")  # 10MB
    max_image_dimension: int = Field(default=4096, alias="MAX_IMAGE_DIMENSION")
    max_image_pixels: int = Field(default=16_000_000, alias="MAX_IMAGE_PIXELS")

    # --- Model Control ---
    allow_mock_models: bool = Field(default=False, alias="ALLOW_MOCK_MODELS")

    # --- Paths ---
    root_dir: Path = Path(__file__).resolve().parent.parent

    # --- Detection Defaults ---
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    max_detections: int = 100

    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @model_validator(mode="after")
    def validate_production_readiness(self) -> "Settings":
        """Strict validation for production mode."""
        env_clean = self.environment.strip().lower()
        is_prod = env_clean in ("production", "prod")

        if is_prod:
            # 1. Reject weak or default JWT secret
            secret = self.jwt_secret.strip()
            if (
                len(secret) < 32
                or secret in KNOWN_INSECURE_SECRETS
                or any(bad in secret.lower() for bad in ("change-me", "secretkey", "admin123", "password123"))
            ):
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: "
                    "In production, JWT_SECRET must be at least 32 characters long and cannot be a default or known weak secret."
                )

            # 2. Reject SQLite in production
            if self.db_driver.strip().lower() == "sqlite":
                raise ValueError(
                    "DATABASE CONFIGURATION ERROR: "
                    "SQLite is not permitted in production. DB_DRIVER must be 'postgresql'."
                )

            # 3. Reject mock models in production
            if self.allow_mock_models:
                raise ValueError(
                    "AI SAFETY ERROR: "
                    "ALLOW_MOCK_MODELS cannot be True in production."
                )

        return self

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
        return self.environment.strip().lower() in ("production", "prod")

    @property
    def database_url(self) -> str:
        """Synchronous database URL (for Alembic)."""
        if self.db_driver.strip().lower() == "sqlite":
            db_name = self.db_database if (self.db_database and self.db_database != "stms") else "stms.db"
            if not db_name.endswith((".db", ".sqlite", ".sqlite3")):
                db_name += ".db"
            db_path = Path(db_name) if Path(db_name).is_absolute() else self.root_dir / db_name
            return f"sqlite:///{db_path.as_posix()}"
        user = urllib.parse.quote_plus(self.db_user)
        pwd = urllib.parse.quote_plus(self.db_password)
        return (
            f"postgresql://{user}:{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
        )

    @property
    def database_url_async(self) -> str:
        """Async database URL (for SQLAlchemy async engine)."""
        if self.db_driver.strip().lower() == "sqlite":
            db_name = self.db_database if (self.db_database and self.db_database != "stms") else "stms.db"
            if not db_name.endswith((".db", ".sqlite", ".sqlite3")):
                db_name += ".db"
            db_path = Path(db_name) if Path(db_name).is_absolute() else self.root_dir / db_name
            return f"sqlite+aiosqlite:///{db_path.as_posix()}"
        user = urllib.parse.quote_plus(self.db_user)
        pwd = urllib.parse.quote_plus(self.db_password)
        return (
            f"postgresql+asyncpg://{user}:{pwd}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton. Call this to get the app configuration."""
    return Settings()

