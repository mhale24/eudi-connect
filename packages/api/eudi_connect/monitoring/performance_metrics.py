"""Performance monitoring for EUDI-Connect.

This module provides OpenTelemetry integration for tracking credential
exchange performance metrics.

Example usage:
    ```python
    from eudi_connect.monitoring.performance_metrics import PerformanceMonitor

    # Create a monitor with default configuration
    monitor = PerformanceMonitor()

    # Track credential issuance time
    with monitor.measure_time("credential.issuance", {"operation": "issue"}):
        credential = issue_credential(...)

    # Track verification time with explicit start/end
    monitor.start_timer("credential.verification")
    result = verify_credential(...)
    monitor.end_timer("credential.verification", {"status": "success" if result else "failed"})
    ```
"""
import time
import logging
import functools
import contextlib
from typing import Dict, Optional, Any, Callable, Iterator, TypeVar, cast

# Optional OpenTelemetry imports - will gracefully degrade if not available
try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

# Define function type variable for decorators
F = TypeVar('F', bound=Callable[..., Any])


class PerformanceMonitor:
    """Performance monitoring for EUDI-Connect operations.
    
    This class provides utilities for tracking performance metrics and
    reporting them to OpenTelemetry monitoring.
    """
    
    def __init__(
        self,
        service_name: str = "eudi-connect",
        enable_console_export: bool = False,
        enable_otlp_export: bool = True,
        otlp_endpoint: Optional[str] = None,
        include_hostname: bool = True,
    ):
        """Initialize the performance monitor.
        
        Args:
            service_name: Name of the service for reporting
            enable_console_export: Whether to export metrics to console
            enable_otlp_export: Whether to export metrics to OTLP endpoint
            otlp_endpoint: OTLP endpoint URL (default: from environment)
            include_hostname: Whether to include hostname in resource
        """
        self.service_name = service_name
        self.active_timers = {}
        self._initialize_metrics(
            enable_console_export,
            enable_otlp_export,
            otlp_endpoint,
            include_hostname,
        )
        
    def _initialize_metrics(
        self,
        enable_console_export: bool,
        enable_otlp_export: bool,
        otlp_endpoint: Optional[str],
        include_hostname: bool,
    ):
        """Initialize OpenTelemetry metrics.
        
        Args:
            enable_console_export: Whether to export metrics to console
            enable_otlp_export: Whether to export metrics to OTLP endpoint
            otlp_endpoint: OTLP endpoint URL
            include_hostname: Whether to include hostname in resource
        """
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available. Install with 'pip install opentelemetry-api opentelemetry-sdk'")
            self.meter = None
            return
            
        # Create resource with service information
        resource_attributes = {
            "service.name": self.service_name,
        }
        
        # Add hostname if requested
        if include_hostname:
            import socket
            resource_attributes["service.instance.id"] = socket.gethostname()
            
        resource = Resource.create(resource_attributes)
        
        # Create metric readers
        readers = []
        
        if enable_console_export:
            console_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=60000,  # Export every minute
            )
            readers.append(console_reader)
            
        if enable_otlp_export:
            try:
                otlp_reader = PeriodicExportingMetricReader(
                    OTLPMetricExporter(endpoint=otlp_endpoint),
                    export_interval_millis=15000,  # Export every 15 seconds
                )
                readers.append(otlp_reader)
            except Exception as e:
                logger.error(f"Failed to initialize OTLP exporter: {e}")
        
        # Set up meter provider
        if readers:
            provider = MeterProvider(metric_readers=readers, resource=resource)
            metrics.set_meter_provider(provider)
            self.meter = metrics.get_meter(self.service_name)
            
            # Create metrics
            self.operation_time = self.meter.create_histogram(
                name="operation.time",
                description="Time taken by operations in milliseconds",
                unit="ms",
            )
            
            self.operation_count = self.meter.create_counter(
                name="operation.count",
                description="Count of operations",
                unit="1",
            )
            
            logger.info(f"Performance monitoring initialized for {self.service_name}")
        else:
            logger.warning("No metric exporters configured. Monitoring will not be active.")
            self.meter = None
        
    def start_timer(self, operation: str) -> str:
        """Start a timer for measuring operation duration.
        
        Args:
            operation: Name of the operation to time
            
        Returns:
            Timer ID for stopping the timer
        """
        timer_id = f"{operation}_{time.time_ns()}"
        self.active_timers[timer_id] = time.perf_counter()
        return timer_id
        
    def end_timer(
        self,
        timer_id: str,
        attributes: Optional[Dict[str, str]] = None,
    ) -> float:
        """End a timer and record the operation duration.
        
        Args:
            timer_id: Timer ID from start_timer
            attributes: Optional attributes for the metric
            
        Returns:
            Duration in milliseconds, or -1 if timer not found
        """
        if timer_id not in self.active_timers:
            logger.warning(f"Timer {timer_id} not found")
            return -1
            
        # Calculate duration
        start_time = self.active_timers.pop(timer_id)
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Extract operation name from timer_id
        operation = timer_id.split('_')[0]
        
        # Record metrics
        self._record_metrics(operation, duration_ms, attributes)
        
        return duration_ms
        
    def _record_metrics(
        self,
        operation: str,
        duration_ms: float,
        attributes: Optional[Dict[str, str]] = None,
    ):
        """Record metrics to OpenTelemetry.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            attributes: Optional attributes for the metric
        """
        if not self.meter:
            # OpenTelemetry not available, just log
            logger.debug(f"Operation {operation} took {duration_ms:.2f}ms")
            return
            
        # Prepare attributes
        attrs = {"operation": operation}
        if attributes:
            attrs.update(attributes)
            
        # Record metrics
        self.operation_time.record(duration_ms, attrs)
        self.operation_count.add(1, attrs)
        
    @contextlib.contextmanager
    def measure_time(
        self,
        operation: str,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Iterator[None]:
        """Context manager for measuring operation time.
        
        Args:
            operation: Name of the operation
            attributes: Optional attributes for the metric
            
        Yields:
            None
        """
        timer_id = self.start_timer(operation)
        try:
            yield
        finally:
            self.end_timer(timer_id, attributes)
            
    def time_function(
        self,
        operation: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Callable[[F], F]:
        """Decorator for timing function execution.
        
        Args:
            operation: Name of the operation (default: function name)
            attributes: Optional attributes for the metric
            
        Returns:
            Function decorator
        """
        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                op_name = operation or func.__name__
                with self.measure_time(op_name, attributes):
                    return func(*args, **kwargs)
            return cast(F, wrapper)
        return decorator


# Initialize a default global monitor instance
default_monitor = PerformanceMonitor()


def time_operation(
    operation: Optional[str] = None,
    attributes: Optional[Dict[str, str]] = None,
    monitor: Optional[PerformanceMonitor] = None,
) -> Callable[[F], F]:
    """Decorator for timing function execution using the default monitor.
    
    Args:
        operation: Name of the operation (default: function name)
        attributes: Optional attributes for the metric
        monitor: Optional custom monitor instance
        
    Returns:
        Function decorator
    """
    _monitor = monitor or default_monitor
    return _monitor.time_function(operation, attributes)


@contextlib.contextmanager
def measure_operation_time(
    operation: str,
    attributes: Optional[Dict[str, str]] = None,
    monitor: Optional[PerformanceMonitor] = None,
) -> Iterator[None]:
    """Context manager for measuring operation time using the default monitor.
    
    Args:
        operation: Name of the operation
        attributes: Optional attributes for the metric
        monitor: Optional custom monitor instance
        
    Yields:
        None
    """
    _monitor = monitor or default_monitor
    with _monitor.measure_time(operation, attributes):
        yield
