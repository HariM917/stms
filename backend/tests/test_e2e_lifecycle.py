"""
End-to-end lifecycle and production configuration test suite.

Verifies:
1. End-to-end user workflow:
   Register -> Login -> HttpOnly Cookie / Session -> Dashboard Access ->
   Object Detection -> Pothole Detection -> Weather Detection ->
   Traffic Reports Submission & Listing -> AI Insights -> Signal Optimization ->
   Logout -> Revocation Check (old token/cookie returns 401).
2. Production startup configuration checks:
   - Rejection of weak/default JWT secrets in production.
   - Rejection of SQLite in production.
   - Rejection of ALLOW_MOCK_MODELS=True in production.
   - Successful initialization with valid PostgreSQL, Redis, and strong JWT secret.
"""
import io

import cv2
import numpy as np
import pytest
from httpx import AsyncClient

from app.config import Settings


def _create_test_image_bytes() -> bytes:
    """Create a minimal 100x100 JPEG image in memory for testing detection endpoints."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), -1)
    success, buffer = cv2.imencode(".jpg", img)
    assert success
    return buffer.tobytes()


@pytest.mark.asyncio
async def test_full_e2e_user_flow(client: AsyncClient, db_engine):
    """
    Execute full lifecycle from registration through logout and session revocation.
    """
    image_bytes = _create_test_image_bytes()

    # 1. Register new operator user
    email = "operator_e2e@traffic.gov.in"
    password = "SecureE2EPass123!"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"name": "Traffic Operator", "email": email, "password": password},
    )
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert reg_data["success"] is True
    assert "token" in reg_data
    assert "user" in reg_data

    # Elevate user role to operator in database for authorized endpoints
    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.models.db.user import User

    session_factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(update(User).where(User.email == email).values(role="operator"))
        await session.commit()

    # 2. Login to obtain authenticated session and cookie
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, login_resp.text
    login_data = login_resp.json()
    assert login_data["success"] is True
    token = login_data["token"]
    assert token is not None
    assert "access_token" in login_resp.cookies

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 3. Access authenticated profile/dashboard endpoint
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200, me_resp.text
    me_data = me_resp.json()
    assert me_data["email"] == email
    assert me_data["role"] == "operator"

    # 4. Object detection
    obj_resp = await client.post(
        "/api/v1/detect/objects",
        headers=auth_headers,
        files={"file": ("test.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    assert obj_resp.status_code == 200, obj_resp.text
    obj_data = obj_resp.json()
    assert obj_data["success"] is True
    assert "detections" in obj_data
    assert "visualization" in obj_data

    # 5. Pothole detection
    pot_resp = await client.post(
        "/api/v1/detect/potholes",
        headers=auth_headers,
        files={"file": ("test.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    assert pot_resp.status_code == 200, pot_resp.text
    pot_data = pot_resp.json()
    assert pot_data["success"] is True

    # 6. Weather detection
    weather_resp = await client.post(
        "/api/v1/detect/weather",
        headers=auth_headers,
        files={"file": ("test.jpg", io.BytesIO(image_bytes), "image/jpeg")},
    )
    assert weather_resp.status_code == 200, weather_resp.text
    weather_data = weather_resp.json()
    assert weather_data["success"] is True

    # 7. Submit traffic report
    report_payload = {
        "junction_id": "JUNC-DELHI-001",
        "weather_condition": "clear",
        "congestion_level": 0.45,
        "vehicle_count": 85,
        "pedestrian_count": 12,
        "railway_crossing_active": False,
        "notes": "E2E verification report",
    }
    rpt_resp = await client.post(
        "/api/v1/reports",
        headers=auth_headers,
        json=report_payload,
    )
    assert rpt_resp.status_code == 201, rpt_resp.text
    rpt_data = rpt_resp.json()
    assert rpt_data["success"] is True
    report_id = rpt_data["report"]["id"]

    # Retrieve recent reports and verify presence
    rec_resp = await client.get("/api/v1/reports/recent", headers=auth_headers)
    assert rec_resp.status_code == 200, rec_resp.text
    rec_data = rec_resp.json()
    assert rec_data["success"] is True
    assert any(r["id"] == report_id for r in rec_data["reports"])

    # 8. AI Insights generation (both /insights/generate and /generate/insights aliases)
    insight_resp1 = await client.post(
        "/api/v1/insights/generate",
        headers=auth_headers,
        json={"prompt": "Current junction JUNC-DELHI-001 has 85 vehicles. Recommend signal policy."},
    )
    assert insight_resp1.status_code == 200, insight_resp1.text
    assert insight_resp1.json()["success"] is True
    assert len(insight_resp1.json()["insights"]) > 0

    insight_resp2 = await client.post(
        "/api/v1/generate/insights",
        headers=auth_headers,
        json={"prompt": "Peak traffic advisory analysis"},
    )
    assert insight_resp2.status_code == 200, insight_resp2.text
    assert insight_resp2.json()["success"] is True

    # 9. Signal optimization
    opt_resp = await client.post(
        "/api/v1/optimize/signals",
        headers=auth_headers,
        json={
            "junction_id": "JUNC-DELHI-001",
            "traffic_data": {"vehicle_count": 85, "pedestrian_count": 12},
            "weather_data": {"condition": "clear", "confidence": 0.95},
        },
    )
    assert opt_resp.status_code == 200, opt_resp.text
    opt_data = opt_resp.json()
    assert opt_data["success"] is True
    assert "signal_timings" in opt_data

    # 10. Logout and session invalidation
    logout_resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_resp.status_code == 200, logout_resp.text
    assert logout_resp.json()["success"] is True

    # 11. Verify old token and session can NO LONGER access protected endpoints
    revoked_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert revoked_resp.status_code == 401, f"Expected 401 on revoked session, got: {revoked_resp.status_code}"

    revoked_rpt = await client.post(
        "/api/v1/reports",
        headers=auth_headers,
        json=report_payload,
    )
    assert revoked_rpt.status_code == 401, f"Expected 401 on revoked session, got: {revoked_rpt.status_code}"


def test_production_startup_validation():
    """
    Verify strict configuration validation for production mode:
    - Rejects short/insecure JWT secret
    - Rejects SQLite driver
    - Rejects ALLOW_MOCK_MODELS=True
    - Accepts valid production settings
    """
    # 1. Reject weak secret
    with pytest.raises(ValueError, match="JWT_SECRET must be at least 32 characters"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="too-short",
            DB_DRIVER="postgresql",
            ALLOW_MOCK_MODELS=False,
        )

    with pytest.raises(ValueError, match="cannot be a default or known weak secret"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="change-me-to-a-very-secret-key-32chars!",
            DB_DRIVER="postgresql",
            ALLOW_MOCK_MODELS=False,
        )

    # 2. Reject SQLite in production
    with pytest.raises(ValueError, match="SQLite is not permitted in production"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="a" * 32,
            DB_DRIVER="sqlite",
            ALLOW_MOCK_MODELS=False,
        )

    # 3. Reject mock models in production
    with pytest.raises(ValueError, match="ALLOW_MOCK_MODELS cannot be True in production"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="a" * 32,
            DB_DRIVER="postgresql",
            ALLOW_MOCK_MODELS=True,
        )

    # 4. Valid production configuration succeeds
    prod_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET="super-strong-production-secret-token-key-32ch",
        DB_DRIVER="postgresql",
        DB_HOST="postgres-prod",
        DB_PORT=5432,
        DB_USER="stms_admin",
        DB_PASSWORD="very_secure_db_password_123!",
        DB_DATABASE="stms_production",
        REDIS_URL="redis://redis-prod:6379/0",
        ALLOW_MOCK_MODELS=False,
    )
    assert prod_settings.is_production is True
    assert prod_settings.database_url.startswith("postgresql://")
    assert prod_settings.database_url_async.startswith("postgresql+asyncpg://")


@pytest.mark.asyncio
async def test_rate_limiter_sliding_window_and_normalization():
    """Verify rate limiter sliding window semantics and legacy route normalization."""
    from app.core.rate_limiter import InMemoryRateLimiter, RedisRateLimiter
    from app.middleware.rate_limiter import _find_rule, _normalize_path

    # 1. Path normalization
    assert _normalize_path("/api/login") == "/api/v1/auth/login"
    assert _normalize_path("/api/register") == "/api/v1/auth/register"
    assert _normalize_path("/api/auth/login") == "/api/v1/auth/login"
    assert _normalize_path("/api/v1/auth/login") == "/api/v1/auth/login"
    assert _normalize_path("/api/detect/objects") == "/api/v1/detect/objects"

    # Rule matching
    rule = _find_rule("/api/v1/auth/login")
    assert rule is not None
    assert rule[0] == "/api/v1/auth/login"
    assert rule[1] == 5  # max 5 requests

    # 2. InMemoryRateLimiter sliding window
    limiter = InMemoryRateLimiter()
    key = "test_user_key"
    max_req = 3
    window = 10

    # First 3 should pass
    for _ in range(max_req):
        limited, _ = await limiter.is_rate_limited(key, max_req, window)
        assert limited is False

    # 4th request must be rate limited
    limited, retry_after = await limiter.is_rate_limited(key, max_req, window)
    assert limited is True
    assert retry_after > 0

    # 3. RedisRateLimiter fallback when Redis unavailable
    redis_limiter = RedisRateLimiter("redis://invalid-host-unreachable:6379/0")
    # Even if Redis is not reachable, fallback to InMemory works seamlessly without crash
    r_limited, _ = await redis_limiter.is_rate_limited("fallback_key", 2, 5)
    assert r_limited is False

