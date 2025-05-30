"""Advanced load testing with detailed metrics."""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

from locust import HttpUser, between, events, task
from locust.env import Environment
from locust.stats import RequestStats

from tests.performance.metrics import MetricsCollector


class DetailedStats:
    """Detailed performance statistics."""

    def __init__(self):
        """Initialize stats collector."""
        self.metrics = MetricsCollector()
        self.start_time = datetime.now()
        self.total_requests = 0
        self.failed_requests = 0
        self.response_times: Dict[str, list] = {}

    def log_request(
        self,
        name: str,
        response_time: float,
        response_length: int,
        exception: Optional[Exception] = None,
    ) -> None:
        """Log request details."""
        if name not in self.response_times:
            self.response_times[name] = []
        self.response_times[name].append(response_time)
        
        self.total_requests += 1
        if exception:
            self.failed_requests += 1

    def get_stats(self) -> Dict:
        """Get detailed statistics."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            "duration": duration,
            "total_requests": self.total_requests,
            "requests_per_second": self.total_requests / duration if duration > 0 else 0,
            "failure_rate": (self.failed_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "endpoints": {},
        }

        for name, times in self.response_times.items():
            if times:
                sorted_times = sorted(times)
                total = len(sorted_times)
                stats["endpoints"][name] = {
                    "requests": total,
                    "min_response_time": min(times),
                    "max_response_time": max(times),
                    "avg_response_time": sum(times) / total,
                    "median_response_time": sorted_times[total // 2],
                    "p95_response_time": sorted_times[int(total * 0.95)],
                }

        return stats


class EUDIConnectLoadTest(HttpUser):
    """Advanced load test for EUDI-Connect API."""

    wait_time = between(1, 3)  # Faster pace for load testing
    detailed_stats = DetailedStats()

    def on_start(self):
        """Set up test data."""
        self.api_key = "test_api_key"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

        # Create test credential type
        response = self.client.post(
            "/api/v1/credentials/types",
            headers=self.headers,
            json={
                "name": "LoadTestCredential",
                "version": "1.0",
                "context": ["https://www.w3.org/2018/credentials/v1"],
                "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
            },
        )
        self.credential_type_id = response.json()["id"]

    @task(4)  # Highest priority
    def credential_exchange_flow(self):
        """Complete credential exchange flow."""
        # Issue credential
        start_time = datetime.now()
        issue_response = self.client.post(
            "/api/v1/credentials/issue",
            headers=self.headers,
            json={
                "type_id": self.credential_type_id,
                "subject_did": f"did:web:test{uuid.uuid4()}",
                "claims": {"name": "Load Test"},
            },
            name="credential_issuance",
        )
        
        if issue_response.status_code == 200:
            # Verify credential
            verify_response = self.client.post(
                "/api/v1/credentials/verify",
                headers=self.headers,
                json={"credential": issue_response.json()},
                name="credential_verification",
            )
            
            # Log complete flow timing
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self.detailed_stats.log_request("credential_exchange_flow", duration * 1000, 0)

    @task(2)
    def wallet_operations(self):
        """Wallet session operations."""
        # Create session
        create_response = self.client.post(
            "/api/v1/wallet/sessions",
            headers=self.headers,
            json={
                "wallet_type": "eudi",
                "protocol": "openid4vp",
                "request_payload": {
                    "scope": "openid",
                    "response_type": "id_token",
                    "client_id": f"loadtest_{uuid.uuid4()}",
                    "nonce": str(uuid.uuid4()),
                },
            },
            name="wallet_session_creation",
        )
        
        if create_response.status_code == 200:
            session_id = create_response.json()["id"]
            # Get session status
            self.client.get(
                f"/api/v1/wallet/sessions/{session_id}",
                headers=self.headers,
                name="wallet_session_status",
            )

    @task(1)
    def compliance_operations(self):
        """Compliance operations."""
        # Create scan
        create_response = self.client.post(
            "/api/v1/compliance/scans",
            headers=self.headers,
            json={
                "scan_type": "full",
                "metadata": {"load_test": True},
            },
            name="compliance_scan_creation",
        )
        
        if create_response.status_code == 200:
            scan_id = create_response.json()["id"]
            # Get scan results
            self.client.get(
                f"/api/v1/compliance/scans/{scan_id}",
                headers=self.headers,
                name="compliance_scan_results",
            )


@events.test_start.add_listener
def on_test_start(environment: Environment, **kwargs):
    """Test start handler."""
    print("Starting load test with detailed metrics...")


@events.test_stop.add_listener
def on_test_stop(environment: Environment, **kwargs):
    """Test stop handler."""
    stats = environment.runner.stats
    detailed_stats = environment.runner.user_classes[0].detailed_stats

    print("\n=== Load Test Report ===")
    
    # Overall statistics
    print("\nOverall Statistics:")
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Median Response Time: {stats.total.median_response_time}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95)}ms")
    print(f"Requests/sec: {stats.total.current_rps}")

    # Endpoint-specific statistics
    print("\nEndpoint Statistics:")
    for name, endpoint_stats in detailed_stats.get_stats()["endpoints"].items():
        print(f"\n{name}:")
        print(f"  Requests: {endpoint_stats['requests']}")
        print(f"  Median Response Time: {endpoint_stats['median_response_time']:.2f}ms")
        print(f"  95th Percentile: {endpoint_stats['p95_response_time']:.2f}ms")
        print(f"  Min/Max: {endpoint_stats['min_response_time']:.2f}ms / {endpoint_stats['max_response_time']:.2f}ms")

    # Resource usage
    print("\nResource Usage:")
    resource_stats = detailed_stats.metrics.get_resource_limits()
    for resource, limit in resource_stats.items():
        print(f"  {resource}: {limit}")

    print("\n=== End Report ===\n")
