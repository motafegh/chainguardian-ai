# ChainGuardian AI - Configuration Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-29
**Config Directory:** `config/`

**Related Documentation:**

- [ML Core Technical Documentation](ml_core_technical_documentation.md)
- [API Technical Documentation](api_technical_documentation.md)
- [Monitoring Technical Documentation](monitoring_technical_documentation.md)
- [Hybrid Predictor Technical Documentation](hybrid_predictor_technical_documentation.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Hybrid Configuration (YAML)](#hybrid-configuration-yaml)
4. [Model Registry](#model-registry)
5. [Prometheus Configuration](#prometheus-configuration)
6. [Grafana Configuration](#grafana-configuration)
7. [Environment-Specific Configuration](#environment-specific-configuration)
8. [Configuration Validation](#configuration-validation)
9. [Best Practices](#best-practices)

---

## Overview

The ChainGuardian AI configuration system uses a combination of YAML files, JSON metadata, and provisioning configs to manage all aspects of the ML pipeline, API, and monitoring infrastructure.

### Configuration Hierarchy

```
config/
├── hybrid_config.yaml       # Main ML & API configuration
├── models/                  # Model artifacts and metadata
│   ├── *.pkl               # Model files (ensemble/single)
│   ├── *.json              # Feature metadata
│   └── registry/           # Model versioning
├── prometheus/             # Prometheus alerting rules
│   └── rules.yml
└── grafana/                # Grafana provisioning
    ├── datasources/
    └── dashboards/
```

---

## Directory Structure

### Complete Config Tree

```
config/
├── hybrid_config.yaml                    # Main configuration (281 lines)
├── logs/                                 # Prediction logs
│   └── predictions_2025-12-23.jsonl
├── models/                               # Model artifacts
│   ├── ensemble_model_v7.pkl            # Ensemble model (4 algorithms)
│   ├── ensemble_scaler_v7.pkl           # StandardScaler for ensemble
│   ├── production_model_v7.pkl          # Single XGBoost model
│   ├── production_scaler_v7.pkl         # StandardScaler for single
│   ├── feature_metadata_v7.json         # Feature names & metadata
│   └── registry/                        # Model version control
│       ├── index.json                   # Registry index
│       ├── v1.0.5/                      # Version 1.0.5
│       │   └── metadata.json
│       ├── v1.0.6/                      # Version 1.0.6
│       │   └── metadata.json
│       └── v1.0.7/                      # Latest version
│           └── metadata.json
├── prometheus/                          # Monitoring rules
│   └── rules.yml                        # Alert rules (42 lines)
└── grafana/                             # Dashboard provisioning
    ├── datasources/
    │   └── prometheus.yml               # Prometheus datasource
    └── dashboards/
        └── dashboards.yml               # Dashboard provider
```

---

## Hybrid Configuration (YAML)

**File:** `config/hybrid_config.yaml`
**Size:** 281 lines
**Purpose:** Central configuration for ML training, inference, and monitoring

### Configuration Sections

#### 1. Hyperparameter Tuning

**Lines:** 1-49

```yaml
hyperparameter_tuning:
  enable_optuna: true
  n_trials: 3                     # Number of optimization trials
  timeout_seconds: 120             # Max time for optimization
  direction: maximize              # Maximize AUC
  study_name: "chainguardian_optimization_v2"
  n_jobs: -1                      # Use all CPU cores
  gpu_id: 0                       # GPU device ID

  # GPU acceleration
  gpu_acceleration:
    xgboost_gpu: true
    lightgbm_gpu: true

  # Search spaces for each algorithm
  search_spaces:
    xgboost:
      n_estimators: [50, 100]
      max_depth: [3, 5]
      learning_rate: [0.05, 0.1]
      subsample: [0.5, 1.0]
      colsample_bytree: [0.5, 1.0]
      gamma: [0, 10]
      reg_alpha: [0, 20]
      reg_lambda: [0.1, 20]
      tree_method: ["hist", "gpu_hist"]
      predictor: ["gpu_predictor"]

    random_forest:
      n_estimators: [50, 100]
      max_depth: [5, 10]
      min_samples_split: [2, 20]
      min_samples_leaf: [1, 10]
      n_jobs: -1
      max_features: [0.3, 1.0]

    lightgbm:
      n_estimators: [50, 100]
      num_leaves: [20, 60]        # Reduced to prevent overfitting
      learning_rate: [0.005, 0.3]
      feature_fraction: [0.5, 1.0]
      bagging_fraction: [0.5, 1.0]
      bagging_freq: [1, 10]
      min_child_samples: [5, 50]  # Prevents overfitting
      device: ["gpu"]
      gpu_platform_id: 0
      gpu_device_id: 0
```

**Key Parameters:**

| Parameter | Default | Description | When to Change |
| --------- | ------- | ----------- | -------------- |
| `n_trials` | 3 | Optuna trials | Increase for better tuning (costly) |
| `timeout_seconds` | 120 | Max optimization time | Increase for complex searches |
| `n_jobs` | -1 | Parallel workers | Keep -1 for all cores |
| `gpu_id` | 0 | GPU device | Change for multi-GPU setups |

---

#### 2. Ensemble Configuration

**Lines:** 50-80

```yaml
ensemble:
  enabled: true
  voting_method: "soft"           # Soft voting (probability averaging)
  use_gpu: true
  batch_size: 1024

  # Weight optimization
  weight_optimization:
    method: "genetic_algorithm"   # Options: grid_search, bayesian, genetic
    population_size: 50
    generations: 100
    n_folds: 5

  # Initial weights
  initial_weights:
    xgboost: 0.4
    random_forest: 0.3
    lightgbm: 0.2
    logistic_regression: 0.1

  # Calibration method
  calibration_method: "isotonic"  # Options: sigmoid, isotonic

  # Uncertainty quantification
  uncertainty:
    enable_bootstrap: false
    n_bootstrap_samples: 100
    confidence_level: 0.95
    method: "bayesian"
    mc_dropout_samples: 100
```

**Calibration Methods:**

| Method | Pros | Cons | Best For |
| ------ | ---- | ---- | -------- |
| `sigmoid` (Platt) | Fast, works with small data | Assumes sigmoid shape | Small datasets |
| `isotonic` | More flexible | Needs more data | Large datasets (recommended) |

**Weight Optimization Methods:**

| Method | Speed | Quality | Memory | Use When |
| ------ | ----- | ------- | ------ | -------- |
| `grid_search` | Slow | Good | Low | Small grid |
| `bayesian` | Medium | Excellent | Medium | Default choice |
| `genetic_algorithm` | Fast | Very Good | Low | Large search space |

---

#### 3. Data Augmentation

**Lines:** 81-94

```yaml
augmentation:
  enabled: true
  strategy: "smote"              # Options: smote, mixup, gaussian, combined
  mixup_alpha: 0.4               # Mixup interpolation strength
  gaussian_std: 0.1              # Gaussian noise std dev
  smote_neighbors: 10            # K-neighbors for SMOTE
  max_augmentation_factor: 4.0   # Generate up to 4x original data

  # Progressive augmentation
  progressive_augmentation: true
  epochs: 3                      # Multiple augmentation rounds
  quality_filter: true           # Filter low-quality synthetic samples
```

**Augmentation Strategies:**

| Strategy | Description | Use Case | Performance Impact |
| -------- | ----------- | -------- | ------------------ |
| `smote` | Synthetic minority over-sampling | Class imbalance | Medium |
| `mixup` | Convex combinations of samples | Regularization | Low |
| `gaussian` | Add noise to features | Robustness | Low |
| `combined` | All strategies | Maximum augmentation | High |

**Recommended Settings:**

```yaml
# For balanced datasets
max_augmentation_factor: 2.0
strategy: "mixup"

# For imbalanced datasets
max_augmentation_factor: 4.0
strategy: "smote"

# For small datasets
max_augmentation_factor: 3.0
strategy: "combined"
```

---

#### 4. Batch Processing

**Lines:** 95-107

```yaml
batch_processing:
  enabled: true
  batch_size: 512                # GPU-optimized batch size
  max_workers: 8                 # CPU workers for parallel processing
  enable_vectorization: true     # Use vectorized operations
  use_gpu_batches: true

  # Memory optimization
  preload_data: true             # Preload to RAM
  cache_size_gb: 16              # Data cache size
  chunk_size: 10000              # Process in chunks
```

**Batch Size Guidelines:**

| Hardware | CPU Batch | GPU Batch | Recommended Workers |
| -------- | --------- | --------- | ------------------- |
| CPU only | 32 | N/A | cores - 1 |
| GPU (8GB) | 64 | 512 | cores / 2 |
| GPU (16GB) | 128 | 1024 | cores / 2 |
| GPU (24GB+) | 256 | 2048 | cores / 2 |

---

#### 5. Model Registry

**Lines:** 108-131

```yaml
model_registry:
  registry_path: "config/models/registry"
  keep_last_n_versions: 20       # Retain last 20 versions
  auto_versioning: true          # Auto-increment versions
  enable_experiment_tracking: true

  # Metadata schema
  metadata_schema:
    - model_type
    - performance_metrics
    - training_date
    - feature_list
    - hyperparameters
    - hardware_used
    - training_time
    - data_statistics

  # GPU tracking
  gpu_metadata:
    track_gpu_metrics: true
    memory_usage: true
    inference_speed: true
```

**Version Management:**

```yaml
# Semantic versioning: major.minor.patch
# major: Breaking changes (new features, different output)
# minor: Non-breaking improvements (better accuracy)
# patch: Bug fixes, minor tweaks
```

---

#### 6. Monitoring

**Lines:** 132-156

```yaml
monitoring:
  enable_performance_logging: true
  log_dir: "logs"
  realtime_metrics: true
  enable_tensorboard: true

  # Metrics to track
  metrics_to_track:
    - accuracy
    - auc
    - precision
    - recall
    - f1_score
    - inference_latency
    - gpu_memory_usage
    - cpu_utilization
    - data_quality_scores

  # Drift detection
  drift_detection:
    enabled: true
    window_size: 5000            # Samples for baseline
    drift_threshold: 0.03        # KS test threshold
    check_interval: 1000         # Check every N predictions
    methods: ["ks_test", "mmd", "classifier"]
```

**Drift Detection Methods:**

| Method | Speed | Accuracy | False Positives | Best For |
| ------ | ----- | -------- | --------------- | -------- |
| `ks_test` | Fast | Good | Low | Continuous features |
| `mmd` | Medium | Excellent | Medium | All features |
| `classifier` | Slow | Very Good | Low | Complex drift |

---

#### 7. Feature Engineering

**Lines:** 157-177

```yaml
features:
  preserve_all_engineered: true

  # Feature patterns
  boolean_features: "has_*"
  continuous_features: "*_count,*_ratio,*_score,*_length,*_depth"
  categorical_features: "none"

  # Scaler type
  scaler_type: "robust"          # Options: standard, robust, minmax
```

**Scaler Types:**

| Scaler | Robust to Outliers | Range | Use Case |
| ------ | ------------------ | ----- | -------- |
| `standard` | No | Unbounded | Normal distributions |
| `robust` | **Yes** | Unbounded | **Recommended** (default) |
| `minmax` | No | [0, 1] | Neural networks |

---

#### 8. Thresholds

**Lines:** 178-189

```yaml
thresholds:
  vulnerability_prediction: 0.15  # Classification threshold
  high_confidence: 0.90           # High confidence bar
  low_confidence: 0.30            # Low confidence bar
  override_cei_violations: 2      # CEI violation override
  override_perfect_cei_with_guard: true

  # Adaptive thresholds
  adaptive_thresholds: true       # Adjust based on data
  threshold_smoothing: 0.1        # Smooth threshold changes
```

**Threshold Tuning:**

| Metric | Conservative | Balanced | Aggressive |
| ------ | ------------ | -------- | ---------- |
| `vulnerability_prediction` | 0.3 | 0.15 | 0.05 |
| `high_confidence` | 0.95 | 0.90 | 0.85 |
| `low_confidence` | 0.40 | 0.30 | 0.20 |

**Effect on Metrics:**

```
Lower threshold → More vulnerabilities detected (higher recall, lower precision)
Higher threshold → Fewer false positives (higher precision, lower recall)
```

---

#### 9. Performance Optimization

**Lines:** 190-209

```yaml
performance:
  enable_feature_caching: true
  cache_size: 10000              # LRU cache size
  prediction_timeout_ms: 10000
  memory_limit_mb: 32768         # 32GB RAM limit

  # GPU optimization
  gpu_memory_fraction: 0.8       # Use 80% of GPU
  enable_mixed_precision: true   # FP16 for faster inference
  gpu_batch_size: 2048

  # Parallel processing
  parallel_feature_extraction: true
  n_feature_workers: 4

  # Model optimization
  enable_model_pruning: true
  enable_quantization: true      # Quantize for speed
```

**Performance Impact:**

| Feature | Speedup | Accuracy Impact | Memory Impact |
| ------- | ------- | --------------- | ------------- |
| `feature_caching` | 3-5x | None | +100MB |
| `mixed_precision` | 2x | -0.1% | -50% |
| `quantization` | 4x | -0.5% | -75% |
| `model_pruning` | 1.5x | -1% | -30% |

---

#### 10. GPU Configuration

**Lines:** 237-253

```yaml
gpu:
  enabled: true
  device_id: 0
  memory_growth: true            # Allow dynamic memory allocation
  per_process_gpu_memory_fraction: 0.8

  # CUDA optimization
  cuda_optimizations:
    allow_tensor_core: true      # Use Tensor Cores (RTX GPUs)
    enable_cudnn_autotune: true  # Auto-tune cuDNN kernels
    cudnn_benchmark: true

  # Multi-GPU
  multi_gpu: false
  gpu_devices: [0]
```

**GPU Memory Management:**

```yaml
# For 8GB GPU
per_process_gpu_memory_fraction: 0.7
gpu_batch_size: 512

# For 16GB GPU
per_process_gpu_memory_fraction: 0.8
gpu_batch_size: 1024

# For 24GB+ GPU
per_process_gpu_memory_fraction: 0.9
gpu_batch_size: 2048
```

---

#### 11. Logging and Debugging

**Lines:** 265-281

```yaml
logging:
  level: "INFO"                  # Options: DEBUG, INFO, WARNING, ERROR
  enable_profiling: true
  profile_batch_range: [10, 20]  # Profile batches 10-20

  # TensorBoard
  tensorboard:
    enabled: true
    log_dir: "logs/tensorboard"
    update_freq: "batch"

  # MLflow integration
  mlflow:
    enabled: true
    tracking_uri: "http://localhost:5000"
    experiment_name: "chainguardian_ai"
```

**Logging Levels:**

| Level | Use Case | Output Volume |
| ----- | -------- | ------------- |
| `DEBUG` | Development, troubleshooting | Very High |
| `INFO` | **Production** (recommended) | Medium |
| `WARNING` | Production (minimal logging) | Low |
| `ERROR` | Production (errors only) | Very Low |

---

## Model Registry

**Directory:** `config/models/registry/`

### Index File

**File:** `config/models/registry/index.json`

```json
{
  "versions": [
    {
      "version": "v1.0.7",
      "created": "2025-12-24T13:16:34",
      "description": "Enhanced ensemble with GPU optimization",
      "auc": 0.9978,
      "status": "production"
    },
    {
      "version": "v1.0.6",
      "created": "2025-12-23T10:30:00",
      "description": "Ensemble with isotonic calibration",
      "auc": 0.9965,
      "status": "archived"
    }
  ],
  "current_production": "v1.0.7",
  "current_staging": null
}
```

---

### Version Metadata

**File:** `config/models/registry/v1.0.7/metadata.json`

```json
{
  "version": "v1.0.7",
  "model_type": "ensemble",
  "created": "2025-12-24T13:16:34.916580",
  "description": "Enhanced ensemble with GPU optimization",

  "performance": {
    "test_auc": 0.9978,
    "test_accuracy": 0.9832,
    "test_brier": 0.0146,
    "train_auc": 0.9995,
    "validation_auc": 0.9972
  },

  "ensemble_config": {
    "algorithms": ["xgboost", "random_forest", "lightgbm", "logistic_regression"],
    "weights": {
      "xgboost": 0.45,
      "random_forest": 0.30,
      "lightgbm": 0.20,
      "logistic_regression": 0.05
    },
    "calibration_method": "isotonic",
    "voting_method": "soft"
  },

  "training_info": {
    "dataset_size": 2980,
    "training_samples": 2086,
    "validation_samples": 447,
    "test_samples": 447,
    "n_features": 72,
    "training_time_seconds": 245
  },

  "hyperparameters": {
    "xgboost": {
      "n_estimators": 100,
      "max_depth": 5,
      "learning_rate": 0.1,
      "subsample": 0.8,
      "colsample_bytree": 0.8
    }
  },

  "deployment": {
    "status": "production",
    "deployed_at": "2025-12-24T14:00:00",
    "deployed_by": "training_pipeline",
    "endpoint": "/api/v1/analyze"
  }
}
```

---

## Prometheus Configuration

**File:** `config/prometheus/rules.yml`

### Alert Rules

```yaml
groups:
  - name: chainguardian-alerts
    rules:
      # 1. High Error Rate
      - alert: HighErrorRate
        expr: |
          rate(chainguardian_predictions_total{status="failure"}[5m])
          / rate(chainguardian_predictions_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # 2. High Latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(chainguardian_prediction_latency_seconds_bucket[5m])
          ) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High prediction latency detected"
          description: "95th percentile latency is {{ $value }} seconds"

      # 3. LLM Cost Alert
      - alert: LLMCostExceeded
        expr: chainguardian_llm_cost_estimated > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "LLM cost exceeded $10"
          description: "Current estimated LLM cost is ${{ $value }}"

      # 4. Rate Limit Violations
      - alert: RateLimitViolations
        expr: rate(chainguardian_rate_limit_exceeded_total[10m]) > 5
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High rate limit violations detected"
          description: "{{ $value }} violations per minute"
```

### Alert Severity Levels

| Severity | Response Time | Notification | Examples |
| -------- | ------------- | ------------ | -------- |
| `critical` | Immediate | PagerDuty, SMS | Service down, high cost |
| `warning` | 15 minutes | Slack, Email | High latency, errors |
| `info` | 1 hour | Email | Drift detected |

---

## Grafana Configuration

### Datasource Configuration

**File:** `config/grafana/datasources/prometheus.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: 15s          # Scrape interval
      queryTimeout: 60s          # Query timeout
      httpMethod: POST           # Use POST for large queries
```

### Dashboard Provisioning

**File:** `config/grafana/dashboards/dashboards.yml`

```yaml
apiVersion: 1

providers:
  - name: 'Chainguardian Dashboards'
    orgId: 1
    folder: 'Chainguardian'      # Dashboard folder
    type: file
    disableDeletion: false
    editable: true
    updateIntervalSeconds: 30    # Auto-refresh
    allowUiUpdates: true         # Allow UI edits
    options:
      path: /etc/grafana/provisioning/dashboards
```

---

## Environment-Specific Configuration

### Development

```yaml
# config/hybrid_config.dev.yaml
hyperparameter_tuning:
  n_trials: 3
  timeout_seconds: 120

ensemble:
  enabled: true
  use_gpu: false               # No GPU in dev

batch_processing:
  batch_size: 32               # Smaller batches

performance:
  enable_feature_caching: true
  cache_size: 1000

logging:
  level: "DEBUG"               # Verbose logging
  enable_profiling: true
```

### Staging

```yaml
# config/hybrid_config.staging.yaml
hyperparameter_tuning:
  n_trials: 10
  timeout_seconds: 600

ensemble:
  enabled: true
  use_gpu: true

batch_processing:
  batch_size: 256

performance:
  enable_feature_caching: true
  cache_size: 5000

logging:
  level: "INFO"
  enable_profiling: false
```

### Production

```yaml
# config/hybrid_config.prod.yaml
hyperparameter_tuning:
  n_trials: 50
  timeout_seconds: 3600

ensemble:
  enabled: true
  use_gpu: true

batch_processing:
  batch_size: 512

performance:
  enable_feature_caching: true
  cache_size: 10000
  enable_quantization: true    # Optimize for speed

logging:
  level: "WARNING"             # Minimal logging
  enable_profiling: false
```

---

## Configuration Validation

### Validation Script

```python
# scripts/validate_config.py
import yaml
from pathlib import Path
from chainguardian.ml.core.config_manager import ConfigManager

def validate_config(config_path: str):
    """Validate configuration file."""
    try:
        # Load config
        config_manager = ConfigManager()
        config = config_manager.load_config(config_path)

        # Validate sections
        assert config.hyperparameter_tuning.n_trials > 0
        assert config.ensemble.enabled in [True, False]
        assert config.thresholds.vulnerability_prediction >= 0
        assert config.thresholds.vulnerability_prediction <= 1

        # Validate paths
        registry_path = Path(config.model_registry.registry_path)
        assert registry_path.exists(), f"Registry path not found: {registry_path}"

        print("✅ Configuration is valid")
        return True

    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

if __name__ == "__main__":
    validate_config("config/hybrid_config.yaml")
```

**Usage:**

```bash
python scripts/validate_config.py
```

---

## Best Practices

### 1. Version Control

```bash
# Track config changes in git
git add config/hybrid_config.yaml
git commit -m "feat: increase batch size for GPU optimization"

# Use config branches for experiments
git checkout -b config/experiment-smote
# Modify config
git commit -m "experiment: test SMOTE augmentation"
```

### 2. Configuration Backups

```bash
# Backup before changes
cp config/hybrid_config.yaml config/hybrid_config.yaml.backup

# Timestamp backups
cp config/hybrid_config.yaml config/backups/hybrid_config_$(date +%Y%m%d_%H%M%S).yaml
```

### 3. Environment Variables

```bash
# Override config path via environment
export CHAINGUARDIAN_CONFIG=/path/to/custom/config.yaml

# Override specific values
export CHAINGUARDIAN_GPU_ENABLED=true
export CHAINGUARDIAN_BATCH_SIZE=1024
```

### 4. Configuration Testing

```python
# Test configuration changes
from chainguardian.ml.core import get_config

config = get_config("config/hybrid_config.test.yaml")

# Validate new settings
assert config.ensemble.enabled == True
assert config.batch_processing.batch_size == 512

print("✅ Test config passed")
```

### 5. Documentation

```yaml
# Add comments to explain non-obvious settings
batch_processing:
  batch_size: 512  # Optimized for 16GB GPU (Tesla T4)
  max_workers: 8   # Leave 8 cores for OS (64 core system)
```

---

## Configuration Migration

### Upgrading from v1.0.6 to v1.0.7

```yaml
# New in v1.0.7:

# 1. GPU optimization (NEW)
gpu:
  enabled: true
  memory_fraction: 0.8

# 2. Adaptive thresholds (NEW)
thresholds:
  adaptive_thresholds: true

# 3. Progressive augmentation (NEW)
augmentation:
  progressive_augmentation: true
  epochs: 3

# 4. Genetic algorithm weight optimization (CHANGED)
ensemble:
  weight_optimization:
    method: "genetic_algorithm"  # Was: "bayesian"
```

### Migration Script

```python
def migrate_config_v6_to_v7(old_config_path: str, new_config_path: str):
    """Migrate configuration from v1.0.6 to v1.0.7."""
    import yaml

    with open(old_config_path) as f:
        config = yaml.safe_load(f)

    # Add new GPU section
    config['gpu'] = {
        'enabled': True,
        'device_id': 0,
        'memory_fraction': 0.8
    }

    # Update ensemble
    if 'ensemble' in config:
        config['ensemble']['weight_optimization'] = {
            'method': 'genetic_algorithm',
            'population_size': 50,
            'generations': 100
        }

    with open(new_config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"✅ Migrated config: {old_config_path} → {new_config_path}")
```

---

## Additional Resources

- [ML Core Documentation](ml_core_technical_documentation.md) - ConfigManager usage
- [Hybrid Predictor Documentation](hybrid_predictor_technical_documentation.md) - Threshold tuning
- [Monitoring Documentation](monitoring_technical_documentation.md) - Alert configuration
- [YAML Specification](https://yaml.org/spec/) - YAML syntax reference

---

**Document Version:** 1.0
**Last Updated:** 2025-12-29
**Maintainer:** ChainGuardian AI Team
