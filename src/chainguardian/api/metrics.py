"""
API-specific metrics module.
Re-exports metrics from monitoring for easier imports.
"""
from chainguardian.monitoring.metrics import (
    predictions_total,
    feature_extraction_latency,
    model_confidence,
    vulnerabilities_detected,
    prediction_latency,
    active_predictions,
    model_version
)

__all__ = [
    "predictions_total",
    "feature_extraction_latency", 
    "model_confidence",
    "vulnerabilities_detected",
    "prediction_latency",
    "active_predictions",
    "model_version"
]