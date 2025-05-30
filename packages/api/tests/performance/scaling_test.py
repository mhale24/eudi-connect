"""Scaling tests for EUDI-Connect.

This module provides tools for testing EUDI-Connect under load with
multiple concurrent users and varying throughput levels.

Usage:
    python scaling_test.py --workers 10 --duration 60 --ramp-up 10
"""
import argparse
import asyncio
import json
import logging
import random
import statistics
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
import httpx
import os
import multiprocessing
import queue
import threading
import signal
import sys
from dataclasses import dataclass, asdict, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("scaling_test")


@dataclass
class ScalingTestResult:
    """Result data for a scaling test."""
    
    # Test parameters
    start_time: str
    end_time: str
    duration_seconds: float
    num_workers: int
    ramp_up_seconds: int
    target_rps: float
    
    # Overall metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_operations: int = 0
    
    # Timing metrics by operation
    timings: Dict[str, List[float]] = field(default_factory=dict)
    
    # Derived metrics (calculated after test)
    actual_rps: float = 0.0
    p50_ms: Dict[str, float] = field(default_factory=dict)
    p95_ms: Dict[str, float] = field(default_factory=dict)
    p99_ms: Dict[str, float] = field(default_factory=dict)
    mean_ms: Dict[str, float] = field(default_factory=dict)
    max_ms: Dict[str, float] = field(default_factory=dict)
    error_rate: float = 0.0
    
    def add_timing(self, operation: str, duration_ms: float):
        """Add a timing measurement for an operation.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
        """
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(duration_ms)
        self.total_operations += 1
        
    def calculate_metrics(self):
        """Calculate derived metrics from collected data."""
        # Calculate request rate
        if self.duration_seconds > 0:
            self.actual_rps = self.total_requests / self.duration_seconds
            
        # Calculate error rate
        if self.total_requests > 0:
            self.error_rate = self.failed_requests / self.total_requests
            
        # Calculate timing percentiles for each operation
        for operation, times in self.timings.items():
            if not times:
                continue
                
            sorted_times = sorted(times)
            count = len(sorted_times)
            
            self.p50_ms[operation] = sorted_times[int(count * 0.5)]
            self.p95_ms[operation] = sorted_times[int(count * 0.95)]
            self.p99_ms[operation] = sorted_times[int(count * 0.99)]
            self.mean_ms[operation] = statistics.mean(times)
            self.max_ms[operation] = max(times)


