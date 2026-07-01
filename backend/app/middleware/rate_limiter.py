"""
In-memory sliding-window rate limiter middleware.

Limits the number of requests per IP within a configurable time window.
Intended for auth-sensitive endpoints; detection endpoints are not rate-limited
by default (they are naturally throttled by model inference time).

For production at scale, replace with Redis-backed rate limiting.
"""
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("rate_limiter")


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding-window rate limiter.
    Only applies to paths matching the configured prefixes.
    """

    # Paths that are rate-limited (auth endpoints are the most sensitive)
    RATE_LIMITED_PREFIXES = ("/api/v1/auth/login", "/api/v1/auth/register")

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only rate-limit specific paths
        path = request.url.path
        if not any(path.startswith(prefix) for prefix in self.RATE_LIMITED_PREFIXES):
            return await call_next(request)

        settings = get_settings()
        max_requests = settings.rate_limit_requests
        window_seconds = settings.rate_limit_window_seconds

        # Identify client by IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries outside the window
        timestamps = self._requests[client_ip]
        self._requests[client_ip] = [t for t in timestamps if now - t < window_seconds]
        timestamps = self._requests[client_ip]

        if len(timestamps) >= max_requests:
            retry_after = int(window_seconds - (now - timestamps[0]))
            logger.warning("Rate limit exceeded for IP %s on %s", client_ip, path)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Record this request
        self._requests[client_ip].append(now)
        return await call_next(request)
