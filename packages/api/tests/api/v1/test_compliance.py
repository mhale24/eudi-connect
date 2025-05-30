from typing import Dict
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.models.compliance import models

pytestmark = pytest.mark.asyncio


async def test_list_requirements_empty(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test listing compliance requirements when none exist."""
    response = await client.get("/api/v1/compliance/requirements", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


async def test_list_requirements(
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Test listing compliance requirements."""
    # Create test requirement
    requirement = ComplianceRequirement(
        code="TEST-001",
        name="Test Requirement",
        description="A test requirement",
        category="security",
        severity="high",
        validation_rules={"type": "test"},
        is_active=True,
    )
    db.add(requirement)
    await db.commit()

    response = await client.get("/api/v1/compliance/requirements", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "TEST-001"
    assert data[0]["name"] == "Test Requirement"
    assert data[0]["category"] == "security"


async def test_create_scan(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test creating a compliance scan."""
    response = await client.post(
        "/api/v1/compliance/scans",
        headers=auth_headers,
        json={
            "scan_type": "full",
            "metadata": {"test": "metadata"},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["scan_type"] == "full"
    assert data["metadata"] == {"test": "metadata"}


async def test_create_scan_invalid_type(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test creating a scan with invalid type."""
    response = await client.post(
        "/api/v1/compliance/scans",
        headers=auth_headers,
        json={
            "scan_type": "invalid",
            "metadata": {},
        },
    )
    assert response.status_code == 422


async def test_list_scans(
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
    auth_headers: Dict[str, str],
) -> None:
    """Test listing compliance scans."""
    # Create test scan
    scan = ComplianceScan(
        merchant_id=test_merchant["merchant_id"],
        status="completed",
        scan_type="full",
        metadata={"test": "metadata"},
    )
    db.add(scan)
    await db.commit()

    response = await client.get("/api/v1/compliance/scans", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "completed"
    assert data[0]["scan_type"] == "full"


async def test_get_scan(
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
    auth_headers: Dict[str, str],
) -> None:
    """Test getting a specific compliance scan."""
    # Create test scan
    scan = ComplianceScan(
        merchant_id=test_merchant["merchant_id"],
        status="completed",
        scan_type="full",
        metadata={"test": "metadata"},
    )
    db.add(scan)
    await db.commit()

    response = await client.get(
        f"/api/v1/compliance/scans/{scan.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["scan_type"] == "full"


async def test_get_scan_not_found(
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Test getting a non-existent scan."""
    response = await client.get(
        f"/api/v1/compliance/scans/{uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_get_scan_results(
    client: AsyncClient,
    db: AsyncSession,
    test_merchant: Dict[str, str],
    auth_headers: Dict[str, str],
) -> None:
    """Test getting scan results."""
    # Create test requirement
    requirement = ComplianceRequirement(
        code="TEST-001",
        name="Test Requirement",
        description="A test requirement",
        category="security",
        severity="high",
        validation_rules={"type": "test"},
        is_active=True,
    )
    db.add(requirement)

    # Create test scan
    scan = ComplianceScan(
        merchant_id=test_merchant["merchant_id"],
        status="completed",
        scan_type="full",
        metadata={},
    )
    db.add(scan)

    # Create test result
    result = ComplianceScanResult(
        scan=scan,
        requirement=requirement,
        status="pass",
        details={"message": "Test passed"},
        evidence={"timestamp": "2025-05-26T09:21:56Z"},
    )
    db.add(result)
    await db.commit()

    response = await client.get(
        f"/api/v1/compliance/scans/{scan.id}/results",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "pass"
    assert data[0]["requirement"]["code"] == "TEST-001"
