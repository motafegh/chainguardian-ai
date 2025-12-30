# ChainGuardian AI - Technical Documentation Index

**Version:** 1.0.0
**Last Updated:** 2025-12-29
**Project:** ChainGuardian AI - ML-Powered Smart Contract Vulnerability Detection

---

## Documentation Overview

This documentation suite provides comprehensive technical reference for the ChainGuardian AI system, covering ML pipelines, API services, and observability infrastructure.

### Available Documentation

| Document | Module | Description | Key Topics |
| -------- | ------ | ----------- | ---------- |
| [ML Core](ml_core_technical_documentation.md) | `chainguardian.ml.core` | Machine learning pipeline and model management | Ensemble learning, hyperparameter tuning, model registry, monitoring |
| [Hybrid Predictor](hybrid_predictor_technical_documentation.md) | `chainguardian.ml.models` | Core inference engine with hybrid ML+semantic scoring | Prediction pipeline, confidence calibration, SHAP explanations, batch processing |
| [API](api_technical_documentation.md) | `chainguardian.api` | REST API service and endpoints | FastAPI, prediction endpoints, LLM reports, rate limiting |
| [Monitoring](monitoring_technical_documentation.md) | `chainguardian.monitoring` | Observability and metrics | Prometheus metrics, alerting, cost tracking, dashboards |
| [Configuration Guide](configuration_guide.md) | `config/` | Complete configuration reference | YAML config, model registry, Prometheus rules, Grafana dashboards |

---

## Quick Start Guide

### For Developers

**1. Understanding the ML Pipeline:**
- Start with [ML Core Documentation](ml_core_technical_documentation.md)
- Learn about the ensemble model architecture
- Understand feature extraction and prediction flow

**2. Building API Integrations:**
- Read [API Documentation](api_technical_documentation.md)
- Review endpoint specifications and request/response schemas
- Implement error handling and retry logic

**3. Setting Up Monitoring:**
- Check [Monitoring Documentation](monitoring_technical_documentation.md)
- Configure Prometheus metrics collection
- Set up Grafana dashboards and alerts

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ChainGuardian AI System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   API Layer (FastAPI)                     │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │  Endpoints                                       │    │  │
│  │  │  • POST /api/v1/analyze                         │    │  │
│  │  │  • POST /api/v1/predict-from-features           │    │  │
│  │  │  • POST /api/v1/reports/generate                │    │  │
│  │  │  • GET  /health                                 │    │  │
│  │  │  • GET  /metrics                                │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  │                                                           │  │
│  │  Middleware: Rate Limiting | CORS | Request Tracing      │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼──────────────────────────────────────┐  │
│  │              ML Core Layer                               │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │  Components                                      │    │  │
│  │  │  • ConfigManager        - Configuration          │    │  │
│  │  │  • PathResolver         - Path management        │    │  │
│  │  │  • HyperparameterTuner - Optuna optimization    │    │  │
│  │  │  • HeterogeneousEnsemble - Multi-model ensemble  │    │  │
│  │  │  • SmartContractAugmenter - Data augmentation   │    │  │
│  │  │  • ModelRegistry        - Version control       │    │  │
│  │  │  • MLMonitor            - Performance tracking  │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └────────────────────┬──────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼──────────────────────────────────────┐  │
│  │           Monitoring Layer (Prometheus)                  │  │
│  │  • Prediction metrics    • LLM usage tracking            │  │
│  │  • Model confidence      • Rate limiting metrics         │  │
│  │  • Feature extraction    • Cost estimation               │  │
│  │  • Vulnerability detection                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Integration Map

### ML Core ↔ API Integration

| ML Core Component | API Usage | Purpose |
| ----------------- | --------- | ------- |
| `EnhancedHybridPredictorV2` | `predict.py` | Make vulnerability predictions |
| `FeaturePipeline` | `predict.py`, `reports.py` | Extract features from contracts |
| `ModelRegistry` | `model_loader.py` | Load versioned models |
| `PathResolver` | `model_loader.py` | Resolve model file paths |
| `MLMonitor` | All endpoints | Track predictions and drift |

### API ↔ Monitoring Integration

| API Component | Monitoring Metrics | Purpose |
| ------------- | ------------------ | ------- |
| `predict.py` | `predictions_total`, `prediction_latency`, `model_confidence` | Track prediction performance |
| `reports.py` | `llm_requests_total`, `llm_tokens_total`, `llm_cost_estimated` | Monitor LLM usage and costs |
| `rate_limiter.py` | `rate_limit_exceeded_total` | Track rate limit violations |
| `main.py` | `http_requests_total`, `http_request_duration_seconds` | HTTP metrics via Instrumentator |

### ML Core ↔ Monitoring Integration

| ML Core Component | Monitoring Integration | Purpose |
| ----------------- | ---------------------- | ------- |
| `HeterogeneousEnsemble` | `model_confidence`, `predictions_total` | Track ensemble predictions |
| `FeaturePipeline` | `feature_extraction_latency`, `feature_extraction_errors` | Monitor feature extraction |
| `ModelRegistry` | `model_version_info` | Track deployed model versions |
| `MLMonitor` | Complements Prometheus metrics | Drift detection and performance baselines |

