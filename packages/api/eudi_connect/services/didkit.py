"""DIDKit service for credential operations."""
import json
import logging
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException, status

from eudi_connect.core.config import settings
from eudi_connect.services import didkit_wrapper
from eudi_connect.services.cache import get_cache_service
from eudi_connect.models.revocation import RevocationList

logger = logging.getLogger(__name__)

class DIDKitService:
    """Service for handling DIDKit operations."""

    def __init__(self, key_path: str | None = None):
        """Initialize DIDKit service.

        Args:
            key_path: Path to key file, defaults to settings.DIDKIT_KEY_PATH
        """
        logger.debug(f"DIDKitService.__init__ received key_path={key_path}")
        logger.debug(f"Current settings.DIDKIT_KEY_PATH={settings.DIDKIT_KEY_PATH}")
        
        self.key_path = key_path or settings.DIDKIT_KEY_PATH
        logger.debug(f"DIDKitService will use key_path={self.key_path}")
        
        # Check if file exists
        key_file = Path(self.key_path)
        logger.debug(f"Key file exists: {key_file.exists()}, absolute path: {key_file.absolute()}")
        
        self.key = ""
        self.did = None
        self.verification_method = None
        self._initialized = False

    def init(self):
        """Initialize DID and verification method synchronously."""
        logger.debug(f"DIDKitService.init() called, _initialized={self._initialized}")
        if self._initialized:
            logger.debug("DIDKitService already initialized, skipping init")
            return
            
        # Load key
        try:
            logger.debug(f"Attempting to load key from {self.key_path}")
            key_file = Path(self.key_path)
            logger.debug(f"Key file exists: {key_file.exists()}, absolute path: {key_file.absolute()}")
            
            with open(self.key_path, "r") as f:
                self.key = f.read().strip()
                logger.debug(f"Key loaded, length: {len(self.key)}, first 10 chars: {self.key[:10] if self.key else 'EMPTY'}")
        except Exception as e:
            logger.error(f"Failed to load DIDKit key: {e}")
            # Log the current directory for context
            logger.error(f"Current working directory: {Path.cwd()}")
            raise ValueError(f"Failed to load DIDKit key: {e}")

        # Get DID from key
        try:
            logger.debug("Attempting to generate DID from key")
            self.did = didkit_wrapper.key_to_did("key", self.key)
            logger.debug(f"Generated DID: {self.did}")
        except Exception as e:
            logger.error(f"Failed to get DID from key: {e}")
            logger.error(f"Key length: {len(self.key)}, first 10 chars: {self.key[:10] if self.key else 'EMPTY'}")
            raise ValueError(f"Failed to get DID from key: {e}")

        # Get verification method
        try:
            logger.debug("Attempting to generate verification method from key")
            self.verification_method = didkit_wrapper.key_to_verification_method("key", self.key)
            logger.debug(f"Generated verification method: {self.verification_method}")
            self._initialized = True
            logger.debug("DIDKitService initialization complete")
        except Exception as e:
            logger.error(f"Failed to get verification method: {e}")
            logger.error(f"DID: {self.did}, Key length: {len(self.key)}")
            raise ValueError(f"Failed to get verification method: {e}")

    async def async_init(self):
        """Initialize DID and verification method asynchronously."""
        # For now, just call the synchronous version since the operations are quick
        # In a production environment, this could be made truly async
        if not self._initialized:
            self.init()

    def _prepare_credential(
        self,
        type_name: str,
        context: list[str],
        subject_did: str,
        claims: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare a credential for signing.

        Args:
            type_name: Credential type name
            context: JSON-LD context
            subject_did: Subject DID
            claims: Credential claims

        Returns:
            Prepared credential
        """
        return {
            "@context": context,
            "type": ["VerifiableCredential", type_name],
            "issuer": self.did,
            "issuanceDate": datetime.now(timezone.utc).isoformat(),
            "credentialSubject": {
                "id": subject_did,
                **claims
            }
        }

    def _prepare_proof_options(
        self,
        proof_options: Dict[str, Any] | None = None
    ) -> str:
        """Prepare proof options for credential issuance.

        Args:
            proof_options: Optional proof options

        Returns:
            Proof options as JSON string
        """
        # Default proof options
        options = {
            "verificationMethod": self.verification_method,
            "proofPurpose": "assertionMethod",
            "created": datetime.now(timezone.utc).isoformat(),
        }

        # Add custom options
        if proof_options:
            options.update(proof_options)

        return json.dumps(options)

    def issue_credential(
        self,
        credential_or_type_name=None,
        context: list[str] = None,
        subject_did: str = None,
        claims: Dict[str, Any] = None,
        credential: Dict[str, Any] = None,
        proof_options: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        logger.debug(f"DIDKitService.issue_credential called with type={credential_or_type_name}, subject_did={subject_did}")
        """Issue a credential.

        Args:
            credential_or_type_name: Either a credential dict or type name string
            context: JSON-LD context (used only if credential_or_type_name is a string)
            subject_did: Subject DID (used only if credential_or_type_name is a string)
            claims: Credential claims (used only if credential_or_type_name is a string)
            credential: Alternative way to pass credential (if not using first parameter)
            proof_options: Optional proof options.

        Returns:
            The signed credential.

        Raises:
            HTTPException: If issuance fails
        """
        # Make sure DID and verification method are initialized
        if self.did is None or self.verification_method is None:
            self.init()
        try:
            # Handle the case where credential is passed as first parameter
            credential_to_sign = None
            
            # First check if first parameter is a credential (dict with @context)
            if isinstance(credential_or_type_name, dict) and "@context" in credential_or_type_name:
                credential_to_sign = credential_or_type_name
            # Next check if credential is provided as a named parameter
            elif credential is not None:
                credential_to_sign = credential
            # Finally, try to build credential from individual fields
            elif isinstance(credential_or_type_name, str) and context and subject_did and claims:
                credential_to_sign = self._prepare_credential(
                    type_name=credential_or_type_name,
                    context=context,
                    subject_did=subject_did,
                    claims=claims
                )
            else:
                raise ValueError("Invalid credential parameters provided")
                
            # Convert to JSON strings
            credential_str = json.dumps(credential_to_sign)
            proof_options_str = self._prepare_proof_options(proof_options)

            # Issue credential
            signed_credential = didkit_wrapper.issue_credential(
                credential_str,
                proof_options_str,
                self.key
            )

            # Parse and return
            return json.loads(signed_credential)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to issue credential: {str(e)}"
            )

    async def check_revocation_status(self, issuer_did: str, credential_type_id: str, revocation_index: int) -> bool:
        """Check if a credential has been revoked.

        Args:
            issuer_did: The DID of the credential issuer
            credential_type_id: The type of the credential
            revocation_index: The index in the revocation list

        Returns:
            True if revoked, False otherwise
        """
        # Get the cache service
        cache = get_cache_service()
        
        # Generate a cache key for this revocation check
        cache_key = f"revocation:{issuer_did}:{credential_type_id}:{revocation_index}"
        
        # Try to get the result from cache first
        cached_result = await cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for revocation status check: {cache_key}")
            return cached_result
            
        logger.debug(f"Cache miss for revocation status check: {cache_key}")
        
        try:
            # Get the revocation list for this issuer and credential type
            # Note: This would need to be implemented with proper database query
            # For now, we'll return False (not revoked) as a placeholder
            revocation_list = None  # TODO: Implement database query for RevocationList
            
            if not revocation_list:
                # No revocation list exists, so credential is not revoked
                # Cache this result for a longer time (1 hour) as it's unlikely to change soon
                await cache.set(cache_key, False, ttl=3600)
                return False
                
            # Decompress the bitstring
            bitstring = zlib.decompress(revocation_list.encoded_list)
            
            # Check the bit at the specified index
            byte_index = revocation_index // 8
            bit_position = revocation_index % 8
            
            # If the index is beyond our current bitstring length, it's not revoked
            if byte_index >= len(bitstring):
                # Cache this result (15 minutes)
                await cache.set(cache_key, False, ttl=900)
                return False
                
            # Check if the bit is set
            is_revoked = bool((bitstring[byte_index] >> bit_position) & 1)
            
            # Cache the result - use different TTLs based on status
            # Revoked credentials should be cached longer (1 hour) as they won't change
            # Non-revoked might become revoked, so cache for shorter time (5 minutes)
            ttl = 3600 if is_revoked else 300
            await cache.set(cache_key, is_revoked, ttl=ttl)
            
            return is_revoked
            
        except Exception as e:
            # Log the error but don't fail the check - assume not revoked
            logger.error(f"Error checking revocation status: {e}")
            # Don't cache errors
            return False

    def verify_credential(
        self,
        credential: Dict[str, Any],
        proof_options: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        logger.debug(f"DIDKitService.verify_credential called with credential type={credential.get('type', 'Unknown')}")
        """Verify a credential.

        Args:
            credential: Credential to verify
            proof_options: Optional proof options

        Returns:
            Verification result

        Raises:
            HTTPException: If verification fails
        """
        # Make sure DID and verification method are initialized
        if self.did is None or self.verification_method is None:
            self.init()
        try:
            # Prepare credential and proof options
            credential_str = json.dumps(credential)
            proof_options_str = self._prepare_proof_options(proof_options)

            # Verify credential
            result = didkit_wrapper.verify_credential(
                credential_str,
                proof_options_str
            )

            # Parse verification result
            try:
                verification_result = json.loads(result)
                assert isinstance(verification_result, dict)
                return verification_result
            except (json.JSONDecodeError, AssertionError) as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid verification result format: {str(e)}"
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to verify credential: {str(e)}"
            )

    def revoke_credential(
        self,
        credential_id: str,
        proof_options: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """Revoke a credential.

        Args:
            credential_id: ID of credential to revoke
            proof_options: Optional proof options

        Returns:
            Revocation status

        Raises:
            HTTPException: If revocation fails
        """
        # Make sure DID and verification method are initialized
        if self.did is None or self.verification_method is None:
            self.init()
        try:
            # Create revocation status credential
            revocation_status = {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://w3id.org/vc-revocation-list-2020/v1"
                ],
                "type": ["VerifiableCredential", "RevocationList2020Credential"],
                "issuer": self.did,
                "issuanceDate": datetime.now(timezone.utc).isoformat(),
                "credentialSubject": {
                    "id": f"urn:uuid:{credential_id}",
                    "type": "RevocationList2020",
                    "encodedList": "H4sIAAAAAAAA...",  # TODO: Implement proper revocation list
                    "revocationListIndex": "0"
                }
            }

            # Sign revocation status
            status_str = json.dumps(revocation_status)
            proof_options_str = self._prepare_proof_options(proof_options)
            signed_status = didkit_wrapper.issue_credential(
                status_str,
                proof_options_str,
                self.key
            )

            # Parse revocation status
            try:
                status_result = json.loads(signed_status)
                assert isinstance(status_result, dict)
                return status_result
            except (json.JSONDecodeError, AssertionError) as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid revocation status format: {str(e)}"
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to revoke credential: {str(e)}"
            )


# Create service instance lazily
_didkit_service = None

def get_didkit_service() -> DIDKitService:
    """Get or create DIDKit service instance."""
    global _didkit_service
    logger.debug(f"get_didkit_service called, existing instance: {_didkit_service is not None}")
    if _didkit_service is None:
        logger.debug("Creating new DIDKitService instance")
        _didkit_service = DIDKitService()
        logger.debug("Initializing new DIDKitService instance")
        _didkit_service.init()  # Initialize synchronously on first access
    return _didkit_service
