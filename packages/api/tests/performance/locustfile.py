"""Load testing with Locust."""
import json
import uuid
from datetime import datetime, timedelta

from locust import HttpUser, between, task


class EUDIConnectUser(HttpUser):
    """Simulated EUDI-Connect API user."""

    # Wait between 1-5 seconds between tasks
    wait_time = between(1, 5)

    def on_start(self):
        """Set up test data when user starts."""
        # Create test merchant and get API key
        self.api_key = "test_api_key"  # In real tests, create this dynamically
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

    @task(3)  # Higher weight for credential operations
    def issue_credential(self):
        """Issue a credential."""
        self.client.post(
            "/api/v1/credentials/issue",
            headers=self.headers,
            json={
                "type_id": self.credential_type_id,
                "subject_did": f"did:web:test{uuid.uuid4()}",
                "claims": {"name": "Load Test"},
            },
        )

    @task(3)
    def verify_credential(self):
        """Verify a credential."""
        test_credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential", "LoadTestCredential"],
            "issuer": "did:web:test.com",
            "issuanceDate": datetime.utcnow().isoformat(),
            "credentialSubject": {
                "id": f"did:web:subject{uuid.uuid4()}",
                "name": "Load Test Subject"
            },
            "proof": {
                "type": "Ed25519Signature2020",
                "created": datetime.utcnow().isoformat(),
                "verificationMethod": "did:web:test.com#key1",
                "proofPurpose": "assertionMethod",
                "proofValue": str(uuid.uuid4())
            }
        }

        self.client.post(
            "/api/v1/credentials/verify",
            headers=self.headers,
            json={"credential": test_credential},
        )

    @task(2)
    def create_wallet_session(self):
        """Create a wallet session."""
        self.client.post(
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
        )

    @task(1)
    def create_compliance_scan(self):
        """Create a compliance scan."""
        self.client.post(
            "/api/v1/compliance/scans",
            headers=self.headers,
            json={
                "scan_type": "full",
                "metadata": {"load_test": True},
            },
        )

    @task(1)
    def get_usage_metrics(self):
        """Get usage metrics."""
        self.client.get(
            "/api/v1/billing/usage",
            headers=self.headers,
        )
