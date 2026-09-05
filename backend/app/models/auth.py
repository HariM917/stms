"""
Pydantic models for authentication endpoints.
"""

from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class RegisterRequest(BaseModel):
    """Registration request body."""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255, pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=8, max_length=128, description="Password must be at least 8 characters")


class LoginRequest(BaseModel):
    """Login request body."""
    email: str = Field(..., min_length=5, max_length=255, pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Public user data (never includes password)."""
    id: str
    name: str
    email: str
    role: str = "user"
    phone: str | None = None
    avatar_url: str | None = None
    created_at: str | None = None


class AuthResponse(BaseModel):
    """Response for login/register containing token and user."""
    success: bool
    message: str
    token: str | None = None
    user: UserResponse | None = None


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class ProfileUpdateRequest(BaseModel):
    """Request to update user profile."""
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, min_length=5, max_length=20)


class ChangePasswordRequest(BaseModel):
    """Request to change password."""
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128, description="New password must be at least 8 characters")

