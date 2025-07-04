"""
Centralized error handling and exception management for EUDI-Connect API.

This module provides standardized error responses and logging for API endpoints.
"""
import logging
import traceback
from typing import Any, Dict, Optional, Type, Union

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger("eudi_connect.errors")

# Define standard error response model
class ErrorResponse(BaseModel):
    """Standard error response model for API errors."""
    status: str = Field("error", description="Error status indicator")
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
# Error codes
class ErrorCode:
    """Standard error codes for API errors."""
    # Authentication errors
    INVALID_API_KEY = "invalid_api_key"
    EXPIRED_API_KEY = "expired_api_key"
    REVOKED_API_KEY = "revoked_api_key"
    MISSING_API_KEY = "missing_api_key"
    
    # Wallet session errors
    SESSION_NOT_FOUND = "session_not_found"
    SESSION_EXPIRED = "session_expired"
    INVALID_SESSION_REQUEST = "invalid_session_request"
    SESSION_ALREADY_USED = "session_already_used"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "resource_not_found"
    RESOURCE_ALREADY_EXISTS = "resource_already_exists"
    
    # Validation errors
    VALIDATION_ERROR = "validation_error"
    INVALID_PAYLOAD = "invalid_payload"
    INVALID_FORMAT = "invalid_format"
    
    # Server errors
    INTERNAL_ERROR = "internal_error"
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"

# Custom exceptions that map to standard error responses
class APIError(HTTPException):
    """Base class for all API errors."""
    def __init__(
        self, 
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code)
        self.error_code = error_code
        self.message = message
        self.details = details

class AuthenticationError(APIError):
    """Authentication or authorization errors."""
    def __init__(
        self,
        error_code: str = ErrorCode.INVALID_API_KEY,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            message=message,
            details=details
        )

class NotFoundError(APIError):
    """Resource not found errors."""
    def __init__(
        self,
        error_code: str = ErrorCode.RESOURCE_NOT_FOUND,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            message=message,
            details=details
        )

class ValidationError(APIError):
    """Input validation errors."""
    def __init__(
        self,
        error_code: str = ErrorCode.VALIDATION_ERROR,
        message: str = "Validation error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            message=message,
            details=details
        )

class ServerError(APIError):
    """Internal server errors."""
    def __init__(
        self,
        error_code: str = ErrorCode.INTERNAL_ERROR,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            message=message,
            details=details
        )

# Additional exception classes for compatibility
class NotFoundException(NotFoundError):
    """Alias for NotFoundError for backward compatibility."""
    pass

class ValidationException(ValidationError):
    """Alias for ValidationError for backward compatibility."""
    pass

class ExpiredResourceException(APIError):
    """Resource has expired and is no longer valid."""
    def __init__(
        self,
        error_code: str = "resource_expired",
        message: str = "Resource has expired",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            error_code=error_code,
            message=message,
            details=details
        )

class DatabaseException(APIError):
    """Database operation errors."""
    def __init__(
        self,
        error_code: str = ErrorCode.DATABASE_ERROR,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            message=message,
            details=details
        )

class InvalidStateException(APIError):
    """Invalid state or operation errors."""
    def __init__(
        self,
        error_code: str = "invalid_state",
        message: str = "Invalid state for this operation",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            message=message,
            details=details
        )

# Exception handler for FastAPI
async def api_exception_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle API exceptions and return standardized error responses."""
    # Log the error with different levels based on severity
    if exc.status_code >= 500:
        logger.error(
            f"Server error: {exc.error_code} - {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "details": exc.details,
                "status_code": exc.status_code
            }
        )
        # Include stack trace for server errors
        logger.debug(traceback.format_exc())
    elif exc.status_code >= 400:
        logger.warning(
            f"Client error: {exc.error_code} - {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "details": exc.details,
                "status_code": exc.status_code
            }
        )
    
    # Return standardized error response
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.error_code,
            message=exc.message,
            details=exc.details
        ).dict(exclude_none=True)
    )

# Register exception handlers with FastAPI
def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(APIError, api_exception_handler)
    
    # Also handle standard HTTPException
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        error_code = f"http_{exc.status_code}"
        
        # Map common HTTP exceptions to our error codes
        if exc.status_code == 401:
            error_code = ErrorCode.INVALID_API_KEY
        elif exc.status_code == 404:
            error_code = ErrorCode.RESOURCE_NOT_FOUND
        elif exc.status_code == 422:
            error_code = ErrorCode.VALIDATION_ERROR
            
        # Log the error
        logger.warning(
            f"HTTP exception: {error_code} - {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code
            }
        )
        
        # Return standardized error response
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=error_code,
                message=str(exc.detail),
                details=None
            ).dict(exclude_none=True)
        )
    
    # Handle validation exceptions from Pydantic
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the error with stack trace
        logger.error(
            f"Unhandled exception: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__
            }
        )
        logger.debug(traceback.format_exc())
        
        # Return standardized error response for unhandled exceptions
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code=ErrorCode.INTERNAL_ERROR,
                message="An unexpected error occurred",
                details={"type": type(exc).__name__} if not isinstance(exc, APIError) else None
            ).dict(exclude_none=True)
        )
