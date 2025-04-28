"""
Main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .api.v1 import tao_dividends

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Tao Dividends API Service",
    debug=True,  # Enable debug mode
)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
