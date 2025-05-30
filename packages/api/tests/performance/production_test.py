"""Production environment performance test for EUDI-Connect.

This script tests the performance of EUDI-Connect's credential exchange operations
in a production or staging environment with real infrastructure.

Usage:
    python production_test.py --api-key YOUR_API_KEY --endpoint https://api.eudi-connect.example.com
"""
import argparse
import asyncio
import json
import logging
import statistics
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import httpx
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("production_test")


class ProductionTest:
    """Production testing utility for EUDI-Connect API."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        timeout: int = 30,
    ):
        """Initialize the production test.
        
        Args:
            api_key: API key for authentication
            endpoint: API endpoint URL (e.g., https://api.eudi-connect.example.com)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        
        # Store results
        self.results = {}
        
        # Performance targets in milliseconds
        self.targets = {
            "mvp": 800,  # MVP target: ≤800ms P95
            "future": 300,  # Future target: ≤300ms
        }
        
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        
    async def create_sample_credential(self, index: int = 0) -> Dict:
        """Create a sample credential for testing.
        
        Args:
            index: Index for creating unique credentials
            
        Returns:
            Sample credential data
        """
        current_time = datetime.now(timezone.utc)
        expiry_time = current_time + timedelta(days=30)
        
        return {
            "credentialType": "EUDISampleCredential",
            "claims": {
                "id": f"did:example:subject_{uuid.uuid4()}",
                "firstName": f"Test{index}",
                "lastName": f"User{index}",
                "dateOfBirth": "1990-01-01",
                "nationality": "EU",
                "issuanceDate": current_time.isoformat(),
                "expirationDate": expiry_time.isoformat(),
                "testIndex": index,
                "testId": str(uuid.uuid4()),
            }
        }
        
    async def test_issuance(self, num_credentials: int = 10) -> Dict:
        """Test credential issuance performance.
        
        Args:
            num_credentials: Number of credentials to issue
            
        Returns:
            Performance metrics
        """
        logger.info(f"Testing issuance of {num_credentials} credentials...")
        
        # Create sample credentials
        credentials = [await self.create_sample_credential(i) for i in range(num_credentials)]
        
        # Track timings and results
        timings = []
        issued_credentials = []
        
        # Issue credentials sequentially
        for i, credential in enumerate(credentials):
            try:
                # Measure issuance time
                start_time = time.time()
                response = await self.client.post(
                    f"{self.endpoint}/v1/credentials/issue",
                    json=credential,
                )
                end_time = time.time()
                
                # Calculate timing
                elapsed_ms = (end_time - start_time) * 1000
                timings.append(elapsed_ms)
                
                if response.status_code == 200:
                    issued_credential = response.json()
                    issued_credentials.append(issued_credential)
                    logger.info(f"Successfully issued credential {i+1}/{num_credentials} in {elapsed_ms:.2f}ms")
                else:
                    logger.error(f"Failed to issue credential {i+1}/{num_credentials}: {response.text}")
            except Exception as e:
                logger.error(f"Error issuing credential {i+1}/{num_credentials}: {e}")
        
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Issuance metrics: {metrics}")
        
        # Store results and issued credentials for further tests
        self.results["issuance"] = metrics
        self.issued_credentials = issued_credentials
        
        return metrics
        
    async def test_verification(self, num_credentials: Optional[int] = None) -> Dict:
        """Test credential verification performance.
        
        Args:
            num_credentials: Optional number of credentials to verify (defaults to all issued)
            
        Returns:
            Performance metrics
        """
        # Use previously issued credentials
        if not hasattr(self, "issued_credentials") or not self.issued_credentials:
            logger.error("No issued credentials available for verification")
            return {}
            
        credentials_to_verify = self.issued_credentials
        if num_credentials is not None:
            credentials_to_verify = credentials_to_verify[:num_credentials]
            
        logger.info(f"Testing verification of {len(credentials_to_verify)} credentials...")
        
        # Track timings
        timings = []
        
        # Verify credentials sequentially
        for i, credential in enumerate(credentials_to_verify):
            try:
                # Measure verification time
                start_time = time.time()
                response = await self.client.post(
                    f"{self.endpoint}/v1/credentials/verify",
                    json={"credential": credential},
                )
                end_time = time.time()
                
                # Calculate timing
                elapsed_ms = (end_time - start_time) * 1000
                timings.append(elapsed_ms)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully verified credential {i+1}/{len(credentials_to_verify)} "
                               f"in {elapsed_ms:.2f}ms: {result.get('valid', False)}")
                else:
                    logger.error(f"Failed to verify credential {i+1}/{len(credentials_to_verify)}: {response.text}")
            except Exception as e:
                logger.error(f"Error verifying credential {i+1}/{len(credentials_to_verify)}: {e}")
        
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Verification metrics: {metrics}")
        
        # Store results
        self.results["verification"] = metrics
        
        return metrics
        
    async def test_revocation(self, num_credentials: Optional[int] = None) -> Dict:
        """Test credential revocation performance.
        
        Args:
            num_credentials: Optional number of credentials to revoke (defaults to all issued)
            
        Returns:
            Performance metrics
        """
        # Use previously issued credentials
        if not hasattr(self, "issued_credentials") or not self.issued_credentials:
            logger.error("No issued credentials available for revocation")
            return {}
            
        credentials_to_revoke = self.issued_credentials
        if num_credentials is not None:
            credentials_to_revoke = credentials_to_revoke[:num_credentials]
            
        logger.info(f"Testing revocation of {len(credentials_to_revoke)} credentials...")
        
        # Track timings
        timings = []
        
        # Revoke credentials sequentially
        for i, credential in enumerate(credentials_to_revoke):
            try:
                credential_id = credential.get("id")
                if not credential_id:
                    logger.error(f"Credential {i+1} has no ID, skipping revocation")
                    continue
                    
                # Measure revocation time
                start_time = time.time()
                response = await self.client.post(
                    f"{self.endpoint}/v1/credentials/revoke",
                    json={"credentialId": credential_id},
                )
                end_time = time.time()
                
                # Calculate timing
                elapsed_ms = (end_time - start_time) * 1000
                timings.append(elapsed_ms)
                
                if response.status_code == 200:
                    logger.info(f"Successfully revoked credential {i+1}/{len(credentials_to_revoke)} "
                               f"in {elapsed_ms:.2f}ms")
                else:
                    logger.error(f"Failed to revoke credential {i+1}/{len(credentials_to_revoke)}: {response.text}")
            except Exception as e:
                logger.error(f"Error revoking credential {i+1}/{len(credentials_to_revoke)}: {e}")
        
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Revocation metrics: {metrics}")
        
        # Store results
        self.results["revocation"] = metrics
        
        return metrics
        
    async def test_full_lifecycle(self, num_credentials: int = 10) -> Dict:
        """Test the full credential lifecycle (issue, verify, revoke) for each credential.
        
        This test measures end-to-end performance of the entire credential lifecycle.
        
        Args:
            num_credentials: Number of credentials to process
            
        Returns:
            Performance metrics
        """
        logger.info(f"Testing full lifecycle of {num_credentials} credentials...")
        
        # Track timings and results
        timings = []
        
        # Process each credential through its full lifecycle
        for i in range(num_credentials):
            try:
                credential_data = await self.create_sample_credential(i)
                
                # Measure full lifecycle time
                start_time = time.time()
                
                # Issue
                issue_response = await self.client.post(
                    f"{self.endpoint}/v1/credentials/issue",
                    json=credential_data,
                )
                
                if issue_response.status_code != 200:
                    logger.error(f"Failed to issue credential {i+1}: {issue_response.text}")
                    continue
                    
                issued_credential = issue_response.json()
                
                # Verify
                verify_response = await self.client.post(
                    f"{self.endpoint}/v1/credentials/verify",
                    json={"credential": issued_credential},
                )
                
                if verify_response.status_code != 200:
                    logger.error(f"Failed to verify credential {i+1}: {verify_response.text}")
                    continue
                    
                # Revoke
                credential_id = issued_credential.get("id")
                if not credential_id:
                    logger.error(f"Credential {i+1} has no ID, skipping revocation")
                    continue
                    
                revoke_response = await self.client.post(
                    f"{self.endpoint}/v1/credentials/revoke",
                    json={"credentialId": credential_id},
                )
                
                if revoke_response.status_code != 200:
                    logger.error(f"Failed to revoke credential {i+1}: {revoke_response.text}")
                    continue
                
                end_time = time.time()
                
                # Calculate timing
                elapsed_ms = (end_time - start_time) * 1000
                timings.append(elapsed_ms)
                
                logger.info(f"Completed full lifecycle for credential {i+1}/{num_credentials} in {elapsed_ms:.2f}ms")
                
            except Exception as e:
                logger.error(f"Error processing credential {i+1} lifecycle: {e}")
        
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Full lifecycle metrics: {metrics}")
        
        # Store results
        self.results["full_lifecycle"] = metrics
        
        return metrics
        
    async def test_concurrent_operations(self, num_credentials: int = 10, concurrency: int = 5) -> Dict:
        """Test concurrent credential operations.
        
        Args:
            num_credentials: Total number of credentials to process
            concurrency: Maximum number of concurrent operations
            
        Returns:
            Performance metrics by operation
        """
        logger.info(f"Testing concurrent operations with {num_credentials} credentials (concurrency: {concurrency})...")
        
        # Create sample credentials
        credentials = [await self.create_sample_credential(i) for i in range(num_credentials)]
        
        # Test concurrent issuance
        async def issue_credential(credential_data, index):
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{self.endpoint}/v1/credentials/issue",
                    json=credential_data,
                )
                end_time = time.time()
                
                elapsed_ms = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    issued_credential = response.json()
                    logger.info(f"Successfully issued credential {index+1} in {elapsed_ms:.2f}ms")
                    return issued_credential, elapsed_ms
                else:
                    logger.error(f"Failed to issue credential {index+1}: {response.text}")
                    return None, elapsed_ms
            except Exception as e:
                logger.error(f"Error issuing credential {index+1}: {e}")
                return None, 0
        
        # Execute concurrent issuance
        issuance_tasks = []
        for i, credential in enumerate(credentials):
            task = asyncio.create_task(issue_credential(credential, i))
            issuance_tasks.append(task)
            
            # Limit concurrency
            if len(issuance_tasks) >= concurrency:
                # Wait for some tasks to complete before adding more
                done, issuance_tasks = await asyncio.wait(
                    issuance_tasks, 
                    return_when=asyncio.FIRST_COMPLETED
                )
        
        # Wait for all remaining issuance tasks
        if issuance_tasks:
            done, _ = await asyncio.wait(issuance_tasks)
            
        # Collect results
        issued_credentials = []
        issuance_timings = []
        
        for task in done:
            credential, timing = await task
            if credential:
                issued_credentials.append(credential)
            if timing > 0:
                issuance_timings.append(timing)
                
        # Calculate issuance metrics
        issuance_metrics = self._calculate_metrics(issuance_timings)
        logger.info(f"Concurrent issuance metrics: {issuance_metrics}")
        
        # Now test concurrent verification
        async def verify_credential(credential, index):
            try:
                start_time = time.time()
                response = await self.client.post(
                    f"{self.endpoint}/v1/credentials/verify",
                    json={"credential": credential},
                )
                end_time = time.time()
                
                elapsed_ms = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Successfully verified credential {index+1} in {elapsed_ms:.2f}ms")
                    return result, elapsed_ms
                else:
                    logger.error(f"Failed to verify credential {index+1}: {response.text}")
                    return None, elapsed_ms
            except Exception as e:
                logger.error(f"Error verifying credential {index+1}: {e}")
                return None, 0
                
        # Execute concurrent verification
        verification_tasks = []
        for i, credential in enumerate(issued_credentials):
            task = asyncio.create_task(verify_credential(credential, i))
            verification_tasks.append(task)
            
            # Limit concurrency
            if len(verification_tasks) >= concurrency:
                # Wait for some tasks to complete before adding more
                done, verification_tasks = await asyncio.wait(
                    verification_tasks, 
                    return_when=asyncio.FIRST_COMPLETED
                )
        
        # Wait for all remaining verification tasks
        if verification_tasks:
            done, _ = await asyncio.wait(verification_tasks)
            
        # Collect verification timings
        verification_timings = []
        for task in done:
            _, timing = await task
            if timing > 0:
                verification_timings.append(timing)
                
        # Calculate verification metrics
        verification_metrics = self._calculate_metrics(verification_timings)
        logger.info(f"Concurrent verification metrics: {verification_metrics}")
        
        # Store concurrent results
        self.results["concurrent"] = {
            "issuance": issuance_metrics,
            "verification": verification_metrics,
            "concurrency": concurrency,
        }
        
        return self.results["concurrent"]
        
    def _calculate_metrics(self, timings: List[float]) -> Dict:
        """Calculate performance metrics from timing data.
        
        Args:
            timings: List of timing measurements in milliseconds
            
        Returns:
            Dictionary of performance metrics
        """
        if not timings:
            return {}
            
        # Sort timings for percentile calculations
        sorted_timings = sorted(timings)
        
        # Calculate metrics
        return {
            "mean": statistics.mean(timings),
            "median": statistics.median(timings),
            "min": min(timings),
            "max": max(timings),
            "p95": sorted_timings[int(len(sorted_timings) * 0.95)],
            "p99": sorted_timings[int(len(sorted_timings) * 0.99)],
            "stddev": statistics.stdev(timings) if len(timings) > 1 else 0,
            "samples": len(timings),
        }
        
    def check_performance_targets(self) -> Dict[str, bool]:
        """Check if results meet performance targets.
        
        Returns:
            Dictionary of target check results
        """
        target_checks = {}
        
        # Check full lifecycle against MVP and future targets
        if "full_lifecycle" in self.results:
            lifecycle_p95 = self.results["full_lifecycle"].get("p95", float("inf"))
            target_checks["mvp_latency"] = lifecycle_p95 <= self.targets["mvp"]
            target_checks["future_latency"] = lifecycle_p95 <= self.targets["future"]
            
        # Check concurrent operations
        if "concurrent" in self.results:
            if "issuance" in self.results["concurrent"]:
                issuance_p95 = self.results["concurrent"]["issuance"].get("p95", float("inf"))
                target_checks["concurrent_issuance"] = issuance_p95 <= self.targets["mvp"]
                
            if "verification" in self.results["concurrent"]:
                verification_p95 = self.results["concurrent"]["verification"].get("p95", float("inf"))
                target_checks["concurrent_verification"] = verification_p95 <= self.targets["mvp"]
        
        return target_checks
        
    def save_results(self, filename: str = None) -> str:
        """Save benchmark results to file.
        
        Args:
            filename: Optional filename (defaults to timestamp-based name)
            
        Returns:
            Path to saved results file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prod_test_results_{timestamp}.json"
            
        # Add performance target checks
        self.results["meets_targets"] = self.check_performance_targets()
        
        # Add test metadata
        self.results["metadata"] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint": self.endpoint,
            "performance_targets": self.targets,
        }
        
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"Test results saved to {filename}")
        return filename


async def run_tests(args):
    """Run all production tests."""
    # Create test instance
    test = ProductionTest(
        api_key=args.api_key,
        endpoint=args.endpoint,
        timeout=args.timeout,
    )
    
    try:
        # Run tests
        if args.test_issuance or args.test_all:
            await test.test_issuance(args.num_credentials)
            
        if args.test_verification or args.test_all:
            await test.test_verification(args.num_credentials)
            
        if args.test_revocation or args.test_all:
            await test.test_revocation(args.num_credentials)
            
        if args.test_lifecycle or args.test_all:
            await test.test_full_lifecycle(args.num_credentials)
            
        if args.test_concurrent or args.test_all:
            await test.test_concurrent_operations(
                args.num_credentials,
                args.concurrency,
            )
            
        # Save results
        test.save_results(args.output)
        
        # Print summary
        print("\n=== PRODUCTION TEST SUMMARY ===")
        
        if "issuance" in test.results:
            print("\nIssuance Metrics:")
            metrics = test.results["issuance"]
            print(f"  Mean: {metrics.get('mean', 'N/A'):.2f}ms")
            print(f"  P95: {metrics.get('p95', 'N/A'):.2f}ms")
            print(f"  Samples: {metrics.get('samples', 'N/A')}")
            
        if "verification" in test.results:
            print("\nVerification Metrics:")
            metrics = test.results["verification"]
            print(f"  Mean: {metrics.get('mean', 'N/A'):.2f}ms")
            print(f"  P95: {metrics.get('p95', 'N/A'):.2f}ms")
            print(f"  Samples: {metrics.get('samples', 'N/A')}")
            
        if "revocation" in test.results:
            print("\nRevocation Metrics:")
            metrics = test.results["revocation"]
            print(f"  Mean: {metrics.get('mean', 'N/A'):.2f}ms")
            print(f"  P95: {metrics.get('p95', 'N/A'):.2f}ms")
            print(f"  Samples: {metrics.get('samples', 'N/A')}")
            
        if "full_lifecycle" in test.results:
            print("\nFull Lifecycle Metrics:")
            metrics = test.results["full_lifecycle"]
            print(f"  Mean: {metrics.get('mean', 'N/A'):.2f}ms")
            print(f"  P95: {metrics.get('p95', 'N/A'):.2f}ms")
            print(f"  Samples: {metrics.get('samples', 'N/A')}")
            
        if "concurrent" in test.results:
            print("\nConcurrent Operation Metrics:")
            print(f"  Concurrency: {test.results['concurrent'].get('concurrency', 'N/A')}")
            
            if "issuance" in test.results["concurrent"]:
                metrics = test.results["concurrent"]["issuance"]
                print(f"  Issuance P95: {metrics.get('p95', 'N/A'):.2f}ms")
                
            if "verification" in test.results["concurrent"]:
                metrics = test.results["concurrent"]["verification"]
                print(f"  Verification P95: {metrics.get('p95', 'N/A'):.2f}ms")
                
        if "meets_targets" in test.results:
            print("\nPerformance Targets:")
            for target, achieved in test.results["meets_targets"].items():
                status = "✅ PASS" if achieved else "❌ FAIL"
                print(f"  {target}: {status}")
                
    finally:
        # Clean up
        await test.close()


def main():
    """Run production tests from command line."""
    parser = argparse.ArgumentParser(description="EUDI-Connect production performance test")
    
    # API connection parameters
    parser.add_argument("--api-key", type=str, required=True, help="API key for authentication")
    parser.add_argument("--endpoint", type=str, required=True, help="API endpoint URL")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    
    # Test parameters
    parser.add_argument("--num-credentials", type=int, default=10, help="Number of credentials to test")
    parser.add_argument("--concurrency", type=int, default=5, help="Maximum concurrent operations")
    parser.add_argument("--output", type=str, help="Output file path")
    
    # Test selection
    parser.add_argument("--test-all", action="store_true", help="Run all tests")
    parser.add_argument("--test-issuance", action="store_true", help="Test credential issuance")
    parser.add_argument("--test-verification", action="store_true", help="Test credential verification")
    parser.add_argument("--test-revocation", action="store_true", help="Test credential revocation")
    parser.add_argument("--test-lifecycle", action="store_true", help="Test full credential lifecycle")
    parser.add_argument("--test-concurrent", action="store_true", help="Test concurrent operations")
    
    args = parser.parse_args()
    
    # If no specific tests selected, run all
    if not any([
        args.test_all,
        args.test_issuance,
        args.test_verification,
        args.test_revocation,
        args.test_lifecycle,
        args.test_concurrent,
    ]):
        args.test_all = True
    
    # Run tests asynchronously
    asyncio.run(run_tests(args))


if __name__ == "__main__":
    main()
