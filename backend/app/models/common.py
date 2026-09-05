"""
Common response models used across multiple routers.
"""

from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response envelope."""
    success: bool
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    detail: str | None = None
