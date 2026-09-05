"""
Comprehensive production-readiness and security test suite.
Verifies:
- Session revocation on logout
- Invalidation of all sessions on password change
- Rejection of deactivated users
- Rejection of weak JWT secret in production
- Rejection of SQLite in production
- Rejection of mock models in production
- Image size limit enforcement (HTTP 413)
- Magic byte validation (rejection of spoofed files)
"""
import io

import pytest

from app.config import Settings

# ---- Phase 2 & 11: Production Config Validation ----

def test_production_rejects_weak_jwt_secret():
    """Production mode must reject weak or default JWT secrets."""
    with pytest.raises(ValueError, match="JWT_SECRET must be at least 32 characters long"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="short-secret",
            DB_DRIVER="postgresql",
            DB_PASSWORD="secure_db_pass_123",
            ALLOW_MOCK_MODELS=False,
        )

    with pytest.raises(ValueError, match="cannot be a default or known weak secret"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="change-me-in-production-long-enough-now",
            DB_DRIVER="postgresql",
            DB_PASSWORD="secure_db_pass_123",
            ALLOW_MOCK_MODELS=False,
        )


def test_production_rejects_sqlite():
    """Production mode must reject SQLite database driver."""
    with pytest.raises(ValueError, match="SQLite is not permitted in production"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="production-random-secret-key-at-least-32-chars-long",
            DB_DRIVER="sqlite",
            ALLOW_MOCK_MODELS=False,
        )


def test_production_rejects_mock_models():
    """Production mode must disallow mock models."""
    with pytest.raises(ValueError, match="ALLOW_MOCK_MODELS cannot be True in production"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="production-random-secret-key-at-least-32-chars-long",
            DB_DRIVER="postgresql",
            DB_PASSWORD="secure_db_pass_123",
            ALLOW_MOCK_MODELS=True,
        )


# ---- Phase 2.3: Session & Revocation Tests ----

@pytest.mark.asyncio
async def test_session_revocation_on_logout(client):
    """Logging out must revoke that specific session token."""
    client.cookies.clear()
    reg_resp = await client.post("/api/v1/auth/register", json={
        "name": "Logout Tester",
        "email": "logout_test@example.com",
        "password": "securepassword123",
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Profile works with active session
    prof1 = await client.get("/api/v1/auth/profile", headers=headers)
    assert prof1.status_code == 200

    # Logout
    logout_resp = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # Token must now be rejected
    client.cookies.clear()
    prof2 = await client.get("/api/v1/auth/profile", headers=headers)
    assert prof2.status_code == 401


@pytest.mark.asyncio
async def test_password_change_invalidates_all_previous_sessions(client):
    """Changing password must invalidate all existing sessions."""
    client.cookies.clear()
    reg_resp = await client.post("/api/v1/auth/register", json={
        "name": "Password Changer",
        "email": "pwd_change@example.com",
        "password": "initialpassword123",
    })
    token1 = reg_resp.json()["token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Change password
    client.cookies.clear()
    chg_resp = await client.put(
        "/api/v1/auth/change-password",
        json={
            "current_password": "initialpassword123",
            "new_password": "newpassword456",
        },
        headers=headers1,
    )
    assert chg_resp.status_code == 200
    token2 = chg_resp.json()["token"]

    # Old token1 must now be rejected
    client.cookies.clear()
    check_old = await client.get("/api/v1/auth/profile", headers=headers1)
    assert check_old.status_code == 401

    # New token2 must work
    client.cookies.clear()
    check_new = await client.get("/api/v1/auth/profile", headers={"Authorization": f"Bearer {token2}"})
    assert check_new.status_code == 200


@pytest.mark.asyncio
async def test_deactivated_user_rejected(client, db_engine):
    """Deactivated user account must be rejected with 403."""
    client.cookies.clear()
    email = "deactivated_user@example.com"
    reg_resp = await client.post("/api/v1/auth/register", json={
        "name": "To Be Deactivated",
        "email": email,
        "password": "testpass123",
    })
    token = reg_resp.json()["token"]

    # Deactivate user directly in DB
    from sqlalchemy import update
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from app.models.db.user import User
    session_factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(update(User).where(User.email == email).values(is_active=False))
        await session.commit()

    # Request must be rejected with 403 Forbidden
    client.cookies.clear()
    response = await client.get("/api/v1/auth/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


# ---- Phase 5: Image Upload Security Tests ----

@pytest.mark.asyncio
async def test_spoofed_file_signature_rejected(client, auth_headers):
    """Uploading a text file spoofed as an image/png must be rejected with 400."""
    fake_png = b"This is plain text pretending to be a PNG"
    response = await client.post(
        "/api/v1/detect/objects",
        headers=auth_headers,
        files={"file": ("fake.png", io.BytesIO(fake_png), "image/png")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_oversized_upload_rejected(client, auth_headers):
    """Uploading a file exceeding max upload size must return HTTP 413."""
    # 11 MB fake payload
    oversized_data = b"\xff\xd8\xff" + b"\x00" * (11 * 1024 * 1024)
    response = await client.post(
        "/api/v1/detect/objects",
        headers=auth_headers,
        files={"file": ("huge.jpg", io.BytesIO(oversized_data), "image/jpeg")},
    )
    assert response.status_code == 413
