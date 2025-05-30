from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eudi_connect.models.base import Base, BaseModelMixin


class Merchant(Base, BaseModelMixin):
    """Merchant model."""
    __tablename__ = "merchant"
    name: Mapped[str] = mapped_column(String(255))
    did: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    users: Mapped[List["MerchantUser"]] = relationship(
        back_populates="merchant",
        cascade="all, delete-orphan"
    )
    api_keys: Mapped[List["APIKey"]] = relationship(
        back_populates="merchant",
        cascade="all, delete-orphan"
    )
    webhooks: Mapped[List["Webhook"]] = relationship(
        back_populates="merchant",
        cascade="all, delete-orphan"
    )


class MerchantUser(Base, BaseModelMixin):
    """Merchant user model."""
    __tablename__ = "merchant_user"
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))
    last_login: Mapped[datetime | None]

    # Foreign keys
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant.id", ondelete="CASCADE")
    )

    # Relationships
    merchant: Mapped[Merchant] = relationship(back_populates="users")


class APIKey(Base, BaseModelMixin):
    """API key model."""
    __tablename__ = "api_key"
    name: Mapped[str] = mapped_column(String(255))
    key_prefix: Mapped[str] = mapped_column(String(16))
    key_hash: Mapped[str] = mapped_column(String(255))
    scopes: Mapped[List[str]] = mapped_column(ARRAY(String))
    expires_at: Mapped[datetime | None]
    revoked_at: Mapped[datetime | None]

    # Foreign keys
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant.id", ondelete="CASCADE")
    )

    # Relationships
    merchant: Mapped[Merchant] = relationship(back_populates="api_keys")


class Webhook(Base, BaseModelMixin):
    """Webhook configuration model."""
    __tablename__ = "webhook"
    url: Mapped[str] = mapped_column(String(1024))
    events: Mapped[List[str]] = mapped_column(ARRAY(String))
    is_active: Mapped[bool] = mapped_column(default=True)
    secret_hash: Mapped[str] = mapped_column(String(255))
    last_success: Mapped[datetime | None]
    last_failure: Mapped[datetime | None]
    failure_count: Mapped[int] = mapped_column(server_default=text("0"))

    # Foreign keys
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant.id", ondelete="CASCADE")
    )

    # Relationships
    merchant: Mapped[Merchant] = relationship(back_populates="webhooks")
