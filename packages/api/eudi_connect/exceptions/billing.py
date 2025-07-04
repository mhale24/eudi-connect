"""
Billing related exceptions for the API.
"""
from fastapi import HTTPException, status


class BillingError(HTTPException):
    """Base class for billing errors."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(
            status_code=status_code,
            detail=detail
        )


class SubscriptionNotFoundError(BillingError):
    """Exception raised when a subscription is not found."""
    
    def __init__(self, detail: str = "No active subscription found"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND
        )


class PlanNotFoundError(BillingError):
    """Exception raised when a billing plan is not found."""
    
    def __init__(self, detail: str = "Plan not found"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND
        )


class StripeIntegrationError(BillingError):
    """Exception raised when there is an issue with Stripe integration."""
    
    def __init__(self, detail: str = "Stripe integration error"):
        super().__init__(detail=detail)


class StripeNotConfiguredError(BillingError):
    """Exception raised when Stripe is not configured."""
    
    def __init__(self, detail: str = "Stripe integration not configured"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_501_NOT_IMPLEMENTED
        )


class InvalidBillingCycleError(BillingError):
    """Exception raised when an invalid billing cycle is provided."""
    
    def __init__(self, detail: str = "Invalid billing cycle. Must be 'monthly' or 'yearly'"):
        super().__init__(detail=detail)


class UsageQuotaExceededError(BillingError):
    """Exception raised when the usage quota is exceeded."""
    
    def __init__(self, detail: str = "Usage quota exceeded for current subscription"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )
