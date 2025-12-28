"""
Prometheus Metrics for ChainGuardian API

This module defines custom metrics for ML model monitoring.
Auto-instrumented metrics (requests, latency) are handled by Instrumentator.

Metric Naming Convention (Prometheus best practices):
- Use underscores (not camelCase)
- End with unit suffix (_total, _seconds, _bytes)
- Include subsystem prefix (chainguardian_)
"""

from prometheus_client import Counter, Histogram, Gauge
from typing import Optional


# ==============================================================================
# PREDICTION METRICS
# ==============================================================================

# Counter: Total predictions made
predictions_total = Counter(
    name='chainguardian_predictions_total',
    documentation='Total number of vulnerability predictions made',
    labelnames=['endpoint', 'model_version', 'status']
    # Labels allow filtering:
    # - endpoint: /predict, /analyze, /batch
    # - model_version: v1.0.7
    # - status: success, error
)

# Histogram: Prediction latency distribution
prediction_latency = Histogram(
    name='chainguardian_prediction_latency_seconds',
    documentation='Time taken to complete a prediction (feature extraction + inference)',
    labelnames=['endpoint'],
    # Buckets define histogram bins (in seconds)
    # These values are optimized for ML inference (50ms - 5s range)
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Histogram: Model confidence score distribution
model_confidence = Histogram(
    name='chainguardian_model_confidence_score',
    documentation='Model confidence scores (0.0 - 1.0)',
    labelnames=['prediction_class'],
    # Buckets for probability distribution (0.0 - 1.0)
    buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0)
)


# ==============================================================================
# VULNERABILITY METRICS
# ==============================================================================

# Counter: Vulnerabilities detected by type
vulnerabilities_detected = Counter(
    name='chainguardian_vulnerabilities_detected_total',
    documentation='Total vulnerabilities detected, by type',
    labelnames=['vulnerability_type', 'severity']
    # vulnerability_type: reentrancy, overflow, access_control
    # severity: critical, high, medium, low
)


# ==============================================================================
# FEATURE EXTRACTION METRICS
# ==============================================================================

# Histogram: Feature extraction time
feature_extraction_latency = Histogram(
    name='chainguardian_feature_extraction_seconds',
    documentation='Time taken to extract 89 features from contract',
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
)

# Counter: Feature extraction errors
feature_extraction_errors = Counter(
    name='chainguardian_feature_extraction_errors_total',
    documentation='Failed feature extractions',
    labelnames=['error_type']
    # error_type: slither_timeout, parsing_error, invalid_solidity
)


# ==============================================================================
# MODEL PERFORMANCE METRICS
# ==============================================================================

# Gauge: Current model version in use
model_version_info = Gauge(
    name='chainguardian_model_version_info',
    documentation='Currently loaded model version',
    labelnames=['version', 'auc_score', 'trained_date']
)


# ==============================================================================
# HELPER FUNCTIONS (Called from routers)
# ==============================================================================

def record_prediction(
    endpoint: str,
    model_version: str,
    status: str = "success",
    latency_seconds: Optional[float] = None,
    confidence: Optional[float] = None,
    prediction_class: Optional[str] = None
):
    """
    Record a prediction event with all associated metrics.
    
    Call this from your predict router after each prediction.
    
    Args:
        endpoint: API endpoint name ("/predict", "/analyze")
        model_version: Model version used (e.g., "v1.0.7")
        status: "success" or "error"
        latency_seconds: Time taken for prediction
        confidence: Model confidence (0.0 - 1.0)
        prediction_class: "vulnerable" or "safe"
    
    Example:
        record_prediction(
            endpoint="/predict",
            model_version="v1.0.7",
            status="success",
            latency_seconds=0.34,
            confidence=0.92,
            prediction_class="vulnerable"
        )
    """
    # Increment prediction counter
    predictions_total.labels(
        endpoint=endpoint,
        model_version=model_version,
        status=status
    ).inc()
    
    # Record latency if provided
    if latency_seconds is not None:
        prediction_latency.labels(endpoint=endpoint).observe(latency_seconds)
    
    # Record confidence if provided
    if confidence is not None and prediction_class is not None:
        model_confidence.labels(prediction_class=prediction_class).observe(confidence)


def record_vulnerability(vulnerability_type: str, severity: str = "high"):
    """
    Record a detected vulnerability.
    
    Args:
        vulnerability_type: Type of vulnerability (e.g., "reentrancy")
        severity: "critical", "high", "medium", "low"
    
    Example:
        record_vulnerability("reentrancy", "critical")
    """
    vulnerabilities_detected.labels(
        vulnerability_type=vulnerability_type,
        severity=severity
    ).inc()


def record_feature_extraction(latency_seconds: float, success: bool = True, error_type: Optional[str] = None):
    """
    Record feature extraction metrics.
    
    Args:
        latency_seconds: Time taken to extract features
        success: Whether extraction succeeded
        error_type: If failed, the error type (e.g., "slither_timeout")
    
    Example:
        record_feature_extraction(0.5, success=True)
        record_feature_extraction(10.0, success=False, error_type="slither_timeout")
    """
    if success:
        feature_extraction_latency.observe(latency_seconds)
    else:
        if error_type:
            feature_extraction_errors.labels(error_type=error_type).inc()


def set_model_info(version: str, auc_score: float, trained_date: str):
    """
    Set model version information (call once at startup).
    
    Args:
        version: Model version (e.g., "v1.0.7")
        auc_score: AUC score (e.g., 0.9978)
        trained_date: Training date (e.g., "2025-12-15")
    
    Example:
        set_model_info("v1.0.7", 0.9978, "2025-12-15")
    """
    model_version_info.labels(
        version=version,
        auc_score=str(auc_score),
        trained_date=trained_date
    ).set(1)  # Set to 1 (just an indicator, not a meaningful value)
