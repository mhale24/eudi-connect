"""Credential Exchange Performance Benchmark.

This module provides benchmarking tools to measure the performance of credential
exchange operations (issuance, verification, revocation) against the EUDI-Connect
performance targets:
- MVP: ≤800ms P95 credential exchange latency
- Future: ≤300ms performance target

Usage:
    python benchmark_credential_exchange.py --iterations 5 --batch-size 10
"""
import argparse
import json
import logging
import statistics
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("credential_benchmark")


class CredentialBenchmark:
    """Benchmark utility for credential exchange performance."""

    def __init__(self, mock_mode: bool = True):
        """Initialize the credential benchmark utility.
        
        Args:
            mock_mode: If True, use mock implementations instead of actual services
        """
        self.mock_mode = mock_mode
        self.results = {}
        
        # Performance targets in milliseconds
        self.targets = {
            "mvp": 800,  # MVP target: ≤800ms P95
            "future": 300,  # Future target: ≤300ms
            "issuance": 500,  # Target for credential issuance
            "verification": 200,  # Target for credential verification
            "revocation": 300,  # Target for credential revocation
        }
        
        # Setup components based on mode
        if mock_mode:
            self.setup_mock_components()
        else:
            self.setup_real_components()
            
    def setup_mock_components(self):
        """Set up mock components for testing."""
        # Mock DIDKit service
        self.didkit_service = MockDIDKitService()
        
        # Mock database
        self.db = MockDatabase()
        
        # Mock credential service
        self.credential_service = MockCredentialService(
            didkit_service=self.didkit_service,
            db=self.db,
        )
        
    def setup_real_components(self):
        """Set up real components for production benchmarking."""
        # This would be implemented to connect to real services
        # For now, we'll just use the mock implementation
        logger.warning("Real component setup not implemented, using mocks")
        self.setup_mock_components()
        
    def create_sample_credential(self, index: int = 0) -> Dict:
        """Create a sample credential for benchmarking.
        
        Args:
            index: Index for creating unique credentials
            
        Returns:
            Sample credential data
        """
        return {
            "id": f"credential_{uuid.uuid4()}",
            "type": ["VerifiableCredential", "EUDICredential"],
            "issuer": "did:example:issuer",
            "issuanceDate": datetime.now(timezone.utc).isoformat(),
            "credentialSubject": {
                "id": f"did:example:subject_{index}",
                "name": f"Test Subject {index}",
                "attributes": {
                    "age": 30 + (index % 10),
                    "country": "EU",
                    "verified": True,
                    "score": 95.5 + (index % 5),
                }
            },
            "proof": {
                "type": "Ed25519Signature2020",
                "created": datetime.now(timezone.utc).isoformat(),
                "verificationMethod": "did:example:issuer#key-1",
                "proofPurpose": "assertionMethod",
                "proofValue": f"mock_proof_value_{index}_{uuid.uuid4().hex}",
            }
        }
        
    def benchmark_issuance(
        self,
        num_credentials: int = 10,
        batch_size: int = 1,
    ) -> Dict:
        """Benchmark credential issuance performance.
        
        Args:
            num_credentials: Number of credentials to issue
            batch_size: Number of credentials to issue in each batch
            
        Returns:
            Performance metrics
        """
        logger.info(f"Benchmarking issuance of {num_credentials} credentials (batch size: {batch_size})...")
        
        # Generate sample credentials
        credentials = [self.create_sample_credential(i) for i in range(num_credentials)]
        
        # Track timings for each issuance
        timings = []
        
        # Process in batches
        for i in range(0, num_credentials, batch_size):
            batch = credentials[i:i+batch_size]
            
            # Benchmark batch issuance
            start_time = time.time()
            for credential in batch:
                self.credential_service.issue_credential(credential)
            end_time = time.time()
            
            # Calculate timing for the batch
            batch_time_ms = (end_time - start_time) * 1000
            
            # If batch size > 1, calculate average time per credential
            if batch_size > 1:
                per_credential_ms = batch_time_ms / len(batch)
                for _ in range(len(batch)):
                    timings.append(per_credential_ms)
            else:
                timings.append(batch_time_ms)
        
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Issuance metrics: {metrics}")
        
        # Store results
        self.results["issuance"] = metrics
        return metrics
        
    def benchmark_verification(
        self,
        num_credentials: int = 10,
        batch_size: int = 1,
    ) -> Dict:
        """Benchmark credential verification performance.
        
        Args:
            num_credentials: Number of credentials to verify
            batch_size: Number of credentials to verify in each batch
            
        Returns:
            Performance metrics
        """
        logger.info(f"Benchmarking verification of {num_credentials} credentials (batch size: {batch_size})...")
        
        # Generate and issue sample credentials first
        credentials = []
        for i in range(num_credentials):
            credential = self.create_sample_credential(i)
            issued = self.credential_service.issue_credential(credential)
            credentials.append(issued)
        
        # Track timings for each verification
        timings = []
        
        # Process in batches
        for i in range(0, num_credentials, batch_size):
            batch = credentials[i:i+batch_size]
            
            # Benchmark batch verification
            start_time = time.time()
            for credential in batch:
                self.credential_service.verify_credential(credential)
            end_time = time.time()
            
            # Calculate timing for the batch
            batch_time_ms = (end_time - start_time) * 1000
            
            # If batch size > 1, calculate average time per credential
            if batch_size > 1:
                per_credential_ms = batch_time_ms / len(batch)
                for _ in range(len(batch)):
                    timings.append(per_credential_ms)
            else:
                timings.append(batch_time_ms)
        
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Verification metrics: {metrics}")
        
        # Store results
        self.results["verification"] = metrics
        return metrics
        
    def benchmark_revocation(
        self,
        num_credentials: int = 10,
        batch_size: int = 1,
    ) -> Dict:
        """Benchmark credential revocation performance.
        
        Args:
            num_credentials: Number of credentials to revoke
            batch_size: Number of credentials to revoke in each batch
            
        Returns:
            Performance metrics
        """
        logger.info(f"Benchmarking revocation of {num_credentials} credentials (batch size: {batch_size})...")
        
        # Generate and issue sample credentials first
        credentials = []
        for i in range(num_credentials):
            credential = self.create_sample_credential(i)
            issued = self.credential_service.issue_credential(credential)
            credentials.append(issued)
        
        # Track timings for each revocation
        timings = []
        
        # Process in batches
        for i in range(0, num_credentials, batch_size):
            batch = credentials[i:i+batch_size]
            
            # Benchmark batch revocation
            start_time = time.time()
            for credential in batch:
                self.credential_service.revoke_credential(credential["id"])
            end_time = time.time()
            
            # Calculate timing for the batch
            batch_time_ms = (end_time - start_time) * 1000
            
            # If batch size > 1, calculate average time per credential
            if batch_size > 1:
                per_credential_ms = batch_time_ms / len(batch)
                for _ in range(len(batch)):
                    timings.append(per_credential_ms)
            else:
                timings.append(batch_time_ms)
        
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Revocation metrics: {metrics}")
        
        # Store results
        self.results["revocation"] = metrics
        return metrics
        
    def benchmark_full_lifecycle(
        self,
        num_credentials: int = 10,
    ) -> Dict:
        """Benchmark the full credential lifecycle (issue, verify, revoke).
        
        Args:
            num_credentials: Number of credentials to process
            
        Returns:
            Performance metrics for the full lifecycle
        """
        logger.info(f"Benchmarking full lifecycle of {num_credentials} credentials...")
        
        # Track timings for each credential's full lifecycle
        timings = []
        
        for i in range(num_credentials):
            # Create credential
            credential = self.create_sample_credential(i)
            
            # Benchmark full lifecycle
            start_time = time.time()
            
            # Issue
            issued = self.credential_service.issue_credential(credential)
            
            # Verify
            self.credential_service.verify_credential(issued)
            
            # Revoke
            self.credential_service.revoke_credential(issued["id"])
            
            end_time = time.time()
            
            # Calculate timing
            full_lifecycle_ms = (end_time - start_time) * 1000
            timings.append(full_lifecycle_ms)
        
        # Calculate metrics
        metrics = self._calculate_metrics(timings)
        logger.info(f"Full lifecycle metrics: {metrics}")
        
        # Store results
        self.results["full_lifecycle"] = metrics
        return metrics
        
    def run_full_benchmark(
        self,
        num_credentials: int = 10,
        batch_sizes: List[int] = None,
        iterations: int = 3,
    ) -> Dict:
        """Run a complete benchmark suite for credential exchange.
        
        Args:
            num_credentials: Number of credentials to process
            batch_sizes: List of batch sizes to test
            iterations: Number of benchmark iterations
            
        Returns:
            Comprehensive benchmark results
        """
        if batch_sizes is None:
            batch_sizes = [1, 5, 10]
            
        logger.info(f"Running full credential exchange benchmark ({iterations} iterations)...")
        
        results = {
            "issuance": {},
            "verification": {},
            "revocation": {},
            "full_lifecycle": {},
            "system_info": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "num_credentials": num_credentials,
                "batch_sizes": batch_sizes,
                "iterations": iterations,
                "performance_targets": self.targets,
            }
        }
        
        # Run multiple iterations
        for iteration in range(iterations):
            logger.info(f"Starting benchmark iteration {iteration+1}/{iterations}")
            
            # Test each batch size
            for batch_size in batch_sizes:
                batch_key = f"batch_{batch_size}"
                
                # Initialize batch results if needed
                for operation in ["issuance", "verification", "revocation"]:
                    if batch_key not in results[operation]:
                        results[operation][batch_key] = []
                
                # Benchmark operations with this batch size
                issuance_metrics = self.benchmark_issuance(num_credentials, batch_size)
                results["issuance"][batch_key].append(issuance_metrics)
                
                verification_metrics = self.benchmark_verification(num_credentials, batch_size)
                results["verification"][batch_key].append(verification_metrics)
                
                revocation_metrics = self.benchmark_revocation(num_credentials, batch_size)
                results["revocation"][batch_key].append(revocation_metrics)
            
            # Benchmark full lifecycle (always single credential operations)
            lifecycle_metrics = self.benchmark_full_lifecycle(num_credentials)
            if "single" not in results["full_lifecycle"]:
                results["full_lifecycle"]["single"] = []
            results["full_lifecycle"]["single"].append(lifecycle_metrics)
        
        # Aggregate results
        aggregated_results = self._aggregate_results(results)
        
        # Check against performance targets
        meets_targets = self._check_performance_targets(aggregated_results)
        aggregated_results["meets_targets"] = meets_targets
        
        return aggregated_results
        
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
        
    def _aggregate_results(self, results: Dict) -> Dict:
        """Aggregate results from multiple iterations.
        
        Args:
            results: Raw benchmark results
            
        Returns:
            Aggregated results
        """
        aggregated = {
            "issuance": {},
            "verification": {},
            "revocation": {},
            "full_lifecycle": {},
            "system_info": results["system_info"],
        }
        
        # Metrics to aggregate
        metrics_to_aggregate = ["mean", "median", "min", "max", "p95", "p99"]
        
        # Aggregate each operation and batch size
        for operation in ["issuance", "verification", "revocation", "full_lifecycle"]:
            for batch_key, batch_results in results[operation].items():
                aggregated[operation][batch_key] = {}
                
                for metric in metrics_to_aggregate:
                    values = [result[metric] for result in batch_results if metric in result]
                    if values:
                        aggregated[operation][batch_key][f"{metric}_avg"] = statistics.mean(values)
                        aggregated[operation][batch_key][f"{metric}_min"] = min(values)
                        aggregated[operation][batch_key][f"{metric}_max"] = max(values)
                
                # Include total samples
                aggregated[operation][batch_key]["total_samples"] = sum(
                    result.get("samples", 0) for result in batch_results
                )
        
        return aggregated
        
    def _check_performance_targets(self, results: Dict) -> Dict[str, bool]:
        """Check if results meet performance targets.
        
        Args:
            results: Aggregated benchmark results
            
        Returns:
            Dictionary of target check results
        """
        target_checks = {}
        
        # Check issuance performance
        if "issuance" in results and "batch_1" in results["issuance"]:
            issuance_p95 = results["issuance"]["batch_1"].get("p95_avg", float("inf"))
            target_checks["issuance"] = issuance_p95 <= self.targets["issuance"]
        
        # Check verification performance
        if "verification" in results and "batch_1" in results["verification"]:
            verification_p95 = results["verification"]["batch_1"].get("p95_avg", float("inf"))
            target_checks["verification"] = verification_p95 <= self.targets["verification"]
        
        # Check revocation performance
        if "revocation" in results and "batch_1" in results["revocation"]:
            revocation_p95 = results["revocation"]["batch_1"].get("p95_avg", float("inf"))
            target_checks["revocation"] = revocation_p95 <= self.targets["revocation"]
        
        # Check full lifecycle against MVP and future targets
        if "full_lifecycle" in results and "single" in results["full_lifecycle"]:
            lifecycle_p95 = results["full_lifecycle"]["single"].get("p95_avg", float("inf"))
            target_checks["mvp_latency"] = lifecycle_p95 <= self.targets["mvp"]
            target_checks["future_latency"] = lifecycle_p95 <= self.targets["future"]
        
        return target_checks
        
    def save_results(self, results: Dict, filename: str = None) -> str:
        """Save benchmark results to file.
        
        Args:
            results: Benchmark results dictionary
            filename: Optional filename (defaults to timestamp-based name)
            
        Returns:
            Path to saved results file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"credential_benchmark_{timestamp}.json"
            
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Benchmark results saved to {filename}")
        return filename


# Mock implementations for testing
class MockDIDKitService:
    """Mock implementation of DIDKit service."""
    
    def __init__(self):
        """Initialize the mock DIDKit service."""
        self._initialized = True
        self.did = "did:example:issuer"
        self.verification_method = "did:example:issuer#key-1"
        
    def initialize(self):
        """Initialize the service."""
        self._initialized = True
        
    def initialize_sync(self):
        """Initialize the service synchronously."""
        self._initialized = True
        
    def issue_credential(self, credential: Dict) -> Dict:
        """Issue a verifiable credential.
        
        Args:
            credential: Credential to issue
            
        Returns:
            Issued credential with proof
        """
        # Simulate processing time
        time.sleep(0.005)  # 5ms delay
        
        # Add proof if not present
        if "proof" not in credential:
            credential["proof"] = {
                "type": "Ed25519Signature2020",
                "created": datetime.now(timezone.utc).isoformat(),
                "verificationMethod": self.verification_method,
                "proofPurpose": "assertionMethod",
                "proofValue": f"mock_proof_value_{uuid.uuid4().hex}",
            }
            
        return credential
        
    def verify_credential(self, credential: Dict) -> bool:
        """Verify a credential.
        
        Args:
            credential: Credential to verify
            
        Returns:
            True if verification succeeded, False otherwise
        """
        # Simulate processing time
        time.sleep(0.002)  # 2ms delay
        
        # Always return success for mock
        return True


class MockDatabase:
    """Mock database implementation."""
    
    def __init__(self):
        """Initialize the mock database."""
        self.credential_logs = []
        
    def log_credential_operation(
        self,
        operation: str,
        credential_id: str,
        status: str,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """Log a credential operation.
        
        Args:
            operation: Operation type (issue, verify, revoke)
            credential_id: ID of the credential
            status: Operation status
            error: Optional error message
            metadata: Optional operation metadata
        """
        # Simulate database write delay
        time.sleep(0.001)  # 1ms delay
        
        log_entry = {
            "id": str(uuid.uuid4()),
            "operation": operation,
            "credential_id": credential_id,
            "status": status,
            "error": error,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self.credential_logs.append(log_entry)
        return log_entry


class MockCredentialService:
    """Mock credential service implementation."""
    
    def __init__(self, didkit_service: MockDIDKitService, db: MockDatabase):
        """Initialize the mock credential service.
        
        Args:
            didkit_service: DIDKit service instance
            db: Database instance
        """
        self.didkit_service = didkit_service
        self.db = db
        self.issued_credentials = {}  # Store issued credentials by ID
        
    def issue_credential(self, credential: Dict) -> Dict:
        """Issue a verifiable credential.
        
        Args:
            credential: Credential to issue
            
        Returns:
            Issued credential with proof
        """
        try:
            # Issue credential using DIDKit
            issued_credential = self.didkit_service.issue_credential(credential)
            
            # Store in memory
            self.issued_credentials[issued_credential["id"]] = issued_credential
            
            # Log successful operation
            self.db.log_credential_operation(
                operation="issue",
                credential_id=issued_credential["id"],
                status="success",
                metadata={"issuer": issued_credential["issuer"]},
            )
            
            return issued_credential
            
        except Exception as e:
            # Log failed operation
            self.db.log_credential_operation(
                operation="issue",
                credential_id=credential.get("id", "unknown"),
                status="error",
                error=str(e),
            )
            
            raise
            
    def verify_credential(self, credential: Dict) -> bool:
        """Verify a credential.
        
        Args:
            credential: Credential to verify
            
        Returns:
            True if verification succeeded, False otherwise
        """
        try:
            # Verify credential using DIDKit
            result = self.didkit_service.verify_credential(credential)
            
            # Log operation
            status = "success" if result else "failed"
            self.db.log_credential_operation(
                operation="verify",
                credential_id=credential["id"],
                status=status,
                metadata={"result": result},
            )
            
            return result
            
        except Exception as e:
            # Log failed operation
            self.db.log_credential_operation(
                operation="verify",
                credential_id=credential.get("id", "unknown"),
                status="error",
                error=str(e),
            )
            
            raise
            
    def revoke_credential(self, credential_id: str) -> bool:
        """Revoke a credential.
        
        Args:
            credential_id: ID of the credential to revoke
            
        Returns:
            True if revocation succeeded, False otherwise
        """
        try:
            # Check if credential exists
            if credential_id not in self.issued_credentials:
                raise ValueError(f"Credential {credential_id} not found")
                
            # Simulate revocation delay
            time.sleep(0.003)  # 3ms delay
            
            # Remove from storage
            del self.issued_credentials[credential_id]
            
            # Log operation
            self.db.log_credential_operation(
                operation="revoke",
                credential_id=credential_id,
                status="success",
            )
            
            return True
            
        except Exception as e:
            # Log failed operation
            self.db.log_credential_operation(
                operation="revoke",
                credential_id=credential_id,
                status="error",
                error=str(e),
            )
            
            raise


def main():
    """Run benchmark as a command-line tool."""
    parser = argparse.ArgumentParser(description="Credential exchange performance benchmark")
    parser.add_argument("--num-credentials", type=int, default=50, help="Number of credentials")
    parser.add_argument("--iterations", type=int, default=3, help="Benchmark iterations")
    parser.add_argument("--batch-sizes", type=str, default="1,5,10", help="Batch sizes (comma-separated)")
    parser.add_argument("--output", type=str, help="Output file path")
    args = parser.parse_args()
    
    # Parse batch sizes
    batch_sizes = [int(size) for size in args.batch_sizes.split(",")]
    
    # Run benchmark
    benchmark = CredentialBenchmark(mock_mode=True)
    results = benchmark.run_full_benchmark(
        num_credentials=args.num_credentials,
        batch_sizes=batch_sizes,
        iterations=args.iterations,
    )
    
    # Save results
    benchmark.save_results(results, args.output)
    
    # Print summary
    print("\n=== CREDENTIAL BENCHMARK SUMMARY ===")
    print(f"Credentials: {args.num_credentials}, Iterations: {args.iterations}")
    print(f"Batch sizes: {batch_sizes}")
    
    # Print operation metrics
    for operation in ["issuance", "verification", "revocation"]:
        print(f"\n{operation.capitalize()} Metrics:")
        for batch_key, metrics in results[operation].items():
            if "p95_avg" in metrics:
                print(f"  {batch_key} - P95: {metrics['p95_avg']:.2f}ms")
    
    # Print full lifecycle metrics
    if "single" in results["full_lifecycle"]:
        lifecycle = results["full_lifecycle"]["single"]
        print("\nFull Lifecycle Metrics:")
        print(f"  P95: {lifecycle.get('p95_avg', 'N/A')}ms")
    
    # Print performance targets
    print("\nPerformance Targets:")
    for target, achieved in results["meets_targets"].items():
        status = "✅ PASS" if achieved else "❌ FAIL"
        print(f"  {target}: {status}")


if __name__ == "__main__":
    main()
