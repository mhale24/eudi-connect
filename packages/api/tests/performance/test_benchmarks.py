"""Micro-benchmarks for core operations."""
import asyncio
from typing import AsyncGenerator, Dict
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.models.credential import CredentialType
from tests.conftest import app_fixture, auth_headers, client, db, test_merchant


@pytest.mark.benchmark(
    min_rounds=50,
    max_time=2.0,
    min_time=0.1,
    timer=asyncio.get_event_loop().time,
)
async def test_credential_issuance_benchmark(
    benchmark,
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Benchmark credential issuance performance."""
    # Create test credential type
    cred_type = CredentialType(
        name="BenchmarkCredential",
        version="1.0",
        context=["https://www.w3.org/2018/credentials/v1"],
        schema={"type": "object", "properties": {"name": {"type": "string"}}},
        is_active=True,
    )
    db.add(cred_type)
    await db.commit()

    async def issue_credential():
        return await client.post(
            "/api/v1/credentials/issue",
            headers=auth_headers,
            json={
                "type_id": str(cred_type.id),
                "subject_did": "did:web:test.com",
                "claims": {"name": "Benchmark Test"},
            },
        )

    # Run benchmark
    result = await benchmark(issue_credential)
    assert result.status_code == 200

    # Verify performance target
    assert benchmark.stats["mean"] < 0.8  # 800ms target


@pytest.mark.benchmark(
    min_rounds=50,
    max_time=2.0,
    min_time=0.1,
    timer=asyncio.get_event_loop().time,
)
async def test_credential_verification_benchmark(
    benchmark,
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Benchmark credential verification performance."""
    # Create a test credential for verification
    test_credential = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiableCredential", "BenchmarkCredential"],
        "issuer": "did:web:test.com",
        "issuanceDate": "2025-05-26T09:21:56Z",
        "credentialSubject": {
            "id": "did:web:subject.com",
            "name": "Benchmark Subject"
        },
        "proof": {
            "type": "Ed25519Signature2020",
            "created": "2025-05-26T09:21:56Z",
            "verificationMethod": "did:web:test.com#key1",
            "proofPurpose": "assertionMethod",
            "proofValue": "test123"
        }
    }

    async def verify_credential():
        return await client.post(
            "/api/v1/credentials/verify",
            headers=auth_headers,
            json={"credential": test_credential},
        )

    # Run benchmark
    result = await benchmark(verify_credential)
    assert result.status_code == 200

    # Verify performance target
    assert benchmark.stats["mean"] < 0.8  # 800ms target


@pytest.mark.benchmark(
    min_rounds=50,
    max_time=2.0,
    min_time=0.1,
    timer=asyncio.get_event_loop().time,
)
async def test_wallet_session_creation_benchmark(
    benchmark,
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Benchmark wallet session creation performance."""
    async def create_session():
        return await client.post(
            "/api/v1/wallet/sessions",
            headers=auth_headers,
            json={
                "wallet_type": "eudi",
                "protocol": "openid4vp",
                "request_payload": {
                    "scope": "openid",
                    "response_type": "id_token",
                    "client_id": "benchmark_client",
                    "nonce": str(uuid4()),
                },
            },
        )

    # Run benchmark
    result = await benchmark(create_session)
    assert result.status_code == 200

    # Verify performance target
    assert benchmark.stats["mean"] < 0.1  # 100ms target for session creation


@pytest.mark.benchmark(
    min_rounds=50,
    max_time=2.0,
    min_time=0.1,
    timer=asyncio.get_event_loop().time,
)
async def test_compliance_scan_creation_benchmark(
    benchmark,
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Benchmark compliance scan creation performance."""
    async def create_scan():
        return await client.post(
            "/api/v1/compliance/scans",
            headers=auth_headers,
            json={
                "scan_type": "full",
                "metadata": {"benchmark": True},
            },
        )

    # Run benchmark
    result = await benchmark(create_scan)
    assert result.status_code == 200

    # Verify performance target
    assert benchmark.stats["mean"] < 0.2  # 200ms target for scan creation
