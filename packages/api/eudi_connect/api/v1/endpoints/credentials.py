from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID
import json
import jsonschema
import logging

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, and_, desc
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import asyncio

from eudi_connect.api.deps import APIKeyAuth, DB
from eudi_connect.models.credential import CredentialLog, CredentialType
from eudi_connect.services.didkit import DIDKitService, get_didkit_service
from eudi_connect.services.notification import NotificationService
from eudi_connect.exceptions.credential import (
    CredentialTypeNotFoundError,
    CredentialSchemaValidationError,
    CredentialIssuanceError,
    CredentialVerificationError,
    CredentialNotFoundError,
    CredentialRevocationError,
    CredentialInvalidFormatError
)
from eudi_connect.api.v1.schemas.credential import (
    CredentialTypeResponse,
    CredentialIssueRequest,
    CredentialVerifyRequest,
    CredentialRevokeRequest,
    CredentialBatchRevokeRequest,
    CredentialBatchResponse,
    CredentialOperationResponse,
    CredentialListParams
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Maximum number of concurrent revocation operations
MAX_CONCURRENT_OPERATIONS = 10

@router.get("/logs", response_model=List[CredentialOperationResponse])
async def list_credential_logs(
    db: DB,
    api_key: APIKeyAuth,
    params: CredentialListParams = Depends()
) -> List[CredentialOperationResponse]:
    """
    List credential operation logs with optional filtering.
    
    Returns a paginated list of credential operation logs. Results can be filtered
    by subject DID, operation type, status, and credential type ID.
    """
    logger.info(f"Listing credential logs for merchant: {api_key.merchant_id}")
    
    try:
        # Build query filters
        filters = [CredentialLog.merchant_id == api_key.merchant_id]
        
        if params.subject_did:
            filters.append(CredentialLog.subject_did == params.subject_did)
            
        if params.operation:
            filters.append(CredentialLog.operation == params.operation.value)
            
        if params.status:
            filters.append(CredentialLog.status == params.status.value)
            
        if params.type_id:
            filters.append(CredentialLog.credential_type_id == params.type_id)
            
        # Execute query with filters, pagination, and ordering
        result = await db.execute(
            select(CredentialLog)
            .where(and_(*filters))
            .order_by(desc(CredentialLog.created_at))
            .offset(params.offset)
            .limit(params.limit)
        )
        logs = result.scalars().all()
        
        # Convert SQLAlchemy models to response format
        response_logs = []
        for log in logs:
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
            response_logs.append(
                CredentialOperationResponse.model_validate(log_dict)
            )
        
        logger.debug(f"Found {len(response_logs)} credential logs")
        return response_logs
        
    except Exception as e:
        logger.error(f"Error listing credential logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list credential logs: {str(e)}"
        )


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


# Old credential type response model removed - now using imported model from schemas


# Old credential issue request model removed - now using imported model from schemas


# Old credential verify request model removed - now using imported model from schemas


# Old credential revoke request model removed - now using imported model from schemas


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
async def get_credential_types(db: DB, api_key: APIKeyAuth) -> List[CredentialTypeResponse]:
    """Get all credential types available to the merchant."""
    logger.info(f"Fetching credential types for merchant: {api_key.merchant_id}")
    
    try:
        query = select(CredentialType).where(CredentialType.is_active == True)
        result = await db.execute(query)
        credential_types = result.scalars().all()

        response_models = []
        for c_type in credential_types:
            response_models.append(
                CredentialTypeResponse(
                    id=c_type.id,
                    name=c_type.name,
                    version=c_type.version,
                    context=c_type.context,
                    schema=c_type.schema,
                    is_active=c_type.is_active,
                    created_at=c_type.created_at
                )
            )
        
        logger.debug(f"Found {len(response_models)} active credential types")
        return response_models
        
    except Exception as e:
        logger.error(f"Error fetching credential types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch credential types: {str(e)}"
        )


@router.post("/issue", response_model=CredentialOperationResponse)
async def issue_credential(
    db: DB,
    api_key: APIKeyAuth,
    request: CredentialIssueRequest,
) -> CredentialOperationResponse:
    """Issue a new credential."""
    logger.info(f"Issuing credential for merchant: {api_key.merchant_id}, type: {request.type_id}, subject: {request.subject_did}")
    didkit_service = get_didkit_service()

    # Find the requested credential type
    try:
        result = await db.execute(
            select(CredentialType).where(
                CredentialType.id == request.type_id,
                CredentialType.is_active.is_(True)
            )
        )
        credential_type = result.scalar_one_or_none()
        
        if credential_type is None:
            raise CredentialTypeNotFoundError(str(request.type_id))
        
        # Validate claims against the credential type schema
        try:
            jsonschema.validate(instance=request.claims, schema=credential_type.schema)
        except jsonschema.exceptions.ValidationError as e:
            raise CredentialSchemaValidationError(str(e))
        
        # Create credential log entry
        credential_log = CredentialLog(
            merchant_id=api_key.merchant_id,
            credential_type_id=credential_type.id,
            operation="issue",
            status="processing",
            subject_did=request.subject_did,
            log_metadata={
                "claims": request.claims,
                "proof_options": request.proof_options or {},
            }
        )
        db.add(credential_log)
        await db.commit()
        
        try:
            # Issue the credential using DIDKit
            logger.debug(f"Calling DIDKit service to issue credential")
            credential_result = await didkit_service.issue_credential(
                types=["VerifiableCredential", credential_type.name],
                issuer=api_key.merchant_did,
                subject_id=request.subject_did,
                context=credential_type.context,
                claims=request.claims,
                proof_options=request.proof_options or {},
            )
            
            # Update the credential log with the issued credential proof
            credential_log.status = "completed"
            credential_log.proof = credential_result
            await db.commit()
            
            # Convert to response model
            result = {
                "id": credential_log.id,
                "operation": credential_log.operation,
                "status": credential_log.status,
                "error": None,
                "log_metadata": credential_log.log_metadata,
                "subject_did": credential_log.subject_did,
                "proof": credential_log.proof,
                "created_at": credential_log.created_at,
            }
            logger.info(f"Successfully issued credential with ID: {credential_log.id}")
            return CredentialOperationResponse.model_validate(result)
        except Exception as e:
            # Update the credential log with the error
            credential_log.status = "failed"
            credential_log.error = str(e)
            await db.commit()
            
            logger.error(f"Failed to issue credential: {str(e)}")
            raise CredentialIssuanceError(str(e))
    except (CredentialTypeNotFoundError, CredentialSchemaValidationError, CredentialIssuanceError) as e:
        # These exceptions are already properly formatted
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in issue_credential: {str(e)}")
        await db.commit()

        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to issue credential: {str(e)}"
        )


