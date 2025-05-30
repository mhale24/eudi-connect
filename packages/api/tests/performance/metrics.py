"""Performance metrics collection and analysis."""
import asyncio
import gc
import os
import resource
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

import psutil
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from eudi_connect.database import get_db


@dataclass
class QueryMetrics:
    """Database query performance metrics."""
    query: str
    execution_time: float
    rows_affected: int
    index_usage: bool


@dataclass
class EndpointMetrics:
    """API endpoint performance metrics."""
    path: str
    method: str
    status_code: int
    response_time: float
    cpu_usage: float
    memory_usage: float
    db_queries: List[QueryMetrics]


class MetricsCollector:
    """Collects and analyzes performance metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.process = psutil.Process(os.getpid())
        self.metrics: List[EndpointMetrics] = []
        self._start_cpu_percent = 0.0
        self._start_memory = 0.0
        self._query_metrics: List[QueryMetrics] = []

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        gc.collect()  # Force garbage collection for accurate measurement
        return self.process.memory_info().rss / 1024 / 1024

    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        return self.process.cpu_percent()

    async def _collect_query_metrics(
        self,
        session: AsyncSession,
        query: sa.Select[Any],
    ) -> QueryMetrics:
        """Collect metrics for a single database query."""
        # Get query execution plan
        plan = await session.execute(f"EXPLAIN {query}")
        plan_rows = plan.fetchall()
        index_usage = any("Index Scan" in str(row) for row in plan_rows)

        # Execute query with timing
        start_time = time.perf_counter()
        result = await session.execute(query)
        execution_time = time.perf_counter() - start_time

        return QueryMetrics(
            query=str(query),
            execution_time=execution_time,
            rows_affected=result.rowcount,
            index_usage=index_usage,
        )

    @asynccontextmanager
    async def measure_endpoint(
        self,
        path: str,
        method: str,
    ) -> AsyncGenerator[None, None]:
        """Measure endpoint performance metrics."""
        # Start measurements
        self._start_cpu_percent = self._get_cpu_usage()
        self._start_memory = self._get_memory_usage()
        start_time = time.perf_counter()
        self._query_metrics = []

        try:
            yield
        finally:
            # Calculate metrics
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            end_cpu = self._get_cpu_usage()

            self.metrics.append(EndpointMetrics(
                path=path,
                method=method,
                status_code=200,  # Set actual status code in your tests
                response_time=end_time - start_time,
                cpu_usage=end_cpu - self._start_cpu_percent,
                memory_usage=end_memory - self._start_memory,
                db_queries=self._query_metrics.copy(),
            ))

    def get_latency_percentiles(self) -> Dict[str, float]:
        """Calculate latency percentiles."""
        if not self.metrics:
            return {}

        response_times = sorted(m.response_time for m in self.metrics)
        total = len(response_times)

        return {
            "p50": response_times[int(total * 0.50)],
            "p75": response_times[int(total * 0.75)],
            "p90": response_times[int(total * 0.90)],
            "p95": response_times[int(total * 0.95)],
            "p99": response_times[int(total * 0.99)] if total >= 100 else None,
        }

    def get_throughput(self, duration: float) -> float:
        """Calculate requests per second."""
        return len(self.metrics) / duration

    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        memory_usages = [m.memory_usage for m in self.metrics]
        return {
            "min": min(memory_usages),
            "max": max(memory_usages),
            "avg": sum(memory_usages) / len(memory_usages),
        }

    def get_cpu_stats(self) -> Dict[str, float]:
        """Get CPU usage statistics."""
        cpu_usages = [m.cpu_usage for m in self.metrics]
        return {
            "min": min(cpu_usages),
            "max": max(cpu_usages),
            "avg": sum(cpu_usages) / len(cpu_usages),
        }

    def get_db_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        all_queries = [q for m in self.metrics for q in m.db_queries]
        if not all_queries:
            return {}

        return {
            "total_queries": len(all_queries),
            "avg_query_time": sum(q.execution_time for q in all_queries) / len(all_queries),
            "slow_queries": len([q for q in all_queries if q.execution_time > 0.1]),
            "index_usage_pct": sum(1 for q in all_queries if q.index_usage) / len(all_queries) * 100,
        }

    def get_resource_limits(self) -> Dict[str, int]:
        """Get system resource limits."""
        return {
            "max_memory": resource.getrlimit(resource.RLIMIT_AS)[0],
            "max_cpu_time": resource.getrlimit(resource.RLIMIT_CPU)[0],
            "max_processes": resource.getrlimit(resource.RLIMIT_NPROC)[0],
            "max_files": resource.getrlimit(resource.RLIMIT_NOFILE)[0],
        }

    def print_report(self, duration: float) -> None:
        """Print a comprehensive performance report."""
        print("\n=== Performance Report ===")
        
        print("\nLatency (seconds):")
        for percentile, value in self.get_latency_percentiles().items():
            if value is not None:
                print(f"  {percentile}: {value:.3f}s")

        print("\nThroughput:")
        print(f"  {self.get_throughput(duration):.2f} requests/second")

        print("\nMemory Usage (MB):")
        for stat, value in self.get_memory_stats().items():
            print(f"  {stat}: {value:.2f}MB")

        print("\nCPU Usage (%):")
        for stat, value in self.get_cpu_stats().items():
            print(f"  {stat}: {value:.1f}%")

        print("\nDatabase Performance:")
        for stat, value in self.get_db_stats().items():
            if isinstance(value, float):
                print(f"  {stat}: {value:.2f}")
            else:
                print(f"  {stat}: {value}")

        print("\nResource Limits:")
        for resource_name, limit in self.get_resource_limits().items():
            print(f"  {resource_name}: {limit}")

        print("\n=== End Report ===\n")
