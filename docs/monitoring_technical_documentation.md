# ChainGuardian AI - Monitoring Module Technical Documentation

**Version:** 1.0.0
**Last Updated:** 2025-12-29
**Module Path:** `src/chainguardian/monitoring`
**Related Documentation:**
- [API Technical Documentation](api_technical_documentation.md)
- [ML Core Technical Documentation](ml_core_technical_documentation.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Metrics Reference](#metrics-reference)
4. [Integration Guide](#integration-guide)
5. [Grafana Dashboards](#grafana-dashboards)
6. [Alerting Rules](#alerting-rules)
7. [Performance Monitoring](#performance-monitoring)
8. [Cost Tracking](#cost-tracking)
9. [Best Practices](#best-practices)

---

## Overview

The ChainGuardian AI Monitoring module provides comprehensive observability for the entire ML pipeline and API layer. It implements Prometheus metrics following industry best practices for metric naming, labeling, and aggregation.

### Key Features

- **Prometheus Native**: Industry-standard metrics format
- **Multi-Dimensional**: Rich labels for detailed filtering
- **Real-Time Monitoring**: Sub-second metric updates
- **Cost Tracking**: LLM usage and cost estimation
- **Performance Metrics**: Latency histograms with percentiles
- **Error Tracking**: Detailed error categorization
- **Resource Monitoring**: Active requests, memory usage

### Metrics Categories

1. **Prediction Metrics**: ML model predictions and performance
2. **Vulnerability Metrics**: Detected vulnerabilities by type and severity
3. **Feature Extraction Metrics**: Feature pipeline performance
4. **LLM Metrics**: Large Language Model usage and costs
5. **API Metrics**: HTTP requests, rate limiting
6. **Model Performance**: Version tracking and quality metrics

---

## Architecture

### Monitoring Stack

```
┌────────────────────────────────────────────────────────────┐
│              ChainGuardian Application                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │         API Layer (FastAPI)                      │    │
│  │  • Prediction endpoints                          │    │
│  │  • Report generation                             │    │
│  │  • Rate limiting                                 │    │
│  └───────┬──────────────────────────────────────────┘    │
│          │                                                │
│  ┌───────▼──────────────────────────────────────────┐    │
│  │      ML Core Layer                               │    │
│  │  • Feature extraction                            │    │
│  │  • Model inference                               │    │
│  │  • Ensemble predictions                          │    │
│  └───────┬──────────────────────────────────────────┘    │
│          │                                                │
│  ┌───────▼──────────────────────────────────────────┐    │
│  │      Monitoring Module                           │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │  metrics.py                              │   │    │
│  │  │  • predictions_total                     │   │    │
│  │  │  • prediction_latency                    │   │    │
│  │  │  • model_confidence                      │   │    │
│  │  │  • vulnerabilities_detected              │   │    │
│  │  │  • feature_extraction_latency            │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  │  ┌──────────────────────────────────────────┐   │    │
│  │  │  llm_metrics.py                          │   │    │
│  │  │  • llm_requests_total                    │   │    │
│  │  │  • llm_tokens_total                      │   │    │
│  │  │  • llm_latency_seconds                   │   │    │
│  │  │  • llm_cost_estimated                    │   │    │
│  │  │  • rate_limit_exceeded_total             │   │    │
│  │  └──────────────────────────────────────────┘   │    │
│  └───────┬──────────────────────────────────────────┘    │
│          │                                                │
└──────────┼────────────────────────────────────────────────┘
           │
           │ Expose /metrics endpoint
           ▼
    ┌──────────────────────────────────┐
    │      Prometheus Server           │
    │  • Scrape metrics every 15s      │
    │  • Store time-series data        │
    │  • Evaluate alerting rules       │
    └───────┬──────────────────────────┘
            │
            ▼
    ┌──────────────────────────────────┐
    │      Grafana Dashboards          │
    │  • Real-time visualization       │
    │  • Alerting & notifications      │
    │  • Historical analysis           │
    └──────────────────────────────────┘
```

### Data Flow

```
Application Event (e.g., prediction made)
    ↓
Metric Recording (Counter.inc(), Histogram.observe())
    ↓
Prometheus Client Library (local aggregation)
    ↓
/metrics Endpoint (HTTP text exposition format)
    ↓
Prometheus Server (scrape every 15s)
    ↓
Time-Series Database (PromQL queryable)
    ↓
Grafana Dashboard (visualization)
```

---

## Metrics Reference

### Prediction Metrics

#### `chainguardian_predictions_total`

**Type:** Counter
**Location:** [metrics.py:22](../src/chainguardian/monitoring/metrics.py#L22)
**Description:** Total number of vulnerability predictions made

**Labels:**
- `endpoint` - API endpoint (`/analyze`, `/predict-from-features`)
- `model_version` - Model version (e.g., `v1.0.7`)
- `status` - Request status (`success`, `error`)

**Example Usage:**
```python
from chainguardian.monitoring.metrics import predictions_total

predictions_total.labels(
    endpoint="/analyze",
    model_version="v1.0.7",
    status="success"
).inc()
```

**PromQL Queries:**
```promql
# Total prediction rate (requests/second)
rate(chainguardian_predictions_total[5m])

# Success rate
rate(chainguardian_predictions_total{status="success"}[5m])
/ rate(chainguardian_predictions_total[5m])

# Error rate by endpoint
rate(chainguardian_predictions_total{status="error"}[5m])
```

---

#### `chainguardian_prediction_latency_seconds`

**Type:** Histogram
**Location:** [metrics.py:33](../src/chainguardian/monitoring/metrics.py#L33)
**Description:** Time taken to complete a prediction (feature extraction + inference)

**Labels:**
- `endpoint` - API endpoint

**Buckets:** `(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)` seconds

**Example Usage:**
```python
from chainguardian.monitoring.metrics import prediction_latency

prediction_latency.labels(endpoint="/analyze").observe(0.916)
```

**PromQL Queries:**
```promql
# P95 latency
histogram_quantile(0.95,
  rate(chainguardian_prediction_latency_seconds_bucket[5m])
)

# P99 latency
histogram_quantile(0.99,
  rate(chainguardian_prediction_latency_seconds_bucket[5m])
)

# Average latency
rate(chainguardian_prediction_latency_seconds_sum[5m])
/ rate(chainguardian_prediction_latency_seconds_count[5m])
```

---

#### `chainguardian_model_confidence_score`

**Type:** Histogram
**Location:** [metrics.py:43](../src/chainguardian/monitoring/metrics.py#L43)
**Description:** Distribution of model confidence scores (0.0 - 1.0)

**Labels:**
- `prediction_class` - Prediction class (`vulnerable`, `safe`)

**Buckets:** `(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0)`

**Example Usage:**
```python
from chainguardian.monitoring.metrics import model_confidence

model_confidence.labels(prediction_class="vulnerable").observe(0.92)
```

**PromQL Queries:**
```promql
# Average confidence by class
avg(chainguardian_model_confidence_score) by (prediction_class)

# Percentage of high-confidence predictions (>0.9)
sum(rate(chainguardian_model_confidence_score_bucket{le="1.0"}[5m]))
- sum(rate(chainguardian_model_confidence_score_bucket{le="0.9"}[5m]))

# Confidence distribution percentiles
histogram_quantile(0.50,
  rate(chainguardian_model_confidence_score_bucket[5m])
)
```

---

#### `chainguardian_active_predictions`

**Type:** Gauge
**Location:** [metrics.py:52](../src/chainguardian/monitoring/metrics.py#L52)
**Description:** Number of predictions currently being processed (concurrent requests)

**Example Usage:**
```python
from chainguardian.monitoring.metrics import active_predictions

# At request start
active_predictions.inc()

try:
    # Process prediction
    result = predictor.predict(...)
finally:
    # At request end (even on error)
    active_predictions.dec()
```

**PromQL Queries:**
```promql
# Current active predictions
chainguardian_active_predictions

# Max concurrent predictions in last 5 minutes
max_over_time(chainguardian_active_predictions[5m])

# Average concurrency
avg_over_time(chainguardian_active_predictions[5m])
```

---

### Vulnerability Metrics

#### `chainguardian_vulnerabilities_detected_total`

**Type:** Counter
**Location:** [metrics.py:63](../src/chainguardian/monitoring/metrics.py#L63)
**Description:** Total vulnerabilities detected, categorized by type and severity

**Labels:**
- `vulnerability_type` - Type of vulnerability (`reentrancy`, `overflow`, `access_control`, `unchecked_call`)
- `severity` - Severity level (`critical`, `high`, `medium`, `low`)

**Example Usage:**
```python
from chainguardian.monitoring.metrics import vulnerabilities_detected

vulnerabilities_detected.labels(
    vulnerability_type="reentrancy",
    severity="high"
).inc()
```

**PromQL Queries:**
```promql
# Vulnerabilities detected per second
rate(chainguardian_vulnerabilities_detected_total[5m])

# Top 5 most common vulnerabilities
topk(5, sum(rate(chainguardian_vulnerabilities_detected_total[1h])) by (vulnerability_type))

# Critical vulnerabilities only
rate(chainguardian_vulnerabilities_detected_total{severity="critical"}[5m])

# Vulnerability breakdown by severity
sum(rate(chainguardian_vulnerabilities_detected_total[5m])) by (severity)
```

---

### Feature Extraction Metrics

#### `chainguardian_feature_extraction_seconds`

**Type:** Histogram
**Location:** [metrics.py:77](../src/chainguardian/monitoring/metrics.py#L77)
**Description:** Time taken to extract 89 features from smart contract

**Buckets:** `(0.1, 0.25, 0.5, 1.0, 2.0, 5.0)` seconds

**Example Usage:**
```python
from chainguardian.monitoring.metrics import feature_extraction_latency

feature_extraction_latency.observe(0.85)
```

**PromQL Queries:**
```promql
# P95 feature extraction time
histogram_quantile(0.95,
  rate(chainguardian_feature_extraction_seconds_bucket[5m])
)

# Slow extractions (> 2 seconds)
sum(rate(chainguardian_feature_extraction_seconds_bucket{le="5.0"}[5m]))
- sum(rate(chainguardian_feature_extraction_seconds_bucket{le="2.0"}[5m]))
```

---

#### `chainguardian_feature_extraction_errors_total`

**Type:** Counter
**Location:** [metrics.py:84](../src/chainguardian/monitoring/metrics.py#L84)
**Description:** Failed feature extractions

**Labels:**
- `error_type` - Error category (`slither_timeout`, `parsing_error`, `invalid_solidity`)

**Example Usage:**
```python
from chainguardian.monitoring.metrics import feature_extraction_errors

feature_extraction_errors.labels(error_type="slither_timeout").inc()
```

**PromQL Queries:**
```promql
# Feature extraction error rate
rate(chainguardian_feature_extraction_errors_total[5m])

# Most common errors
topk(3, sum(rate(chainguardian_feature_extraction_errors_total[1h])) by (error_type))
```

---

### Model Performance Metrics

#### `chainguardian_model_version_info`

**Type:** Gauge
**Location:** [metrics.py:97](../src/chainguardian/monitoring/metrics.py#L97)
**Description:** Currently loaded model version with metadata

**Labels:**
- `version` - Model version (e.g., `v1.0.7`)
- `auc_score` - Test AUC score (e.g., `0.9978`)
- `trained_date` - Training date (e.g., `2025-12-15`)

**Example Usage:**
```python
from chainguardian.monitoring.metrics import model_version_info

model_version_info.labels(
    version="v1.0.7",
    auc_score="0.9978",
    trained_date="2025-12-15"
).set(1)
```

**PromQL Queries:**
```promql
# Current model version
chainguardian_model_version_info

# Get model metadata
chainguardian_model_version_info{version="v1.0.7"}
```

---

### LLM Metrics

#### `chainguardian_llm_requests_total`

**Type:** Counter
**Location:** [llm_metrics.py:7](../src/chainguardian/monitoring/llm_metrics.py#L7)
**Description:** Total number of LLM requests made

**Labels:**
- `model` - LLM model name (`llama3.1`, `mistral`, `codellama`, `phi3`)
- `endpoint` - API endpoint (`/reports/generate`)
- `status` - Request status (`started`, `success`, `failure`)

**Example Usage:**
```python
from chainguardian.monitoring.llm_metrics import llm_requests_total

llm_requests_total.labels(
    model="llama3.1",
    endpoint="/reports/generate",
    status="success"
).inc()
```

**PromQL Queries:**
```promql
# LLM requests per second
rate(chainguardian_llm_requests_total{status="success"}[5m])

# LLM error rate
rate(chainguardian_llm_requests_total{status="failure"}[5m])
/ rate(chainguardian_llm_requests_total[5m])

# Requests by model
sum(rate(chainguardian_llm_requests_total[5m])) by (model)
```

---

#### `chainguardian_llm_tokens_total`

**Type:** Counter
**Location:** [llm_metrics.py:13](../src/chainguardian/monitoring/llm_metrics.py#L13)
**Description:** Total tokens processed by LLM

**Labels:**
- `model` - LLM model name
- `direction` - Token direction (`input`, `output`)

**Example Usage:**
```python
from chainguardian.monitoring.llm_metrics import llm_tokens_total

llm_tokens_total.labels(model="llama3.1", direction="input").inc(1200)
llm_tokens_total.labels(model="llama3.1", direction="output").inc(850)
```

**PromQL Queries:**
```promql
# Total tokens per second
rate(chainguardian_llm_tokens_total[5m])

# Input vs output tokens
sum(rate(chainguardian_llm_tokens_total[5m])) by (direction)

# Tokens by model
sum(rate(chainguardian_llm_tokens_total[1h])) by (model)

# Total tokens in last 24 hours
increase(chainguardian_llm_tokens_total[24h])
```

---

#### `chainguardian_llm_latency_seconds`

**Type:** Histogram
**Location:** [llm_metrics.py:38](../src/chainguardian/monitoring/llm_metrics.py#L38)
**Description:** LLM response latency in seconds

**Labels:**
- `model` - LLM model name

**Buckets:** `[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]` seconds

**Example Usage:**
```python
from chainguardian.monitoring.llm_metrics import llm_latency_seconds

llm_latency_seconds.labels(model="llama3.1").observe(2.45)
```

**PromQL Queries:**
```promql
# P95 LLM latency
histogram_quantile(0.95,
  rate(chainguardian_llm_latency_seconds_bucket[5m])
)

# Average latency by model
rate(chainguardian_llm_latency_seconds_sum[5m])
/ rate(chainguardian_llm_latency_seconds_count[5m])
```

---

#### `chainguardian_llm_cost_estimated`

**Type:** Gauge
**Location:** [llm_metrics.py:46](../src/chainguardian/monitoring/llm_metrics.py#L46)
**Description:** Estimated LLM cost in USD

**Labels:**
- `model` - LLM model name
- `provider` - LLM provider (`ollama-local`, `openai`, `anthropic`)

**Example Usage:**
```python
from chainguardian.monitoring.llm_metrics import llm_cost_estimated, estimate_llm_cost

cost = estimate_llm_cost(input_tokens=1200, output_tokens=850, model="llama3.1")
llm_cost_estimated.labels(model="llama3.1", provider="ollama-local").set(cost)
```

**Cost Estimation:**
```python
# Cost rates (per 1M tokens)
cost_rates = {
    "llama3.1": {"input": 0.5, "output": 0.75},
    "mistral": {"input": 0.25, "output": 0.25},
    "codellama": {"input": 0.75, "output": 1.0},
    "phi3": {"input": 0.1, "output": 0.1}
}
```

**PromQL Queries:**
```promql
# Total estimated cost
sum(chainguardian_llm_cost_estimated)

# Cost by model
sum(chainguardian_llm_cost_estimated) by (model)

# Daily cost estimate
sum(chainguardian_llm_cost_estimated) * 86400 / 15
```

---

#### `chainguardian_active_llm_requests`

**Type:** Gauge
**Location:** [llm_metrics.py:64](../src/chainguardian/monitoring/llm_metrics.py#L64)
**Description:** Number of active LLM requests currently being processed

**Example Usage:**
```python
from chainguardian.monitoring.llm_metrics import active_llm_requests

active_llm_requests.inc()  # Start
try:
    llm_response = await ollama.generate(...)
finally:
    active_llm_requests.dec()  # End
```

**PromQL Queries:**
```promql
# Current active LLM requests
chainguardian_active_llm_requests

# Max concurrent LLM requests
max_over_time(chainguardian_active_llm_requests[5m])
```

---

#### `chainguardian_llm_errors_total`

**Type:** Counter
**Location:** [llm_metrics.py:19](../src/chainguardian/monitoring/llm_metrics.py#L19)
**Description:** Total LLM errors

**Labels:**
- `model` - LLM model name
- `error_type` - Error category (`timeout`, `connection_error`, `rate_limit`)

---

#### `chainguardian_llm_cache_hits_total`

**Type:** Counter
**Location:** [llm_metrics.py:25](../src/chainguardian/monitoring/llm_metrics.py#L25)
**Description:** Total LLM cache hits

**Labels:**
- `model` - LLM model name
- `cache_type` - Cache type (`semantic`, `exact`)

---

#### `chainguardian_rate_limit_exceeded_total`

**Type:** Counter
**Location:** [llm_metrics.py:31](../src/chainguardian/monitoring/llm_metrics.py#L31)
**Description:** Total rate limit violations

**Labels:**
- `endpoint` - API endpoint
- `ip_address` - Client IP address

**Example Usage:**
```python
from chainguardian.monitoring.llm_metrics import rate_limit_exceeded_total

rate_limit_exceeded_total.labels(
    endpoint="/api/v1/analyze",
    ip_address="192.168.1.100"
).inc()
```

**PromQL Queries:**
```promql
# Rate limit violations per second
rate(chainguardian_rate_limit_exceeded_total[5m])

# Most violated endpoints
topk(5, sum(rate(chainguardian_rate_limit_exceeded_total[1h])) by (endpoint))

# Top abusive IPs
topk(10, sum(rate(chainguardian_rate_limit_exceeded_total[1h])) by (ip_address))
```

---

## Integration Guide

### API Layer Integration

**Location:** [predict.py](../src/chainguardian/api/routers/predict.py)

```python
from chainguardian.monitoring.metrics import (
    predictions_total,
    prediction_latency,
    model_confidence,
    vulnerabilities_detected,
    feature_extraction_latency,
    active_predictions
)

@router.post("/api/v1/analyze")
async def analyze_contract(request: ContractAnalysisRequest):
    # Track active prediction
    active_predictions.inc()

    start_time = time.time()

    try:
        # Feature extraction
        extraction_start = time.time()
        features = pipeline.analyze_contract(...)
        extraction_time = time.time() - extraction_start

        # Track feature extraction latency
        feature_extraction_latency.observe(extraction_time)

        # ML prediction
        prediction_start = time.time()
        result = predictor.predict_single(features)
        prediction_time = time.time() - prediction_start

        # Track prediction latency
        prediction_latency.labels(endpoint="/analyze").observe(prediction_time)

        # Track model confidence
        confidence = result["calibrated_confidence"]
        prediction_class = "vulnerable" if result["prediction"] == 1 else "safe"
        model_confidence.labels(prediction_class=prediction_class).observe(confidence)

        # Track vulnerabilities
        for reason in result.get("semantic_reasons", []):
            severity = determine_severity(reason)
            vulnerabilities_detected.labels(
                vulnerability_type="general",
                severity=severity
            ).inc()

        # Track successful prediction
        predictions_total.labels(
            endpoint="/analyze",
            model_version="v1.0.7",
            status="success"
        ).inc()

        return response

    except Exception as e:
        # Track failed prediction
        predictions_total.labels(
            endpoint="/analyze",
            model_version="v1.0.7",
            status="failure"
        ).inc()
        raise

    finally:
        # Decrement active predictions
        active_predictions.dec()
```

---

### LLM Integration

**Location:** [reports.py](../src/chainguardian/api/routers/reports.py)

```python
from chainguardian.monitoring.llm_metrics import (
    llm_requests_total,
    llm_tokens_total,
    llm_latency_seconds,
    llm_cost_estimated,
    active_llm_requests,
    estimate_llm_cost
)

@router.post("/api/v1/reports/generate")
async def generate_report(request: GenerateReportRequest):
    # Track active LLM request
    active_llm_requests.inc()

    llm_start_time = time.time()

    try:
        # Track request start
        llm_requests_total.labels(
            model=request.llm_model,
            endpoint="/reports/generate",
            status="started"
        ).inc()

        # Generate report
        llm_response = await ollama.generate(...)

        # Track latency
        llm_latency = time.time() - llm_start_time
        llm_latency_seconds.labels(model=request.llm_model).observe(llm_latency)

        # Track tokens
        input_tokens = len(user_prompt.split())
        output_tokens = len(llm_response.get("response", "").split())

        llm_tokens_total.labels(
            model=request.llm_model,
            direction="input"
        ).inc(input_tokens)

        llm_tokens_total.labels(
            model=request.llm_model,
            direction="output"
        ).inc(output_tokens)

        # Track cost
        cost = estimate_llm_cost(input_tokens, output_tokens, request.llm_model)
        llm_cost_estimated.labels(
            model=request.llm_model,
            provider="ollama-local"
        ).set(cost)

        # Track success
        llm_requests_total.labels(
            model=request.llm_model,
            endpoint="/reports/generate",
            status="success"
        ).inc()

        return response

    except Exception as e:
        # Track failure
        llm_requests_total.labels(
            model=request.llm_model,
            endpoint="/reports/generate",
            status="failure"
        ).inc()
        raise

    finally:
        active_llm_requests.dec()
```

---

### Helper Functions

**Location:** [metrics.py:108](../src/chainguardian/monitoring/metrics.py#L108)

```python
from chainguardian.monitoring.metrics import (
    record_prediction,
    record_vulnerability,
    record_feature_extraction,
    set_model_info
)

# At application startup
set_model_info(
    version="v1.0.7",
    auc_score=0.9978,
    trained_date="2025-12-15"
)

# During prediction
record_prediction(
    endpoint="/analyze",
    model_version="v1.0.7",
    status="success",
    latency_seconds=0.916,
    confidence=0.92,
    prediction_class="vulnerable"
)

# When vulnerability detected
record_vulnerability("reentrancy", severity="high")

# After feature extraction
record_feature_extraction(
    latency_seconds=0.85,
    success=True
)

# On extraction error
record_feature_extraction(
    latency_seconds=10.0,
    success=False,
    error_type="slither_timeout"
)
```

---

## Grafana Dashboards

### Dashboard 1: API Performance Overview

**JSON Import:** See `grafana/dashboards/api_performance.json`

**Panels:**

1. **Request Rate**
```promql
rate(chainguardian_predictions_total[5m])
```

2. **Error Rate**
```promql
rate(chainguardian_predictions_total{status="error"}[5m])
/ rate(chainguardian_predictions_total[5m])
```

3. **P95 Latency**
```promql
histogram_quantile(0.95,
  rate(chainguardian_prediction_latency_seconds_bucket[5m])
)
```

4. **Active Predictions**
```promql
chainguardian_active_predictions
```

5. **Success Rate by Endpoint**
```promql
sum(rate(chainguardian_predictions_total{status="success"}[5m])) by (endpoint)
/ sum(rate(chainguardian_predictions_total[5m])) by (endpoint)
```

---

### Dashboard 2: ML Model Performance

**Panels:**

1. **Model Confidence Distribution**
```promql
sum(rate(chainguardian_model_confidence_score_bucket[5m])) by (le, prediction_class)
```

2. **Low Confidence Predictions** (<0.7)
```promql
sum(rate(chainguardian_model_confidence_score_bucket{le="0.7"}[5m]))
/ sum(rate(chainguardian_model_confidence_score_count[5m]))
```

3. **Vulnerabilities Detected**
```promql
sum(rate(chainguardian_vulnerabilities_detected_total[5m])) by (vulnerability_type)
```

4. **Critical Vulnerabilities**
```promql
rate(chainguardian_vulnerabilities_detected_total{severity="critical"}[5m])
```

5. **Feature Extraction Time**
```promql
histogram_quantile(0.95,
  rate(chainguardian_feature_extraction_seconds_bucket[5m])
)
```

---

### Dashboard 3: LLM Usage & Costs

**Panels:**

1. **LLM Request Rate**
```promql
rate(chainguardian_llm_requests_total{status="success"}[5m])
```

2. **LLM Latency**
```promql
histogram_quantile(0.95,
  rate(chainguardian_llm_latency_seconds_bucket[5m])
) by (model)
```

3. **Token Usage**
```promql
sum(rate(chainguardian_llm_tokens_total[5m])) by (direction)
```

4. **Estimated Hourly Cost**
```promql
sum(chainguardian_llm_cost_estimated) * 3600 / 15
```

5. **Daily Token Budget**
```promql
sum(increase(chainguardian_llm_tokens_total[24h]))
```

6. **Active LLM Requests**
```promql
chainguardian_active_llm_requests
```

---

### Dashboard 4: Rate Limiting & Security

**Panels:**

1. **Rate Limit Violations**
```promql
rate(chainguardian_rate_limit_exceeded_total[5m])
```

2. **Top Violated Endpoints**
```promql
topk(5, sum(rate(chainguardian_rate_limit_exceeded_total[1h])) by (endpoint))
```

3. **Top Abusive IPs**
```promql
topk(10, sum(rate(chainguardian_rate_limit_exceeded_total[1h])) by (ip_address))
```

4. **Feature Extraction Errors**
```promql
rate(chainguardian_feature_extraction_errors_total[5m]) by (error_type)
```

---

## Alerting Rules

### Prometheus Alerting Rules

**File:** `prometheus/alerts.yml`

```yaml
groups:
  - name: chainguardian_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(chainguardian_predictions_total{status="error"}[5m])
          / rate(chainguardian_predictions_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(chainguardian_prediction_latency_seconds_bucket[5m])
          ) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High P95 latency"
          description: "P95 latency is {{ $value }}s (threshold: 2s)"

      # Low confidence predictions
      - alert: LowConfidencePredictions
        expr: |
          sum(rate(chainguardian_model_confidence_score_bucket{le="0.7"}[5m]))
          / sum(rate(chainguardian_model_confidence_score_count[5m])) > 0.1
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "High rate of low-confidence predictions"
          description: "{{ $value | humanizePercentage }} of predictions have confidence < 0.7"

      # Feature extraction failures
      - alert: FeatureExtractionFailures
        expr: |
          rate(chainguardian_feature_extraction_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Feature extraction failing"
          description: "{{ $value }} failures per second"

      # LLM errors
      - alert: LLMErrors
        expr: |
          rate(chainguardian_llm_requests_total{status="failure"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LLM requests failing"
          description: "{{ $value }} LLM failures per second"

      # High LLM cost
      - alert: HighLLMCost
        expr: |
          sum(chainguardian_llm_cost_estimated) * 86400 / 15 > 10
        for: 1h
        labels:
          severity: info
        annotations:
          summary: "High estimated daily LLM cost"
          description: "Estimated daily cost: ${{ $value }}"

      # Rate limiting abuse
      - alert: RateLimitAbuse
        expr: |
          rate(chainguardian_rate_limit_exceeded_total[5m]) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate of rate limit violations"
          description: "{{ $value }} violations per second"

      # Model not responding
      - alert: ModelNotResponding
        expr: |
          rate(chainguardian_predictions_total[5m]) == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "No predictions in last 5 minutes"
          description: "Model may be down or stuck"
```

---

### Alert Notification Channels

**Slack Integration:**
```yaml
receivers:
  - name: slack
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#chainguardian-alerts'
        title: 'ChainGuardian Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

**PagerDuty Integration:**
```yaml
receivers:
  - name: pagerduty
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        severity: '{{ .CommonLabels.severity }}'
```

---

## Performance Monitoring

### Key Performance Indicators (KPIs)

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Request Success Rate | > 99% | < 95% |
| P95 Latency | < 1.5s | > 2.0s |
| Model Confidence | > 0.85 avg | < 0.7 for >10% |
| Feature Extraction Success | > 98% | < 95% |
| LLM Success Rate | > 95% | < 90% |
| Active Predictions | < 50 | > 100 |

---

### Performance Analysis Queries

**1. Latency Breakdown:**
```promql
# Feature extraction time
histogram_quantile(0.95, rate(chainguardian_feature_extraction_seconds_bucket[5m]))

# Prediction time
histogram_quantile(0.95, rate(chainguardian_prediction_latency_seconds_bucket[5m]))

# Total time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**2. Throughput Analysis:**
```promql
# Requests per second
rate(chainguardian_predictions_total[5m])

# Successful predictions per second
rate(chainguardian_predictions_total{status="success"}[5m])

# Max throughput achieved
max_over_time(rate(chainguardian_predictions_total[5m])[1h])
```

**3. Error Analysis:**
```promql
# Error rate trend
rate(chainguardian_predictions_total{status="error"}[5m])

# Errors by endpoint
sum(rate(chainguardian_predictions_total{status="error"}[5m])) by (endpoint)
```

---

## Cost Tracking

### LLM Cost Monitoring

**Daily Cost Estimate:**
```promql
sum(chainguardian_llm_cost_estimated) * 86400 / 15
```

**Monthly Projection:**
```promql
sum(chainguardian_llm_cost_estimated) * 2592000 / 15
```

**Cost by Model:**
```promql
sum(chainguardian_llm_cost_estimated) by (model) * 86400 / 15
```

**Token Usage Analysis:**
```promql
# Daily tokens
sum(increase(chainguardian_llm_tokens_total[24h]))

# Input vs output ratio
sum(rate(chainguardian_llm_tokens_total{direction="output"}[5m]))
/ sum(rate(chainguardian_llm_tokens_total{direction="input"}[5m]))
```

---

### Cost Optimization

**Recommendations:**

1. **Model Selection:**
   - Use `phi3` for simple reports (10x cheaper)
   - Use `llama3.1` for complex analysis
   - Reserve `codellama` for code-heavy reports

2. **Prompt Optimization:**
   - Reduce input token count by summarizing features
   - Set `num_predict` limit to avoid excessive output
   - Use caching for repeated prompts

3. **Rate Limiting:**
   - Implement stricter limits on `/reports/generate`
   - Consider tiered pricing based on report depth

---

## Best Practices

### 1. Metric Naming

Follow Prometheus naming conventions:

```python
# Good
chainguardian_predictions_total  # Clear subsystem prefix, unit suffix
chainguardian_latency_seconds    # Standard unit suffix

# Bad
predictions                      # No subsystem prefix
latency_ms                       # Non-standard unit (use seconds)
```

---

### 2. Label Cardinality

Keep label cardinality low to avoid memory issues:

```python
# Good - Low cardinality
predictions_total.labels(
    endpoint="/analyze",           # ~5 values
    model_version="v1.0.7",        # ~10 values
    status="success"               # 2 values
)

# Bad - High cardinality
predictions_total.labels(
    contract_address="0x123...",   # Millions of values - DON'T DO THIS
    user_id="12345"                # Thousands of values - AVOID
)
```

---

### 3. Histogram Buckets

Choose buckets appropriate for your latency distribution:

```python
# API latency (milliseconds to seconds)
buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

# LLM latency (seconds to minutes)
buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)

# Feature extraction (sub-second to seconds)
buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
```

---

### 4. Counter vs Gauge

```python
# Counter - Always increasing (use for totals)
predictions_total.inc()           # Predictions made
llm_tokens_total.inc(1200)        # Tokens processed

# Gauge - Can go up or down (use for current state)
active_predictions.inc()          # Current in-flight requests
active_predictions.dec()
model_confidence.set(0.92)        # Current value
```

---

### 5. Error Tracking

Always track errors with appropriate labels:

```python
try:
    result = predictor.predict(...)
    predictions_total.labels(status="success").inc()
except ValidationError as e:
    predictions_total.labels(status="validation_error").inc()
except ModelError as e:
    predictions_total.labels(status="model_error").inc()
except Exception as e:
    predictions_total.labels(status="unknown_error").inc()
    raise
```

---

### 6. Cleanup in Finally Blocks

Always decrement gauges in finally blocks:

```python
active_predictions.inc()
try:
    result = process()
finally:
    active_predictions.dec()  # Always executes
```

---

## Integration with Other Modules

### ML Core Module

The monitoring module integrates with [ML Core](ml_core_technical_documentation.md) to track:

- **ModelRegistry**: Track model versions and deployments
- **MLMonitor**: Complement drift detection with Prometheus metrics
- **HeterogeneousEnsemble**: Track ensemble predictions and confidence
- **HyperparameterTuner**: Track optimization trials (future enhancement)

**Example:**
```python
from chainguardian.ml.core import ModelRegistry
from chainguardian.monitoring.metrics import set_model_info

registry = ModelRegistry()
latest = registry.get_model()

set_model_info(
    version=latest['version'],
    auc_score=latest['metadata']['performance_metrics']['auc'],
    trained_date=latest['metadata']['training_info']['date']
)
```

---

### API Module

The monitoring module is used throughout the [API module](api_technical_documentation.md):

- **predict.py**: Track predictions, latency, confidence
- **reports.py**: Track LLM usage, tokens, costs
- **rate_limiter.py**: Track rate limit violations
- **main.py**: Prometheus instrumentation

---

## Troubleshooting

### Common Issues

**1. Metrics not appearing:**
```bash
# Check /metrics endpoint
curl http://localhost:8000/metrics | grep chainguardian

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

**2. High memory usage:**
```promql
# Check label cardinality
count({__name__=~"chainguardian_.*"}) by (__name__)
```

**3. Missing labels:**
```python
# Always provide all labels
predictions_total.labels(
    endpoint="/analyze",  # Required
    model_version="v1.0.7",  # Required
    status="success"  # Required
).inc()
```

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [ML Core Documentation](ml_core_technical_documentation.md)
- [API Documentation](api_technical_documentation.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-29
**Maintainer:** ChainGuardian AI Team