@router.post("/revoke", response_model=CredentialOperationResponse, status_code=status.HTTP_200_OK)
async def revoke_credential(
    db: DB,
    request: CredentialRevokeRequest,
    api_key: APIKeyAuth,
) -> CredentialOperationResponse:
    """Revoke a credential.

    Returns:
        A log of the revocation operation.
    """
    try:
        # Mock key and verification method for demo purposes
        # In production, these should be securely stored and accessed
        key = "-----BEGIN PRIVATE KEY-----\nMIGHAgEAMB...\n-----END PRIVATE KEY-----"
        verification_method = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK#z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
        
        # Placeholder for merchant identification - in production would be from auth
        merchant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        
        # Extract VID (uuid) from credential ID
        credential_id = request.credential_id
        credential_uuid = None
        
        # Try to extract a UUID from the credential ID if it's embedded
        # This is a common pattern: urn:uuid:00000000-0000-0000-0000-000000000000
        match = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', credential_id)
        if match:
            credential_uuid = uuid.UUID(match.group(1))    
        
        # Use a deterministic approach to generate index if none provided
        revocation_index = request.revocation_index
        if revocation_index is None:
            # Create a deterministic hash based on the credential ID
            # This ensures the same credential always gets the same index
            h = hashlib.sha256(credential_id.encode()).digest()
            # Use the first 4 bytes to create an integer index
            revocation_index = int.from_bytes(h[:4], byteorder='big') % 1000000
            
        subject_did = "did:example:subject"  # Placeholder
        issuer_did = "did:example:issuer"   # Placeholder
            
        # Initialize DIDKit service with a database session
        didkit_service = DIDKitService(db)
        
        # Get a unique credential type ID for revocation list management
        # In a real system, you'd determine this from the credential or your data
        credential_type_id = uuid.UUID("00000000-0000-0000-0000-000000000005")
        
        # Revoke the credential
        revocation_status_credential = await didkit_service.revoke_credential(
            credential_id=credential_id,
            issuer_did=issuer_did,
            credential_type_id=credential_type_id,
            revocation_index=revocation_index,
            key=key,
            verification_method=verification_method
        )
        
        # Log the operation
        log_entry = CredentialLog(
            id=uuid.uuid4(),
            merchant_id=merchant_id,
            credential_type_id=credential_type_id,
            operation=CredentialOperation.REVOKE.value,
            status=CredentialStatus.SUCCESS.value,
            subject_did=subject_did,
            log_metadata={
                "credential_id": credential_id,
                "revocation_index": revocation_index,
                "reason": request.reason
            },
            proof=json.loads(revocation_status_credential),
        )
        
        db.add(log_entry)
        await db.commit()
        
        # Send notification if webhook is configured
        notification_service = NotificationService(db)
        await notification_service.send_revocation_notification(log_entry)
        
        return log_entry
    except Exception as e:
        # Log failure
        log_entry = CredentialLog(
            id=uuid.uuid4(),
            merchant_id=merchant_id if "merchant_id" in locals() else uuid.UUID("00000000-0000-0000-0000-000000000001"),
            credential_type_id=credential_type_id if "credential_type_id" in locals() else uuid.UUID("00000000-0000-0000-0000-000000000005"),
            operation=CredentialOperation.REVOKE.value,
            status=CredentialStatus.FAILED.value,
            subject_did=subject_did if "subject_did" in locals() else "unknown",
            log_metadata={"error": str(e), "credential_id": request.credential_id},
            proof={},
        )
        
        db.add(log_entry)
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke credential: {str(e)}"
        )


