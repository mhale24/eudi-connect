import json
import os
import tempfile
import uuid
from typing import AsyncGenerator, Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.models.credential import CredentialType
from eudi_connect.services.didkit import DIDKitService

# Mark all tests as asyncio tests
pytestmark = pytest.mark.asyncio

# Set each test to use function scope to prevent session conflicts
@pytest.fixture(scope="function", autouse=True)
def function_scope():
    """Ensure each test runs in isolation."""
    pass

# Create a global test service instance
import os
TEST_KEY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'didkit_test_key.json'))
print(f"DEBUG: DIDKit test key path: {TEST_KEY_PATH}")
import os
print(f"DEBUG: Key file exists: {os.path.exists(TEST_KEY_PATH)}")
data_dir = os.path.dirname(TEST_KEY_PATH)
print(f"DEBUG: Data dir: {data_dir}")
print(f"DEBUG: Data dir contents: {os.listdir(data_dir) if os.path.exists(data_dir) else 'NOT FOUND'}")
tests_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
print(f"DEBUG: Tests dir: {tests_dir}")
print(f"DEBUG: Tests dir contents: {os.listdir(tests_dir) if os.path.exists(tests_dir) else 'NOT FOUND'}")
test_didkit_service = DIDKitService(key_path=TEST_KEY_PATH)
test_didkit_service.init()  # Initialize synchronously for test setup


@pytest_asyncio.fixture(autouse=True)
async def setup_didkit() -> AsyncGenerator[None, None]:
    """Setup DIDKit service for tests."""
    # Override the global service instance in the module
    from eudi_connect.services.didkit import _didkit_service
    from eudi_connect.core.config import settings
    
    # Save original settings and replace with test settings
    original_key_path = settings.DIDKIT_KEY_PATH
    settings.DIDKIT_KEY_PATH = TEST_KEY_PATH
    
    # Save the original service and replace with our test service
    original_service = _didkit_service
    _didkit_service = test_didkit_service
    
    yield
    
    # Restore original settings and service
    settings.DIDKIT_KEY_PATH = original_key_path
    _didkit_service = original_service


