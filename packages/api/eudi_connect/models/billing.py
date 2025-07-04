from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eudi_connect.models.base import Base, BaseModelMixin


class BillingPlan(Base, BaseModelMixin):
    """Billing plan model."""
    __tablename__ = "billingplan"
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(String(1024))
    price_monthly: Mapped[int]  # Price in cents
    price_yearly: Mapped[int]  # Price in cents
    features: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(default=True)
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(255))
    stripe_price_id_yearly: Mapped[str | None] = mapped_column(String(255))

    # Relationships
    subscriptions: Mapped[List["MerchantSubscription"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan"
    )


class MerchantSubscription(Base, BaseModelMixin):
    """Merchant subscription model."""
    __tablename__ = "merchantsubscription"
    is_active: Mapped[bool] = mapped_column(default=True)
    billing_cycle: Mapped[str] = mapped_column(String(50))  # monthly, yearly
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))

    # Foreign keys
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant.id", ondelete="CASCADE")
    )
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("billingplan.id", ondelete="RESTRICT")
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship()
    plan: Mapped[BillingPlan] = relationship(back_populates="subscriptions")
    usage_records: Mapped[List["UsageRecord"]] = relationship(
        back_populates="subscription",
        cascade="all, delete-orphan"
    )


class UsageRecord(Base, BaseModelMixin):
    """Usage record model for metered billing."""
    __tablename__ = "usagerecord"
    operation: Mapped[str] = mapped_column(String(50))  # credential_issue, credential_verify, etc.
    quantity: Mapped[int]
    usage_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    stripe_usage_record_id: Mapped[str | None] = mapped_column(String(255))

    # Foreign keys
    subscription_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchantsubscription.id", ondelete="CASCADE")
    )

    # Relationships
    subscription: Mapped[MerchantSubscription] = relationship(back_populates="usage_records")