@router.post("/batch/revoke", response_model=CredentialBatchResponse, status_code=status.HTTP_200_OK)
async def batch_revoke_credentials(
    db: DB,
    request: CredentialBatchRevokeRequest,
    api_key: APIKeyAuth,
) -> CredentialBatchResponse:
    """Revoke multiple credentials in a batch.

    Returns:
        A batch response containing logs for each revocation operation.
    """
    # Mock key and verification method for demo purposes
    # In production, these should be securely stored and accessed
    key = "-----BEGIN PRIVATE KEY-----\nMIGHAgEAMB...\n-----END PRIVATE KEY-----"
    verification_method = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK#z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
    
    # Placeholder for merchant identification - in production would be from auth
    merchant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    # Initialize DIDKit service with a database session
    didkit_service = DIDKitService(db)
    
    # Get a unique credential type ID for revocation list management
    # In a real system, you'd determine this from the credential or your data
    credential_type_id = uuid.UUID("00000000-0000-0000-0000-000000000005")
    
    # Subject and issuer placeholders - in production these would be derived from the credentials
    subject_did = "did:example:subject"  # Placeholder
    issuer_did = "did:example:issuer"   # Placeholder
    
    # Create log entries for each operation
    log_entries = []
    
    # Use a semaphore to limit concurrent operations
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_OPERATIONS)
    
    # Create a task for each credential revocation
    async def process_credential(item):
        async with semaphore:
            try:
                # Extract credential ID
                credential_id = item.credential_id
                
                # Use provided revocation index or generate one deterministically
                revocation_index = item.revocation_index
                if revocation_index is None:
                    # Create a deterministic hash based on the credential ID
                    h = hashlib.sha256(credential_id.encode()).digest()
                    # Use the first 4 bytes to create an integer index
                    revocation_index = int.from_bytes(h[:4], byteorder='big') % 1000000
                
                # Revoke the credential
                revocation_status_credential = await didkit_service.revoke_credential(
                    credential_id=credential_id,
                    issuer_did=issuer_did,
                    credential_type_id=credential_type_id,
                    revocation_index=revocation_index,
                    key=key,
                    verification_method=verification_method
                )
                
                # Create success log entry
                log_entry = CredentialLog(
                    id=uuid.uuid4(),
                    merchant_id=merchant_id,
                    credential_type_id=credential_type_id,
                    operation=CredentialOperation.REVOKE.value,
                    status=CredentialStatus.SUCCESS.value,
                    subject_did=subject_did,
                    log_metadata={
                        "credential_id": credential_id,
                        "revocation_index": revocation_index,
                        "reason": item.reason,
                        "batch_operation": True
                    },
                    proof=json.loads(revocation_status_credential),
                )
                
                return log_entry
            except Exception as e:
                # Create failure log entry
                log_entry = CredentialLog(
                    id=uuid.uuid4(),
                    merchant_id=merchant_id,
                    credential_type_id=credential_type_id,
                    operation=CredentialOperation.REVOKE.value,
                    status=CredentialStatus.FAILED.value,
                    subject_did=subject_did,
                    log_metadata={
                        "error": str(e),
                        "credential_id": item.credential_id,
                        "batch_operation": True
                    },
                    proof={},
                )
                
                return log_entry
    
    # Process all credentials concurrently with limited parallelism
    tasks = [process_credential(item) for item in request.credentials]
    log_entries = await asyncio.gather(*tasks)
    
    # Add all log entries to the database
    db.add_all(log_entries)
    await db.commit()
    
    # Prepare summary statistics
    total = len(log_entries)
    successful = sum(1 for log in log_entries if log.status == CredentialStatus.SUCCESS.value)
    failed = total - successful
    
    # Group by reason if applicable
    reasons = defaultdict(int)
    for log in log_entries:
        if log.status == CredentialStatus.SUCCESS.value and "reason" in log.log_metadata and log.log_metadata["reason"]:
            reasons[log.log_metadata["reason"]] += 1
    
    summary = {
        "total": total,
        "successful": successful,
        "failed": failed,
        "reasons": dict(reasons)
    }
    
    # Send batch notification if webhooks are configured
    notification_service = NotificationService(db)
    
    # Send individual notifications with batch flag
    for log_entry in log_entries:
        if log_entry.status == CredentialStatus.SUCCESS.value:
            # Non-blocking notification send to avoid delaying the response
            asyncio.create_task(notification_service.send_revocation_notification(
                log_entry, is_batch=True
            ))
    
    # Also send an aggregate batch notification
    log_ids = [log.id for log in log_entries]
    asyncio.create_task(notification_service.send_batch_revocation_notification(
        merchant_id, summary, log_ids
    ))
    
    # Return batch response
    return CredentialBatchResponse(
        results=log_entries,
        summary=summary
    )


