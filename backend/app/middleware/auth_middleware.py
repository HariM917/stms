"""
Authentication middleware — FastAPI dependencies for JWT-based auth with session revocation and cookies.
"""
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.db.session import UserSession
from app.models.db.user import User
from app.repositories import user_repository
from app.services.auth_service import decode_access_token
from app.utils.logging import get_logger

logger = get_logger("auth_middleware")

_bearer_scheme = HTTPBearer(auto_error=False)

ROLE_LEVELS = {
    "admin": 30,
    "operator": 20,
    "user": 10,
}


def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    """Extract token from Authorization header or HttpOnly cookie."""
    if credentials and credentials.credentials:
        return credentials.credentials
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    # Also check Authorization header directly in case HTTPBearer didn't capture
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency: extract JWT, decode it, verify against active server-side sessions,
    and return the authenticated User.
    """
    token = _extract_token(request, credentials)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
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

    # Session / JTI check for revocation
    jti: str | None = payload.get("jti")
    if jti:
        result = await db.execute(
            select(UserSession).where(
                UserSession.id == jti,
                UserSession.user_id == user.id,
            )
        )
        session = result.scalar_one_or_none()
        if session is None or session.logout_time is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked or logged out",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request.state.session_id = jti
    else:
        settings = get_settings()
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing session identifier (jti)",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


def require_role(*required_roles: str) -> Callable:
    """
    Role check supporting role hierarchy (admin > operator > user).
    """
    min_required_level = min(ROLE_LEVELS.get(r, 0) for r in required_roles) if required_roles else 0

    async def _role_checker(user: User = Depends(get_current_user)) -> User:
        user_level = ROLE_LEVELS.get(user.role, 0)
        # Direct match or hierarchical match
        if user.role not in required_roles and user_level < min_required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role(s): {', '.join(required_roles)}",
            )
        return user

    return _role_checker


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Like get_current_user, but returns None instead of raising when unauthenticated."""
    token = _extract_token(request, credentials)
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await user_repository.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        return None

    jti = payload.get("jti")
    if jti:
        result = await db.execute(
            select(UserSession).where(
                UserSession.id == jti,
                UserSession.user_id == user.id,
            )
        )
        session = result.scalar_one_or_none()
        if session is None or session.logout_time is not None:
            return None
        request.state.session_id = jti

    return user

