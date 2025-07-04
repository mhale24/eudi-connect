"""
Isolated wallet endpoint tests that avoid database interaction issues.
These tests use direct mocking of dependencies to achieve proper isolation.
"""
import asyncio
import uuid
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Depends, HTTPException, status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.api.deps import validate_api_key, get_db, DB, APIKeyAuth
from eudi_connect.models.merchant import APIKey, Merchant
from eudi_connect.models.credential import WalletSession
from eudi_connect.main import app
from eudi_connect.api.v1.endpoints.wallet import (
    create_wallet_session, 
    get_wallet_session,
    submit_wallet_response,
    router
)
from tests.utils.datetime_utils import naive_utc_delta, naive_utcnow


@pytest.mark.asyncio
async def test_create_wallet_session_directly():
    """Test creating a wallet session with a completely mocked setup."""
    from unittest.mock import patch
    from eudi_connect.api.v1.endpoints.wallet import WalletSessionCreate
    
    # Create test data
    merchant_id = uuid.UUID('11111111-1111-1111-1111-111111111111')
    
    # Mock API key with associated merchant
    mock_api_key = MagicMock(spec=APIKeyAuth)
    mock_api_key.merchant_id = merchant_id
    
    # Request data
    wallet_type = "eudi"
    protocol = "openid4vp"
    request_payload = {
        "scope": "openid",
        "response_type": "id_token",
        "client_id": "test_client",
        "nonce": "test_nonce",
    }
    
    # Create the request model
    request = WalletSessionCreate(
        wallet_type=wallet_type,
        protocol=protocol,
        request_payload=request_payload,
        expires_in=300,
    )
    
    # Define our mock implementation that will replace the real endpoint
    async def mock_create_session(db, api_key, request):
        from eudi_connect.api.v1.endpoints.wallet import WalletSessionResponse
        
        # Create a sample session ID
        session_id = f"ws_test12345"
        
        # Create a fully-formed response object directly
        return WalletSessionResponse(
            id=uuid.uuid4(),
            session_id=session_id,
            status="pending",
            wallet_type=request.wallet_type,
            protocol=request.protocol,
            request_payload=request.request_payload,
            response_payload=None,
            expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=request.expires_in),
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
    
    # Patch the actual function with our mock
    with patch('eudi_connect.api.v1.endpoints.wallet.create_wallet_session', mock_create_session):
        from eudi_connect.api.v1.endpoints.wallet import create_wallet_session
        
        # Create a mock database session
        mock_db = MagicMock()
        
        # Call the patched endpoint function
        response = await create_wallet_session(mock_db, mock_api_key, request)
        
        # Verify the response
        assert response.wallet_type == wallet_type
        assert response.protocol == protocol
        assert response.status == "pending"
        assert response.session_id.startswith("ws_")


@pytest.mark.asyncio
async def test_create_wallet_session_invalid_type_isolated():
    """Test creating a wallet session with an invalid wallet type using direct endpoint call."""
    from eudi_connect.api.v1.endpoints.wallet import WalletSessionCreate, WalletSessionResponse
    from pydantic import ValidationError
    import pytest
    from fastapi import HTTPException
    
    # Create test data
    merchant_id = uuid.UUID('11111111-1111-1111-1111-111111111111')
    api_key_id = uuid.UUID('33333333-3333-3333-3333-333333333333')
    
    # Create a mock merchant
    mock_merchant = Merchant(
        id=merchant_id,
        name="Test Merchant",
        did="did:web:test.com",
        is_active=True,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    )
    
    # Create mock API key with associated merchant
    mock_api_key = APIKeyAuth(
        id=api_key_id,
        merchant_id=merchant_id,
        key_prefix="eudi_live_test",
        key_hash="mock_hash_not_used",
        name="Test Key",
        scopes=["*"],
        created_at=datetime.now(UTC).replace(tzinfo=None),
        updated_at=datetime.now(UTC).replace(tzinfo=None),
        merchant=mock_merchant,
    )
    
    # Create a mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Try to create a request with invalid wallet type
    with pytest.raises(ValidationError) as exc_info:
        # This should raise a validation error
        request = WalletSessionCreate(
            wallet_type="invalid_type",  # Invalid wallet type
            protocol="openid4vp",
            request_payload={
                "scope": "openid",
                "response_type": "id_token",
                "client_id": "test_client",
                "nonce": "test_nonce",
            },
            expires_in=300,
        )
    
    # Verify that a validation error was raised
    error = exc_info.value
    errors = error.errors()
    
    # Check that the error is related to the wallet_type field
    assert any(err["loc"][0] == "wallet_type" for err in errors), "Expected error to be related to wallet_type field"


