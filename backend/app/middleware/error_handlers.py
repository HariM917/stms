"""
Global exception handlers for the FastAPI application.

Provides structured, consistent error responses for all exception types.
"""
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.middleware.request_id import get_request_id
from app.utils.logging import get_logger

logger = get_logger("error_handler")


def register_error_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTPExceptions with a structured response."""
        request_id = get_request_id()
        logger.warning(
            "HTTP %d on %s %s — %s [request_id=%s]",
            exc.status_code, request.method, request.url.path, exc.detail, request_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "request_id": request_id,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors with readable field-level detail."""
        request_id = get_request_id()
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            "Validation error on %s %s — %d field(s) [request_id=%s]",
            request.method, request.url.path, len(errors), request_id,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation error",
                "errors": errors,
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions — never leak stack traces in production."""
        request_id = get_request_id()
        logger.error(
            "Unhandled exception on %s %s [request_id=%s]: %s",
            request.method, request.url.path, request_id, exc,
            exc_info=True,
        )

        from app.config import get_settings
        settings = get_settings()

        # In development, include the error message; in production, hide it
        detail = str(exc) if not settings.is_production else None

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "detail": detail,
                "request_id": request_id,
            },
        )
