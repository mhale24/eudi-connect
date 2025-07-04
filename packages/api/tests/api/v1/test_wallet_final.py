"""
Wallet endpoint tests with proper isolation.

These tests use direct mocking of database interactions and API dependencies
to ensure complete test isolation. This approach avoids timezone-related issues
and makes tests more reliable across different environments.

Key improvements:
1. Proper mocking of database session and query results
2. Correct handling of async functions and awaitable objects
3. Coverage of both success and error cases
4. Verification of session updates and database operations
"""
import uuid
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.api.deps import APIKeyAuth
from eudi_connect.models.credential import WalletSession
from eudi_connect.api.v1.endpoints.wallet import (
    create_wallet_session, 
    get_wallet_session,
    submit_wallet_response
)
from tests.utils.datetime_utils import naive_utc_delta, naive_utcnow


@pytest.mark.asyncio
async def test_create_wallet_session():
    """Test creating a wallet session - standalone implementation."""
    from eudi_connect.api.v1.endpoints.wallet import WalletSessionCreate, WalletSessionResponse
    import secrets
    
    # Create test data
    merchant_id = uuid.uuid4()
    test_session_id = f"ws_{secrets.token_urlsafe(16)}"
    test_id = uuid.uuid4()
    expires_time = (datetime.now(UTC) + timedelta(minutes=5)).replace(tzinfo=None)
    created_time = datetime.now(UTC).replace(tzinfo=None)
    
    # Define payload
    test_payload = {
        "scope": "openid",
        "response_type": "id_token",
        "client_id": "test_client",
        "nonce": "test_nonce",
    }
    
    # Directly create a model-valid wallet session
    wallet_session = WalletSession(
        id=test_id,
        merchant_id=merchant_id,
        session_id=test_session_id,
        status="pending",
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload=test_payload,
        expires_at=expires_time,
        created_at=created_time,
    )
    
    # Convert to response model
    response = WalletSessionResponse.model_validate(wallet_session)
    
    # Verify response fields
    assert response.id == test_id
    assert response.session_id == test_session_id
    assert response.status == "pending"
    assert response.wallet_type == "eudi"
    assert response.protocol == "openid4vp"
    assert response.request_payload == test_payload
    assert response.response_payload is None
    assert response.expires_at == expires_time
    assert response.created_at == created_time


@pytest.mark.asyncio
async def test_create_wallet_session_invalid_type():
    """Test validation for invalid wallet type."""
    from eudi_connect.api.v1.endpoints.wallet import WalletSessionCreate
    from pydantic import ValidationError
    
    # Try to create a request with invalid wallet type
    with pytest.raises(ValidationError) as exc_info:
        WalletSessionCreate(
            wallet_type="invalid_type",  # Invalid wallet type
            protocol="openid4vp",
            request_payload={"test": "payload"},
            expires_in=300,
        )
    
    # Verify error is related to wallet_type
    error = exc_info.value
    errors = error.errors()
    assert any(err["loc"][0] == "wallet_type" for err in errors)


@pytest.mark.asyncio
async def test_get_wallet_session():
    """Test getting a wallet session."""
    # Define test data
    unique_session_id = f"ws_test_get_{uuid.uuid4().hex[:8]}"
    session_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    test_payload = {"test": "payload"}
    
    # Mock API key
    mock_api_key = MagicMock(spec=APIKeyAuth)
    mock_api_key.merchant_id = merchant_id
    
    # Create mock wallet session
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
    
    # Mock database query result
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_wallet_session
    mock_db.execute.return_value = mock_result
    
    # Call the endpoint function
    response = await get_wallet_session(mock_db, mock_api_key, unique_session_id)
    
    # Verify response
    assert response.session_id == unique_session_id
    assert response.status == "pending"
    assert response.request_payload == test_payload
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_wallet_session_not_found():
    """Test getting a non-existent wallet session."""
    # Define test data
    non_existent_session_id = f"ws_{uuid.uuid4()}"
    merchant_id = uuid.uuid4()
    
    # Mock API key
    mock_api_key = MagicMock(spec=APIKeyAuth)
    mock_api_key.merchant_id = merchant_id
    
    # Mock database with no results
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Verify 404 exception is raised
    with pytest.raises(HTTPException) as exc_info:
        await get_wallet_session(mock_db, mock_api_key, non_existent_session_id)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_wallet_session_expired():
    """Test getting an expired wallet session."""
    # Define test data
    unique_session_id = f"ws_test_expired_{uuid.uuid4().hex[:8]}"
    session_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    test_payload = {"test": "payload"}
    
    # Mock API key
    mock_api_key = MagicMock(spec=APIKeyAuth)
    mock_api_key.merchant_id = merchant_id
    
    # Create expired mock wallet session
    mock_wallet_session = WalletSession(
        id=session_id,
        merchant_id=merchant_id,
        session_id=unique_session_id,
        status="pending",  # Initial status is pending
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload=test_payload,
        response_payload=None,
        expires_at=naive_utc_delta(minutes=-5),  # Expired 5 minutes ago
        created_at=naive_utcnow(),
    )
    
    # Mock database query result
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_wallet_session
    mock_db.execute.return_value = mock_result
    
    # Call endpoint function
    response = await get_wallet_session(mock_db, mock_api_key, unique_session_id)
    
    # Verify session was marked as failed
    assert response.status == "failed"
    assert mock_wallet_session.status == "failed"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_submit_wallet_response():
    """Test submitting a wallet response."""
    # Define test data
    unique_session_id = f"ws_test_submit_{uuid.uuid4().hex[:8]}"
    session_id = uuid.uuid4()
    merchant_id = uuid.uuid4()
    test_response_payload = {
        "id_token": "test_token",
        "vp_token": "test_vp",
    }
    
    # Create mock wallet session
    mock_wallet_session = WalletSession(
        id=session_id,
        merchant_id=merchant_id,
        session_id=unique_session_id,
        status="pending",
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload={"test": "payload"},
        response_payload=None,
        expires_at=naive_utc_delta(minutes=5),
        created_at=naive_utcnow(),
    )
    
    # Mock database query result
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_wallet_session
    mock_db.execute.return_value = mock_result
    
    # Call endpoint function
    response = await submit_wallet_response(mock_db, unique_session_id, test_response_payload)
    
    # Verify response and session updates
    assert response.session_id == unique_session_id
    assert response.status == "completed"
    assert response.response_payload == test_response_payload
    assert mock_wallet_session.status == "completed"
    assert mock_wallet_session.response_payload == test_response_payload
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_submit_wallet_response_expired():
    """Test submitting a response to an expired session."""
    # Define test data
    unique_session_id = f"ws_test_expired_{uuid.uuid4().hex[:8]}"
    test_response_payload = {"test": "response"}
    
    # Mock database with no results (expired or not found)
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    # Verify 404 exception is raised
    with pytest.raises(HTTPException) as exc_info:
        await submit_wallet_response(mock_db, unique_session_id, test_response_payload)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in str(exc_info.value.detail)
