from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eudi_connect.models.base import Base, BaseModelMixin


class CredentialType(Base, BaseModelMixin):
    """Credential type model."""
    __tablename__ = "credentialtype"
    name: Mapped[str] = mapped_column(String(255), unique=True)
    version: Mapped[str] = mapped_column(String(50))
    context: Mapped[List[str]] = mapped_column(ARRAY(String))
    schema: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    logs: Mapped[List["CredentialLog"]] = relationship(
        back_populates="credential_type",
        cascade="all, delete-orphan"
    )


class CredentialLog(Base, BaseModelMixin):
    """Credential operation log model."""
    __tablename__ = "credentiallog"
    operation: Mapped[str] = mapped_column(String(50))  # issue, verify, revoke
    status: Mapped[str] = mapped_column(String(50))  # success, failed
    error: Mapped[str | None] = mapped_column(String(1024))
    log_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    subject_did: Mapped[str] = mapped_column(String(255))
    proof: Mapped[Dict[str, Any]] = mapped_column(JSONB)

    # Foreign keys
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant.id", ondelete="CASCADE")
    )
    credential_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("credentialtype.id", ondelete="CASCADE")
    )
    wallet_session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("walletsession.id", ondelete="SET NULL")
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship()
    credential_type: Mapped[CredentialType] = relationship(back_populates="logs")
    wallet_session: Mapped["WalletSession | None"] = relationship()


class WalletSession(Base, BaseModelMixin):
    """Wallet interaction session model."""
    __tablename__ = "walletsession"
    status: Mapped[str] = mapped_column(String(50))  # pending, active, completed, failed
    session_id: Mapped[str] = mapped_column(String(255), unique=True)
    wallet_type: Mapped[str] = mapped_column(String(50))
    protocol: Mapped[str] = mapped_column(String(50))  # openid4vp, siopv2
    request_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    response_payload: Mapped[Dict[str, Any] | None] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    # Foreign keys
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant.id", ondelete="CASCADE")
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship()
    credential_logs: Mapped[List[CredentialLog]] = relationship(
        back_populates="wallet_session"
    )
