"""Advanced performance benchmarks with detailed metrics."""
import asyncio
import time
from typing import AsyncGenerator, Dict, List
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.models.credential import CredentialType
from tests.conftest import app_fixture, auth_headers, client, db, test_merchant
from tests.performance.metrics import MetricsCollector


@pytest.mark.benchmark(
    min_rounds=100,  # Increased for better statistics
    max_time=5.0,
    min_time=0.1,
    timer=asyncio.get_event_loop().time,
)
async def test_credential_exchange_performance(
    benchmark,
    client: AsyncClient,
    db: AsyncSession,
    auth_headers: Dict[str, str],
) -> None:
    """Benchmark complete credential exchange flow with detailed metrics."""
    metrics = MetricsCollector()
    
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

    async def credential_exchange():
        # Step 1: Issue credential
        async with metrics.measure_endpoint("/api/v1/credentials/issue", "POST"):
            issue_response = await client.post(
                "/api/v1/credentials/issue",
                headers=auth_headers,
                json={
                    "type_id": str(cred_type.id),
                    "subject_did": f"did:web:test{uuid4()}",
                    "claims": {"name": "Advanced Benchmark"},
                },
            )
            assert issue_response.status_code == 200
            credential = issue_response.json()

        # Step 2: Verify credential
        async with metrics.measure_endpoint("/api/v1/credentials/verify", "POST"):
            verify_response = await client.post(
                "/api/v1/credentials/verify",
                headers=auth_headers,
                json={"credential": credential},
            )
            assert verify_response.status_code == 200

        return verify_response

    # Run benchmark
    start_time = time.perf_counter()
    result = await benchmark(credential_exchange)
    duration = time.perf_counter() - start_time

    # Print detailed metrics report
    metrics.print_report(duration)

    # Assert performance targets
    latency_percentiles = metrics.get_latency_percentiles()
    assert latency_percentiles["p95"] < 0.8  # 800ms target for P95
    assert latency_percentiles["p50"] < 0.3  # 300ms target for P50
    assert metrics.get_throughput(duration) > 10  # Min 10 RPS


@pytest.mark.benchmark(
    min_rounds=100,
    max_time=5.0,
    min_time=0.1,
    timer=asyncio.get_event_loop().time,
)
async def test_concurrent_wallet_sessions(
    benchmark,
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Benchmark concurrent wallet session creation."""
    metrics = MetricsCollector()
    
    async def create_concurrent_sessions():
        # Create 10 concurrent sessions
        async with metrics.measure_endpoint("/api/v1/wallet/sessions", "POST"):
            tasks = []
            for _ in range(10):
                tasks.append(
                    client.post(
                        "/api/v1/wallet/sessions",
                        headers=auth_headers,
                        json={
                            "wallet_type": "eudi",
                            "protocol": "openid4vp",
                            "request_payload": {
                                "scope": "openid",
                                "response_type": "id_token",
                                "client_id": f"benchmark_{uuid4()}",
                                "nonce": str(uuid4()),
                            },
                        },
                    )
                )
            responses = await asyncio.gather(*tasks)
            assert all(r.status_code == 200 for r in responses)
            return responses

    # Run benchmark
    start_time = time.perf_counter()
    result = await benchmark(create_concurrent_sessions)
    duration = time.perf_counter() - start_time

    # Print detailed metrics report
    metrics.print_report(duration)

    # Assert performance targets
    latency_percentiles = metrics.get_latency_percentiles()
    assert latency_percentiles["p95"] < 0.2  # 200ms target for P95
    assert metrics.get_throughput(duration) > 50  # Min 50 RPS for session creation


@pytest.mark.benchmark(
    min_rounds=50,
    max_time=5.0,
    min_time=0.1,
    timer=asyncio.get_event_loop().time,
)
async def test_compliance_scan_performance(
    benchmark,
    client: AsyncClient,
    auth_headers: Dict[str, str],
) -> None:
    """Benchmark compliance scanning with resource monitoring."""
    metrics = MetricsCollector()
    
    async def run_compliance_scan():
        async with metrics.measure_endpoint("/api/v1/compliance/scans", "POST"):
            # Create and start scan
            create_response = await client.post(
                "/api/v1/compliance/scans",
                headers=auth_headers,
                json={
                    "scan_type": "full",
                    "metadata": {"benchmark": True},
                },
            )
            assert create_response.status_code == 200
            scan_id = create_response.json()["id"]

            # Poll for completion
            for _ in range(10):  # Max 10 attempts
                status_response = await client.get(
                    f"/api/v1/compliance/scans/{scan_id}",
                    headers=auth_headers,
                )
                if status_response.json()["status"] == "completed":
                    break
                await asyncio.sleep(0.1)

            return status_response

    # Run benchmark
    start_time = time.perf_counter()
    result = await benchmark(run_compliance_scan)
    duration = time.perf_counter() - start_time

    # Print detailed metrics report
    metrics.print_report(duration)

    # Assert performance targets
    db_stats = metrics.get_db_stats()
    assert db_stats["avg_query_time"] < 0.1  # 100ms avg query time
    assert db_stats["index_usage_pct"] > 90  # >90% index usage

    memory_stats = metrics.get_memory_stats()
    assert memory_stats["max"] < 512  # Max 512MB memory usage