async def test_list_credential_types_empty(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test listing credential types when none exist."""
    response = await client.get("/api/v1/credentials/types", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_credential_types(
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test listing credential types."""
    # Create test credential type
    cred_type = CredentialType(
        name="TestCredential",
        version="1.0",
        context=["https://www.w3.org/2018/credentials/v1"],
        schema={"type": "object", "properties": {}},
        is_active=True,
    )
    db.add(cred_type)
    await db.commit()

    response = await client.get("/api/v1/credentials/types", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "TestCredential"
    assert data[0]["version"] == "1.0"


async def test_issue_credential_invalid_type(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test issuing credential with invalid type."""
    response = await client.post(
        "/api/v1/credentials/issue",
        headers=auth_headers,
        json={
            "type_id": str(uuid.uuid4()),
            "subject_did": "did:web:test.com",
            "claims": {"name": "Test"},
        },
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_issue_credential(
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test issuing a valid credential."""
    # Create test credential type
    cred_type = CredentialType(
        name="TestCredential",
        version="1.0",
        context=["https://www.w3.org/2018/credentials/v1"],
        schema={"type": "object", "properties": {"name": {"type": "string"}}},
        is_active=True,
    )
    db.add(cred_type)
    await db.commit()

    response = await client.post(
        "/api/v1/credentials/issue",
        headers=auth_headers,
        json={
            "type_id": str(cred_type.id),
            "subject_did": "did:web:test.com",
            "claims": {"name": "Test"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "issue"
    assert data["status"] == "success"
    assert data["subject_did"] == "did:web:test.com"


async def test_verify_credential(
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test verifying a credential."""
    # Create test credential type
    cred_type = CredentialType(
        name="TestCredential",
        version="1.0",
        context=["https://www.w3.org/2018/credentials/v1"],
        schema={"type": "object", "properties": {"name": {"type": "string"}}},
        is_active=True,
    )
    db.add(cred_type)
    await db.commit()

    # First issue a credential via API
    response = await client.post(
        "/api/v1/credentials/issue",
        json={
            "type_id": str(cred_type.id),
            "subject_did": "did:web:test.com",
            "claims": {"name": "Test Subject"}
        },
        headers=auth_headers,
    )
    
    # Print response content for debugging
    print(f"Issue response status: {response.status_code}")
    print(f"Issue response content: {response.content}")
    
    assert response.status_code == 200
    issue_data = response.json()
    credential = issue_data["log_metadata"]["credential"]
    
    # Verify the credential via API
    response = await client.post(
        "/api/v1/credentials/verify",
        json={
            "credential": credential,
        },
        headers=auth_headers,
    )
    
    # Print verification response for debugging
    print(f"Verify response status: {response.status_code}")
    print(f"Verify response content: {response.content}")

    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "verify"
    assert data["status"] == "success"
    assert data["subject_did"] == "did:web:test.com"


async def test_verify_invalid_credential(
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test verifying an invalid credential."""
    # Create test credential type
    cred_type = CredentialType(
        name="TestCredential",
        version="1.0",
        context=["https://www.w3.org/2018/credentials/v1"],
        schema={"type": "object", "properties": {"name": {"type": "string"}}},
        is_active=True,
    )
    db.add(cred_type)
    await db.commit()
    
    # Create an invalid credential (wrong signature)
    credential = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential", "TestCredential"],
        "issuer": test_didkit_service.did,
        "issuanceDate": "2025-05-26T14:30:00Z",
        "credentialSubject": {
            "id": "did:web:test.com",
            "name": "Test Subject"
        },
        "proof": {
            "type": "Ed25519Signature2020",
            "created": "2025-05-26T14:30:00Z",
            "verificationMethod": test_didkit_service.verification_method,
            "proofPurpose": "assertionMethod",
            "proofValue": "invalid"
        }
    }

    response = await client.post(
        "/api/v1/credentials/verify",
        json={"credential": credential},
        headers=auth_headers,
    )
    
    # Print response for debugging
    print(f"Verify invalid response status: {response.status_code}")
    print(f"Verify invalid response content: {response.content}")
    
    assert response.status_code == 400
    assert "verification failed" in response.json()["detail"].lower()


async def test_revoke_credential(
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test revoking a credential."""
    # Create test credential type
    cred_type = CredentialType(
        name="TestCredential",
        version="1.0",
        context=["https://www.w3.org/2018/credentials/v1"],
        schema={"type": "object", "properties": {"name": {"type": "string"}}},
        is_active=True,
    )
    db.add(cred_type)
    await db.commit()

    # Issue a test credential via API
    response = await client.post(
        "/api/v1/credentials/issue",
        headers=auth_headers,
        json={
            "type_id": str(cred_type.id),
            "subject_did": "did:web:test.com",
            "claims": {"name": "Test Subject"},
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Get the credential ID
    credential_id = data["id"]
    
    # Revoke the credential
    response = await client.post(
        "/api/v1/credentials/revoke",
        json={
            "credential_id": credential_id,
            "reason": "Test revocation"
        },
        headers=auth_headers,
    )
    
    # Print revocation response for debugging
    print(f"Revoke response status: {response.status_code}")
    print(f"Revoke response content: {response.content}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["operation"] == "revoke"
    assert data["status"] == "success"
    assert data["subject_did"] == "did:web:test.com"


async def test_revoke_nonexistent_credential(
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test revoking a nonexistent credential."""
    # Ensure the session is clean and ready for this test
    await db.rollback()
    
    # Use a random UUID that won't exist in the database
    test_id = str(uuid.uuid4())
    
    # Make the request to revoke a nonexistent credential
    response = await client.post(
        "/api/v1/credentials/revoke",
        headers=auth_headers,
        json={"credential_id": test_id},
    )
    
    # Print response for debugging
    print(f"Revoke nonexistent response status: {response.status_code}")
    print(f"Revoke nonexistent response content: {response.content}")
    
    # Verify the expected response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    # Ensure the session is committed before finishing the test
    await db.commit()
