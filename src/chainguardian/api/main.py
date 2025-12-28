"""
FastAPI application entry point for ChainGuardian AI.
"""
import logging
import json
import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

# Import routers
from chainguardian.api.routers import health, predict
from chainguardian.api.routers import reports  # New reports router
from chainguardian.api.middleware.rate_limiter import setup_rate_limiting

# Setup structured logging
from pythonjsonlogger import jsonlogger

# Create request ID context variable
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

# Configure structured JSON logging
logger = logging.getLogger("chainguardian")
logger.setLevel(logging.INFO)

# Create JSON formatter
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={
        "asctime": "timestamp",
        "levelname": "level",
        "name": "logger"
    }
)

# Create console handler
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Create FastAPI app instance
app = FastAPI(
    title="ChainGuardian AI API",
    description=(
        "ML-powered smart contract vulnerability detection with LLM report generation. "
        "Analyzes Solidity contracts using ensemble ML (99.78% AUC) "
        "with comprehensive feature extraction (AST, graph, semantic analysis)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify allowed domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests."""
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request start
    logger.info("Request started", extra={
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown"
    })
    
    try:
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log request completion
        logger.info("Request completed", extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "duration_ms": 0  # Would calculate from start time
        })
        
        return response
        
    except Exception as e:
        # Log error
        logger.error("Request failed", extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "error": str(e)
        })
        raise

# Setup rate limiting (will be configured based on environment)
REDIS_URL = "redis://redis:6379/0"
setup_rate_limiting(app, REDIS_URL)

# Include routers
app.include_router(health.router)
app.include_router(predict.router)
app.include_router(reports.router)  # New reports endpoints

# Add Prometheus instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=[".*admin.*", "/metrics"],
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    env_var_name="ENABLE_METRICS",
    excluded_status_codes=[401, 403, 404, 405],
    # Add custom labels
    body_handlers=[],
    inprogress_labels=True,
    latency_lowr_buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error("Unhandled exception", extra={
        "request_id": request_id,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "endpoint": str(request.url),
        "method": request.method
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "request_id": request_id,
            "support": "contact@chainguardian.ai"
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize resources at startup."""
    print("=" * 70)
    print("🚀 ChainGuardian AI API Starting...")
    print("=" * 70)
    print("📊 Model: Ensemble (XGBoost + RF + LightGBM + LogReg)")
    print("🎯 Performance: 99.78% AUC, 66ms latency")
    print("🔧 Features: 89 (AST + Graph + Semantic)")
    print("🤖 LLM Integration: Ollama + Multiple Models")
    print("📈 Monitoring: Prometheus + Grafana + Structured Logging")
    print("🔒 Security: Rate Limiting + Request Tracing")
    print("=" * 70)
    print("📖 Documentation: http://localhost:8000/docs")
    print("🏥 Health Check:  http://localhost:8000/health")
    print("📊 Metrics:       http://localhost:8000/metrics")
    print("🔮 Analyze:       POST http://localhost:8000/api/v1/analyze")
    print("📝 Reports:       POST http://localhost:8000/api/v1/reports/generate")
    print("⚡ Direct Pred:   POST http://localhost:8000/api/v1/predict-from-features")
    print("=" * 70)
    
    # Log startup
    logger.info("Application started", extra={
        "service": "chainguardian-api",
        "version": "1.0.0",
        "environment": "development"
    })

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources at shutdown."""
    print("\n👋 ChainGuardian AI API shutting down...")
    logger.info("Application shutting down")