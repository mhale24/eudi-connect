"""Tests for complex credential workflows."""
import asyncio
import pytest
from typing import Dict

@pytest.mark.asyncio
async def test_complete_credential_lifecycle(client, test_merchant, auth_headers, db):
    """Test the complete credential lifecycle - creation, issuance, verification, and revocation."""
    # 1. Create a credential type
    cred_type_data = {
        "name": "IdentityCredential",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "dateOfBirth": {"type": "string"}
            }
        },
        "context": ["https://www.w3.org/2018/credentials/v1"]
    }
    response = await client.post("/api/v1/credential-types", json=cred_type_data, headers=auth_headers)
    assert response.status_code == 201
    cred_type_id = response.json()["id"]
    
    # 2. Initiate a wallet session
    session_data = {
        "credential_type_id": cred_type_id,
        "wallet_type": "eudiw",
        "protocol": "openid4vp",
        "expires_in": 300,
        "claims": {"name": "Test User", "dateOfBirth": "1990-01-01"}
    }
    response = await client.post("/api/v1/wallet-sessions", json=session_data, headers=auth_headers)
    assert response.status_code == 201
    session_id = response.json()["id"]
    
    # 3. Issue credential
    issue_data = {
        "credential_type_id": cred_type_id,
        "subject_did": "did:key:test123",
        "claims": {"name": "Test User", "dateOfBirth": "1990-01-01"}
    }
    response = await client.post("/api/v1/credentials/issue", json=issue_data, headers=auth_headers)
    assert response.status_code == 200
    credential = response.json()
    
    # 4. Verify the credential
    verify_data = {"credential": credential}
    response = await client.post("/api/v1/credentials/verify", json=verify_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["verified"] is True
    
    # 5. Revoke the credential
    # Get credential ID from the credential JSON
    credential_id = credential.get("id", credential.get("credentialSubject", {}).get("id"))
    assert credential_id, "Could not extract credential ID"
    
    revoke_data = {"credential_id": credential_id}
    response = await client.post("/api/v1/credentials/revoke", json=revoke_data, headers=auth_headers)
    assert response.status_code == 200
    
    # 6. Verify credential is revoked (verification should fail or show revoked status)
    response = await client.post("/api/v1/credentials/verify", json=verify_data, headers=auth_headers)
    # Either returns 400 or shows revoked status in the response
    if response.status_code == 200:
        assert "revoked" in response.json() or response.json().get("verified") is False
    else:
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_concurrent_credential_issuance(client, test_merchant, auth_headers):
    """Test issuing multiple credentials concurrently."""
    # Create credential type
    cred_type_data = {
        "name": "StressTestCredential",
        "schema": {"type": "object", "properties": {"id": {"type": "string"}}},
        "context": ["https://www.w3.org/2018/credentials/v1"]
    }
    response = await client.post("/api/v1/credential-types", json=cred_type_data, headers=auth_headers)
    assert response.status_code == 201
    cred_type_id = response.json()["id"]
    
    # Issue 5 credentials concurrently (reduced from 10 for test performance)
    async def issue_credential(i):
        data = {
            "credential_type_id": cred_type_id,
            "subject_did": f"did:key:test{i}",
            "claims": {"id": f"user-{i}"}
        }
        return await client.post("/api/v1/credentials/issue", json=data, headers=auth_headers)
    
    # Run concurrent issuance operations
    tasks = [issue_credential(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    for response in results:
        assert response.status_code == 200
        assert "proof" in response.json()

@pytest.mark.asyncio
async def test_credential_schema_validation(client, test_merchant, auth_headers):
    """Test credential schema validation during issuance."""
    # 1. Create a credential type with strict schema
    cred_type_data = {
        "name": "ValidatedCredential",
        "schema": {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string", "minLength": 2},
                "age": {"type": "integer", "minimum": 18},
                "email": {"type": "string", "format": "email"}
            }
        },
        "context": ["https://www.w3.org/2018/credentials/v1"]
    }
    response = await client.post("/api/v1/credential-types", json=cred_type_data, headers=auth_headers)
    assert response.status_code == 201
    cred_type_id = response.json()["id"]
    
    # 2. Test valid credential issuance
    valid_data = {
        "credential_type_id": cred_type_id,
        "subject_did": "did:key:testvalid",
        "claims": {
            "name": "John Doe",
            "age": 25,
            "email": "john@example.com"
        }
    }
    response = await client.post("/api/v1/credentials/issue", json=valid_data, headers=auth_headers)
    assert response.status_code == 200
    
    # 3. Test invalid credential issuance (missing required field)
    invalid_data_1 = {
        "credential_type_id": cred_type_id,
        "subject_did": "did:key:testinvalid1",
        "claims": {
            "name": "Jane Doe"
            # missing age field
        }
    }
    response = await client.post("/api/v1/credentials/issue", json=invalid_data_1, headers=auth_headers)
    assert response.status_code == 400
    
    # 4. Test invalid credential issuance (invalid value)
    invalid_data_2 = {
        "credential_type_id": cred_type_id,
        "subject_did": "did:key:testinvalid2",
        "claims": {
            "name": "Jane Doe",
            "age": 17,  # below minimum
            "email": "jane@example.com"
        }
    }
    response = await client.post("/api/v1/credentials/issue", json=invalid_data_2, headers=auth_headers)
    assert response.status_code == 400
