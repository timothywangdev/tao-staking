import time
from typing import Tuple
import sys

from opentelemetry import trace
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
import logging
import logging_loki
from multiprocessing import Queue

INFO = Gauge("fastapi_app_info", "FastAPI application information.", ["app_name"])
REQUESTS = Counter(
    "fastapi_requests_total",
    "Total count of requests by method and path.",
    ["method", "path", "app_name"],
)
RESPONSES = Counter(
    "fastapi_responses_total",
    "Total count of responses by method, path and status codes.",
    ["method", "path", "status_code", "app_name"],
)
REQUESTS_PROCESSING_TIME = Histogram(
    "fastapi_requests_duration_seconds",
    "Histogram of requests processing time by path (in seconds)",
    ["method", "path", "app_name"],
)
EXCEPTIONS = Counter(
    "fastapi_exceptions_total",
    "Total count of exceptions raised by path and exception type",
    ["method", "path", "exception_type", "app_name"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "fastapi_requests_in_progress",
    "Gauge of requests by method and path currently being processed",
    ["method", "path", "app_name"],
)

# Global queue for all loggers
log_queue = Queue(-1)


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, app_name: str = "fastapi-app") -> None:
        super().__init__(app)
        self.app_name = app_name
        INFO.labels(app_name=self.app_name).inc()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        path, is_handled_path = self.get_path(request)

        if not is_handled_path:
            return await call_next(request)

        REQUESTS_IN_PROGRESS.labels(method=method, path=path, app_name=self.app_name).inc()
        REQUESTS.labels(method=method, path=path, app_name=self.app_name).inc()
        before_time = time.perf_counter()
        try:
            response = await call_next(request)
        except BaseException as e:
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            EXCEPTIONS.labels(
                method=method, path=path, exception_type=type(e).__name__, app_name=self.app_name
            ).inc()
            raise e from None
        else:
            status_code = response.status_code
            after_time = time.perf_counter()
            # retrieve trace id for exemplar
            span = trace.get_current_span()
            trace_id = trace.format_trace_id(span.get_span_context().trace_id)

            REQUESTS_PROCESSING_TIME.labels(
                method=method, path=path, app_name=self.app_name
            ).observe(after_time - before_time, exemplar={"TraceID": trace_id})
        finally:
            RESPONSES.labels(
                method=method, path=path, status_code=status_code, app_name=self.app_name
            ).inc()
            REQUESTS_IN_PROGRESS.labels(method=method, path=path, app_name=self.app_name).dec()

        return response

    @staticmethod
    def get_path(request: Request) -> Tuple[str, bool]:
        for route in request.app.routes:
            match, child_scope = route.matches(request.scope)
            if match == Match.FULL:
                return route.path, True

        return request.url.path, False


def metrics(request: Request) -> Response:
    return Response(generate_latest(REGISTRY), headers={"Content-Type": CONTENT_TYPE_LATEST})


def setting_otlp(app: ASGIApp, app_name: str, endpoint: str, log_correlation: bool = True) -> None:
    # Setting OpenTelemetry
    # set the service name to show in traces
    resource = Resource.create(attributes={"service.name": app_name, "compose_service": app_name})

    # set the tracer provider
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)

    tracer.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))

    if log_correlation:
        LoggingInstrumentor().instrument(set_logging_format=True)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)


def is_running_tests() -> bool:
    """Check if code is running in a test environment."""
    return "pytest" in sys.modules


def setting_api_logging(loki_url: str):
    """Set up logging to Loki using QueueHandler for async logging."""

    # Configure formatter to include service name and trace ID
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [service=api] %(message)s")

    # Add stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Add stream handler
    root_logger.addHandler(stream_handler)

    # Only add Loki handler if not in test environment
    if not is_running_tests():
        # Create Loki handler with queue
        loki_handler = logging_loki.LokiQueueHandler(
            Queue(-1),
            url=loki_url,
            tags={"service": "api"},
            version="1",
        )
        loki_handler.setFormatter(formatter)
        root_logger.addHandler(loki_handler)

        # Add test logs
        logging.info("API logging initialized - Testing Loki connection")
        logging.info(f"Loki URL: {loki_url}")
    else:
        logging.info("Running in test environment - Loki logging disabled")


def setting_celery_logging(loki_url: str):
    """Set up Celery-specific logging to Loki."""
    global log_queue

    # Configure formatter to include service name
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] [service=celery-worker] [%(processName)s] %(message)s"
    )

    # Add stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Configure Celery loggers
    loggers = ["celery", "celery.task", "celery.worker"]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Add stream handler
        logger.addHandler(stream_handler)

        # Only add Loki handler if not in test environment
        if not is_running_tests():
            # Create Loki handler with queue for Celery logs
            celery_handler = logging_loki.LokiQueueHandler(
                Queue(-1), url=loki_url, tags={"service": "celery-worker"}, version="1"
            )
            celery_handler.setFormatter(formatter)
            logger.addHandler(celery_handler)

    if not is_running_tests():
        logging.info("Celery logging initialized with Loki")
    else:
        logging.info("Running in test environment - Celery Loki logging disabled")
