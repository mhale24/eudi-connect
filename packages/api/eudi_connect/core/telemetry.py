from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from eudi_connect.core.config import settings


def configure_telemetry() -> None:
    """Configure OpenTelemetry for distributed tracing."""
    if not settings.TELEMETRY_ENABLED or not settings.OTLP_ENDPOINT:
        return

    # Create resource
    resource = Resource.create({
        "service.name": settings.PROJECT_NAME,
        "service.version": settings.VERSION,
        "deployment.environment": "production",
    })

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Create OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=settings.OTLP_ENDPOINT)
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
