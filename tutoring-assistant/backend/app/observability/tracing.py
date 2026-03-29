import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def setup_tracing(app=None, engine=None):
    settings = get_settings()

    resource = Resource.create({
        "service.name": settings.otel_service_name,
        "service.version": "1.0.0",
    })

    provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    HTTPXClientInstrumentor().instrument()

    if engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=engine)

    if app is not None:
        FastAPIInstrumentor.instrument_app(app)

    logger.info(f"OpenTelemetry tracing initialized, exporting to {settings.otel_exporter_otlp_endpoint}")
