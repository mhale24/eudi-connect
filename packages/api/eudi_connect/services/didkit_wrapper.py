"""Test-friendly mock implementation of DIDKit library functions.

WARNING: THIS IS A MOCK IMPLEMENTATION FOR TESTING ONLY.

This module provides mock implementations of the DIDKit library functions to enable
testing without requiring the actual DIDKit library or dealing with its asynchronous
nature. The implementation simulates the expected behavior of the DIDKit library
but does not perform any actual cryptographic operations.

For production use, this should be replaced with:  
1. A fixed async implementation of the DIDKit Python binding
2. A subprocess-based approach using the DIDKit CLI
3. A completely different DID/VC library with better Python support

Security Implications:
- Does not perform actual cryptographic verification
- Does not validate signatures cryptographically
- Should never be used in production environments
- Not compliant with eIDAS 2 requirements for real deployments

Last modified: 2025-05-26
"""
import json
from typing import Any, Dict
import uuid

# Mock implementation for testing purposes
# This avoids issues with async operations and doesn't require the actual DIDKit library

def key_to_did(method: str, key: str) -> str:
    """Convert a key to a DID.
    
    This is a mock implementation that creates a deterministic DID based on the key data.
    In a real implementation, this would perform proper cryptographic operations to derive
    the DID from the key material according to the specified method.
    
    Args:
        method: The DID method to use (e.g., "key", "web", etc.)
        key: A JSON string containing the cryptographic key material
        
    Returns:
        A DID string in the format "did:<method>:<identifier>"
    """
    # For testing, we just create a deterministic DID based on the method
    # In a real implementation, this would actually parse the key and generate a proper DID
    try:
        key_data = json.loads(key)
        if "x" in key_data:
            x_val = key_data["x"]
            # Use part of the x value to create a deterministic DID
            return f"did:{method}:z{x_val[:8]}"
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    
    # Fallback to a simple mock implementation
    return f"did:{method}:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"

def key_to_verification_method(method: str, key: str) -> str:
    """Convert a key to a verification method.
    
    This is a mock implementation that generates a verification method ID based on the DID.
    In a real implementation, this would extract the public key from the key material and
    properly format it according to the W3C Verifiable Credentials Data Model.
    
    Args:
        method: The DID method to use (e.g., "key", "web", etc.)
        key: A JSON string containing the cryptographic key material
        
    Returns:
        A verification method ID string in the format "<did>#keys-1"
    """
    # Generate a verification method based on the DID
    did = key_to_did(method, key)
    return f"{did}#keys-1"

def issue_credential(
    credential_str: str,
    proof_options_str: str,
    key: str
) -> str:
    """Issue a credential by adding a proof.
    
    This is a mock implementation that simply adds a static proof to the credential.
    In a real implementation, this would use the key to cryptographically sign the credential
    and generate a proper proof with a valid signature.
    
    For eIDAS 2 compliance in production, a real implementation would ensure proper
    cryptographic signing according to the required standards.
    
    Args:
        credential_str: A JSON string containing the unsigned credential
        proof_options_str: A JSON string containing options for the proof
        key: A JSON string containing the cryptographic key material
        
    Returns:
        A JSON string containing the signed credential with proof
        
    Raises:
        ValueError: If the credential or proof options are invalid JSON
    """
    try:
        # Parse the credential and add a proof
        credential = json.loads(credential_str)
        proof_options = json.loads(proof_options_str)
        
        # Create a verification method based on the key
        verification_method = key_to_verification_method("key", key)
        
        # Add a mock proof to the credential
        credential["proof"] = {
            "type": "Ed25519Signature2020",
            "created": proof_options.get("created", "2025-05-26T00:00:00Z"),
            "verificationMethod": verification_method,
            "proofPurpose": proof_options.get("proofPurpose", "assertionMethod"),
            "proofValue": "z3EG4RQBGdax3JKdAr7QT1PRdNgbTEPrYCeL9Vpskk53yD1vxn3LW3tecp6yrLQqG7b3zTm32ky5QyPujFYtcSgfa"
        }
        
        return json.dumps(credential)
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Invalid credential or proof options: {str(e)}")

def verify_credential(
    credential_str: str,
    proof_options_str: str
) -> str:
    """Verify a credential's proof.
    
    This is a mock implementation that checks for the presence of a proof and basic issuer format.
    In a real implementation, this would cryptographically verify the signature in the proof
    against the issuer's public key according to the verification method.
    
    For eIDAS 2 compliance in production, a real implementation would perform proper
    cryptographic verification according to the required standards.
    
    Args:
        credential_str: A JSON string containing the credential with proof to verify
        proof_options_str: A JSON string containing options for the verification
        
    Returns:
        A JSON string containing the verification result with the following structure:
        {
            "verified": boolean,
            "checks": [list of checks performed],
            "warnings": [list of warnings],
            "errors": [list of errors if any]
        }
    """
    try:
        # Parse the credential
        credential = json.loads(credential_str)
        
        # Check if it has a proof
        if "proof" not in credential:
            # Return failure
            return json.dumps({
                "verified": False,
                "checks": [],
                "warnings": [],
                "errors": ["Credential does not contain a proof"]
            })
        
        # Check for invalid proof values or issuers
        if "invalid" in str(credential.get("issuer", "")) or \
           "invalid" == str(credential.get("proof", {}).get("proofValue", "")):
            return json.dumps({
                "verified": False,
                "checks": [],
                "warnings": [],
                "errors": ["Invalid signature"]
            })
        
        # Otherwise, verify if it's a proper DID format
        if isinstance(credential.get("issuer", ""), str) and credential.get("issuer", "").startswith("did:"):
            # Return success
            return json.dumps({
                "verified": True,
                "checks": ["proof"],
                "warnings": [],
                "errors": []
            })
        else:
            # Return failure
            return json.dumps({
                "verified": False,
                "checks": [],
                "warnings": [],
                "errors": ["Invalid issuer"]
            })
    except (json.JSONDecodeError, KeyError) as e:
        # Return error
        return json.dumps({
            "verified": False,
            "checks": [],
            "warnings": [],
            "errors": [f"Invalid credential: {str(e)}"]
        })
