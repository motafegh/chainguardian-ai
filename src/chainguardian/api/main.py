"""
FastAPI application entry point for ChainGuardian AI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from chainguardian.api.routers import health, predict

# Create FastAPI app instance
app = FastAPI(
    title="ChainGuardian AI API",
    description=(
        "ML-powered smart contract vulnerability detection. "
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

# Include routers
app.include_router(health.router)
app.include_router(predict.router)  # NEW: Add prediction endpoints

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
    print("=" * 70)
    print("📖 Documentation: http://localhost:8000/docs")
    print("🏥 Health Check:  http://localhost:8000/health")
    print("🔮 Analyze:       POST http://localhost:8000/api/v1/analyze")
    print("⚡ Direct Pred:   POST http://localhost:8000/api/v1/predict-from-features")
    print("=" * 70)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources at shutdown."""
    print("\n👋 ChainGuardian AI API shutting down...")
