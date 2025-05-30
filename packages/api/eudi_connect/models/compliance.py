from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eudi_connect.models.base import Base


class ComplianceRequirement(Base):
    """Compliance requirement model."""
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1024))
    category: Mapped[str] = mapped_column(String(50))
    severity: Mapped[str] = mapped_column(String(50))
    validation_rules: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    scan_results: Mapped[List["ComplianceScanResult"]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan"
    )


class ComplianceScan(Base):
    """Compliance scan model."""
    status: Mapped[str] = mapped_column(String(50))  # pending, running, completed, failed
    scan_type: Mapped[str] = mapped_column(String(50))  # full, incremental
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    error: Mapped[str | None] = mapped_column(String(1024))
    scan_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB)

    # Foreign keys
    merchant_id: Mapped[UUID] = mapped_column(
        ForeignKey("merchant.id", ondelete="CASCADE")
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship()
    results: Mapped[List["ComplianceScanResult"]] = relationship(
        back_populates="scan",
        cascade="all, delete-orphan"
    )


class ComplianceScanResult(Base):
    """Compliance scan result model."""
    status: Mapped[str] = mapped_column(String(50))  # pass, fail, warning
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    evidence: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    remediation: Mapped[str | None] = mapped_column(String(1024))

    # Foreign keys
    scan_id: Mapped[UUID] = mapped_column(
        ForeignKey("compliancescan.id", ondelete="CASCADE")
    )
    requirement_id: Mapped[UUID] = mapped_column(
        ForeignKey("compliancerequirement.id", ondelete="CASCADE")
    )

    # Relationships
    scan: Mapped[ComplianceScan] = relationship(back_populates="results")
    requirement: Mapped[ComplianceRequirement] = relationship(back_populates="scan_results")
