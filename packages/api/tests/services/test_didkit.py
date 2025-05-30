"""Tests for DIDKit service."""
import json
import asyncio
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import pytest
from fastapi import HTTPException

from eudi_connect.services.didkit import DIDKitService



@pytest.fixture
def event_loop():
    """Create an event loop for each test case."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture
def didkit_service(event_loop) -> DIDKitService:
    """Create a test DIDKit service."""
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
        service = DIDKitService(key_path=key_path)
        service.init()
        yield service
    finally:
        Path(key_path).unlink()


def test_didkit_service_init(didkit_service: DIDKitService) -> None:
    """Test DIDKit service initialization."""
    # Test DID and verification method
    assert didkit_service.did is not None
    assert didkit_service.did.startswith("did:key:")
    assert didkit_service.verification_method is not None
    assert didkit_service.verification_method.startswith("did:key:")


def test_prepare_credential(didkit_service: DIDKitService) -> None:
    """Test credential preparation."""
    type_name = "TestCredential"
    context = ["https://www.w3.org/2018/credentials/v1"]
    subject_did = "did:web:test.com"
    claims = {"name": "Test Subject"}

    credential = didkit_service._prepare_credential(
        type_name=type_name,
        context=context,
        subject_did=subject_did,
        claims=claims
    )

    assert credential["@context"] == context
    assert credential["type"] == ["VerifiableCredential", type_name]
    assert credential["issuer"] == didkit_service.did
    assert "issuanceDate" in credential
    assert credential["credentialSubject"] == {"id": subject_did, **claims}


def test_prepare_proof_options(didkit_service: DIDKitService) -> None:
    """Test proof options preparation."""
    proof_options = {
        "created": datetime.now(timezone.utc).isoformat(),
        "domain": "example.com",
        "challenge": "123",
    }

    # Test with custom options
    result = didkit_service._prepare_proof_options(proof_options)
    assert isinstance(result, str)
    result_dict = json.loads(result)
    assert "created" in result_dict
    assert "domain" in result_dict
    assert "challenge" in result_dict

    # Test with default options
    result = didkit_service._prepare_proof_options(None)
    assert isinstance(result, str)
    result_dict = json.loads(result)
    assert "created" in result_dict
    assert "verificationMethod" in result_dict
    assert result_dict["verificationMethod"] == didkit_service.verification_method
    assert result_dict["proofPurpose"] == "assertionMethod"


def test_issue_credential(didkit_service: DIDKitService):
    """Test issuing a credential."""
    # Test credential
    credential = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1"
        ],
        "type": ["VerifiableCredential", "TestCredential"],
        "issuer": didkit_service.did,
        "issuanceDate": "2023-01-01T00:00:00Z",
        "credentialSubject": {
            "id": "did:example:123",
            "test": "value"
        }
    }

    # Issue credential
    signed = didkit_service.issue_credential(credential)

    # Check credential
    assert signed["@context"] == credential["@context"]
    assert signed["type"] == credential["type"]
    assert signed["issuer"] == credential["issuer"]
    assert signed["issuanceDate"] == credential["issuanceDate"]
    assert signed["credentialSubject"] == credential["credentialSubject"]
    assert "proof" in signed
    assert signed["proof"]["type"] == "Ed25519Signature2020"
    assert signed["proof"]["verificationMethod"] == didkit_service.verification_method


def test_verify_credential(didkit_service: DIDKitService) -> None:
    """Test credential verification."""
    # First prepare and issue a credential
    credential = didkit_service._prepare_credential(
        type_name="TestCredential",
        context=["https://www.w3.org/2018/credentials/v1"],
        subject_did="did:web:test.com",
        claims={"name": "Test Subject"}
    )

    # Issue the credential
    try:
        signed_credential = didkit_service.issue_credential(credential)

        # Verify credential
        result = didkit_service.verify_credential(signed_credential)

        # Check result
        assert isinstance(result, dict)
        assert "checks" in result
        assert "warnings" in result
        assert "errors" in result
        assert result["verified"] is True
    except HTTPException as e:
        pytest.fail(f"Failed to verify credential: {e.detail}")


def test_verify_invalid_credential(didkit_service: DIDKitService) -> None:
    """Test invalid credential verification."""
    # Create an invalid credential
    invalid_credential = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential"],
        "issuer": "did:example:invalid",
        "issuanceDate": datetime.now(timezone.utc).isoformat(),
        "credentialSubject": {
            "id": "did:example:123",
            "name": "Test Subject"
        },
        "proof": {
            "type": "Ed25519Signature2018",
            "created": "2025-05-26T14:30:00Z",
            "verificationMethod": "did:example:invalid#key-1",
            "proofPurpose": "assertionMethod",
            "jws": "invalid_signature"
        }
    }

    try:
        # Verify the invalid credential
        result = didkit_service.verify_credential(invalid_credential)

        # Check verification result
        assert isinstance(result, dict)
        assert "verified" in result
        assert result["verified"] is False
    except HTTPException as e:
        # We expect an error for invalid credentials
        assert e.status_code == 400


def test_revoke_credential(didkit_service: DIDKitService) -> None:
    """Test credential revocation."""
    credential_id = "urn:uuid:123"

    try:
        status = didkit_service.revoke_credential(credential_id)

        # Check revocation status
        assert isinstance(status, dict)
        assert "@context" in status
        assert "type" in status
        assert "credentialSubject" in status
        assert status["credentialSubject"]["id"] == f"urn:uuid:{credential_id}"
        assert "proof" in status
        assert isinstance(status["proof"], dict)
    except HTTPException as e:
        pytest.fail(f"Failed to revoke credential: {e.detail}")
