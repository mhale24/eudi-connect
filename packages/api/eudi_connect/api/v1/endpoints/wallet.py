from datetime import datetime, timedelta, UTC
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select

from eudi_connect.api.deps import APIKeyAuth, DB
from eudi_connect.models.credential import WalletSession

router = APIRouter()


class WalletSessionCreate(BaseModel):
    """Wallet session creation request model."""
    wallet_type: str = Field(..., pattern="^(eudi|ebsi|iota)$")
    protocol: str = Field(..., pattern="^(openid4vp|siopv2)$")
    request_payload: Dict[str, Any]
    expires_in: int = Field(default=300, ge=60, le=3600)  # 5 minutes default, max 1 hour


class WalletSessionResponse(BaseModel):
    """Wallet session response model."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    session_id: str
    status: str
    wallet_type: str
    protocol: str
    request_payload: Dict[str, Any]
    response_payload: Dict[str, Any] | None
    expires_at: datetime
    created_at: datetime


@router.post("/sessions", response_model=WalletSessionResponse)
async def create_wallet_session(
    db: DB,
    api_key: APIKeyAuth,
    request: WalletSessionCreate,
) -> WalletSessionResponse:
    """Create a new wallet interaction session."""
    # Generate session ID (in practice, this would be more sophisticated)
    import secrets
    session_id = f"ws_{secrets.token_urlsafe(32)}"

    # Create wallet session
    session = WalletSession(
        merchant_id=api_key.merchant_id,
        session_id=session_id,
        status="pending",
        wallet_type=request.wallet_type,
        protocol=request.protocol,
        request_payload=request.request_payload,
        expires_at=(datetime.now(UTC) + timedelta(seconds=request.expires_in)).replace(tzinfo=None)
    )
    db.add(session)
    await db.commit()

    return WalletSessionResponse.model_validate(session)


@router.get("/sessions/{session_id}", response_model=WalletSessionResponse)
async def get_wallet_session(
    db: DB,
    api_key: APIKeyAuth,
    session_id: str,
) -> WalletSessionResponse:
    """Get wallet session status."""
    result = await db.execute(
        select(WalletSession)
        .where(WalletSession.session_id == session_id)
        .where(WalletSession.merchant_id == api_key.merchant_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Check if session has expired
    if session.expires_at < datetime.now(UTC).replace(tzinfo=None):
        session.status = "failed"
        await db.commit()

    return WalletSessionResponse.model_validate(session)


@router.post("/sessions/{session_id}/response", response_model=WalletSessionResponse)
async def submit_wallet_response(
    db: DB,
    session_id: str,
    response: Dict[str, Any],
) -> WalletSessionResponse:
    """Submit wallet response for a session."""
    result = await db.execute(
        select(WalletSession)
        .where(WalletSession.session_id == session_id)
        .where(WalletSession.status == "pending")
        .where(WalletSession.expires_at > datetime.now(UTC).replace(tzinfo=None))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active session not found"
        )

    # Update session with response
    session.status = "completed"
    session.response_payload = response
    await db.commit()

    return WalletSessionResponse.model_validate(session)