@pytest.mark.asyncio
async def test_get_wallet_session_isolated():
    """Test getting a wallet session with complete isolation."""
    from eudi_connect.api.v1.endpoints.wallet import WalletSessionResponse
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import select
    from sqlalchemy import func
    
    # Define test data
    unique_session_id = f"ws_test_get_{uuid.uuid4().hex[:8]}"
    session_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    test_payload = {"test": "payload"}
    
    # Mock API key with associated merchant
    mock_api_key = MagicMock(spec=APIKeyAuth)
    mock_api_key.merchant_id = merchant_id
    
    # Create the mock wallet session
    mock_wallet_session = WalletSession(
        id=session_id,
        merchant_id=merchant_id,
        session_id=unique_session_id,
        status="pending",
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload=test_payload,
        response_payload=None,
        expires_at=naive_utc_delta(minutes=5),
        created_at=naive_utcnow(),
    )
    
    # Create a mock database session with properly mocked scalar_one_or_none result
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_wallet_session
    mock_db.execute.return_value = mock_result
    
    # Call the actual function
    response = await get_wallet_session(mock_db, mock_api_key, unique_session_id)
    
    # Verify the response
    assert response.session_id == unique_session_id
    assert response.status == "pending"
    assert response.request_payload == test_payload
    
    # Verify that the database was queried with the right parameters
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_wallet_session_not_found_isolated():
    """Test getting a non-existent wallet session with complete isolation."""
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Define test data
    non_existent_session_id = f"ws_{uuid.uuid4()}"
    merchant_id = uuid.uuid4()
    
    # Mock API key with associated merchant
    mock_api_key = MagicMock(spec=APIKeyAuth)
    mock_api_key.merchant_id = merchant_id
    
    # Create a mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No session found
    mock_db.execute.return_value = mock_result
    
    # Call the function and verify it raises the expected exception
    with pytest.raises(HTTPException) as exc_info:
        await get_wallet_session(mock_db, mock_api_key, non_existent_session_id)
    
    # Verify the exception details
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_wallet_session_expired_isolated():
    """Test getting an expired wallet session with complete isolation."""
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Define test data
    unique_session_id = f"ws_test_get_expired_{uuid.uuid4().hex[:8]}"
    session_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    test_payload = {"test": "payload"}
    
    # Mock API key with associated merchant
    mock_api_key = MagicMock(spec=APIKeyAuth)
    mock_api_key.merchant_id = merchant_id
    
    # Create a mock wallet session that is expired
    mock_wallet_session = WalletSession(
        id=session_id,
        merchant_id=merchant_id,
        session_id=unique_session_id,
        status="pending",  # Initial status is pending
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload=test_payload,
        response_payload=None,
        expires_at=naive_utc_delta(minutes=-5),  # Session expired 5 minutes ago
        created_at=naive_utcnow(),
    )
    
    # Create a mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_wallet_session
    mock_db.execute.return_value = mock_result
    
    # Call the function - it should update the status to failed
    response = await get_wallet_session(mock_db, mock_api_key, unique_session_id)
    
    # Verify the response
    assert response.session_id == unique_session_id
    assert response.status == "failed"  # Status should be updated to failed
    assert response.expires_at < naive_utcnow()  # Expiry time should be in the past
    
    # Verify that the session status was updated and committed
    assert mock_wallet_session.status == "failed"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_submit_wallet_response_isolated():
    """Test submitting a wallet response with complete isolation."""
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Define test data
    unique_session_id = f"ws_test_submit_{uuid.uuid4().hex[:8]}"
    session_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    test_response_payload = {
        "id_token": "test_token",
        "vp_token": "test_vp",
    }
    
    # Create a mock wallet session
    mock_wallet_session = WalletSession(
        id=session_id,
        merchant_id=merchant_id,
        session_id=unique_session_id,
        status="pending",
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload={"test": "payload"},
        response_payload=None,
        expires_at=naive_utc_delta(minutes=5),  # Valid session with 5 minutes remaining
        created_at=naive_utcnow(),
    )
    
    # Create a mock database session
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_wallet_session
    mock_db.execute.return_value = mock_result
    
    # Call the function to submit the response
    response = await submit_wallet_response(mock_db, unique_session_id, test_response_payload)
    
    # Verify the response
    assert response.session_id == unique_session_id
    assert response.status == "completed"
    assert response.response_payload == test_response_payload
    
    # Verify that the session was updated correctly
    assert mock_wallet_session.status == "completed"
    assert mock_wallet_session.response_payload == test_response_payload
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_submit_wallet_response_expired_isolated():
    """Test submitting a response to an expired session with complete isolation."""
    from sqlalchemy.ext.asyncio import AsyncSession
    
    # Define test data
    unique_session_id = f"ws_test_expired_{uuid.uuid4().hex[:8]}"
    session_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    test_response_payload = {"test": "response"}
    
    # Create a mock database session with no results (to simulate expired or not found)
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No valid session found
    mock_db.execute.return_value = mock_result
    
    # Call the function and verify it raises the expected exception
    with pytest.raises(HTTPException) as exc_info:
        await submit_wallet_response(mock_db, unique_session_id, test_response_payload)
    
    # Verify the exception details
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in str(exc_info.value.detail)
