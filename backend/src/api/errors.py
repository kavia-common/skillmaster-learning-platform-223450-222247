"""Standardized error handling utilities for the API layer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    BAD_REQUEST = "BAD_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error response payload."""
    code: ErrorCode = Field(..., description="Standard error code")
    message: str = Field(..., description="Human-friendly error message")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="UTC timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Optional extra context for debugging")


class ApplicationError(Exception):
    """Base exception class for application-level errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_model(self) -> ErrorDetail:
        return ErrorDetail(code=self.code, message=self.message, details=self.details)


def application_error_handler(_: Request, exc: ApplicationError) -> JSONResponse:
    """FastAPI handler for ApplicationError exceptions."""
    payload = exc.to_model().model_dump()
    return JSONResponse(status_code=exc.status_code, content={"error": payload})


def generic_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """FastAPI handler for unexpected exceptions."""
    payload = ErrorDetail(
        code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred",
        details={"reason": str(exc)[:200]},
    ).model_dump()
    return JSONResponse(status_code=500, content={"error": payload})
