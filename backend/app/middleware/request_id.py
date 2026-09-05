"""
Request ID middleware — assigns a unique ID to every request for tracing.

The ID is added to:
  - The response header `X-Request-ID`
  - The logging context (via ContextVar)
"""
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variable to hold the current request ID (accessible from anywhere)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates or forwards a unique request ID.
    If the client sends an `X-Request-ID` header, it is reused.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Use client-provided ID or generate a new one
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        request_id_ctx.set(rid)

        # Store on request state for easy access in route handlers
        request.state.request_id = rid

        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


def get_request_id() -> str:
    """Get the current request ID (for use in logging or error responses)."""
    return request_id_ctx.get("")
