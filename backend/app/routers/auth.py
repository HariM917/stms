"""
Authentication router — production-grade with JWT, bcrypt, and database persistence.

Consolidates all auth functionality (previously split between Python and Node.js)
into a single, clean set of endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.auth import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    UserResponse,
)
from app.models.db.user import User
from app.models.db.session import UserSession
from app.repositories import user_repository
from app.services.auth_service import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.utils.logging import get_logger

logger = get_logger("auth")
router = APIRouter(prefix="/auth", tags=["authentication"])


def _user_to_response(user: User) -> UserResponse:
    """Convert a User ORM instance to a UserResponse model."""
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        phone=user.phone,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


# ---- Registration ----

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user with hashed password."""
    existing = await user_repository.get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await user_repository.create_user(
        db,
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
    )

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})

    logger.info("New user registered: %s", body.email)
    return AuthResponse(
        success=True,
        message="Registration successful",
        token=token,
        user=_user_to_response(user),
    )


# ---- Login ----

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return a JWT token."""
    user = await user_repository.get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Create JWT
    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})

    # Record login session
    session = UserSession(
        user_id=user.id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add(session)

    logger.info("User logged in: %s", body.email)
    return AuthResponse(
        success=True,
        message="Login successful",
        token=token,
        user=_user_to_response(user),
    )


# ---- Logout ----

@router.post("/logout")
async def logout(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate the current session (marks latest session as logged out)."""
    from sqlalchemy import select, update
    from app.models.db.session import UserSession as SessionModel
    from datetime import datetime, timezone

    # Mark the most recent open session as logged out
    stmt = (
        update(SessionModel)
        .where(
            SessionModel.user_id == user.id,
            SessionModel.logout_time.is_(None),
        )
        .values(logout_time=datetime.now(timezone.utc))
    )
    await db.execute(stmt)

    logger.info("User logged out: %s", user.email)
    return {"success": True, "message": "Logged out successfully"}


# ---- Profile ----

@router.get("/profile", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user)):
    """Get the current user's profile."""
    return _user_to_response(user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's profile fields."""
    update_fields = {}
    if body.name is not None:
        update_fields["name"] = body.name
    if body.phone is not None:
        update_fields["phone"] = body.phone

    if not update_fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    updated_user = await user_repository.update_user(db, user, **update_fields)
    logger.info("Profile updated: %s", user.email)
    return _user_to_response(updated_user)


# ---- Change Password ----

@router.put("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's password."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    await user_repository.update_user(db, user, password_hash=hash_password(body.new_password))
    logger.info("Password changed: %s", user.email)
    return {"success": True, "message": "Password changed successfully"}


# ---- Delete Account ----

@router.delete("/account")
async def delete_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete the current user's account and all associated data."""
    email = user.email
    await user_repository.delete_user(db, user)
    logger.info("Account deleted: %s", email)
    return {"success": True, "message": "Account deleted successfully"}


# ---- Users list (admin/public) ----

@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    """Get list of registered users (public info only)."""
    users = await user_repository.list_users(db)
    users_list = [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role}
        for u in users
    ]
    return {"success": True, "count": len(users_list), "users": users_list}
