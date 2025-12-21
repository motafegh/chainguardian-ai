# ChainGuardian API Specification v1.0

**Author:** Ali  
**Date:** December 21, 2024  
**Status:** Design Phase (Week 3, Day 1)

## Overview
REST API for smart contract vulnerability analysis using ML model + semantic analysis.

---

## Base Configuration

Development: http://localhost:8000/api/v1
Production: TBD (Week 5)

text

**Authentication:** None (Week 3), API Key (Week 5)  
**Rate Limiting:** None (Week 3), 100 req/hour (Week 5)  
**Timeout:** 30 seconds per request

---

## Endpoints

### 1. POST /api/v1/analyze

Analyze Solidity contract for vulnerabilities.

**Request Body:**
{
"code": "contract SimpleStorage { uint256 value; }",
"include_features": false
}



**Request Validation:**
- `code`: Required, string, 10-50000 characters
- `include_features`: Optional, boolean, default false

**Success Response (200):**
{
"prediction": "VULNERABLE",
"confidence": 0.87,
"risk_score": 0.82,
"cei_violations": 3,
"timestamp": "2024-12-21T14:30:00Z",
"model_version": "1.0",
"features": null
}



**Error Responses:**

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | ERR_001 | Invalid Solidity syntax |
| 400 | ERR_002 | Code exceeds 50KB limit |
| 422 | ERR_004 | Slither analysis failed |
| 500 | ERR_103 | Model prediction failed |
| 504 | ERR_105 | Request timeout (>30s) |

---

### 2. GET /api/v1/health

Service health check.

**Success Response (200):**
{
"status": "healthy",
"model_version": "1.0",
"model_loaded": true,
"database_connected": true,
"uptime_seconds": 3600
}

text

**Error Response (503):**
{
"status": "unhealthy",
"model_loaded": false,
"database_connected": false,
"error": "Model file not found"
}

text

---

## Example Usage

### cURL
Analyze contract
curl -X POST http://localhost:8000/api/v1/analyze
-H "Content-Type: application/json"
-d '{"code": "contract Test { function withdraw() external { msg.sender.call{value: 1 ether}(""); } }"}'

Health check
curl http://localhost:8000/api/v1/health

text

### Python
import requests

Analyze
response = requests.post(
"http://localhost:8000/api/v1/analyze",
json={"code": "contract Safe { uint256 value; }"}
)
print(response.json())

Health check
health = requests.get("http://localhost:8000/api/v1/health")
print(health.json())

text

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response time (p95) | <10s | Prometheus histogram |
| Throughput | 100 req/hour | Request counter |
| Uptime | >99% | Health check monitoring |
| Error rate | <5% | 5xx response ratio |

---

## Compatibility with Existing Code

**Reused Components:**
- `src/chainguardian/feature_extraction/pipeline.py` → Feature extraction
- `src/chainguardian/ml/models/hybrid_predictor.py` → ML predictions
- `src/chainguardian/database/manager.py` → Database access
- `models/saved_models/hybrid_xgboost_v1.pkl` → Trained model

**No Breaking Changes:** API wraps existing code, CLI scripts still work.

