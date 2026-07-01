"""
Authentication middleware — FastAPI dependencies for JWT-based auth.

Usage in routes:
    from app.middleware.auth_middleware import get_current_user, require_role

    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        ...

    @router.delete("/admin-only")
    async def admin_route(user: User = Depends(require_role("admin"))):
        ...
"""
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db.user import User
from app.repositories import user_repository
from app.services.auth_service import decode_access_token
from app.utils.logging import get_logger

logger = get_logger("auth_middleware")

# HTTP Bearer scheme — extracts token from "Authorization: Bearer <token>"
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: extract JWT from Authorization header, decode it,
    and return the corresponding User from the database.

    Raises HTTPException 401 if token is missing, invalid, or user not found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await user_repository.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


def require_role(*roles: str) -> Callable:
    """
    Factory that returns a FastAPI dependency requiring the current user
    to have one of the specified roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def _role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role(s): {', '.join(roles)}",
            )
        return user

    return _role_checker


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Like get_current_user, but returns None instead of raising
    if no token is provided. Useful for routes that behave differently
    for authenticated vs anonymous users.
    """
    if credentials is None:
        return None

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None

    user = await user_repository.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        return None

    return user