---

## Key Features by Module

### ML Core Features

- **Hyperparameter Optimization**: Bayesian optimization with Optuna (TPE sampler)
- **Ensemble Learning**: Multi-algorithm ensemble (XGBoost, RF, LightGBM, LogReg)
- **Probability Calibration**: Platt scaling for improved confidence estimates
- **Data Augmentation**: SMOTE, Mixup, Gaussian noise strategies
- **Model Versioning**: Semantic versioning with rollback capabilities
- **Drift Detection**: Statistical drift detection (KS test) with alerting
- **Path Management**: Environment-aware absolute path resolution

**Performance:**
- Test AUC: **99.78%**
- Prediction Latency: **66ms** (ensemble inference)
- Feature Count: **89** (AST + Graph + Semantic)

### API Features

- **RESTful Endpoints**: FastAPI with automatic OpenAPI docs
- **Contract Analysis**: Full pipeline from code to prediction
- **Direct Prediction**: Skip feature extraction for pre-computed features
- **LLM Report Generation**: Automated security audit reports via Ollama
- **Rate Limiting**: Redis-backed distributed token bucket
- **Request Tracing**: UUID-based request tracking across services
- **CORS Support**: Configurable cross-origin resource sharing
- **Health Checks**: Kubernetes-compatible liveness/readiness probes

**Performance:**
- Average Latency: **916ms** (850ms features + 66ms prediction)
- P95 Latency: **~1.2s**
- Rate Limits: 10 req/min (analyze), 20 req/min (predict), 5 req/min (reports)

### Monitoring Features

- **15+ Custom Metrics**: Predictions, vulnerabilities, LLM usage, rate limits
- **Prometheus Native**: Standard exposition format with histogram buckets
- **Multi-Dimensional Labels**: Rich filtering by endpoint, model, status, severity
- **Cost Tracking**: Real-time LLM cost estimation and budgeting
- **Alerting Rules**: Pre-configured alerts for errors, latency, and drift
- **Grafana Dashboards**: Ready-to-import dashboard templates
- **Performance KPIs**: Success rate, latency percentiles, confidence distribution

---

## Common Workflows

### 1. Deploy New Model Version

**Steps:**

1. **Train Model** (ML Core)
   ```python
   from chainguardian.ml.core import HyperparameterTuner, HeterogeneousEnsemble

   tuner = HyperparameterTuner(config, feature_names)
   results = tuner.optimize(X_train, y_train, n_trials=100)

   ensemble = HeterogeneousEnsemble(config, feature_names)
   ensemble.fit(X_train, y_train)
   ```

2. **Register Model** (ML Core)
   ```python
   from chainguardian.ml.core import ModelRegistry

   registry = ModelRegistry()
   version = registry.register_model(model_info, description="New ensemble")
   ```

3. **Update Monitoring** (Monitoring)
   ```python
   from chainguardian.monitoring.metrics import set_model_info

   set_model_info(version="v1.0.8", auc_score=0.9985, trained_date="2025-12-29")
   ```

4. **Deploy & Verify** (API)
   - Restart API service
   - Check `/api/v1/models/info` endpoint
   - Monitor `model_version_info` metric

---

### 2. Analyze Smart Contract

**Steps:**

1. **Send Request** (API)
   ```bash
   curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"contract_code": "...", "contract_name": "VulnerableBank"}'
   ```

2. **Feature Extraction** (ML Core → API)
   - Pipeline extracts 89 features
   - Tracked via `feature_extraction_latency` metric

3. **Prediction** (ML Core)
   - Ensemble makes prediction
   - Confidence calibrated via Platt scaling
   - Tracked via `predictions_total`, `model_confidence`

4. **Monitor Results** (Monitoring)
   ```promql
   # Check prediction latency
   histogram_quantile(0.95, rate(chainguardian_prediction_latency_seconds_bucket[5m]))

   # Check confidence
   avg(chainguardian_model_confidence_score)
   ```

---

### 3. Generate Security Report

**Steps:**

1. **Send Request** (API)
   ```bash
   curl -X POST http://localhost:8000/api/v1/reports/generate \
     -d '{"contract_code": "...", "format": "markdown", "depth": "intermediate"}'
   ```

2. **Feature Extraction & Prediction** (ML Core → API)
   - Extract features
   - Run ML prediction
   - Detect vulnerabilities

3. **LLM Report Generation** (API → Ollama)
   - Build detailed prompt
   - Call Ollama API
   - Generate human-readable report
   - Tracked via `llm_requests_total`, `llm_tokens_total`, `llm_cost_estimated`

4. **Monitor Costs** (Monitoring)
   ```promql
   # Daily cost estimate
   sum(chainguardian_llm_cost_estimated) * 86400 / 15

   # Token usage
   sum(rate(chainguardian_llm_tokens_total[1h])) by (direction)
   ```

---

### 4. Monitor System Health

**Steps:**

1. **Check Prometheus Metrics** (Monitoring)
   ```bash
   curl http://localhost:8000/metrics | grep chainguardian
   ```

