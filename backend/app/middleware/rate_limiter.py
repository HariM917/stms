"""
Comprehensive rate limiter middleware.
Protects auth, detection, optimization, insights, and report endpoints with normalized path keys.
"""
from typing import Optional, Tuple
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.core.rate_limiter import get_rate_limiter
from app.services.auth_service import decode_access_token
from app.utils.logging import get_logger

logger = get_logger("rate_limiter_middleware")

# (prefix, max_requests, window_seconds)
RATE_LIMIT_RULES: list[Tuple[str, int, int]] = [
    ("/api/v1/auth/login", 5, 60),
    ("/api/v1/auth/register", 3, 60),
    ("/api/v1/auth/change-password", 3, 60),
    ("/api/v1/detect", 30, 60),
    ("/api/v1/optimize", 20, 60),
    ("/api/v1/insights", 15, 60),
    ("/api/v1/reports", 30, 60),
]


def _normalize_path(path: str) -> str:
    """Normalize legacy unversioned routes (e.g., /api/auth/login -> /api/v1/auth/login)."""
    if path.startswith("/api/v1/"):
        return path
    if path.startswith("/api/"):
        # Replace first /api/ with /api/v1/
        return "/api/v1/" + path[5:]
    return path


def _find_rule(normalized_path: str) -> Optional[Tuple[str, int, int]]:
    """Find the most specific matching rate limit rule."""
    for prefix, max_req, window in RATE_LIMIT_RULES:
        if normalized_path.startswith(prefix):
            return prefix, max_req, window
    return None


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter applying per-route security limits.
    Prevents brute-force, DoS on ML models, and API scraping.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        if settings.environment == "test" and not getattr(request.state, "enable_rate_limit_test", False):
            return await call_next(request)

        normalized_path = _normalize_path(request.url.path)
        rule = _find_rule(normalized_path)

        if not rule:
            return await call_next(request)

        rule_prefix, max_requests, window_seconds = rule

        # Determine caller identity (authenticated user ID if token present, else client IP)
        client_ip = request.client.host if request.client else "unknown"
        user_id = None

        # Try extract user_id from Authorization header or cookie
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif "access_token" in request.cookies:
            token = request.cookies.get("access_token")

        if token:
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                user_id = str(payload["sub"])

        client_key = f"user_{user_id}" if user_id else f"ip_{client_ip}"
        bucket_key = f"{client_key}:{rule_prefix}"

        limiter = get_rate_limiter()
        is_limited, retry_after = await limiter.is_rate_limited(
            key=bucket_key,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        if is_limited:
            logger.warning("Rate limit exceeded for %s on %s (retry_after=%ds)", client_key, normalized_path, retry_after)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please slow down and try again later.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
