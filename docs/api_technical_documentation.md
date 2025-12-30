# ChainGuardian AI - API Module Technical Documentation

**Version:** 1.0.0
**Last Updated:** 2025-12-29
**Module Path:** `src/chainguardian/api`

**Related Documentation:**

- [ML Core Technical Documentation](ml_core_technical_documentation.md)
- [Monitoring Technical Documentation](monitoring_technical_documentation.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Request & Response Schemas](#request--response-schemas)
5. [Middleware](#middleware)
6. [Dependencies & Model Loading](#dependencies--model-loading)
7. [Monitoring & Observability](#monitoring--observability)
8. [Deployment](#deployment)
9. [API Usage Examples](#api-usage-examples)
10. [Error Handling](#error-handling)

---

## Overview

The ChainGuardian AI API is a production-ready FastAPI service that exposes ML-powered smart contract vulnerability detection capabilities through RESTful HTTP endpoints. It integrates with the [ML Core module](ml_core_technical_documentation.md) for predictions and feature extraction, and provides comprehensive LLM-powered security report generation.

### Key Features

- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Multi-Format Analysis**: Full contract analysis and direct feature prediction
- **LLM Report Generation**: Automated security audit reports using Ollama
- **Rate Limiting**: Redis-backed distributed rate limiting
- **Observability**: Prometheus metrics, structured logging, request tracing
- **High Performance**: 66ms average prediction latency, 99.78% AUC
- **Production-Ready**: CORS, error handling, health checks, graceful shutdown

### Technology Stack

- **Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn
- **Validation**: Pydantic v2
- **Rate Limiting**: Redis + token bucket algorithm
- **Metrics**: Prometheus (via prometheus-fastapi-instrumentator)
- **Logging**: JSON structured logging (python-json-logger)
- **LLM Integration**: Ollama (local inference)
- **ML Backend**: [ChainGuardian ML Core](ml_core_technical_documentation.md)

---

## Architecture

### System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   ChainGuardian API Layer                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              FastAPI Application                     │   │
│  │  (main.py)                                          │   │
│  └───────┬──────────────────────────────────────────────┘   │
│          │                                                   │
│  ┌───────▼──────────────────────────────────────────────┐   │
│  │              Middleware Stack                        │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  1. Request ID Injection                            │   │
│  │  2. CORS                                            │   │
│  │  3. Rate Limiting (Redis)                           │   │
│  │  4. Prometheus Instrumentation                       │   │
│  │  5. Exception Handler                               │   │
│  └───────┬──────────────────────────────────────────────┘   │
│          │                                                   │
│  ┌───────▼──────────────────────────────────────────────┐   │
│  │                   Routers                            │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  • /health           - Health checks                │   │
│  │  • /api/v1/analyze   - Full contract analysis       │   │
│  │  • /api/v1/predict-from-features - Direct predict   │   │
│  │  • /api/v1/reports/generate - LLM reports           │   │
│  │  • /metrics          - Prometheus metrics            │   │
│  └───────┬──────────────────────────────────────────────┘   │
│          │                                                   │
│  ┌───────▼──────────────────────────────────────────────┐   │
│  │             Dependencies & Services                   │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  • Model Loader (Singleton)                         │   │
│  │  • Feature Pipeline (Cached)                        │   │
│  │  • Ollama Client (LLM)                              │   │
│  │  • Redis Client (Rate Limiting)                     │   │
│  └───────┬──────────────────────────────────────────────┘   │
│          │                                                   │
└──────────┼───────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────┐
    │   ML Core Module Integration     │
    ├──────────────────────────────────┤
    │  • EnhancedHybridPredictorV2    │
    │  • FeaturePipeline               │
    │  • ModelRegistry                 │
    │  • MLMonitor                     │
    └──────────────────────────────────┘
```

### Request Flow

```
HTTP Request
    ↓
[1] Request ID Middleware (UUID injection)
    ↓
[2] CORS Middleware (Access-Control headers)
    ↓
[3] Rate Limit Middleware (Redis check)
    ↓
[4] Prometheus Instrumentation (metrics tracking)
    ↓
[5] Route Handler (/analyze, /predict, /reports)
    ↓
[6] Request Validation (Pydantic schemas)
    ↓
[7] Dependency Injection (Model Loader)
    ↓
┌───────────────────────────────────┐
│  Contract Analysis Flow           │
├───────────────────────────────────┤
│  7a. Save contract to temp file   │
│  7b. Feature extraction pipeline  │
│  7c. ML prediction                │
│  7d. Result formatting            │
│  7e. Metrics logging              │
└───────────────────────────────────┘
    ↓
[8] Response Construction (Pydantic)
    ↓
[9] Response Headers (X-Request-ID, rate limits)
    ↓
[10] Structured Logging
    ↓
HTTP Response (JSON)
```

---

## API Endpoints

### 1. Health & Status Endpoints

#### `GET /health`

**Purpose:** Health check for Kubernetes/Docker liveness probes

**Response:**
```json
{
  "status": "healthy",
  "service": "chainguardian-ai",
  "version": "1.0.0"
}
```

**Usage:**
```bash
curl http://localhost:8000/health
```

---

#### `GET /`

**Purpose:** Root endpoint with API metadata

**Response:**
```json
{
  "message": "ChainGuardian AI - ML-Powered Smart Contract Auditing",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

#### `GET /metrics`

**Purpose:** Prometheus metrics endpoint for monitoring

**Response:** Prometheus text format with metrics:
- `predictions_total` - Total predictions by endpoint, model version, status
- `prediction_latency_seconds` - Prediction latency histogram
- `feature_extraction_latency_seconds` - Feature extraction time
- `model_confidence` - Model confidence distribution
- `vulnerabilities_detected` - Vulnerabilities by type and severity
- `active_predictions` - Current in-flight predictions
- `llm_requests_total` - LLM API requests
- `llm_tokens_total` - Token usage (input/output)
- `llm_latency_seconds` - LLM response time
- `rate_limit_exceeded_total` - Rate limit violations

**Integration:** Scraped by Prometheus every 15 seconds

---

### 2. Prediction Endpoints

#### `POST /api/v1/analyze`

**Purpose:** Full contract analysis pipeline (code → features → prediction)

**Route Handler:** [predict.py:46](../src/chainguardian/api/routers/predict.py#L46)

**Request Schema:** `ContractAnalysisRequest`

```json
{
  "contract_code": "pragma solidity ^0.8.0;\n\ncontract Example {\n  uint256 public value;\n}",
  "contract_name": "Example",
  "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
  "include_features": false,
  "include_explanations": false
}
```

**Request Fields:**
- `contract_code` (required): Solidity source code (10-100,000 characters)
- `contract_name` (optional): Contract name (auto-detected if omitted)
- `contract_address` (optional): Ethereum address for tracking
- `include_features` (optional): Return extracted features in response
- `include_explanations` (optional): Include SHAP explanations (+2s latency)

**Response Schema:** `ContractAnalysisResponse`

```json
{
  "is_safe": true,
  "risk_score": 0.05,
  "confidence": 0.95,
  "vulnerabilities": [
    {
      "type": "reentrancy",
      "severity": "high",
      "confidence": 0.92,
      "description": "Potential reentrancy vulnerability in withdraw function"
    }
  ],
  "summary": {
    "num_functions": 15,
    "num_external_calls": 3,
    "cyclomatic_complexity": 5.2,
    "lines_of_code": 120,
    "has_critical_issues": false,
    "complexity_rating": "low"
  },
  "contract_name": "SimpleToken",
  "contract_address": "0x1234...",
  "model_version": "v1.0.7",
  "feature_extraction_time_ms": 850,
  "prediction_time_ms": 66,
  "total_time_ms": 916,
  "timestamp": "2025-12-29T10:30:00.000Z",
  "extracted_features": null,
  "explanations": null
}
```

**Processing Pipeline:**
1. Validate Solidity code syntax
2. Save to temporary file
3. Extract 89 features via `FeaturePipeline`
4. ML prediction via `EnhancedHybridPredictorV2`
5. Convert ML output to user-friendly format
6. Track metrics (latency, confidence, vulnerabilities)
7. Clean up temporary files

**Performance:**
- Average latency: **916ms** (850ms feature extraction + 66ms prediction)
- P95 latency: ~1200ms
- P99 latency: ~1500ms

**Error Handling:**
- 400: Invalid contract code, syntax errors, feature extraction failure
- 429: Rate limit exceeded (10 requests/minute)
- 500: Internal server error, model loading failure

**Rate Limit:** 10 requests per minute per IP

---

#### `POST /api/v1/predict-from-features`

**Purpose:** Direct prediction from pre-extracted features (advanced users)

**Route Handler:** [predict.py:209](../src/chainguardian/api/routers/predict.py#L209)

**Request Schema:** `DirectPredictionRequest`

```json
{
  "features": {
    "num_functions": 15.0,
    "max_cyclomatic_complexity": 8.0,
    "cei_violations": 0.0,
    "has_reentrancy": 0.0,
    "num_external_calls": 5.0
  },
  "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
  "include_explanations": false
}
```

**Request Fields:**
- `features` (required): Dictionary of 89 numeric features
- `contract_address` (optional): Ethereum address
- `include_explanations` (optional): Include SHAP explanations

**Validation:**
- All feature values must be numeric (int/float)
- No NaN or Inf values allowed
- Feature names must match training set

**Response Schema:** `DirectPredictionResponse`

```json
{
  "prediction": "SAFE",
  "confidence": 0.98,
  "probabilities": {
    "safe": 0.98,
    "vulnerable": 0.02
  },
  "model_version": "v1.0.7",
  "model_type": "ensemble",
  "prediction_time_ms": 66,
  "timestamp": "2025-12-29T10:30:00.000Z",
  "contract_address": "0x1234...",
  "explanations": null
}
```

**Performance:**
- Average latency: **66ms**
- P95 latency: ~85ms
- P99 latency: ~120ms

**Use Cases:**
- ML researchers with custom feature extraction
- A/B testing different feature sets
- Batch processing with pre-computed features
- Integration with existing feature pipelines

**Rate Limit:** 20 requests per minute per IP

---

#### `GET /api/v1/models/info`

**Purpose:** Get model metadata and performance metrics

**Response:**
```json
{
  "model_version": "v1.0.7",
  "model_type": "ensemble",
  "performance_metrics": {
    "test_auc": 0.9978,
    "test_accuracy": 0.9832,
    "brier_score": 0.0146
  }
}
```

---

### 3. Report Generation Endpoints

#### `POST /api/v1/reports/generate`

**Purpose:** Generate comprehensive security audit reports using LLM

**Route Handler:** [reports.py:267](../src/chainguardian/api/routers/reports.py#L267)

**Request Schema:** `GenerateReportRequest`

```json
{
  "contract_code": "pragma solidity ^0.8.0;\ncontract Example { ... }",
  "contract_name": "VulnerableContract",
  "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
  "format": "markdown",
  "depth": "intermediate",
  "include_recommendations": true,
  "include_code_snippets": false,
  "llm_model": "llama3.1"
}
```

**Request Fields:**
- `contract_code` (required): Solidity source code
- `contract_name` (optional): Contract name
- `contract_address` (optional): Ethereum address
- `format`: Report format (pdf, html, markdown, json)
- `depth`: Technical depth (beginner, intermediate, advanced, expert)
- `include_recommendations`: Include security recommendations
- `include_code_snippets`: Include vulnerable code snippets
- `llm_model`: LLM model to use (llama3.1, mistral, codellama, phi3)

**Response Schema:** `ReportResponse`

```json
{
  "report_id": "rep_1735471800_1234",
  "content": "# Security Audit Report\n\n## Contract: VulnerableContract\n\n### Executive Summary\n...",
  "format": "markdown",
  "model_used": "llama3.1",
  "generation_time_ms": 2450,
  "token_count": {
    "input": 1200,
    "output": 850
  },
  "estimated_cost_usd": 0.0000012,
  "contract_name": "VulnerableContract",
  "contract_address": "0x1234...",
  "timestamp": "2025-12-29T10:30:00Z"
}
```

**Report Structure:**
1. **Executive Summary**: Overall assessment, risk level, key findings
2. **Contract Overview**: Basic information, technical specifications
3. **Vulnerability Analysis**: Detailed issue analysis with severity
4. **Risk Assessment**: Impact analysis, exploitation likelihood
5. **Recommendations**: Specific fixes, best practices, testing steps
6. **Technical Appendix**: Detailed explanations (depth-dependent)

**Processing Pipeline:**
1. Extract features from contract code
2. Run ML prediction
3. Build comprehensive prompt with:
   - Contract code (first 2000 chars)
   - ML analysis results
   - Extracted features
   - Detected vulnerabilities
4. Generate report via Ollama API
5. Track LLM metrics (tokens, latency, cost)

**Performance:**
- Average latency: **2450ms** (850ms features + 1600ms LLM generation)
- Token usage: ~1200 input + ~850 output
- Cost: $0.0000012 (local Ollama, effectively free)

**Technical Depth Levels:**

| Depth | Target Audience | Details |
|-------|----------------|---------|
| `beginner` | Non-technical stakeholders | Simple language, no code |
| `intermediate` | Developers | Some technical details |
| `advanced` | Security engineers | Full technical analysis |
| `expert` | Security researchers | Code snippets, deep analysis |

**Rate Limit:** 5 requests per minute per IP (resource-intensive)

---

#### `GET /api/v1/reports/formats`

**Purpose:** Get available report formats and models

**Response:**
```json
{
  "formats": ["pdf", "html", "markdown", "json"],
  "depths": ["beginner", "intermediate", "advanced", "expert"],
  "available_models": ["llama3.1", "mistral", "codellama", "phi3"],
  "example_request": { ... }
}
```

---

#### `GET /api/v1/reports/features-sample`

**Purpose:** Test feature extraction without LLM generation (debugging)

**Response:**
```json
{
  "success": true,
  "features": { ... },
  "feature_count": 89,
  "contract_name": "Sample",
  "sample_features": { ... },
  "feature_categories": {
    "vulnerability_flags": 15,
    "severity_counts": 8,
    "ast_features": 25,
    "graph_features": 30,
    "semantic_features": 11
  }
}
```

---

## Request & Response Schemas

### Request Schemas

All request schemas use Pydantic v2 for validation.

#### ContractAnalysisRequest

**Location:** [request.py:11](../src/chainguardian/api/schemas/request.py#L11)

**Validators:**
- `validate_solidity_code`: Checks for pragma/contract keywords, balanced braces, size limit (100KB)
- `validate_contract_name`: Ensures valid Solidity identifier format

**Validation Rules:**
```python
# Code validation
- Must contain 'pragma' or 'contract'
- Balanced braces { }
- Size limit: 100KB
- Min length: 10 characters

# Contract name validation
- Must be valid Solidity identifier
- Pattern: ^[a-zA-Z_][a-zA-Z0-9_]*$

# Address validation
- Must match Ethereum address format
- Pattern: ^0x[a-fA-F0-9]{40}$
```

---

#### DirectPredictionRequest

**Location:** [request.py:104](../src/chainguardian/api/schemas/request.py#L104)

**Validators:**
- `validate_features`: Ensures numeric values, no NaN/Inf

**Validation Rules:**
```python
# Features validation
- All values must be int or float
- No NaN or Infinity values
- Feature dictionary cannot be empty
```

---

#### GenerateReportRequest

**Location:** [reports.py:46](../src/chainguardian/api/routers/reports.py#L46)

**Fields:**
- `format`: Enum (pdf, html, markdown, json)
- `depth`: Enum (beginner, intermediate, advanced, expert)
- `llm_model`: String (default: "llama3.1")

---

### Response Schemas

#### ContractAnalysisResponse

**Location:** [response.py:31](../src/chainguardian/api/schemas/response.py#L31)

**Key Fields:**
- `is_safe` (bool): Overall safety verdict
- `risk_score` (float): 0.0 (safe) to 1.0 (maximum risk)
- `confidence` (float): Model confidence (0.0-1.0)
- `vulnerabilities` (list): Detected issues with severity
- `summary` (object): High-level metrics
- `extracted_features` (optional): Raw features if requested
- `explanations` (optional): SHAP explanations if requested

**Nested Types:**
- `VulnerabilitySummary`: type, severity, confidence, description
- `AnalysisSummary`: num_functions, external_calls, complexity, LOC

---

#### DirectPredictionResponse

**Location:** [response.py:132](../src/chainguardian/api/schemas/response.py#L132)

**Key Fields:**
- `prediction` (string): "SAFE" or "VULNERABLE"
- `confidence` (float): Model confidence
- `probabilities` (dict): Class probabilities
- `model_version` (string): Model version
- `model_type` (string): "ensemble" or "single"
- `prediction_time_ms` (int): Latency in milliseconds

---

#### ReportResponse

**Location:** [reports.py:105](../src/chainguardian/api/routers/reports.py#L105)

**Key Fields:**
- `report_id` (string): Unique report identifier
- `content` (string): Generated report content
- `format` (string): Report format used
- `model_used` (string): LLM model
- `generation_time_ms` (int): Total generation time
- `token_count` (dict): Input/output token counts
- `estimated_cost_usd` (float): Estimated cost

---

## Middleware

### 1. Request ID Middleware

**Location:** [main.py:68](../src/chainguardian/api/main.py#L68)

**Purpose:** Inject unique request ID for tracing

**Implementation:**
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

**Features:**
- UUID v4 generation
- Added to request state
- Included in response headers
- Used in structured logging
- Thread-safe via ContextVar

---

### 2. CORS Middleware

**Location:** [main.py:58](../src/chainguardian/api/main.py#L58)

**Configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: whitelist domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Recommendations:**
```python
# Production configuration
allow_origins=[
    "https://chainguardian.ai",
    "https://app.chainguardian.ai"
],
allow_methods=["GET", "POST"],
allow_headers=["Content-Type", "Authorization"],
```

---

### 3. Rate Limit Middleware

**Location:** [rate_limiter.py:54](../src/chainguardian/api/middleware/rate_limiter.py#L54)

**Purpose:** Distributed rate limiting using Redis token bucket algorithm

**Implementation Details:**

**Algorithm:**
```
1. Extract client IP from request
2. Skip rate limiting for private/internal IPs
3. Match request path to configured limits
4. Check Redis for current request count
5. If limit exceeded, return 429
6. Otherwise, increment counter and pass through
```

**Redis Key Format:**
```
rate_limit:<ip>:<path>
Example: rate_limit:192.168.1.100:/api/v1/analyze
```

**Token Bucket Implementation:**
```python
# First request in window
redis.setex(key, window_seconds, 1)

# Subsequent requests
redis.incr(key)  # Preserves TTL

# Check limit
current_count >= limit → 429 Too Many Requests
```

**Default Rate Limits:**
```python
{
    "/api/v1/analyze": {"limit": 10, "window": 60},
    "/api/v1/predict-from-features": {"limit": 20, "window": 60},
    "/api/v1/reports/generate": {"limit": 5, "window": 60},
    "/health": {"limit": 30, "window": 60},
    "/metrics": {"limit": 30, "window": 60}
}
```

**Response Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1735471860
Retry-After: 45
```

**Private Network Exemptions:**
- 10.0.0.0/8 (Docker networks)
- 172.16.0.0/12 (Docker networks)
- 192.168.0.0/16 (Private networks)
- 127.0.0.0/8 (Localhost)

**429 Response:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Limit is 10 per 60 seconds.",
  "retry_after": 45,
  "limits": { ... }
}
```

**Prometheus Metrics:**
```python
rate_limit_exceeded_total{endpoint="/api/v1/analyze", ip_address="1.2.3.4"}
```

**Configuration:**
```python
# Custom limits
custom_limits = {
    "/api/v1/custom": {"limit": 100, "window": 60}
}
setup_rate_limiting(app, redis_url="redis://redis:6379", limits=custom_limits)
```

---

### 4. Prometheus Instrumentation

**Location:** [main.py:135](../src/chainguardian/api/main.py#L135)

**Automatic Metrics:**
- `http_requests_total` - Total HTTP requests by method, status, endpoint
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Current in-flight requests

**Custom Metrics:**
See [Monitoring & Observability](#monitoring--observability) section

---

### 5. Global Exception Handler

**Location:** [main.py:138](../src/chainguardian/api/main.py#L138)

**Purpose:** Catch unhandled exceptions and return structured error responses

**Response Format:**
```json
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "support": "contact@chainguardian.ai"
}
```

**Features:**
- Structured error logging
- Request ID tracking
- Generic error message (no sensitive data leakage)
- Support contact information

---

## Dependencies & Model Loading

### Model Loader

**Location:** [model_loader.py:9](../src/chainguardian/api/dependencies/model_loader.py#L9)

**Purpose:** Singleton pattern for ML model loading

**Implementation:**
```python
_predictor: Optional[object] = None

def get_predictor():
    """Lazy loading with caching."""
    global _predictor
    if _predictor is None:
        _predictor = load_predictor()
    return _predictor

def load_predictor():
    """Load using PathResolver for environment-aware paths."""
    from chainguardian.ml.core.path_resolver import path_resolver
    from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2

    models_dir = path_resolver.models_dir
    predictor = EnhancedHybridPredictorV2(
        models_dir=str(models_dir),
        enable_shap=True,
        enable_monitoring=True
    )
    return predictor
```

**Key Features:**
- **Singleton Pattern**: Model loaded once at startup
- **Lazy Loading**: Only loaded when first request arrives
- **PathResolver Integration**: Works across Docker, Poetry, local environments
- **SHAP Enabled**: Supports explanation requests
- **Monitoring Enabled**: Tracks predictions and drift

**Dependency Injection:**
```python
@router.post("/api/v1/analyze")
async def analyze_contract(
    request: ContractAnalysisRequest,
    predictor: EnhancedHybridPredictorV2 = Depends(get_predictor)
):
    # predictor is injected automatically
    ml_result = predictor.predict_single(features=features)
```

**Benefits:**
- Memory efficient (single model instance)
- Fast requests (no model reloading)
- Testable (can mock dependency)
- Clean separation of concerns

---

### Feature Pipeline

**Location:** [predict.py:34](../src/chainguardian/api/routers/predict.py#L34)

**Purpose:** Cached feature extraction pipeline

**Implementation:**
```python
@lru_cache()
def get_pipeline() -> FeaturePipeline:
    """Get feature extraction pipeline (cached)."""
    print("🔄 Loading feature extraction pipeline...")
    pipeline = FeaturePipeline()
    print("✅ Pipeline loaded")
    return pipeline
```

**Usage:**
```python
pipeline = get_pipeline()
features = pipeline.analyze_contract(
    contract_path=temp_path,
    contract_name=contract_name,
    metadata={"address": request.contract_address}
)
```

**Features Extracted:** 89 features across categories:
- **AST Features**: Functions, LOC, complexity
- **Graph Features**: CFG, call graph, data flow
- **Semantic Features**: Reentrancy, CEI violations
- **Vulnerability Flags**: has_reentrancy, has_unchecked_call
- **Severity Counts**: high_severity_count, medium_severity_count

---

### Ollama Client

**Location:** [reports.py:224](../src/chainguardian/api/routers/reports.py#L224)

**Purpose:** Async HTTP client for Ollama LLM API

**Implementation:**
```python
class OllamaClient:
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, model: str, prompt: str, system: Optional[str] = None):
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 4000
            }
        }

        if system:
            payload["system"] = system

        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        return response.json()
```

**Supported Models:**
- `llama3.1` - General purpose (default)
- `mistral` - Fast, accurate
- `codellama` - Code-focused
- `phi3` - Lightweight

**Generation Parameters:**
- `temperature: 0.3` - Low randomness for consistent reports
- `top_p: 0.9` - Nucleus sampling
- `num_predict: 4000` - Max output tokens

**Dependency Injection:**
```python
async def get_ollama_client() -> OllamaClient:
    return OllamaClient()

@router.post("/reports/generate")
async def generate_report(
    request: GenerateReportRequest,
    ollama: OllamaClient = Depends(get_ollama_client)
):
    llm_response = await ollama.generate(
        model=request.llm_model,
        prompt=user_prompt,
        system=system_prompt
    )
```

---

## Monitoring & Observability

### Structured Logging

**Configuration:** [main.py:21](../src/chainguardian/api/main.py#L21)

**Format:** JSON structured logs via `python-json-logger`

**Example Log Entry:**
```json
{
  "timestamp": "2025-12-29T10:30:00.123Z",
  "level": "INFO",
  "logger": "chainguardian",
  "message": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "url": "/api/v1/analyze",
  "status_code": 200,
  "duration_ms": 916
}
```

**Log Levels:**
- `INFO`: Request start/completion, model loading
- `WARNING`: Rate limit warnings, feature extraction issues
- `ERROR`: Unhandled exceptions, model errors

**Log Fields:**
- `request_id`: Unique request identifier
- `method`: HTTP method
- `url`: Request URL
- `client`: Client IP address
- `status_code`: HTTP status
- `duration_ms`: Request duration
- `error_type`: Exception type (on errors)
- `error_message`: Exception message

---

### Prometheus Metrics

**Metrics Location:** `chainguardian.monitoring.metrics`

#### Prediction Metrics

**predictions_total**
```python
predictions_total = Counter(
    'predictions_total',
    'Total predictions made',
    ['endpoint', 'model_version', 'status']
)
```

**Usage:**
```python
predictions_total.labels(
    endpoint="/analyze",
    model_version="v1.0.7",
    status="success"
).inc()
```

---

**prediction_latency_seconds**
```python
prediction_latency = Histogram(
    'prediction_latency_seconds',
    'Time spent on ML prediction',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0]
)
```

**Usage:**
```python
prediction_latency.observe(prediction_time_ms / 1000)
```

---

**feature_extraction_latency**
```python
feature_extraction_latency = Histogram(
    'feature_extraction_latency_seconds',
    'Time spent extracting features'
)
```

---

**model_confidence**
```python
model_confidence = Histogram(
    'model_confidence',
    'Model confidence scores',
    ['prediction_class'],
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
)
```

**Usage:**
```python
model_confidence.labels(
    prediction_class="vulnerable"
).observe(confidence)
```

---

**vulnerabilities_detected**
```python
vulnerabilities_detected = Counter(
    'vulnerabilities_detected_total',
    'Total vulnerabilities detected',
    ['vulnerability_type', 'severity']
)
```

---

**active_predictions**
```python
active_predictions = Gauge(
    'active_predictions',
    'Number of predictions currently being processed'
)
```

**Usage:**
```python
active_predictions.inc()  # At start
# ... processing ...
active_predictions.dec()  # At end (in finally block)
```

---

#### LLM Metrics

**llm_requests_total**
```python
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API requests',
    ['model', 'endpoint', 'status']
)
```

---

**llm_tokens_total**
```python
llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total tokens processed',
    ['model', 'direction']  # direction: input/output
)
```

---

**llm_latency_seconds**
```python
llm_latency_seconds = Histogram(
    'llm_latency_seconds',
    'LLM request latency',
    ['model']
)
```

---

**llm_cost_estimated**
```python
llm_cost_estimated = Gauge(
    'llm_cost_estimated_usd',
    'Estimated LLM cost in USD',
    ['model', 'provider']
)
```

---

**rate_limit_exceeded_total**
```python
rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Number of rate limit violations',
    ['endpoint', 'ip_address']
)
```

---

### Grafana Dashboards

**Recommended Panels:**

1. **Request Rate**: `rate(http_requests_total[5m])`
2. **Error Rate**: `rate(http_requests_total{status_code=~"5.."}[5m])`
3. **Prediction Latency**: `histogram_quantile(0.95, prediction_latency_seconds)`
4. **Model Confidence**: `avg(model_confidence)`
5. **Active Predictions**: `active_predictions`
6. **LLM Token Usage**: `rate(llm_tokens_total[1h])`
7. **Rate Limit Violations**: `rate(rate_limit_exceeded_total[5m])`

---

### Complete Monitoring Reference

For comprehensive monitoring documentation including:

- Complete metrics reference with all 15+ metrics
- PromQL query examples
- Alerting rules and thresholds
- Cost tracking and optimization
- Performance analysis queries
- Grafana dashboard templates
- Best practices and troubleshooting

**See:** [Monitoring Technical Documentation](monitoring_technical_documentation.md)

**Key Monitoring Features:**

1. **Prediction Metrics**: Track all predictions with latency, confidence, and success rates
2. **Vulnerability Detection**: Monitor detected vulnerabilities by type and severity
3. **Feature Extraction**: Track feature extraction performance and errors
4. **LLM Usage**: Monitor token usage, costs, and LLM request latency
5. **Rate Limiting**: Track violations and identify abusive IPs
6. **Model Performance**: Monitor model version, confidence distribution, and drift

**Quick Metrics Overview:**

| Metric | Type | Purpose | Alert Threshold |
| ------ | ---- | ------- | --------------- |
| `predictions_total` | Counter | Total predictions | Error rate > 5% |
| `prediction_latency_seconds` | Histogram | Prediction time | P95 > 2.0s |
| `model_confidence_score` | Histogram | Confidence dist. | <0.7 for >10% |
| `active_predictions` | Gauge | Concurrent requests | > 100 |
| `vulnerabilities_detected_total` | Counter | Vulnerabilities found | Critical > 0.1/s |
| `llm_requests_total` | Counter | LLM API calls | Failure rate > 10% |
| `llm_tokens_total` | Counter | Token usage | Daily > budget |
| `llm_cost_estimated` | Gauge | Estimated cost | Daily > $10 |
| `rate_limit_exceeded_total` | Counter | Rate limit hits | > 1.0/s |

---

## Deployment

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Expose port
EXPOSE 8000

# Run application
CMD ["poetry", "run", "uvicorn", "chainguardian.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**Docker Compose:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - redis
      - ollama
    volumes:
      - ./config:/app/config

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"

volumes:
  ollama-data:
```

---

### Kubernetes Deployment

**Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chainguardian-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chainguardian-api
  template:
    metadata:
      labels:
        app: chainguardian-api
    spec:
      containers:
      - name: api
        image: chainguardian/api:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

---

**Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: chainguardian-api
spec:
  selector:
    app: chainguardian-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

**Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chainguardian-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chainguardian-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

### Environment Variables

```bash
# Redis
REDIS_URL=redis://redis:6379/0

# Ollama
OLLAMA_URL=http://ollama:11434

# Monitoring
ENABLE_METRICS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS (production)
ALLOWED_ORIGINS=https://chainguardian.ai,https://app.chainguardian.ai

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

---

## API Usage Examples

### Example 1: Analyze Smart Contract

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "contract_code": "pragma solidity ^0.8.0;\n\ncontract VulnerableBank {\n    mapping(address => uint256) public balances;\n    \n    function withdraw() public {\n        uint256 amount = balances[msg.sender];\n        (bool success, ) = msg.sender.call{value: amount}(\"\");\n        require(success, \"Transfer failed\");\n        balances[msg.sender] = 0;\n    }\n}",
    "contract_name": "VulnerableBank",
    "include_explanations": true
  }'
```

**Response:**
```json
{
  "is_safe": false,
  "risk_score": 0.92,
  "confidence": 0.92,
  "vulnerabilities": [
    {
      "type": "reentrancy",
      "severity": "high",
      "confidence": 0.95,
      "description": "Reentrancy vulnerability: external call before state update"
    }
  ],
  "summary": {
    "num_functions": 1,
    "num_external_calls": 1,
    "cyclomatic_complexity": 2.0,
    "lines_of_code": 9,
    "has_critical_issues": true,
    "complexity_rating": "low"
  },
  "total_time_ms": 950
}
```

---

### Example 2: Direct Prediction

```python
import requests

features = {
    "num_functions": 15,
    "max_cyclomatic_complexity": 8.5,
    "cei_violations": 2,
    "has_reentrancy": 1,
    "num_external_calls": 5
}

response = requests.post(
    "http://localhost:8000/api/v1/predict-from-features",
    json={
        "features": features,
        "include_explanations": False
    }
)

result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']:.2%}")
```

---

### Example 3: Generate Security Report

```python
import requests

contract_code = """
pragma solidity ^0.8.0;

contract TokenSale {
    uint256 public price = 1 ether;

    function buyTokens() public payable {
        require(msg.value >= price, "Insufficient payment");
        // Missing: refund excess payment
        // Missing: transfer tokens
    }
}
"""

response = requests.post(
    "http://localhost:8000/api/v1/reports/generate",
    json={
        "contract_code": contract_code,
        "contract_name": "TokenSale",
        "format": "markdown",
        "depth": "intermediate",
        "include_recommendations": True,
        "llm_model": "llama3.1"
    }
)

report = response.json()
print(report['content'])
```

---

### Example 4: Error Handling

```python
import requests

try:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze",
        json={"contract_code": "invalid code"},
        timeout=30
    )
    response.raise_for_status()
    result = response.json()

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print(f"Validation error: {e.response.json()}")
    elif e.response.status_code == 429:
        retry_after = e.response.headers.get('Retry-After')
        print(f"Rate limited. Retry after {retry_after} seconds")
    elif e.response.status_code == 500:
        print(f"Server error: {e.response.json()}")

except requests.exceptions.Timeout:
    print("Request timed out")
```

---

### Example 5: Integration with ML Core

```python
# Server-side integration example
from chainguardian.api.dependencies.model_loader import get_predictor
from chainguardian.feature_extraction.pipeline import FeaturePipeline

# Load components
predictor = get_predictor()
pipeline = FeaturePipeline()

# Extract features
features = pipeline.analyze_contract(
    contract_path="contracts/Example.sol",
    contract_name="Example"
)

# Predict
result = predictor.predict_single(
    features=features,
    return_details=True,
    explain=True
)

print(f"Prediction: {result['prediction_label']}")
print(f"Confidence: {result['calibrated_confidence']:.2%}")
print(f"Reasons: {result['semantic_reasons']}")
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Causes |
|------|---------|--------|
| 200 | Success | Request processed successfully |
| 400 | Bad Request | Invalid input, validation failure, feature extraction error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unhandled exception, model error |
| 502 | Bad Gateway | Ollama API unavailable |

---

### Error Response Format

All errors follow this structure:

```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": { ... }
}
```

---

### Common Errors

#### 1. Invalid Contract Code (400)

```json
{
  "error": "validation_error",
  "message": "Invalid Solidity code: must contain 'pragma' or 'contract' keyword",
  "request_id": "..."
}
```

**Solution:** Ensure code contains valid Solidity syntax

---

#### 2. Feature Extraction Failed (400)

```json
{
  "error": "feature_extraction_error",
  "message": "Feature extraction failed: Syntax error at line 5",
  "request_id": "..."
}
```

**Solution:** Check contract syntax, ensure all dependencies are available

---

#### 3. Rate Limit Exceeded (429)

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Limit is 10 per 60 seconds.",
  "retry_after": 45,
  "limits": { ... }
}
```

**Headers:**
```
Retry-After: 45
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1735471860
```

**Solution:** Wait for `Retry-After` seconds or implement exponential backoff

---

#### 4. LLM Generation Failed (500)

```json
{
  "error": "llm_error",
  "message": "LLM generation failed: Connection timeout",
  "request_id": "..."
}
```

**Solution:** Check Ollama service availability, retry request

---

#### 5. Model Loading Error (500)

```json
{
  "error": "model_error",
  "message": "Failed to load model: Model file not found",
  "request_id": "..."
}
```

**Solution:** Ensure model files exist at `config/models/`, check PathResolver configuration

---

### Retry Logic

**Recommended Strategy:**

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Usage
response = requests_retry_session().post(
    "http://localhost:8000/api/v1/analyze",
    json={"contract_code": code}
)
```

---

## Integration with ML Core

The API module integrates closely with the [ML Core module](ml_core_technical_documentation.md):

### Component Integration

| API Component | ML Core Component | Purpose |
|--------------|------------------|---------|
| `model_loader.py` | `ModelRegistry` | Load versioned models |
| `predict.py` | `EnhancedHybridPredictorV2` | Make predictions |
| `predict.py` | `FeaturePipeline` | Extract features |
| `main.py` | `MLMonitor` | Track predictions and drift |
| `model_loader.py` | `PathResolver` | Resolve model paths |

### Data Flow

```
API Request
    ↓
[API Layer] predict.py
    ↓
[Feature Extraction] FeaturePipeline
    ↓
[ML Core] EnhancedHybridPredictorV2
    ├─ HeterogeneousEnsemble
    ├─ ModelRegistry
    └─ MLMonitor
    ↓
[API Layer] Response formatting
    ↓
API Response
```

---

## Performance Tuning

### Optimization Tips

1. **Feature Extraction Parallelization:**
```python
# Process multiple contracts in parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(pipeline.analyze_contract, path)
               for path in contract_paths]
    features = [f.result() for f in futures]
```

2. **Model Loading Optimization:**
```python
# Preload model at startup instead of lazy loading
@app.on_event("startup")
async def startup_event():
    get_predictor()  # Force model loading
```

3. **Redis Connection Pooling:**
```python
redis_pool = redis.ConnectionPool.from_url(
    redis_url,
    max_connections=50,
    decode_responses=True
)
redis_client = redis.Redis(connection_pool=redis_pool)
```

4. **Async Feature Extraction:**
```python
# Run feature extraction in thread pool
from fastapi.concurrency import run_in_threadpool

features = await run_in_threadpool(
    pipeline.analyze_contract,
    contract_path=temp_path
)
```

---

## Security Considerations

### Input Validation

- All inputs validated via Pydantic schemas
- Contract code size limited to 100KB
- Ethereum address format validation
- Feature value range checks

### Rate Limiting

- Distributed rate limiting via Redis
- Per-IP and per-endpoint limits
- Automatic exemption for private networks

### Error Handling

- No sensitive data in error messages
- Generic 500 errors for internal failures
- Request ID tracking for debugging

### CORS Configuration

- Whitelist specific origins in production
- Restrict allowed methods and headers

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [ML Core Documentation](ml_core_technical_documentation.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-29
**Maintainer:** ChainGuardian AI Team
