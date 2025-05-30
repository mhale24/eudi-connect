from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID
import json
import jsonschema

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from eudi_connect.api.deps import APIKeyAuth, DB
from eudi_connect.models.credential import CredentialLog, CredentialType
from eudi_connect.services.didkit import DIDKitService, get_didkit_service

router = APIRouter()


def _serialize_for_json(obj: Any) -> Any:
    """Convert objects to JSON serializable format."""
    if isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    elif isinstance(obj, UUID):
        return str(obj)
    elif hasattr(obj, "model_dump"):
        return _serialize_for_json(obj.model_dump())
    return obj


class CredentialTypeResponse(BaseModel):
    """Credential type response model."""
    id: UUID
    name: str
    version: str
    context: List[str]
    schema: Dict[str, Any]
    is_active: bool


class CredentialIssueRequest(BaseModel):
    """Credential issuance request model."""
    type_id: UUID
    subject_did: str = Field(..., pattern=r"^did:")
    claims: Dict[str, Any]
    proof_options: Dict[str, Any] | None = None

    @field_validator("claims")
    def validate_claims(cls, v: Dict[str, Any], values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate claims against credential type schema."""
        if not v:
            raise ValueError("Claims cannot be empty")
        return v


class CredentialVerifyRequest(BaseModel):
    """Credential verification request model."""
    credential: Dict[str, Any]
    proof_options: Dict[str, Any] | None = None


class CredentialRevokeRequest(BaseModel):
    """Credential revocation request model."""
    credential_id: str
    proof_options: Dict[str, Any] | None = None


class CredentialOperationResponse(BaseModel):
    """Credential operation response model."""
    id: UUID
    operation: str
    status: str
    error: str | None
    metadata: Dict[str, Any] = Field(alias="log_metadata")
    subject_did: str
    proof: Dict[str, Any]
    created_at: datetime


@router.get("/types", response_model=List[CredentialTypeResponse])
async def list_credential_types(
    db: DB,
    api_key: APIKeyAuth,
) -> List[CredentialTypeResponse]:
    """List all active credential types."""
    result = await db.execute(
        select(CredentialType)
        .where(CredentialType.is_active.is_(True))
        .order_by(CredentialType.name)
    )
    types = result.scalars().all()
    
    # Convert SQLAlchemy models to dictionaries before Pydantic validation
    response_types = []
    for t in types:
        type_dict = {
            "id": t.id,
            "name": t.name,
            "version": t.version,
            "context": t.context,
            "schema": t.schema,
            "is_active": t.is_active,
            "created_at": t.created_at
        }
        response_types.append(CredentialTypeResponse.model_validate(type_dict))
    
    return response_types


@router.post("/issue", response_model=CredentialOperationResponse)
async def issue_credential(
    db: DB,
    api_key: APIKeyAuth,
    request: CredentialIssueRequest,
) -> CredentialOperationResponse:
    """Issue a new verifiable credential."""
    # Get credential type
    result = await db.execute(
        select(CredentialType)
        .where(CredentialType.id == request.type_id)
        .where(CredentialType.is_active.is_(True))
    )
    cred_type = result.scalar_one_or_none()

    if not cred_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential type not found"
        )

    try:
        # Validate claims against schema
        try:
            jsonschema.validate(request.claims, cred_type.schema)
        except jsonschema.exceptions.ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid claims: {str(e)}"
            )

        # Issue credential using DIDKit
        didkit = get_didkit_service()
        credential = didkit.issue_credential(
            credential_or_type_name=cred_type.name,
            context=cred_type.context,
            subject_did=request.subject_did,
            claims=request.claims,
            proof_options=request.proof_options
        )

        # Log the operation
        log = CredentialLog(
            merchant_id=api_key.merchant_id,
            credential_type_id=cred_type.id,
            operation="issue",
            status="success",
            subject_did=request.subject_did,
            log_metadata={"credential": _serialize_for_json(credential)},
            proof=credential["proof"]
        )
        db.add(log)
        await db.commit()

        # Convert SQLAlchemy model to dictionary for pydantic validation
        log_dict = {
            "id": log.id,
            "operation": log.operation,
            "status": log.status,
            "error": log.error,
            "log_metadata": log.log_metadata,
            "subject_did": log.subject_did,
            "proof": log.proof,
            "created_at": log.created_at
        }
        return CredentialOperationResponse.model_validate(log_dict)

    except Exception as e:
        # Log failed operation
        log = CredentialLog(
            merchant_id=api_key.merchant_id,
            credential_type_id=cred_type.id,
            operation="issue",
            status="failed",
            subject_did=request.subject_did,
            error=str(e),
            log_metadata={"request": _serialize_for_json(request.model_dump())},
            proof={}
        )
        db.add(log)
        await db.commit()

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to issue credential: {str(e)}"
        )


@router.post("/verify", response_model=CredentialOperationResponse)
async def verify_credential(
    db: DB,
    api_key: APIKeyAuth,
    request: CredentialVerifyRequest,
) -> CredentialOperationResponse:
    """Verify a credential."""
    try:
        # Get credential type from the credential
        cred_type_name = request.credential.get("type", [])[1]
        result = await db.execute(
            select(CredentialType)
            .where(CredentialType.name == cred_type_name)
            .where(CredentialType.is_active.is_(True))
        )
        cred_type = result.scalar_one_or_none()

        if not cred_type:
            raise ValueError("Unknown credential type")

        # Verify credential using DIDKit
        didkit = get_didkit_service()
        verification_result = didkit.verify_credential(
            credential=request.credential,
            proof_options=request.proof_options
        )

        # Check if verification succeeded
        if not verification_result.get("verified"):
            raise ValueError(f"Verification failed: {verification_result.get('error')}")

        # Log the operation
        log = CredentialLog(
            merchant_id=api_key.merchant_id,
            credential_type_id=cred_type.id,
            operation="verify",
            status="success",
            subject_did=request.credential["credentialSubject"]["id"],
            log_metadata={"verification_result": _serialize_for_json(verification_result)},
            proof=request.credential.get("proof", {})
        )
        db.add(log)
        await db.commit()

        # Convert SQLAlchemy model to dictionary for pydantic validation
        log_dict = {
            "id": log.id,
            "operation": log.operation,
            "status": log.status,
            "error": log.error,
            "log_metadata": log.log_metadata,
            "subject_did": log.subject_did,
            "proof": log.proof,
            "created_at": log.created_at
        }
        return CredentialOperationResponse.model_validate(log_dict)

    except Exception as e:
        # Log failed operation
        log = CredentialLog(
            merchant_id=api_key.merchant_id,
            credential_type_id=cred_type.id if cred_type else None,
            operation="verify",
            status="failed",
            subject_did=request.credential.get("credentialSubject", {}).get("id", "unknown"),
            error=str(e),
            log_metadata={"credential": _serialize_for_json(request.credential)},
            proof=request.credential.get("proof", {})
        )
        db.add(log)
        await db.commit()

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify credential: {str(e)}"
        )


@router.post("/revoke", response_model=CredentialOperationResponse)
async def revoke_credential(
    db: DB,
    api_key: APIKeyAuth,
    request: CredentialRevokeRequest,
) -> CredentialOperationResponse:
    """Revoke a credential."""
    try:
        try:
            # Get credential log
            result = await db.execute(
                select(CredentialLog)
                .where(CredentialLog.id == request.credential_id)
                .where(CredentialLog.merchant_id == api_key.merchant_id)
                .where(CredentialLog.operation == "issue")
                .where(CredentialLog.status == "success")
            )
            cred_log = result.scalar_one_or_none()
    
            if not cred_log:
                # For non-existent credentials, just raise an exception without logging
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Credential not found or not issued by this merchant"
                )
        except Exception as e:
            # If it's already an HTTPException, just re-raise it
            if isinstance(e, HTTPException):
                raise e
            # Otherwise, wrap it in an HTTPException
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to find credential: {str(e)}"
            )

        # Revoke credential using DIDKit
        didkit = get_didkit_service()
        revocation_status = didkit.revoke_credential(
            credential_id=request.credential_id,
            proof_options=request.proof_options
        )

        # Log the operation
        log = CredentialLog(
            merchant_id=api_key.merchant_id,
            credential_type_id=cred_log.credential_type_id,
            operation="revoke",
            status="success",
            subject_did=cred_log.subject_did,
            log_metadata={"revocation_status": _serialize_for_json(revocation_status)},
            proof=revocation_status.get("proof", {})
        )
        db.add(log)
        await db.commit()

        # Convert SQLAlchemy model to dictionary for pydantic validation
        log_dict = {
            "id": log.id,
            "operation": log.operation,
            "status": log.status,
            "error": log.error,
            "log_metadata": log.log_metadata,
            "subject_did": log.subject_did,
            "proof": log.proof,
            "created_at": log.created_at
        }
        return CredentialOperationResponse.model_validate(log_dict)

    except Exception as e:
        # Get a default credential type if we don't have one
        if not cred_log:
            # If we're dealing with a not found error, don't try to log it to the database
            if isinstance(e, HTTPException) and e.status_code == status.HTTP_404_NOT_FOUND:
                raise e
                
            # Try to get a default credential type for logging
            try:
                default_type_result = await db.execute(
                    select(CredentialType).limit(1)
                )
                default_type = default_type_result.scalar_one_or_none()
                default_type_id = default_type.id if default_type else None
            except Exception:
                default_type_id = None
                
            if not default_type_id:
                # We can't log this error because we need a credential_type_id
                raise e
        
        # Log failed operation
        log = CredentialLog(
            merchant_id=api_key.merchant_id,
            credential_type_id=cred_log.credential_type_id if cred_log else default_type_id,
            operation="revoke",
            status="failed",
            subject_did=cred_log.subject_did if cred_log else "unknown",
            error=str(e),
            log_metadata={"credential_id": _serialize_for_json(request.credential_id)},
            proof={}
        )
        db.add(log)
        await db.commit()

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to revoke credential: {str(e)}"
        )