@router.post("/revoke", response_model=CredentialOperationResponse)
async def revoke_credential(
    db: DB,
    api_key: APIKeyAuth,
    request: CredentialRevokeRequest,
    didkit_service: DIDKitService = Depends(get_didkit_service),
) -> CredentialOperationResponse:
    """Revoke a credential."""
    logger.info(f"Revoking credential for merchant: {api_key.merchant_id}, credential ID: {request.credential_id}")
    didkit_service = didkit_service or get_didkit_service()
    
    try:
        # Validate credential ID
        if not request.credential_id:
            raise CredentialInvalidFormatError("Credential ID is required")
        
        # Look up the credential log to verify it exists and belongs to this merchant
        try:
            result = await db.execute(
                select(CredentialLog)
                .where(
                    CredentialLog.id == request.credential_id,
                    CredentialLog.merchant_id == api_key.merchant_id,
                    CredentialLog.operation == "issue",
                    CredentialLog.status == "completed"
                )
            )
            credential_log = result.scalar_one_or_none()
            
            if not credential_log:
                raise CredentialNotFoundError(request.credential_id)
                
        except CredentialNotFoundError as e:
            # Re-raise as is
            raise e
        except Exception as e:
            # Wrap other database errors
            logger.error(f"Database error looking up credential: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error accessing credential database: {str(e)}"
            )
        
        # Get the credential_type_id from the found credential log
        credential_type_id = credential_log.credential_type_id
        
        # Check if a revocation index was provided, if not generate one
        revocation_index = request.revocation_index
        if revocation_index is None:
            # If no index is provided, use a deterministic method to generate one
            # This example uses a hash of the credential ID modulo 10000 as a simple approach
            # In production, you might want to use a more sophisticated method
            import hashlib
            credential_id_hash = hashlib.sha256(str(credential_log.id).encode()).hexdigest()
            revocation_index = int(credential_id_hash, 16) % 10000
            logger.debug(f"Generated revocation index {revocation_index} for credential {credential_log.id}")
            
        # Create revocation log entry
        revocation_log = CredentialLog(
            merchant_id=api_key.merchant_id,
            credential_type_id=credential_type_id,
            operation="revoke",
            status="processing",
            subject_did=credential_log.subject_did,
            log_metadata={
                "original_credential_id": str(credential_log.id),
                "proof_options": request.proof_options or {},
                "revocation_index": revocation_index,
                "reason": request.reason
            }
        )
        db.add(revocation_log)
        await db.commit()
        
        try:
            # Get or create a key and verification method for revocation
            # In a production system, these would be stored securely and retrieved
            # This is a simplified approach
            key = "fake_key_for_demo"  # In production: retrieve from secure storage
            verification_method = f"{api_key.merchant_did}#keys-1"  # In production: proper key reference
            
            # Revoke credential using DIDKit with persistent storage
            logger.debug(f"Calling DIDKit service to revoke credential with index {revocation_index}")
            revocation_status = await didkit_service.revoke_credential(
                credential_id=str(credential_log.id),
                issuer_did=api_key.merchant_did,
                credential_type_id=credential_type_id,
                revocation_index=revocation_index,
                key=key,
                verification_method=verification_method
            )
            
            # Update the revocation log with result
            revocation_log.status = "completed"
            revocation_log.log_metadata["revocation_status"] = revocation_status
            revocation_log.proof = json.loads(revocation_status).get("proof", {})
            await db.commit()
            
            # Convert to response model
            result = {
                "id": revocation_log.id,
                "operation": revocation_log.operation,
                "status": revocation_log.status,
                "error": revocation_log.error,
                "log_metadata": revocation_log.log_metadata,
                "subject_did": revocation_log.subject_did,
                "proof": revocation_log.proof,
                "created_at": revocation_log.created_at,
            }
            
            logger.info(f"Successfully revoked credential with ID: {request.credential_id} at index {revocation_index}")
            return CredentialOperationResponse.model_validate(result)
            
        except Exception as e:
            # Update the revocation log with the error
            revocation_log.status = "failed"
            revocation_log.error = str(e)
            await db.commit()
            
            logger.error(f"Failed to revoke credential: {str(e)}")
            raise CredentialRevocationError(str(e))
            
    except (CredentialNotFoundError, CredentialInvalidFormatError, CredentialRevocationError) as e:
        # These exceptions are already properly formatted
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in revoke_credential: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
