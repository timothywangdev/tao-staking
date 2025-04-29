"""
Main FastAPI application.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.api.v1 import tao_dividends
import uvicorn
from app.utils import PrometheusMiddleware, metrics, setting_api_logging, setting_otlp
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Tao Dividends API Service",
    debug=True,  # Enable debug mode
)

setting_api_logging(settings.LOKI_URL)
setting_otlp(app, settings.PROJECT_NAME, settings.OTLP_GRPC_ENDPOINT)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)
app.add_middleware(PrometheusMiddleware, app_name=settings.PROJECT_NAME)
app.add_route("/metrics", metrics)


class EndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


# Custom exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code, content={"detail": str(exc.detail), "type": "http_error"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc), "type": "validation_error"})


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": "internal_error",
            "debug_info": {"error_type": type(exc).__name__},
        },
    )


app.include_router(tao_dividends.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    # update uvicorn access logger format
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = (
        "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
    )
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=log_config)
