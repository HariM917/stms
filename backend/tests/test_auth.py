"""
Tests for the authentication endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    """Registration with valid data should return 201 with token and user."""
    response = await client.post("/api/v1/auth/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "securepass123",
    })
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["token"] is not None
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["role"] == "user"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Registering with an existing email should return 409."""
    payload = {"name": "Bob", "email": "bob@example.com", "password": "password123"}

    # First registration should succeed
    response1 = await client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201

    # Second registration with same email should fail
    response2 = await client.post("/api/v1/auth/register", json=payload)
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_register_validation_error(client):
    """Registration with invalid data should return 422."""
    response = await client.post("/api/v1/auth/register", json={
        "name": "",  # Too short
        "email": "invalid",
        "password": "123",  # Too short
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(registered_user, client):
    """Login with correct credentials should return a JWT token."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["token"] is not None
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(registered_user, client):
    """Login with wrong password should return 401."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    """Login with non-existent email should return 401."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile(client, auth_headers):
    """Authenticated user should be able to get their profile."""
    response = await client.get("/api/v1/auth/profile", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


@pytest.mark.asyncio
async def test_get_profile_unauthorized(client):
    """Accessing profile without token should return 401."""
    response = await client.get("/api/v1/auth/profile")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client, auth_headers):
    """Authenticated user should be able to update their profile."""
    response = await client.put("/api/v1/auth/profile", json={
        "name": "Updated Name",
        "phone": "+91-9876543210",
    }, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["phone"] == "+91-9876543210"


@pytest.mark.asyncio
async def test_change_password(client, auth_headers):
    """Authenticated user should be able to change their password."""
    response = await client.put("/api/v1/auth/change-password", json={
        "current_password": "testpass123",
        "new_password": "newpass456",
    }, headers=auth_headers)
    assert response.status_code == 200

    # Verify new password works
    login_response = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "newpass456",
    })
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client, auth_headers):
    """Changing password with wrong current password should return 400."""
    response = await client.put("/api/v1/auth/change-password", json={
        "current_password": "wrongpassword",
        "new_password": "newpass456",
    }, headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_users_list(client, registered_user):
    """Users list endpoint should return registered users."""
    response = await client.get("/api/v1/auth/users")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["count"] >= 1


@pytest.mark.asyncio
async def test_delete_account(client, auth_headers):
    """Authenticated user should be able to delete their account."""
    response = await client.delete("/api/v1/auth/account", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True

    # Verify the token no longer works
    profile_response = await client.get("/api/v1/auth/profile", headers=auth_headers)
    assert profile_response.status_code == 401
