"""
Credential-related exceptions.
"""
from fastapi import status

from eudi_connect.exceptions.base import APIError


class CredentialTypeNotFoundError(APIError):
    """Exception raised when a credential type is not found."""
    def __init__(self, type_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="credential_type_not_found",
            message=f"Credential type with ID '{type_id}' not found or inactive"
        )


class CredentialSchemaValidationError(APIError):
    """Exception raised when credential claims fail to validate against the schema."""
    def __init__(self, error_message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="credential_schema_validation_failed",
            message=f"Claims validation against credential schema failed: {error_message}"
        )


class CredentialIssuanceError(APIError):
    """Exception raised when credential issuance fails."""
    def __init__(self, error_message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="credential_issuance_failed",
            message=f"Failed to issue credential: {error_message}"
        )


class CredentialVerificationError(APIError):
    """Exception raised when credential verification fails."""
    def __init__(self, error_message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="credential_verification_failed",
            message=f"Failed to verify credential: {error_message}"
        )


class CredentialNotFoundError(APIError):
    """Exception raised when a credential is not found."""
    def __init__(self, credential_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="credential_not_found",
            message=f"Credential with ID '{credential_id}' not found or not issued by this merchant"
        )


class CredentialRevocationError(APIError):
    """Exception raised when credential revocation fails."""
    def __init__(self, error_message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="credential_revocation_failed",
            message=f"Failed to revoke credential: {error_message}"
        )


class CredentialInvalidFormatError(APIError):
    """Exception raised when credential format is invalid."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="credential_invalid_format",
            message="The provided credential has an invalid format"
        )


class CredentialInvalidStatusError(APIError):
    """Exception raised when attempting operations on credentials with invalid status."""
    def __init__(self, operation: str, required_status: str, current_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="credential_invalid_status",
            message=f"Cannot perform '{operation}' operation on credential with status '{current_status}', required status: '{required_status}'"
        )
