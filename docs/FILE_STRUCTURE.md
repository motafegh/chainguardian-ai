# 📁 CHAINGUARDIAN AI - FILE STRUCTURE GUIDE

## Quick Navigation
```
src/chainguardian/
├── api/                    # FastAPI application
│   ├── main.py            # App entrypoint (235 lines)
│   ├── routers/           # API endpoints
│   │   ├── predict.py     # ML predictions (320 lines)
│   │   ├── health.py      # Health checks (85 lines)
│   │   └── models.py      # Model management (120 lines)
│   ├── schemas/           # Pydantic models
│   │   ├── request.py     # Request validation (180 lines)
│   │   └── response.py    # Response models (150 lines)
│   ├── dependencies/      # FastAPI dependencies
│   │   └── model_loader.py # Model caching (245 lines)
│   └── middleware/        # Custom middleware
│       └── rate_limiter.py # Rate limiting (180 lines)
│
├── feature_extraction/    # Feature extractors
│   ├── ast_analyzer.py    # AST features (19 dims)
│   ├── contract_analyzer.py # Slither features (39 dims)
│   ├── graph_extractor.py # Graph features (25 dims)
│   └── semantic_analyzer.py # Semantic features (6 dims)
│
├── ml/                    # ML components
│   └── core/
│       ├── heterogeneous_ensemble.py # Ensemble model
│       └── hybrid_predictor.py # ML + rules
│
└── database/              # Database layer
    └── models.py          # SQLAlchemy models
```

## File Purposes

### API Layer

| File | Purpose | Key Features |
|------|---------|--------------|
| `main.py` | FastAPI app | CORS, Prometheus, routers |
| `predict.py` | ML endpoints | Feature extraction, prediction |
| `health.py` | Health checks | Liveness, readiness probes |
| `models.py` | Model management | List models, metadata |
| `request.py` | Input validation | Pydantic schemas, validators |
| `response.py` | Output models | Standardized responses |
| `model_loader.py` | Model caching | Lazy loading, singleton |
| `rate_limiter.py` | Rate limiting | Token bucket, Redis-backed |

### Feature Extraction

| File | Features | Dimensions |
|------|----------|-----------|
| `ast_analyzer.py` | AST metrics | 19 |
| `contract_analyzer.py` | Slither integration | 39 |
| `graph_extractor.py` | NetworkX graphs | 25 |
| `semantic_analyzer.py` | CEI violations | 6 |
| **Total** | | **89** |

### Docker

| File | Purpose | Services |
|------|---------|----------|
| `docker-compose.yml` | Orchestration | 6 services |
| `Dockerfile` | API image | Multi-stage |
| `start.sh` | Startup script | Logging, health |

### Monitoring

| File | Purpose | Metrics |
|------|---------|---------|
| `prometheus.yml` | Scrape config | 15+ custom |
| `rules.yml` | Alert rules | 4 critical |
| `chainguardian-api.json` | Grafana dashboard | 5 panels |

## Most Important Files (Top 10)

1. **src/chainguardian/api/main.py** - Application entry
2. **src/chainguardian/api/routers/predict.py** - Core ML logic
3. **src/chainguardian/api/dependencies/model_loader.py** - Model management
4. **src/chainguardian/api/middleware/rate_limiter.py** - Rate limiting
5. **docker-compose.yml** - Service orchestration
6. **Dockerfile** - Container definition
7. **config/prometheus/prometheus.yml** - Metrics config
8. **config/prometheus/rules.yml** - Alert rules
9. **src/chainguardian/ml/core/hybrid_predictor.py** - ML + rules
10. **tests/integration/test_api_endpoints.py** - Integration tests

## Quick Commands

### View File
```bash
cat src/chainguardian/api/main.py
```

### Edit File
```bash
code src/chainguardian/api/routers/predict.py
```

### Find File
```bash
find . -name "*.py" | grep -i model
```

### File Stats
```bash
wc -l src/chainguardian/**/*.py
```

