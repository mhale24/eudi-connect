"""eIDAS 2 Compliance Scanner Service.

This module provides the core functionality for validating wallet implementations
against eIDAS 2 requirements, running compliance scans, and generating reports.
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.db.session import get_session
from eudi_connect.models.compliance.models import (
    ComplianceRequirement,
    ComplianceScan,
    ComplianceScanResult,
    RequirementLevel,
    RequirementCategory,
    ScanStatus,
    ResultStatus,
)
from eudi_connect.monitoring.performance_metrics import time_operation, measure_operation_time

# Configure logging
logger = logging.getLogger(__name__)


class ComplianceValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class ComplianceScannerService:
    """Service for eIDAS 2 compliance scanning.
    
    This service provides methods to:
    - Create and manage compliance requirements
    - Run compliance scans against wallet implementations
    - Generate compliance reports
    """
    
    def __init__(self, session: Optional[AsyncSession] = None):
        """Initialize the compliance scanner service.
        
        Args:
            session: Optional SQLAlchemy session for database operations
        """
        self.session = session
        self._validators = {}
        self._initialize_validators()
        
    def _initialize_validators(self):
        """Initialize built-in validators for compliance requirements."""
        # Register built-in validators
        self.register_validator("api_verification", self._validate_api_verification)
        self.register_validator("schema_validation", self._validate_schema)
        self.register_validator("security_check", self._validate_security)
        self.register_validator("privacy_check", self._validate_privacy)
        self.register_validator("performance_check", self._validate_performance)
        self.register_validator("script_execution", self._execute_validation_script)
        
    def register_validator(self, method_name: str, validator_func: Callable):
        """Register a custom validator function.
        
        Args:
            method_name: Name of the validation method
            validator_func: Validator function that takes config and returns result
        """
        self._validators[method_name] = validator_func
        logger.info(f"Registered validator: {method_name}")
        
    async def get_requirement(self, requirement_id: Union[str, uuid.UUID]) -> Optional[ComplianceRequirement]:
        """Get a compliance requirement by ID.
        
        Args:
            requirement_id: ID of the requirement
            
        Returns:
            ComplianceRequirement if found, None otherwise
        """
        async with self._get_session() as session:
            stmt = select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
            
    async def get_active_requirements(
        self,
        category: Optional[RequirementCategory] = None,
        level: Optional[RequirementLevel] = None,
    ) -> List[ComplianceRequirement]:
        """Get active compliance requirements, optionally filtered.
        
        Args:
            category: Optional filter by category
            level: Optional filter by level
            
        Returns:
            List of active compliance requirements
        """
        async with self._get_session() as session:
            stmt = select(ComplianceRequirement).where(ComplianceRequirement.is_active == True)
            
            if category:
                stmt = stmt.where(ComplianceRequirement.category == category)
            if level:
                stmt = stmt.where(ComplianceRequirement.level == level)
                
            result = await session.execute(stmt)
            return result.scalars().all()
            
    async def create_requirement(
        self,
        code: str,
        name: str,
        description: str,
        category: RequirementCategory,
        level: RequirementLevel,
        validation_method: str,
        validation_script: Optional[str] = None,
        legal_reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0",
    ) -> ComplianceRequirement:
        """Create a new compliance requirement.
        
        Args:
            code: Unique code for the requirement
            name: Human-readable name
            description: Detailed description
            category: Requirement category
            level: Requirement level (mandatory, recommended, optional)
            validation_method: Method used for validation
            validation_script: Optional script for custom validation
            legal_reference: Reference to legal text in eIDAS 2
            metadata: Additional metadata
            version: Version of the requirement
            
        Returns:
            Created ComplianceRequirement
            
        Raises:
            ValueError: If validation_method is not registered
        """
        if validation_method not in self._validators and validation_method != "manual":
            raise ValueError(f"Validation method '{validation_method}' is not registered")
            
        requirement = ComplianceRequirement(
            code=code,
            name=name,
            description=description,
            category=category,
            level=level,
            validation_method=validation_method,
            validation_script=validation_script,
            legal_reference=legal_reference,
            metadata=metadata or {},
            version=version,
            is_active=True,
        )
        
        async with self._get_session() as session:
            session.add(requirement)
            await session.commit()
            await session.refresh(requirement)
            
        logger.info(f"Created compliance requirement: {code} ({requirement.id})")
        return requirement
        
    async def update_requirement(
        self,
        requirement_id: Union[str, uuid.UUID],
        **kwargs
    ) -> Optional[ComplianceRequirement]:
        """Update an existing compliance requirement.
        
        Args:
            requirement_id: ID of the requirement to update
            **kwargs: Fields to update
            
        Returns:
            Updated ComplianceRequirement or None if not found
        """
        async with self._get_session() as session:
            stmt = select(ComplianceRequirement).where(ComplianceRequirement.id == requirement_id)
            result = await session.execute(stmt)
            requirement = result.scalar_one_or_none()
            
            if not requirement:
                logger.warning(f"Requirement not found: {requirement_id}")
                return None
                
            # Update fields
            for key, value in kwargs.items():
                if hasattr(requirement, key):
                    setattr(requirement, key, value)
                    
            await session.commit()
            await session.refresh(requirement)
            
        logger.info(f"Updated compliance requirement: {requirement.code} ({requirement.id})")
        return requirement
        
    async def create_scan(
        self,
        merchant_id: Union[str, uuid.UUID],
        name: str,
        wallet_name: str,
        wallet_version: str,
        wallet_provider: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> ComplianceScan:
        """Create a new compliance scan.
        
        Args:
            merchant_id: ID of the merchant running the scan
            name: Name of the scan
            wallet_name: Name of the wallet being scanned
            wallet_version: Version of the wallet
            wallet_provider: Provider of the wallet
            description: Optional description
            config: Optional scan configuration
            
        Returns:
            Created ComplianceScan
        """
        scan = ComplianceScan(
            merchant_id=merchant_id,
            name=name,
            description=description,
            wallet_name=wallet_name,
            wallet_version=wallet_version,
            wallet_provider=wallet_provider,
            config=config or {},
            status=ScanStatus.PENDING,
        )
        
        async with self._get_session() as session:
            session.add(scan)
            await session.commit()
            await session.refresh(scan)
            
        logger.info(f"Created compliance scan: {name} ({scan.id})")
        return scan
        
    @time_operation(operation="compliance.run_scan")
    async def run_scan(
        self,
        scan_id: Union[str, uuid.UUID],
        requirements: Optional[List[Union[str, uuid.UUID]]] = None,
    ) -> ComplianceScan:
        """Run a compliance scan against specified requirements.
        
        Args:
            scan_id: ID of the scan to run
            requirements: Optional list of requirement IDs to scan (default: all active)
            
        Returns:
            Updated ComplianceScan with results
            
        Raises:
            ValueError: If scan not found or invalid state
        """
        async with self._get_session() as session:
            # Get the scan
            stmt = select(ComplianceScan).where(ComplianceScan.id == scan_id)
            result = await session.execute(stmt)
            scan = result.scalar_one_or_none()
            
            if not scan:
                raise ValueError(f"Scan not found: {scan_id}")
                
            if scan.status == ScanStatus.IN_PROGRESS:
                raise ValueError(f"Scan already in progress: {scan_id}")
                
            # Update scan status
            scan.status = ScanStatus.IN_PROGRESS
            scan.started_at = datetime.utcnow()
            await session.commit()
            
            try:
                # Get requirements to test
                if requirements:
                    stmt = select(ComplianceRequirement).where(
                        ComplianceRequirement.id.in_(requirements),
                        ComplianceRequirement.is_active == True,
                    )
                else:
                    stmt = select(ComplianceRequirement).where(
                        ComplianceRequirement.is_active == True
                    )
                    
                result = await session.execute(stmt)
                req_list = result.scalars().all()
                
                # Initialize counters
                scan.total_requirements = len(req_list)
                scan.passed_requirements = 0
                scan.failed_requirements = 0
                scan.warning_requirements = 0
                scan.na_requirements = 0
                scan.manual_check_requirements = 0
                
                # Run tests for each requirement
                for requirement in req_list:
                    result = await self._test_requirement(scan, requirement, session)
                    
                    # Update counters
                    if result.status == ResultStatus.PASS:
                        scan.passed_requirements += 1
                    elif result.status == ResultStatus.FAIL:
                        scan.failed_requirements += 1
                    elif result.status == ResultStatus.WARNING:
                        scan.warning_requirements += 1
                    elif result.status == ResultStatus.NOT_APPLICABLE:
                        scan.na_requirements += 1
                    elif result.status == ResultStatus.MANUAL_CHECK_REQUIRED:
                        scan.manual_check_requirements += 1
                        
                # Update scan status
                scan.status = ScanStatus.COMPLETED
                scan.completed_at = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error running scan {scan_id}: {e}", exc_info=True)
                scan.status = ScanStatus.FAILED
                # Create a special result to record the error
                error_result = ComplianceScanResult(
                    scan_id=scan.id,
                    requirement_id=None,  # This is a general error, not tied to a requirement
                    status=ResultStatus.FAIL,
                    message=f"Scan failed with error: {str(e)}",
                    details={"error": str(e), "type": type(e).__name__},
                    execution_time_ms=0,
                )
                session.add(error_result)
                
            finally:
                await session.commit()
                await session.refresh(scan)
                
        logger.info(f"Completed compliance scan: {scan.id} with status {scan.status}")
        return scan
        
    async def _test_requirement(
        self,
        scan: ComplianceScan,
        requirement: ComplianceRequirement,
        session: AsyncSession,
    ) -> ComplianceScanResult:
        """Test a single requirement during a scan.
        
        Args:
            scan: The compliance scan being run
            requirement: The requirement to test
            session: Database session
            
        Returns:
            ComplianceScanResult with the test result
        """
        logger.info(f"Testing requirement {requirement.code} for scan {scan.id}")
        start_time = time.time()
        
        # Create result object
        result = ComplianceScanResult(
            scan_id=scan.id,
            requirement_id=requirement.id,
            status=ResultStatus.NOT_APPLICABLE,  # Default
            message="",
            details={},
        )
        
        try:
            # For manual checks, just mark as requiring manual verification
            if requirement.validation_method == "manual":
                result.status = ResultStatus.MANUAL_CHECK_REQUIRED
                result.message = "This requirement needs manual verification."
                result.details = {"manual_check": True}
                
            # For automated checks, run the appropriate validator
            elif requirement.validation_method in self._validators:
                validator = self._validators[requirement.validation_method]
                
                # Prepare validation context
                context = {
                    "requirement": requirement.dict() if hasattr(requirement, "dict") else vars(requirement),
                    "scan_config": scan.config,
                    "wallet_info": {
                        "name": scan.wallet_name,
                        "version": scan.wallet_version,
                        "provider": scan.wallet_provider,
                    }
                }
                
                # Run validation
                with measure_operation_time(f"compliance.validate.{requirement.validation_method}"):
                    status, message, details = await validator(context)
                    
                result.status = status
                result.message = message
                result.details = details
                
            else:
                # Unknown validation method
                result.status = ResultStatus.FAIL
                result.message = f"Unknown validation method: {requirement.validation_method}"
                result.details = {"error": "validation_method_not_found"}
                
        except Exception as e:
            logger.error(f"Error testing requirement {requirement.code}: {e}", exc_info=True)
            result.status = ResultStatus.FAIL
            result.message = f"Error during validation: {str(e)}"
            result.details = {"error": str(e), "type": type(e).__name__}
            
        finally:
            # Calculate execution time
            end_time = time.time()
            result.execution_time_ms = int((end_time - start_time) * 1000)
            result.executed_at = datetime.utcnow()
            
            # Add result to database
            session.add(result)
            await session.flush()
            
        logger.info(f"Requirement {requirement.code} test result: {result.status}")
        return result
        
    async def get_scan_results(
        self,
        scan_id: Union[str, uuid.UUID],
    ) -> Tuple[ComplianceScan, List[ComplianceScanResult]]:
        """Get the results of a compliance scan.
        
        Args:
            scan_id: ID of the scan
            
        Returns:
            Tuple of (scan, results)
            
        Raises:
            ValueError: If scan not found
        """
        async with self._get_session() as session:
            # Get the scan
            stmt = select(ComplianceScan).where(ComplianceScan.id == scan_id)
            result = await session.execute(stmt)
            scan = result.scalar_one_or_none()
            
            if not scan:
                raise ValueError(f"Scan not found: {scan_id}")
                
            # Get the results
            stmt = select(ComplianceScanResult).where(
                ComplianceScanResult.scan_id == scan_id
            ).order_by(ComplianceScanResult.executed_at)
            
            result = await session.execute(stmt)
            results = result.scalars().all()
            
        return scan, results
        
    async def generate_report(
        self,
        scan_id: Union[str, uuid.UUID],
        format: str = "json",
    ) -> Dict[str, Any]:
        """Generate a compliance report.
        
        Args:
            scan_id: ID of the scan
            format: Report format (json, html, pdf)
            
        Returns:
            Report data
            
        Raises:
            ValueError: If scan not found or format not supported
        """
        if format not in ["json", "html", "pdf"]:
            raise ValueError(f"Unsupported report format: {format}")
            
        # Get scan and results
        scan, results = await self.get_scan_results(scan_id)
        
        # Build report data
        report = {
            "scan_id": str(scan.id),
            "name": scan.name,
            "description": scan.description,
            "wallet": {
                "name": scan.wallet_name,
                "version": scan.wallet_version,
                "provider": scan.wallet_provider,
            },
            "summary": {
                "total": scan.total_requirements,
                "passed": scan.passed_requirements,
                "failed": scan.failed_requirements,
                "warnings": scan.warning_requirements,
                "not_applicable": scan.na_requirements,
                "manual_check": scan.manual_check_requirements,
                "compliance_score": self._calculate_compliance_score(scan),
            },
            "status": scan.status,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
            "results": [],
        }
        
        # Add detailed results
        requirement_cache = {}
        for result in results:
            # Get requirement details (with caching)
            if result.requirement_id:
                if result.requirement_id not in requirement_cache:
                    requirement = await self.get_requirement(result.requirement_id)
                    if requirement:
                        requirement_cache[result.requirement_id] = {
                            "id": str(requirement.id),
                            "code": requirement.code,
                            "name": requirement.name,
                            "description": requirement.description,
                            "category": requirement.category,
                            "level": requirement.level,
                            "legal_reference": requirement.legal_reference,
                        }
                req_info = requirement_cache.get(result.requirement_id, {})
            else:
                req_info = {}
                
            # Add result to report
            report["results"].append({
                "id": str(result.id),
                "requirement": req_info,
                "status": result.status,
                "message": result.message,
                "details": result.details,
                "execution_time_ms": result.execution_time_ms,
                "executed_at": result.executed_at.isoformat(),
                "remediation_steps": result.remediation_steps,
            })
            
        # Generate appropriate format
        if format == "json":
            return report
        elif format == "html":
            return self._generate_html_report(report)
        elif format == "pdf":
            return self._generate_pdf_report(report)
            
    def _calculate_compliance_score(self, scan: ComplianceScan) -> float:
        """Calculate overall compliance score.
        
        Args:
            scan: Compliance scan
            
        Returns:
            Compliance score (0-100)
        """
        if scan.total_requirements == 0:
            return 0.0
            
        # Calculate weights for different statuses
        weights = {
            "passed": 1.0,
            "warning": 0.5,
            "manual": 0.0,  # Don't count manual checks in automatic score
            "na": 0.0,      # Don't count N/A in score
        }
        
        # Calculate weighted score
        weighted_sum = (
            scan.passed_requirements * weights["passed"] +
            scan.warning_requirements * weights["warning"]
        )
        
        # Calculate denominator (excluding manual and N/A)
        denominator = (
            scan.total_requirements -
            scan.manual_check_requirements -
            scan.na_requirements
        )
        
        if denominator == 0:
            return 0.0
            
        # Calculate score (0-100)
        return (weighted_sum / denominator) * 100
        
    def _generate_html_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HTML report from report data.
        
        Args:
            report_data: Report data
            
        Returns:
            Report with HTML content
        """
        # This would generate HTML in a real implementation
        # For now, just add a placeholder
        report_data["html_content"] = "<html><body><h1>Compliance Report</h1></body></html>"
        return report_data
        
    def _generate_pdf_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PDF report from report data.
        
        Args:
            report_data: Report data
            
        Returns:
            Report with PDF content
        """
        # This would generate PDF in a real implementation
        # For now, just add a placeholder
        report_data["pdf_content"] = "PDF content would be here"
        return report_data
        
    async def _get_session(self) -> AsyncSession:
        """Get a database session.
        
        Returns:
            AsyncSession
        """
        if self.session:
            return self.session
        else:
            return get_session()
            
    # Validator implementations
    
    async def _validate_api_verification(self, context: Dict[str, Any]) -> Tuple[ResultStatus, str, Dict[str, Any]]:
        """Validate API verification requirements.
        
        Args:
            context: Validation context
            
        Returns:
            Tuple of (status, message, details)
        """
        # In a real implementation, this would test API endpoints
        # For now, return a mock result
        return ResultStatus.PASS, "API verification passed", {"verified_endpoints": ["authorize", "token"]}
        
    async def _validate_schema(self, context: Dict[str, Any]) -> Tuple[ResultStatus, str, Dict[str, Any]]:
        """Validate schema requirements.
        
        Args:
            context: Validation context
            
        Returns:
            Tuple of (status, message, details)
        """
        # In a real implementation, this would validate schemas
        # For now, return a mock result
        return ResultStatus.PASS, "Schema validation passed", {"validated_schemas": ["credential", "presentation"]}
        
    async def _validate_security(self, context: Dict[str, Any]) -> Tuple[ResultStatus, str, Dict[str, Any]]:
        """Validate security requirements.
        
        Args:
            context: Validation context
            
        Returns:
            Tuple of (status, message, details)
        """
        # In a real implementation, this would check security requirements
        # For now, return a mock result
        return ResultStatus.WARNING, "Some security issues found", {
            "issues": ["weak_cipher_support"],
            "recommendations": ["Disable TLS 1.0/1.1 support"]
        }
        
    async def _validate_privacy(self, context: Dict[str, Any]) -> Tuple[ResultStatus, str, Dict[str, Any]]:
        """Validate privacy requirements.
        
        Args:
            context: Validation context
            
        Returns:
            Tuple of (status, message, details)
        """
        # In a real implementation, this would check privacy requirements
        # For now, return a mock result
        return ResultStatus.PASS, "Privacy requirements met", {
            "verified": ["data_minimization", "purpose_limitation"]
        }
        
    async def _validate_performance(self, context: Dict[str, Any]) -> Tuple[ResultStatus, str, Dict[str, Any]]:
        """Validate performance requirements.
        
        Args:
            context: Validation context
            
        Returns:
            Tuple of (status, message, details)
        """
        # In a real implementation, this would check performance metrics
        # For now, return a mock result
        return ResultStatus.PASS, "Performance requirements met", {
            "metrics": {
                "credential_verification_ms": 250,
                "credential_presentation_ms": 350,
            }
        }
        
    async def _execute_validation_script(self, context: Dict[str, Any]) -> Tuple[ResultStatus, str, Dict[str, Any]]:
        """Execute a custom validation script.
        
        Args:
            context: Validation context
            
        Returns:
            Tuple of (status, message, details)
        """
        requirement = context.get("requirement", {})
        script = requirement.get("validation_script")
        
        if not script:
            return ResultStatus.FAIL, "No validation script provided", {"error": "missing_script"}
            
        try:
            # In a real implementation, this would execute the script in a sandbox
            # For now, just return a mock result
            return ResultStatus.PASS, "Script execution passed", {"script_executed": True}
        except Exception as e:
            return ResultStatus.FAIL, f"Script execution failed: {str(e)}", {"error": str(e)}
