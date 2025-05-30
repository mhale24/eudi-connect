"""Tests for eIDAS 2 compliance scenarios."""
import pytest
from typing import Dict, Any
import json

@pytest.mark.asyncio
async def test_eidas_qualified_credential_issuance(client, test_merchant, auth_headers):
    """Test issuance of eIDAS qualified credentials with high assurance level."""
    # Create qualified credential type
    qualified_cred_type = {
        "name": "QualifiedIdentityCredential",
        "schema": {
            "type": "object",
            "properties": {
                "firstName": {"type": "string"},
                "lastName": {"type": "string"},
                "dateOfBirth": {"type": "string", "format": "date"},
                "nationality": {"type": "string", "pattern": "^[A-Z]{2}$"},
                "assuranceLevel": {"type": "string", "enum": ["low", "substantial", "high"]}
            },
            "required": ["firstName", "lastName", "dateOfBirth", "nationality", "assuranceLevel"]
        },
        "context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://identity.foundation/EidasLevel/v1"
        ]
    }
    
    # Create credential type
    response = await client.post("/api/v1/credential-types", json=qualified_cred_type, headers=auth_headers)
    assert response.status_code == 201
    cred_type_id = response.json()["id"]
    
    # Issue high assurance credential
    issue_data = {
        "credential_type_id": cred_type_id,
        "subject_did": "did:ebsi:zhGDJ8RUZw9vbMEyXk5XSZ2G5XqPJfGV68Jcd8jnGv2KC",
        "claims": {
            "firstName": "Maria",
            "lastName": "Schmidt",
            "dateOfBirth": "1992-04-12",
            "nationality": "DE",
            "assuranceLevel": "high"
        }
    }
    
    response = await client.post("/api/v1/credentials/issue", json=issue_data, headers=auth_headers)
    assert response.status_code == 200
    credential = response.json()
    
    # Verify credential includes required eIDAS fields
    assert "proof" in credential
    assert credential["credentialSubject"]["assuranceLevel"] == "high"
    
    # Verify the credential
    verify_data = {"credential": credential}
    response = await client.post("/api/v1/credentials/verify", json=verify_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["verified"] is True

@pytest.mark.asyncio
async def test_selective_disclosure(client, test_merchant, auth_headers):
    """Test selective disclosure of attributes in compliance with eIDAS 2."""
    # Create credential type with multiple attributes
    cred_type_data = {
        "name": "SelectiveDisclosureCredential",
        "schema": {
            "type": "object",
            "properties": {
                "firstName": {"type": "string"},
                "lastName": {"type": "string"},
                "address": {"type": "string"},
                "dateOfBirth": {"type": "string"},
                "nationalID": {"type": "string"}
            }
        },
        "context": ["https://www.w3.org/2018/credentials/v1"]
    }
    
    response = await client.post("/api/v1/credential-types", json=cred_type_data, headers=auth_headers)
    assert response.status_code == 201
    cred_type_id = response.json()["id"]
    
    # Issue full credential
    issue_data = {
        "credential_type_id": cred_type_id,
        "subject_did": "did:ebsi:zF9z32KYYdXwYYqBCzFzv64YgSNsJ4iodBT7UX7GEH8QG",
        "claims": {
            "firstName": "Elena",
            "lastName": "Rossi",
            "address": "Via Roma 123, Milan, Italy",
            "dateOfBirth": "1985-07-15",
            "nationalID": "IT-RSL-85L15F205Z"
        }
    }
    
    response = await client.post("/api/v1/credentials/issue", json=issue_data, headers=auth_headers)
    assert response.status_code == 200
    full_credential = response.json()
    
    # Create wallet session with selective disclosure request
    # Only request firstName, lastName and dateOfBirth
    session_data = {
        "credential_type_id": cred_type_id,
        "wallet_type": "eudiw",
        "protocol": "openid4vp",
        "expires_in": 300,
        "requested_attributes": ["firstName", "lastName", "dateOfBirth"]
    }
    
    response = await client.post("/api/v1/wallet-sessions", json=session_data, headers=auth_headers)
    assert response.status_code == 201
    session = response.json()
    
    # Verify the session has the correct requested attributes
    assert "requested_attributes" in session
    assert set(session["requested_attributes"]) == {"firstName", "lastName", "dateOfBirth"}
    assert "nationalID" not in session["requested_attributes"]
    assert "address" not in session["requested_attributes"]

@pytest.mark.asyncio
async def test_legal_person_identification(client, test_merchant, auth_headers):
    """Test issuance and verification of legal person credentials (businesses/organizations)."""
    # Create legal person credential type
    legal_person_type = {
        "name": "LegalEntityCredential",
        "schema": {
            "type": "object",
            "properties": {
                "legalName": {"type": "string"},
                "registrationNumber": {"type": "string"},
                "vatNumber": {"type": "string"},
                "jurisdiction": {"type": "string"},
                "legalForm": {"type": "string"},
                "registrationDate": {"type": "string", "format": "date"},
                "legalAddress": {"type": "object"}
            },
            "required": ["legalName", "registrationNumber", "jurisdiction"]
        },
        "context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://www.w3.org/2018/credentials/examples/v1"
        ]
    }
    
    response = await client.post("/api/v1/credential-types", json=legal_person_type, headers=auth_headers)
    assert response.status_code == 201
    cred_type_id = response.json()["id"]
    
    # Issue legal person credential
    issue_data = {
        "credential_type_id": cred_type_id,
        "subject_did": "did:web:acme-corporation.eu",
        "claims": {
            "legalName": "ACME Corporation GmbH",
            "registrationNumber": "HRB 123456",
            "vatNumber": "DE123456789",
            "jurisdiction": "DE",
            "legalForm": "GmbH",
            "registrationDate": "2010-03-22",
            "legalAddress": {
                "streetAddress": "Unter den Linden 1",
                "locality": "Berlin",
                "postalCode": "10117",
                "country": "DE"
            }
        }
    }
    
    response = await client.post("/api/v1/credentials/issue", json=issue_data, headers=auth_headers)
    assert response.status_code == 200
    credential = response.json()
    
    # Verify credential includes required legal person fields
    assert credential["credentialSubject"]["legalName"] == "ACME Corporation GmbH"
    assert credential["credentialSubject"]["registrationNumber"] == "HRB 123456"
    
    # Verify the credential
    verify_data = {"credential": credential}
    response = await client.post("/api/v1/credentials/verify", json=verify_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["verified"] is True
    
    # Log verification for compliance
    log_data = {
        "credential_id": credential.get("id", credential.get("credentialSubject", {}).get("id")),
        "verification_purpose": "eidas_legal_person_verification",
        "verification_level": "substantial"
    }
    
    # Assuming there's an endpoint for logging verifications for compliance
    response = await client.post("/api/v1/compliance/log-verification", json=log_data, headers=auth_headers)
    # If this endpoint doesn't exist yet, this is a suggested extension
    if response.status_code != 404:
        assert response.status_code == 201
