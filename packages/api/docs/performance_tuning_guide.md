# EUDI-Connect Performance Tuning Guide

This guide documents performance optimization patterns and techniques used in the EUDI-Connect platform to achieve our performance targets:

- **MVP Target**: ≤800ms P95 credential exchange latency
- **Future Target**: ≤300ms performance target

## Table of Contents

1. [Performance Monitoring](#performance-monitoring)
2. [Template System Optimization](#template-system-optimization)
3. [Credential Exchange Flow](#credential-exchange-flow)
4. [Testing Methodology](#testing-methodology)
5. [Common Bottlenecks](#common-bottlenecks)
6. [Optimization Patterns](#optimization-patterns)
7. [Performance SLAs](#performance-slas)

## Performance Monitoring

### OpenTelemetry Integration

EUDI-Connect uses OpenTelemetry for comprehensive performance monitoring. The `PerformanceMonitor` class in `eudi_connect/monitoring/performance_metrics.py` provides:

- Function-level timing via decorators
- Context-based measurement for code blocks
- Automatic reporting to configured telemetry backends

Example usage:

```python
from eudi_connect.monitoring.performance_metrics import time_operation, measure_operation_time

# Decorate functions for automatic timing
@time_operation(operation="credential.issuance")
async def issue_credential(credential_data):
    # Function execution will be timed automatically
    return issued_credential

# Use context manager for timing code blocks
async def complex_operation():
    # Prepare data
    
    # Time just the critical section
    with measure_operation_time("critical_operation", {"type": "high_priority"}):
        result = await critical_operation()
        
    # Process result
    return processed_result
```

### Key Metrics

The following metrics are tracked for all credential operations:

| Metric | Description | Target |
|--------|-------------|--------|
| `operation.time` | Time taken by operations in milliseconds | Varies by operation |
| `operation.count` | Count of operations | N/A |

Attributes attached to metrics include:
- `operation`: Name of the operation
- Additional custom attributes for filtering and analysis

## Template System Optimization

The template system has been optimized for high-performance rendering with the following techniques:

### Template Pre-compilation

Templates are pre-compiled and cached to avoid repeated parsing:

```python
# Example of template pre-compilation
def _compile_template(template_content, template_id, format_type):
    cache_key = f"{template_id}:{format_type}"
    
    # Return cached compiled template if available
    if cache_key in _template_cache:
        return _template_cache[cache_key]
        
    # Create a compiled template function
    def compiled_template(data):
        return template_content.format(**data)
        
    # Cache the compiled template
    _template_cache[cache_key] = compiled_template
    return compiled_template
```

### Efficient ID Generation

UUIDs are used for template IDs instead of timestamp-based IDs for better performance and uniqueness:

```python
import uuid
template_id = f"template_{uuid.uuid4().hex}"
```

### Selective Cache Invalidation

The caching system allows invalidating specific templates rather than the entire cache:

```python
def invalidate_cache(template_id=None):
    if template_id:
        # Clear specific template from cache if possible
        if hasattr(self._get_template, 'cache_delete'):
            self._get_template.cache_delete((template_id,))
            return
    # Otherwise, clear the full cache
    self._get_template.cache_clear()
```

### Batch Processing

Templates support batch rendering for improved throughput:

```python
# Batch rendering is more efficient than multiple individual renders
results = template_manager.render_batch(
    template_id="notification_template",
    format=TemplateFormat.HTML,
    alerts=alerts_list
)
```

## Credential Exchange Flow

The credential exchange flow has been optimized for maximum performance:

### Async Processing

All credential operations use asynchronous processing:

```python
async def issue_credential(db: DB, request: CredentialIssueRequest):
    # Asynchronous processing for better throughput
    async with db.session() as session:
        # Issue credential
        
    return result
```

### Connection Pooling

Database connections are properly pooled and reused:

```python
# Example database pool configuration
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### Efficient Error Handling

Error handling is designed to fail fast and avoid unnecessary processing:

```python
async def verify_credential(credential):
    # Validate input early
    if not credential:
        raise ValueError("Credential cannot be empty")
        
    try:
        # Perform verification
        return result
    except Exception as e:
        # Log specific error for diagnostics
        logger.error(f"Verification failed: {e}", exc_info=True)
        # Don't re-raise for better performance in certain scenarios
        return {"valid": False, "error": str(e)}
```

## Testing Methodology

EUDI-Connect uses a comprehensive testing methodology to ensure performance targets are met:

### Unit Performance Tests

- Located in `tests/performance/test_templates_standalone.py`
- Focus on individual component performance
- Run automatically in CI/CD pipeline

### Benchmark Tools

Three main benchmark tools are provided:

1. **Template Benchmarks** (`benchmark_templates.py`):
   - Measures template rendering performance
   - Tests both single and batch operations

2. **Credential Exchange Benchmarks** (`benchmark_credential_exchange.py`):
   - Tests issuance, verification, and revocation
   - Measures full credential lifecycle performance

3. **Production Tests** (`production_test.py`):
   - Tests against actual production/staging environment
   - Measures real-world performance with network latency

4. **Scaling Tests** (`scaling_test.py`):
   - Tests performance under load with concurrent users
   - Identifies system bottlenecks at scale

### Running Performance Tests

Basic usage:

```bash
# Template benchmarks
python tests/performance/benchmark_templates.py --num-templates 5 --num-alerts 100

# Credential exchange benchmarks
python tests/performance/benchmark_credential_exchange.py --num-credentials 50

# Production tests
python tests/performance/production_test.py --api-key YOUR_API_KEY --endpoint https://api.eudi-connect.example.com

# Scaling tests
python tests/performance/scaling_test.py --api-key YOUR_API_KEY --endpoint https://api.eudi-connect.example.com --workers 10 --duration 60
```

## Common Bottlenecks

### Database Operations

- **Problem**: Excessive database queries
- **Solution**: Use batch operations and minimize round trips

```python
# Instead of this:
for item in items:
    await db.add(item)
    await db.commit()

# Do this:
await db.add_all(items)
await db.commit()
```

### Synchronous Operations

- **Problem**: Blocking operations in async code
- **Solution**: Use proper async libraries or move blocking code to thread pools

```python
# Instead of this:
result = blocking_operation()  # Blocks the event loop

# Do this:
import asyncio
result = await asyncio.to_thread(blocking_operation)
```

### Template Rendering

- **Problem**: Repeated template parsing
- **Solution**: Pre-compile and cache templates

### Connection Management

- **Problem**: Connection leaks and excessive creation
- **Solution**: Use proper connection pooling and ensure all connections are released

## Optimization Patterns

### Caching Strategy

EUDI-Connect uses a multi-level caching strategy:

1. **In-Memory Caching**: For frequently accessed templates and configuration
2. **Function-Level Caching**: Using `lru_cache` for expensive operations
3. **Distributed Caching**: For sharing across instances (optional)

### Batch Processing

Whenever possible, operations are batched for efficiency:

```python
# Example of batch processing
async def process_batch(items):
    # Process multiple items in a single operation
    return await _process_items_in_batch(items)
```

### Asynchronous Processing

All I/O-bound operations use async patterns:

```python
# Example of proper async pattern
async def async_operation():
    async with resource_manager() as resource:
        result = await resource.perform_operation()
    return result
```

### Lazy Initialization

Resources are initialized only when needed:

```python
# Example of lazy initialization
class LazyService:
    def __init__(self):
        self._initialized = False
        self._resource = None
        
    async def get_resource(self):
        if not self._initialized:
            await self._initialize()
        return self._resource
        
    async def _initialize(self):
        self._resource = await create_expensive_resource()
        self._initialized = True
```

## Performance SLAs

EUDI-Connect maintains the following performance Service Level Agreements (SLAs):

| Operation | P95 Target (MVP) | P95 Target (Future) |
|-----------|------------------|---------------------|
| Credential Issuance | ≤500ms | ≤200ms |
| Credential Verification | ≤200ms | ≤100ms |
| Credential Revocation | ≤300ms | ≤150ms |
| Full Lifecycle | ≤800ms | ≤300ms |

### Monitoring These SLAs

Performance is continuously monitored against these targets. If you observe degradation:

1. Run the benchmark tools to identify specific bottlenecks
2. Check recent code changes that might have affected performance
3. Review system resources (CPU, memory, network) for constraints
4. Consult the OpenTelemetry dashboards for detailed metrics

## Conclusion

By following these performance optimization patterns and regularly testing against our benchmarks, we can ensure EUDI-Connect maintains its high-performance targets. As new features are added, always consider performance implications and run appropriate tests.

For questions or assistance with performance tuning, contact the EUDI-Connect core team.
