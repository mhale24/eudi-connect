"""Database models for the eIDAS 2 Compliance Scanner.

This module defines the SQLAlchemy ORM models for:
- Compliance requirements (eIDAS 2 requirements)
- Compliance scans (scan execution records)
- Compliance scan results (detailed scan findings)
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, TYPE_CHECKING
import uuid

from sqlalchemy import String, Boolean, ForeignKey, JSON, Enum as SQLAEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eudi_connect.models.base import Base, BaseModelMixin


class RequirementLevel(str, Enum):
    """Level of compliance requirement."""
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


class RequirementCategory(str, Enum):
    """Category of compliance requirement."""
    SECURITY = "security"
    PRIVACY = "privacy"
    INTEROPERABILITY = "interoperability"
    USABILITY = "usability"
    LEGAL = "legal"
    TECHNICAL = "technical"


class ScanStatus(str, Enum):
    """Status of a compliance scan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultStatus(str, Enum):
    """Status of a compliance scan result."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"
    MANUAL_CHECK_REQUIRED = "manual_check_required"


class ComplianceRequirement(Base, BaseModelMixin):
    """eIDAS 2 compliance requirement.
    
    This model represents individual compliance requirements that must be
    checked against wallet implementations.
    """
    __tablename__ = "compliance_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1024))
    category: Mapped[RequirementCategory] = mapped_column(SQLAEnum(RequirementCategory))
    level: Mapped[RequirementLevel] = mapped_column(SQLAEnum(RequirementLevel))
    
    # Validation criteria
    validation_method: Mapped[str] = mapped_column(String(255))
    validation_script: Mapped[Optional[str]] = mapped_column(String(4096), nullable=True)
    
    # Legal reference in the eIDAS 2 regulation
    legal_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Additional metadata stored as JSON
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    
    # Version management
    version: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    results: Mapped[List["ComplianceScanResult"]] = relationship(
        "ComplianceScanResult", back_populates="requirement"
    )


class ComplianceScan(Base, BaseModelMixin):
    """Compliance scan execution record.
    
    This model represents a compliance scan session against a wallet
    implementation.
    """
    __tablename__ = "compliance_scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    
    # Scan information
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    status: Mapped[ScanStatus] = mapped_column(
        SQLAEnum(ScanStatus), default=ScanStatus.PENDING
    )
    
    # Target information
    wallet_name: Mapped[str] = mapped_column(String(255))
    wallet_version: Mapped[str] = mapped_column(String(100))
    wallet_provider: Mapped[str] = mapped_column(String(255))
    
    # Scan configuration
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Results summary
    total_requirements: Mapped[int] = mapped_column(Integer, default=0)
    passed_requirements: Mapped[int] = mapped_column(Integer, default=0)
    failed_requirements: Mapped[int] = mapped_column(Integer, default=0)
    warning_requirements: Mapped[int] = mapped_column(Integer, default=0)
    na_requirements: Mapped[int] = mapped_column(Integer, default=0)
    manual_check_requirements: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps for scan execution
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    results: Mapped[List["ComplianceScanResult"]] = relationship(
        "ComplianceScanResult", back_populates="scan", cascade="all, delete-orphan"
    )


class ComplianceScanResult(Base, BaseModelMixin):
    """Compliance scan result.
    
    This model represents individual requirement check results from a
    compliance scan.
    """
    __tablename__ = "compliance_scan_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("compliance_scans.id"), index=True
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("compliance_requirements.id"), index=True
    )
    
    # Result
    status: Mapped[ResultStatus] = mapped_column(SQLAEnum(ResultStatus))
    message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # Test execution information
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    executed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Remediation guidance
    remediation_steps: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    
    # Relationships
    scan: Mapped["ComplianceScan"] = relationship(
        "ComplianceScan", back_populates="results"
    )
    requirement: Mapped["ComplianceRequirement"] = relationship(
        "ComplianceRequirement", back_populates="results"
    )