class ScalingTestWorker:
    """Worker for performing credential operations in scaling tests."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        worker_id: int,
        result_queue: multiprocessing.Queue,
        stop_event: multiprocessing.Event,
        timeout: int = 30,
    ):
        """Initialize a test worker.
        
        Args:
            api_key: API key for authentication
            endpoint: API endpoint URL
            worker_id: Unique worker identifier
            result_queue: Queue for reporting results
            stop_event: Event for signaling worker to stop
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.worker_id = worker_id
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.timeout = timeout
        self.client = None
        
    async def initialize(self):
        """Initialize the HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
            )
        
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
        
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
                "workerId": self.worker_id,
            }
        }
        
    async def issue_credential(self) -> Tuple[bool, float, Optional[Dict]]:
        """Issue a test credential.
        
        Returns:
            Tuple of (success, duration_ms, issued_credential or None)
        """
        await self.initialize()
        
        try:
            credential_data = await self.create_sample_credential(random.randint(1, 1000))
            
            start_time = time.time()
            response = await self.client.post(
                f"{self.endpoint}/v1/credentials/issue",
                json=credential_data,
            )
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            success = response.status_code == 200
            
            if success:
                issued_credential = response.json()
                return (True, duration_ms, issued_credential)
            else:
                logger.warning(f"Worker {self.worker_id}: Issue failed with status {response.status_code}: {response.text}")
                return (False, duration_ms, None)
                
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Issue error: {e}")
            return (False, 0, None)
            
    async def verify_credential(self, credential: Dict) -> Tuple[bool, float, bool]:
        """Verify a credential.
        
        Args:
            credential: Credential to verify
            
        Returns:
            Tuple of (success, duration_ms, verification_result)
        """
        await self.initialize()
        
        try:
            start_time = time.time()
            response = await self.client.post(
                f"{self.endpoint}/v1/credentials/verify",
                json={"credential": credential},
            )
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            success = response.status_code == 200
            
            if success:
                result = response.json()
                return (True, duration_ms, result.get("valid", False))
            else:
                logger.warning(f"Worker {self.worker_id}: Verify failed with status {response.status_code}: {response.text}")
                return (False, duration_ms, False)
                
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Verify error: {e}")
            return (False, 0, False)
            
    async def revoke_credential(self, credential_id: str) -> Tuple[bool, float]:
        """Revoke a credential.
        
        Args:
            credential_id: ID of the credential to revoke
            
        Returns:
            Tuple of (success, duration_ms)
        """
        await self.initialize()
        
        try:
            start_time = time.time()
            response = await self.client.post(
                f"{self.endpoint}/v1/credentials/revoke",
                json={"credentialId": credential_id},
            )
            end_time = time.time()
            
            duration_ms = (end_time - start_time) * 1000
            success = response.status_code == 200
            
            if not success:
                logger.warning(f"Worker {self.worker_id}: Revoke failed with status {response.status_code}: {response.text}")
                
            return (success, duration_ms)
                
        except Exception as e:
            logger.error(f"Worker {self.worker_id}: Revoke error: {e}")
            return (False, 0)
            
    async def run_credential_lifecycle(self) -> List[Tuple[str, bool, float]]:
        """Run a complete credential lifecycle (issue, verify, revoke).
        
        Returns:
            List of results (operation, success, duration_ms)
        """
        results = []
        
        # Issue credential
        issue_success, issue_duration, credential = await self.issue_credential()
        results.append(("issue", issue_success, issue_duration))
        
        if not issue_success or not credential:
            return results
            
        # Verify credential
        verify_success, verify_duration, verify_result = await self.verify_credential(credential)
        results.append(("verify", verify_success, verify_duration))
        
        # Revoke credential
        credential_id = credential.get("id")
        if credential_id:
            revoke_success, revoke_duration = await self.revoke_credential(credential_id)
            results.append(("revoke", revoke_success, revoke_duration))
            
        return results
        
    async def run_workload(self, duration_seconds: int, delay_ms: int = 0):
        """Run a continuous workload for the specified duration.
        
        Args:
            duration_seconds: Duration to run in seconds
            delay_ms: Optional delay between operations in milliseconds
        """
        logger.info(f"Worker {self.worker_id}: Starting workload for {duration_seconds}s with {delay_ms}ms delay")
        
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time and not self.stop_event.is_set():
            # Run a complete lifecycle
            results = await self.run_credential_lifecycle()
            
            # Report results
            for operation, success, duration_ms in results:
                self.result_queue.put({
                    "worker_id": self.worker_id,
                    "operation": operation,
                    "success": success,
                    "duration_ms": duration_ms,
                    "timestamp": time.time(),
                })
                
            # Apply delay if specified
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000)
                
        logger.info(f"Worker {self.worker_id}: Completed workload")
        await self.close()


def worker_process(
    api_key: str,
    endpoint: str,
    worker_id: int,
    result_queue: multiprocessing.Queue,
    stop_event: multiprocessing.Event,
    duration_seconds: int,
    delay_ms: int,
    ramp_up_seconds: int,
):
    """Worker process function for running in a separate process.
    
    Args:
        api_key: API key for authentication
        endpoint: API endpoint URL
        worker_id: Unique worker identifier
        result_queue: Queue for reporting results
        stop_event: Event for signaling worker to stop
        duration_seconds: Duration to run in seconds
        delay_ms: Delay between operations in milliseconds
        ramp_up_seconds: Time to gradually start workers
    """
    # Calculate delay for this worker based on ramp-up
    if ramp_up_seconds > 0 and worker_id > 0:
        worker_delay = (worker_id / multiprocessing.cpu_count()) * ramp_up_seconds
        time.sleep(worker_delay)
    
    # Create and run worker
    worker = ScalingTestWorker(api_key, endpoint, worker_id, result_queue, stop_event)
    
    # Run workload in async event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(worker.run_workload(duration_seconds, delay_ms))
    except Exception as e:
        logger.error(f"Worker {worker_id} error: {e}")
    finally:
        loop.run_until_complete(worker.close())
        loop.close()


class ScalingTest:
    """Scaling test coordinator for EUDI-Connect."""
    
    def __init__(
        self,
        api_key: str,
        endpoint: str,
        num_workers: int = 0,  # 0 = auto-detect CPU count
        ramp_up_seconds: int = 0,
        target_rps: float = 0.0,  # 0 = unlimited
    ):
        """Initialize the scaling test.
        
        Args:
            api_key: API key for authentication
            endpoint: API endpoint URL
            num_workers: Number of worker processes (0 = auto-detect)
            ramp_up_seconds: Time to gradually start workers
            target_rps: Target requests per second (0 = unlimited)
        """
        self.api_key = api_key
        self.endpoint = endpoint
        self.ramp_up_seconds = ramp_up_seconds
        self.target_rps = target_rps
        
        # Auto-detect worker count if not specified
        if num_workers <= 0:
            self.num_workers = multiprocessing.cpu_count()
        else:
            self.num_workers = num_workers
            
        # Calculate delay between operations if target RPS is specified
        if target_rps > 0:
            # Distribute the load across workers
            requests_per_worker = target_rps / self.num_workers
            self.delay_ms = int(1000 / requests_per_worker) if requests_per_worker > 0 else 0
        else:
            self.delay_ms = 0
            
        # Set up multiprocessing
        self.result_queue = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()
        self.processes = []
        
        # Results
        self.test_result = None
        
    def start_workers(self, duration_seconds: int):
        """Start worker processes.
        
        Args:
            duration_seconds: Test duration in seconds
        """
        logger.info(f"Starting {self.num_workers} workers with {self.delay_ms}ms delay between operations")
        
        for i in range(self.num_workers):
            process = multiprocessing.Process(
                target=worker_process,
                args=(
                    self.api_key,
                    self.endpoint,
                    i,
                    self.result_queue,
                    self.stop_event,
                    duration_seconds,
                    self.delay_ms,
                    self.ramp_up_seconds,
                ),
            )
            process.start()
            self.processes.append(process)
            
    def stop_workers(self):
        """Stop all worker processes."""
        logger.info("Stopping workers")
        self.stop_event.set()
        
        for process in self.processes:
            process.join(timeout=5)
            if process.is_alive():
                logger.warning(f"Force terminating worker process {process.pid}")
                process.terminate()
                
        self.processes = []
        
    def collect_results(self, test_duration: float) -> ScalingTestResult:
        """Collect and process test results.
        
        Args:
            test_duration: Actual test duration in seconds
            
        Returns:
            Test results
        """
        logger.info("Collecting test results")
        
        # Initialize results
        result = ScalingTestResult(
            start_time=datetime.now(timezone.utc).isoformat(),
            end_time=(datetime.now(timezone.utc) + timedelta(seconds=test_duration)).isoformat(),
            duration_seconds=test_duration,
            num_workers=self.num_workers,
            ramp_up_seconds=self.ramp_up_seconds,
            target_rps=self.target_rps,
        )
        
        # Process results from queue
        while not self.result_queue.empty():
            try:
                item = self.result_queue.get(block=False)
                
                operation = item["operation"]
                success = item["success"]
                duration_ms = item["duration_ms"]
                
                # Count requests
                result.total_requests += 1
                if success:
                    result.successful_requests += 1
                else:
                    result.failed_requests += 1
                    
                # Record timing
                if success and duration_ms > 0:
                    result.add_timing(operation, duration_ms)
                    
            except queue.Empty:
                break
                
        # Calculate derived metrics
        result.calculate_metrics()
        return result
        
    def run_test(self, duration_seconds: int) -> ScalingTestResult:
        """Run the scaling test.
        
        Args:
            duration_seconds: Test duration in seconds
            
        Returns:
            Test results
        """
        logger.info(f"Starting scaling test for {duration_seconds}s with {self.num_workers} workers")
        logger.info(f"Target RPS: {self.target_rps if self.target_rps > 0 else 'unlimited'}")
        
        try:
            # Start test
            start_time = time.time()
            self.start_workers(duration_seconds)
            
            # Wait for test duration plus ramp-up time
            total_wait_time = duration_seconds + self.ramp_up_seconds
            time.sleep(total_wait_time)
            
            # Stop test
            self.stop_workers()
            end_time = time.time()
            
            # Collect results
            actual_duration = end_time - start_time
            self.test_result = self.collect_results(actual_duration)
            
            return self.test_result
            
        except KeyboardInterrupt:
            logger.info("Test interrupted")
            self.stop_workers()
            
            # Collect partial results
            if start_time:
                actual_duration = time.time() - start_time
                self.test_result = self.collect_results(actual_duration)
                return self.test_result
            
            return None
            
        except Exception as e:
            logger.error(f"Test error: {e}")
            self.stop_workers()
            return None
            
    def save_results(self, filename: str = None) -> str:
        """Save test results to file.
        
        Args:
            filename: Optional filename (defaults to timestamp-based name)
            
        Returns:
            Path to saved results file
        """
        if not self.test_result:
            logger.warning("No test results to save")
            return None
            
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scaling_test_results_{timestamp}.json"
            
        with open(filename, "w") as f:
            json.dump(asdict(self.test_result), f, indent=2)
            
        logger.info(f"Test results saved to {filename}")
        return filename
        
    def print_summary(self):
        """Print a summary of test results."""
        if not self.test_result:
            logger.warning("No test results to summarize")
            return
            
        result = self.test_result
        
        print("\n=== SCALING TEST SUMMARY ===")
        print(f"Duration: {result.duration_seconds:.1f}s")
        print(f"Workers: {result.num_workers}")
        print(f"Target RPS: {result.target_rps if result.target_rps > 0 else 'unlimited'}")
        print(f"Actual RPS: {result.actual_rps:.2f}")
        print(f"Total Requests: {result.total_requests}")
        print(f"Success Rate: {(1 - result.error_rate) * 100:.1f}%")
        
        # Print operation metrics
        print("\nOperation Metrics (ms):")
        headers = ["Operation", "Count", "Mean", "P50", "P95", "P99", "Max"]
        print(f"{headers[0]:<15} {headers[1]:<8} {headers[2]:<8} {headers[3]:<8} {headers[4]:<8} {headers[5]:<8} {headers[6]:<8}")
        
        for operation in sorted(result.timings.keys()):
            count = len(result.timings[operation])
            mean = result.mean_ms[operation]
            p50 = result.p50_ms[operation]
            p95 = result.p95_ms[operation]
            p99 = result.p99_ms[operation]
            max_val = result.max_ms[operation]
            
            print(f"{operation:<15} {count:<8d} {mean:<8.1f} {p50:<8.1f} {p95:<8.1f} {p99:<8.1f} {max_val:<8.1f}")


def handle_interrupt(signum, frame):
    """Handle interrupt signal."""
    print("\nTest interrupted. Shutting down...")
    sys.exit(1)


def main():
    """Run scaling test from command line."""
    # Set up signal handling
    signal.signal(signal.SIGINT, handle_interrupt)
    
    parser = argparse.ArgumentParser(description="EUDI-Connect scaling test")
    
    # API connection parameters
    parser.add_argument("--api-key", type=str, required=True, help="API key for authentication")
    parser.add_argument("--endpoint", type=str, required=True, help="API endpoint URL")
    
    # Test parameters
    parser.add_argument("--workers", type=int, default=0, help="Number of worker processes (0 = auto)")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--ramp-up", type=int, default=0, help="Ramp-up time in seconds")
    parser.add_argument("--target-rps", type=float, default=0, help="Target requests per second (0 = unlimited)")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    # Run test
    test = ScalingTest(
        api_key=args.api_key,
        endpoint=args.endpoint,
        num_workers=args.workers,
        ramp_up_seconds=args.ramp_up,
        target_rps=args.target_rps,
    )
    
    result = test.run_test(args.duration)
    
    if result:
        test.save_results(args.output)
        test.print_summary()


if __name__ == "__main__":
    main()
