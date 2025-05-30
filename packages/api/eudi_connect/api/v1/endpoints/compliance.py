from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Query, Path, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select

from eudi_connect.api.deps import CurrentUser, DB, APIKeyAuth
from eudi_connect.models.compliance.models import (
    ComplianceRequirement,
    ComplianceScan,
    ComplianceScanResult,
    RequirementCategory,
    RequirementLevel,
    ScanStatus,
    ResultStatus,
)
from eudi_connect.services.compliance_scanner import ComplianceScannerService

router = APIRouter()


class ComplianceRequirementCreate(BaseModel):
    """Compliance requirement creation model."""
    code: str = Field(..., description="Unique code for the requirement")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed description")
    category: RequirementCategory = Field(..., description="Requirement category")
    level: RequirementLevel = Field(..., description="Requirement level (mandatory, recommended, optional)")
    validation_method: str = Field(..., description="Method used for validation")
    validation_script: Optional[str] = Field(None, description="Optional script for custom validation")
    legal_reference: Optional[str] = Field(None, description="Reference to legal text in eIDAS 2")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    version: str = Field("1.0.0", description="Version of the requirement")
    

class ComplianceRequirementResponse(BaseModel):
    """Compliance requirement response model."""
    id: UUID
    code: str
    name: str
    description: str
    category: RequirementCategory
    level: RequirementLevel
    validation_method: str
    legal_reference: Optional[str] = None
    metadata: Dict[str, Any]
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ComplianceScanCreate(BaseModel):
    """Compliance scan creation request model."""
    name: str = Field(..., description="Name of the scan")
    wallet_name: str = Field(..., description="Name of the wallet being scanned")
    wallet_version: str = Field(..., description="Version of the wallet")
    wallet_provider: str = Field(..., description="Provider of the wallet")
    description: Optional[str] = Field(None, description="Optional description")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional scan configuration")
    requirements: Optional[List[UUID]] = Field(None, description="Optional list of requirement IDs to scan (default: all active)")


class ComplianceScanResponse(BaseModel):
    """Compliance scan response model."""
    id: UUID
    merchant_id: UUID
    name: str
    description: Optional[str] = None
    status: ScanStatus
    wallet_name: str
    wallet_version: str
    wallet_provider: str
    config: Dict[str, Any]
    total_requirements: int
    passed_requirements: int
    failed_requirements: int
    warning_requirements: int
    na_requirements: int
    manual_check_requirements: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ComplianceScanResultResponse(BaseModel):
    """Compliance scan result response model."""
    id: UUID
    scan_id: UUID
    requirement_id: UUID
    status: ResultStatus
    message: Optional[str] = None
    details: Dict[str, Any]
    execution_time_ms: int
    executed_at: datetime
    remediation_steps: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    requirement: Optional[ComplianceRequirementResponse] = None


async def run_compliance_scan(
    db: DB,
    scan_id: UUID,
    requirements: Optional[List[UUID]] = None,
) -> None:
    """Background task to run a compliance scan.
    
    Args:
        db: Database session
        scan_id: ID of the scan to run
        requirements: Optional list of requirement IDs to scan
    """
    # Create scanner service
    scanner = ComplianceScannerService()
    
    try:
        # Run the scan
        await scanner.run_scan(scan_id, requirements)
    except Exception as e:
        # Log the error
        logging.error(f"Error running compliance scan {scan_id}: {e}", exc_info=True)


@router.get("/requirements", response_model=List[ComplianceRequirementResponse])
async def list_requirements(
    db: DB,
    current_user: CurrentUser,
    category: Optional[RequirementCategory] = Query(None, description="Filter by category"),
    level: Optional[RequirementLevel] = Query(None, description="Filter by level"),
) -> List[ComplianceRequirementResponse]:
    """List all active compliance requirements.
    
    Optionally filter by category or level.
    """
    scanner = ComplianceScannerService(db)
    requirements = await scanner.get_active_requirements(category, level)
    return [ComplianceRequirementResponse.model_validate(r.__dict__) for r in requirements]


@router.post("/scans", response_model=ComplianceScanResponse)
async def create_scan(
    db: DB,
    current_user: CurrentUser,
    request: ComplianceScanCreate,
    background_tasks: BackgroundTasks,
) -> ComplianceScanResponse:
    """Create and start a new compliance scan."""
    # Create scanner service
    scanner = ComplianceScannerService(db)
    
    # Create scan
    scan = await scanner.create_scan(
        merchant_id=current_user.merchant_id,
        name=request.name,
        wallet_name=request.wallet_name,
        wallet_version=request.wallet_version,
        wallet_provider=request.wallet_provider,
        description=request.description,
        config=request.config,
    )
    
    # Start scan in background
    background_tasks.add_task(run_compliance_scan, db, scan.id, request.requirements)
    
    return ComplianceScanResponse.model_validate(scan.__dict__)


@router.get("/scans", response_model=List[ComplianceScanResponse])
async def list_scans(
    db: DB,
    current_user: CurrentUser,
    status: Optional[ScanStatus] = Query(None, description="Filter by status"),
) -> List[ComplianceScanResponse]:
    """List all compliance scans for the merchant.
    
    Optionally filter by status.
    """
    stmt = select(ComplianceScan).where(ComplianceScan.merchant_id == current_user.merchant_id)
    
    if status:
        stmt = stmt.where(ComplianceScan.status == status)
        
    stmt = stmt.order_by(ComplianceScan.created_at.desc())
    
    result = await db.execute(stmt)
    scans = result.scalars().all()
    return [ComplianceScanResponse.model_validate(s.__dict__) for s in scans]


@router.get("/scans/{scan_id}", response_model=ComplianceScanResponse)
async def get_scan(
    db: DB,
    current_user: CurrentUser,
    scan_id: UUID = Path(..., description="ID of the scan"),
) -> ComplianceScanResponse:
    """Get a specific compliance scan."""
    result = await db.execute(
        select(ComplianceScan)
        .where(ComplianceScan.id == scan_id)
        .where(ComplianceScan.merchant_id == current_user.merchant_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    return ComplianceScanResponse.model_validate(scan.__dict__)


@router.get("/scans/{scan_id}/results", response_model=List[ComplianceScanResultResponse])
async def get_scan_results(
    db: DB,
    current_user: CurrentUser,
    scan_id: UUID = Path(..., description="ID of the scan"),
    status: Optional[ResultStatus] = Query(None, description="Filter by result status"),
) -> List[ComplianceScanResultResponse]:
    """Get results for a specific compliance scan.
    
    Optionally filter by result status.
    """
    # First verify the scan belongs to the merchant
    result = await db.execute(
        select(ComplianceScan)
        .where(ComplianceScan.id == scan_id)
        .where(ComplianceScan.merchant_id == current_user.merchant_id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    # Get scan results with requirements
    scanner = ComplianceScannerService(db)
    scan_obj, results = await scanner.get_scan_results(scan_id)
    
    # Filter by status if provided
    if status:
        results = [r for r in results if r.status == status]
    
    # Fetch requirements for each result and create response objects
    response_results = []
    for result in results:
        requirement = await scanner.get_requirement(result.requirement_id) if result.requirement_id else None
        result_dict = result.__dict__.copy()
        result_dict["requirement"] = ComplianceRequirementResponse.model_validate(requirement.__dict__) if requirement else None
        response_results.append(ComplianceScanResultResponse.model_validate(result_dict))

    return response_results