2. **View Grafana Dashboards** (Monitoring)
   - Navigate to http://localhost:3000
   - Import dashboard templates
   - Monitor KPIs in real-time

3. **Review Alerts** (Monitoring)
   - Check Alertmanager for active alerts
   - Review alert history
   - Investigate anomalies

4. **Analyze Performance** (ML Core)
   ```python
   from chainguardian.ml.core import MLMonitor

   monitor = MLMonitor(config)
   report = monitor.get_performance_report(window_size=1000)
   print(f"Drift detected: {report['drift_detected']}")
   print(f"Accuracy: {report['accuracy']:.2%}")
   ```

---

## Performance Benchmarks

### Latency Breakdown

| Component | P50 | P95 | P99 |
| --------- | --- | --- | --- |
| Feature Extraction | 650ms | 850ms | 1200ms |
| ML Prediction | 50ms | 66ms | 85ms |
| Total (Analyze) | 700ms | 916ms | 1285ms |
| LLM Report | 1800ms | 2450ms | 3500ms |

### Throughput

| Endpoint | Requests/sec | Concurrent Users |
| -------- | ------------ | ---------------- |
| `/analyze` | ~10-15 | 50-100 |
| `/predict-from-features` | ~40-50 | 100-200 |
| `/reports/generate` | ~2-3 | 10-20 |

### Resource Usage

| Component | CPU | Memory | GPU |
| --------- | --- | ------ | --- |
| API Service | 1-2 cores | 2-4 GB | N/A |
| ML Inference | 2-4 cores | 4-8 GB | Optional |
| Ollama (LLM) | 4-8 cores | 8-16 GB | Recommended |

---

## Development Guidelines

### Code Organization

```
src/chainguardian/
├── ml/
│   └── core/                    # ML Core module
│       ├── config_manager.py    # Configuration management
│       ├── path_resolver.py     # Path resolution
│       ├── hyperparameter_tuner.py
│       ├── heterogeneous_ensemble.py
│       ├── data_augmenter.py
│       ├── model_registry.py
│       └── monitoring.py        # ML-specific monitoring
├── api/                         # API module
│   ├── main.py                  # FastAPI app
│   ├── routers/
│   │   ├── health.py
│   │   ├── predict.py
│   │   └── reports.py
│   ├── schemas/
│   │   ├── request.py
│   │   └── response.py
│   ├── middleware/
│   │   └── rate_limiter.py
│   └── dependencies/
│       └── model_loader.py
└── monitoring/                  # Monitoring module
    ├── metrics.py               # Core metrics
    └── llm_metrics.py           # LLM-specific metrics
```

### Testing Strategy

**Unit Tests:**
- ML Core: Test each component independently
- API: Test endpoints with mocked dependencies
- Monitoring: Test metric recording and aggregation

**Integration Tests:**
- End-to-end prediction flow
- Model registry operations
- API + ML Core integration

**Performance Tests:**
- Load testing with locust/k6
- Latency profiling
- Memory leak detection

---

## Troubleshooting Guide

### Common Issues

| Issue | Module | Solution | Documentation |
| ----- | ------ | -------- | ------------- |
| Model not loading | ML Core | Check PathResolver configuration | [ML Core](ml_core_technical_documentation.md#pathresolver) |
| High latency | API | Profile feature extraction | [API](api_technical_documentation.md#performance-tuning) |
| Rate limit errors | API | Adjust Redis configuration | [API](api_technical_documentation.md#rate-limit-middleware) |
| Metrics missing | Monitoring | Check Prometheus scrape config | [Monitoring](monitoring_technical_documentation.md#troubleshooting) |
| LLM errors | API | Verify Ollama service | [API](api_technical_documentation.md#ollama-client) |
| Drift detected | ML Core | Review data distribution changes | [ML Core](ml_core_technical_documentation.md#mlmonitor) |

### Debug Commands

```bash
# Check API health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics

# Test model loading
python -c "from chainguardian.ml.core import ModelRegistry; print(ModelRegistry().list_models())"

# Check feature extraction
curl -X GET http://localhost:8000/api/v1/reports/features-sample

# View Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Redis connection
redis-cli -h localhost -p 6379 ping
```

---

## Contributing

### Adding New Features

1. **Update ML Core** if adding model functionality
2. **Update API** if adding new endpoints
3. **Update Monitoring** if adding new metrics
4. **Update Documentation** for all changes

### Documentation Standards

- Use markdown formatting
- Include code examples
- Add cross-references between docs
- Update version numbers
- Include performance benchmarks

---

## Additional Resources

### External Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Optuna Documentation](https://optuna.readthedocs.io/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)

### Internal Resources

- Model training notebooks: `notebooks/training/`
- Configuration files: `config/`
- Docker compose: `docker-compose.yml`
- Kubernetes manifests: `k8s/`

---

## Version History

| Version | Date | Changes | Author |
| ------- | ---- | ------- | ------ |
| 1.0.0 | 2025-12-29 | Initial documentation release | ChainGuardian AI Team |

---

**Maintained by:** ChainGuardian AI Team
**Contact:** contact@chainguardian.ai
**Repository:** https://github.com/chainguardian/chainguardian-ai
