"""
Authentication related exceptions for the API.
"""
from fastapi import HTTPException, status


class AuthError(HTTPException):
    """Base class for authentication errors."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidCredentialsError(AuthError):
    """Exception raised for invalid credentials."""
    
    def __init__(self, detail: str = "Incorrect email or password"):
        super().__init__(detail=detail)


class InactiveMerchantError(AuthError):
    """Exception raised when merchant account is inactive."""
    
    def __init__(self, detail: str = "Merchant account is inactive"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )


class TokenExpiredError(AuthError):
    """Exception raised when the provided token has expired."""
    
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(detail=detail)


class InvalidTokenError(AuthError):
    """Exception raised when the provided token is invalid."""
    
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(detail=detail)


class InsufficientPermissionsError(AuthError):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )
