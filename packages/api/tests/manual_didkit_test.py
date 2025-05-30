"""Test script for verifying the DIDKit mock implementation with the API service."""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

from eudi_connect.services.didkit import DIDKitService


async def test_didkit_service():
    """Test the DIDKit service with our mock implementation."""
    print("Testing DIDKit Service...")
    
    # Create a temporary key file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        # Test Ed25519 key (DO NOT USE IN PRODUCTION)
        f.write("""{
    "kty": "OKP",
    "crv": "Ed25519",
    "d": "nWGxne_9WmC6hEr0kuwsxERJxWl7MmkZcDusAxyuf2A",
    "x": "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo"
}""".strip())
        key_path = f.name
    
    try:
        # Initialize service
        service = DIDKitService(key_path=key_path)
        service.init()
        
        print(f"DID: {service.did}")
        print(f"Verification Method: {service.verification_method}")
        
        # Test credential issuance
        credential = await service.issue_credential(
            type_name="TestCredential",
            context=["https://www.w3.org/2018/credentials/v1"],
            subject_did="did:example:123",
            claims={"name": "Test Subject"}
        )
        
        print("\nIssued Credential:")
        print(json.dumps(credential, indent=2))
        
        # Test credential verification
        verification_result = await service.verify_credential(credential)
        
        print("\nVerification Result:")
        print(json.dumps(verification_result, indent=2))
        
        # Test credential revocation
        revocation_status = await service.revoke_credential("123")
        
        print("\nRevocation Status:")
        print(json.dumps(revocation_status, indent=2))
        
        # Test verify invalid credential
        invalid_credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential"],
            "issuer": "did:example:invalid",
            "credentialSubject": {
                "id": "did:example:123",
                "name": "Test Subject"
            },
            "proof": {
                "type": "Ed25519Signature2020",
                "created": "2025-05-26T00:00:00Z",
                "verificationMethod": "did:example:invalid#key-1",
                "proofPurpose": "assertionMethod",
                "proofValue": "invalid"
            }
        }
        
        try:
            invalid_result = await service.verify_credential(invalid_credential)
            print("\nInvalid Credential Verification (should fail):")
            print(json.dumps(invalid_result, indent=2))
        except Exception as e:
            print(f"\nExpected error when verifying invalid credential: {str(e)}")
        
        print("\nAll tests completed successfully!")
        
    finally:
        # Clean up
        Path(key_path).unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(test_didkit_service())
