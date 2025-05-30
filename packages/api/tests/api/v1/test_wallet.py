from datetime import datetime, timedelta
from typing import Dict
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.models.credential import WalletSession

pytestmark = pytest.mark.asyncio


async def test_create_wallet_session(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test creating a wallet session."""
    response = await client.post(
        "/api/v1/wallet/sessions",
        headers=auth_headers,
        json={
            "wallet_type": "eudi",
            "protocol": "openid4vp",
            "request_payload": {
                "scope": "openid",
                "response_type": "id_token",
                "client_id": "test_client",
                "nonce": "test_nonce",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["wallet_type"] == "eudi"
    assert data["protocol"] == "openid4vp"
    assert data["status"] == "pending"
    assert data["session_id"].startswith("ws_")


async def test_create_wallet_session_invalid_type(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test creating a wallet session with invalid wallet type."""
    response = await client.post(
        "/api/v1/wallet/sessions",
        headers=auth_headers,
        json={
            "wallet_type": "invalid",
            "protocol": "openid4vp",
            "request_payload": {},
        },
    )
    assert response.status_code == 422


async def test_get_wallet_session(
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
    auth_headers: Dict[str, str],
) -> None:
    """Test getting a wallet session."""
    # Create test session
    session = WalletSession(
        merchant_id=test_merchant["merchant_id"],
        session_id="ws_test",
        status="pending",
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload={"test": "payload"},
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(session)
    await db.commit()

    response = await client.get(
        "/api/v1/wallet/sessions/ws_test",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "ws_test"
    assert data["status"] == "pending"
    assert data["request_payload"] == {"test": "payload"}


async def test_get_wallet_session_not_found(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test getting a non-existent wallet session."""
    response = await client.get(
        f"/api/v1/wallet/sessions/ws_{uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_submit_wallet_response(
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
) -> None:
    """Test submitting a wallet response."""
    # Create test session
    session = WalletSession(
        merchant_id=test_merchant["merchant_id"],
        session_id="ws_test",
        status="pending",
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload={"test": "payload"},
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(session)
    await db.commit()

    response = await client.post(
        "/api/v1/wallet/sessions/ws_test/response",
        json={
            "id_token": "test_token",
            "vp_token": "test_vp",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "ws_test"
    assert data["status"] == "completed"
    assert data["response_payload"] == {
        "id_token": "test_token",
        "vp_token": "test_vp",
    }


async def test_submit_wallet_response_expired(
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
) -> None:
    """Test submitting a response to an expired session."""
    # Create expired test session
    session = WalletSession(
        merchant_id=test_merchant["merchant_id"],
        session_id="ws_test",
        status="pending",
        wallet_type="eudi",
        protocol="openid4vp",
        request_payload={"test": "payload"},
        expires_at=datetime.utcnow() - timedelta(minutes=5),
    )
    db.add(session)
    await db.commit()

    response = await client.post(
        "/api/v1/wallet/sessions/ws_test/response",
        json={"test": "response"},
    )
    assert response.status_code == 404
