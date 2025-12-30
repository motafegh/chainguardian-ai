# ChainGuardian AI - ML Core Module Technical Documentation

**Version:** 2.0.0
**Last Updated:** 2025-12-29
**Module Path:** `src/chainguardian/ml/core`

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Module Components](#module-components)
4. [API Reference](#api-reference)
5. [Configuration](#configuration)
6. [Usage Examples](#usage-examples)
7. [Development Guidelines](#development-guidelines)

---

## Overview

The ChainGuardian AI ML Core module provides a comprehensive, production-ready machine learning pipeline for smart contract vulnerability detection. It implements state-of-the-art MLOps practices including hyperparameter optimization, ensemble learning, model versioning, performance monitoring, and data augmentation.

### Key Features

- **Hyperparameter Optimization**: Bayesian optimization using Optuna with intelligent pruning
- **Heterogeneous Ensemble**: Multi-algorithm ensemble with probability calibration
- **Data Augmentation**: Smart contract-aware augmentation strategies (Mixup, Gaussian, SMOTE)
- **Model Registry**: Version control and deployment management for ML models
- **Performance Monitoring**: Real-time drift detection and performance tracking
- **Path Resolution**: Centralized path management for multi-environment deployments

### Technology Stack

- **ML Frameworks**: XGBoost, LightGBM, Random Forest, Logistic Regression
- **Optimization**: Optuna (Bayesian optimization with TPE sampler)
- **Calibration**: Platt scaling (sigmoid) and isotonic regression
- **Monitoring**: Statistical drift detection (Kolmogorov-Smirnov test)
- **Serialization**: Joblib, JSON, YAML

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                 ChainGuardian AI ML Core                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────┐    ┌──────────────────┐            │
│  │ ConfigManager │◄───│  PathResolver    │            │
│  │               │    │  (Singleton)     │            │
│  └───────┬───────┘    └──────────────────┘            │
│          │                                             │
│  ┌───────▼───────────────────────────────────────┐    │
│  │                                               │    │
│  │  ┌─────────────────┐  ┌──────────────────┐  │    │
│  │  │ Hyperparameter  │  │ Heterogeneous    │  │    │
│  │  │ Tuner (Optuna)  │  │ Ensemble         │  │    │
│  │  └─────────────────┘  └──────────────────┘  │    │
│  │                                               │    │
│  │  ┌─────────────────┐  ┌──────────────────┐  │    │
│  │  │ Data Augmenter  │  │ Model Registry   │  │    │
│  │  │ (SMOTE/Mixup)   │  │ (Versioning)     │  │    │
│  │  └─────────────────┘  └──────────────────┘  │    │
│  │                                               │    │
│  │  ┌─────────────────┐                         │    │
│  │  │ ML Monitor      │                         │    │
│  │  │ (Drift Detection)                         │    │
│  │  └─────────────────┘                         │    │
│  │                                               │    │
│  └───────────────────────────────────────────────┘    │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Data Flow

```
Input Features
    ↓
SmartContractAugmenter (optional)
    ↓
HyperparameterTuner
    ↓
HeterogeneousEnsemble
    ├─ XGBoost (calibrated)
    ├─ Random Forest (calibrated)
    ├─ LightGBM (calibrated)
    └─ Logistic Regression (calibrated)
    ↓
VotingClassifier (weighted soft voting)
    ↓
MLMonitor (drift detection & logging)
    ↓
ModelRegistry (version control)
    ↓
Predictions + Metadata
```

---

## Module Components

### 1. ConfigManager ([config_manager.py](../src/chainguardian/ml/core/config_manager.py))

**Purpose**: Centralized configuration management with type safety and validation.

#### Features
- Type-safe dataclass-based configuration
- YAML configuration loading with fallbacks
- Automatic path resolution
- Validation and normalization
- Enum-based configuration values

#### Key Classes

##### `CalibrationMethod` (Enum)
```python
class CalibrationMethod(Enum):
    SIGMOID = "sigmoid"
    ISOTONIC = "isotonic"
    NONE = "none"
```

##### `Config` (Dataclass)
Main configuration container with sections:
- `hyperparameter_tuning`: Optuna optimization settings
- `ensemble`: Ensemble configuration and weights
- `augmentation`: Data augmentation parameters
- `monitoring`: Drift detection and logging settings
- `model_registry`: Model versioning configuration

#### Usage Example
```python
from chainguardian.ml.core import ConfigManager, get_config

# Load configuration
config_manager = ConfigManager()
config = config_manager.load_config("config/hybrid_config.yaml")

# Access configuration
n_trials = config.hyperparameter_tuning.n_trials
calibration_method = config.ensemble.calibration_method
```

#### Configuration Schema
```yaml
hyperparameter_tuning:
  enable_optuna: true
  n_trials: 50
  timeout_seconds: 3600
  study_name: "chainguardian_optimization"
  search_spaces:
    xgboost:
      n_estimators: [100, 300]
      max_depth: [3, 8]
      learning_rate: [0.01, 0.2]

ensemble:
  enabled: true
  voting_method: "soft"
  calibration_method: "sigmoid"
  initial_weights:
    xgboost: 0.4
    random_forest: 0.3
    lightgbm: 0.2
    logistic_regression: 0.1
  uncertainty:
    enable_bootstrap: false
    n_bootstrap_samples: 100
    confidence_level: 0.95
```

---

### 2. PathResolver ([path_resolver.py](../src/chainguardian/ml/core/path_resolver.py))

**Purpose**: Centralized path management using absolute paths anchored to project root.

#### Features
- Automatic project root detection
- Singleton pattern for consistency
- Cross-environment compatibility (Poetry, Docker, local)
- Directory auto-creation

#### Key Properties
```python
path_resolver.project_root      # Root directory with pyproject.toml
path_resolver.config_dir        # config/
path_resolver.models_dir        # config/models/
path_resolver.registry_dir      # config/models/registry/
path_resolver.logs_dir          # config/logs/
path_resolver.data_dir          # data/
```

#### Usage Example
```python
from chainguardian.ml.core.path_resolver import path_resolver

# Get absolute path to config file
config_path = path_resolver.get_config_file("hybrid_config.yaml")

# Resolve custom path
data_path = path_resolver.resolve("data/contracts/training.csv")

# Get directories
model_save_path = path_resolver.models_dir / "model_v1.pkl"
```

#### Implementation Details
- Searches for `pyproject.toml` from current file up to filesystem root
- Handles both absolute and relative paths
- Creates directories on-demand
- Thread-safe singleton implementation

---

### 3. HyperparameterTuner ([hyperparameter_tuner.py](../src/chainguardian/ml/core/hyperparameter_tuner.py))

**Purpose**: Bayesian hyperparameter optimization using Optuna.

#### Features
- Multi-algorithm optimization (XGBoost, Random Forest, LightGBM)
- Tree-structured Parzen Estimator (TPE) sampling
- Median pruning for early stopping
- Nested cross-validation
- Parameter importance analysis

#### Key Methods

##### `optimize(X, y, n_trials=None)`
Runs Bayesian optimization to find best hyperparameters.

**Parameters:**
- `X` (np.ndarray): Feature matrix (shape: [n_samples, n_features])
- `y` (np.ndarray): Target labels (shape: [n_samples])
- `n_trials` (int, optional): Number of optimization trials (default: from config)

**Returns:**
- `dict`: Results including best_params, best_score, study object, trials dataframe

**Example:**
```python
tuner = HyperparameterTuner(config, feature_names)
results = tuner.optimize(X_train, y_train, n_trials=100)

print(f"Best AUC: {results['best_score']:.4f}")
print(f"Best model: {results['best_params']['model_type']}")
```

##### `get_best_model(X, y)`
Trains and returns the best model found during optimization.

**Returns:**
- Fitted model with optimal hyperparameters

#### Optimization Strategy

1. **Search Space Definition**: Configurable per-algorithm search spaces
2. **Objective Function**: Maximize ROC AUC via stratified K-fold CV
3. **Pruning**: MedianPruner removes unpromising trials early
4. **Sampling**: TPE (Tree-structured Parzen Estimator) for efficient search

#### Algorithm Search Spaces

**XGBoost:**
- `n_estimators`: [100, 300]
- `max_depth`: [3, 8]
- `learning_rate`: [0.01, 0.2] (log scale)
- `subsample`: [0.6, 1.0]
- `colsample_bytree`: [0.6, 1.0]
- `gamma`: [0, 5]
- `reg_alpha`: [0, 10]
- `reg_lambda`: [1, 10]

**Random Forest:**
- `n_estimators`: [100, 300]
- `max_depth`: [5, 15]
- `min_samples_split`: [2, 10]
- `min_samples_leaf`: [1, 4]

**LightGBM:**
- `n_estimators`: [100, 300]
- `num_leaves`: [20, 100]
- `learning_rate`: [0.01, 0.2] (log scale)
- `feature_fraction`: [0.6, 1.0]
- `bagging_fraction`: [0.6, 1.0]

---

### 4. HeterogeneousEnsemble ([heterogeneous_ensemble.py](../src/chainguardian/ml/core/heterogeneous_ensemble.py))

**Purpose**: Advanced ensemble combining multiple algorithms with calibration and uncertainty estimation.

#### Features
- Multi-algorithm ensemble (XGBoost, RF, LightGBM, Logistic Regression)
- Platt scaling (sigmoid) calibration for improved probability estimates
- Bootstrap-based uncertainty quantification
- Dynamic weight optimization
- Weighted soft voting

#### Key Methods

##### `fit(X, y, sample_weight=None)`
Trains the ensemble with calibration.

**Process:**
1. Train individual models
2. Calibrate each model using CalibratedClassifierCV
3. Create weighted voting ensemble
4. Fit voting classifier

##### `predict_proba(X)`
Returns calibrated probabilities with uncertainty estimates.

**Returns:**
- `tuple`: (probabilities, uncertainties)

##### `predict_with_uncertainty(X, threshold=0.5)`
Makes predictions with confidence intervals.

**Returns:**
- `tuple`: (predictions, probabilities, confidence_intervals)

**Example:**
```python
ensemble = HeterogeneousEnsemble(config, feature_names)
ensemble.fit(X_train, y_train)

predictions, probas, confidence = ensemble.predict_with_uncertainty(X_test)

for i in range(len(predictions)):
    print(f"Prediction: {predictions[i]}, "
          f"Probability: {probas[i][1]:.3f}, "
          f"CI: [{confidence[i][0]:.3f}, {confidence[i][1]:.3f}]")
```

##### `optimize_weights(X_val, y_val)`
Optimizes ensemble weights on validation data using gradient-based optimization.

**Objective:** Maximize ROC AUC
**Method:** L-BFGS-B optimization with bounds [0, 1]

#### Calibration Methods

**Platt Scaling (Sigmoid):**
- Fits a logistic regression on model outputs
- Better for small datasets
- Assumes sigmoid-shaped calibration curve

**Isotonic Regression:**
- Non-parametric calibration
- More flexible but requires more data
- Better for large datasets

#### Model Contributions

```python
contributions = ensemble.get_model_contributions(X_test)

# contributions = {
#     'xgboost': array([0.35, 0.42, ...]),
#     'random_forest': array([0.28, 0.31, ...]),
#     'lightgbm': array([0.18, 0.22, ...]),
#     'logistic_regression': array([0.09, 0.05, ...])
# }
```

---

### 5. SmartContractAugmenter ([data_augmenter.py](../src/chainguardian/ml/core/data_augmenter.py))

**Purpose**: Domain-aware data augmentation for smart contract features.

#### Features
- Multiple augmentation strategies
- Domain-specific augmentation rules
- Validation and quality checks
- Configurable augmentation factors

#### Augmentation Strategies

##### 1. Mixup
Creates convex combinations of samples.

**Formula:** `x_new = λ * x_i + (1 - λ) * x_j`

**Parameters:**
- `mixup_alpha`: Beta distribution parameter (default: 0.2)
- `max_augmentation_factor`: Maximum dataset expansion (default: 2.0)

**Use Case:** Small datasets with limited samples

##### 2. Gaussian Noise
Adds controlled noise to continuous features only.

**Parameters:**
- `gaussian_std`: Noise standard deviation relative to feature std (default: 0.05)

**Use Case:** Robustness testing and regularization

##### 3. SMOTE (Synthetic Minority Over-sampling)
Generates synthetic samples using k-nearest neighbors.

**Parameters:**
- `max_augmentation_factor`: Target dataset size multiplier
- `k_neighbors`: Number of neighbors (default: 5)

**Use Case:** Class imbalance correction

#### Usage Example

```python
augmenter = SmartContractAugmenter(config)

# Apply SMOTE augmentation
X_aug, y_aug = augmenter.augment(X_train, y_train, strategy='smote')

# Validate augmentation quality
validation = augmenter.validate_augmentation(
    X_train, X_aug, y_train, y_aug
)

print(f"Samples added: {validation['samples_added']}")
print(f"Validation passed: {validation['validation_passed']}")
```

#### Augmentation Validation

The augmenter validates that:
1. Feature means remain similar (< 10% change)
2. No extreme outliers introduced (99th percentile check)
3. Class balance is preserved or improved

---

### 6. ModelRegistry ([model_registry.py](../src/chainguardian/ml/core/model_registry.py))

**Purpose**: Version control, tracking, and deployment management for ML models.

#### Features
- Semantic versioning (major.minor.patch)
- Comprehensive metadata storage
- Model comparison and rollback
- Environment-based deployment (staging, production)
- Performance tracking
- Automated cleanup

#### Key Methods

##### `register_model(model_info, version=None, description="")`
Registers a new model version.

**model_info structure:**
```python
{
    'model': trained_model,
    'scaler': fitted_scaler,
    'feature_names': ['feature1', 'feature2', ...],
    'config': training_config_dict,
    'performance_metrics': {
        'auc': 0.95,
        'accuracy': 0.92,
        'precision': 0.91,
        'recall': 0.93
    },
    'training_info': {
        'date': '2025-12-29',
        'training_samples': 1000,
        'validation_samples': 200
    },
    'hyperparameters': {...}
}
```

**Returns:** Version string (e.g., "1.0.0")

##### `get_model(version=None)`
Retrieves a model version (latest if version=None).

**Returns:**
```python
{
    'model': loaded_model,
    'scaler': loaded_scaler,
    'metadata': {...},
    'version': '1.0.0',
    'path': '/path/to/version'
}
```

##### `compare_models(version1, version2)`
Compares two model versions.

**Returns:**
```python
{
    'versions': ['1.0.0', '1.1.0'],
    'performance_comparison': {
        'auc': {
            '1.0.0': 0.93,
            '1.1.0': 0.95,
            'difference': 0.02
        }
    },
    'feature_differences': ['Added 5 features'],
    'training_differences': ['training_samples: 800 → 1000']
}
```

##### `promote_model(version, environment='production')`
Promotes a model to an environment.

##### `rollback_model(environment='production', target_version=None)`
Rolls back to a previous version.

##### `cleanup_old_versions(keep_last_n=10)`
Removes old versions to save disk space.

#### Model Storage Structure

```
config/models/registry/
├── index.json                 # Registry index
├── v1.0.0/
│   ├── model.pkl             # Serialized model
│   ├── scaler.pkl            # Serialized scaler
│   └── metadata.json         # Full metadata
├── v1.1.0/
│   ├── model.pkl
│   ├── scaler.pkl
│   └── metadata.json
├── production/               # Production deployment
│   ├── model.pkl
│   ├── scaler.pkl
│   ├── metadata.json
│   └── environment.json
└── staging/                  # Staging deployment
    └── ...
```

#### Usage Example

```python
registry = ModelRegistry()

# Register new model
version = registry.register_model(
    model_info=model_dict,
    description="Improved ensemble with optimized weights"
)

# List all models
models = registry.list_models(detailed=True)

# Compare versions
comparison = registry.compare_models('1.0.0', '1.1.0')

# Promote to production
registry.promote_model(version, environment='production')

# Rollback if needed
registry.rollback_model(environment='production')
```

---

### 7. MLMonitor ([monitoring.py](../src/chainguardian/ml/core/monitoring.py))

**Purpose**: Real-time performance monitoring and drift detection.

#### Features
- Prediction logging with metadata
- Statistical drift detection (Kolmogorov-Smirnov test)
- Performance degradation alerts
- Calibration monitoring
- Exportable monitoring reports

#### Key Methods

##### `log_prediction(features, prediction, ground_truth=None)`
Logs a prediction for monitoring.

**Parameters:**
- `features` (dict): Input features
- `prediction` (dict): Prediction output
- `ground_truth` (bool, optional): Actual label

**Example:**
```python
monitor = MLMonitor(config)

prediction_result = {
    'prediction': True,
    'calibrated_confidence': 0.87,
    'data_quality': {'quality_score': 0.95},
    'processing_time_ms': 12.3
}

monitor.log_prediction(
    features=contract_features,
    prediction=prediction_result,
    ground_truth=True
)
```

##### `get_performance_report(window_size=100)`
Generates performance report for recent predictions.

**Returns:**
```python
{
    'window_size': 100,
    'time_period': {
        'start': '2025-12-29T10:00:00',
        'end': '2025-12-29T12:00:00'
    },
    'accuracy': 0.92,
    'average_confidence': 0.85,
    'calibration_error': 0.07,
    'average_data_quality': 0.93,
    'calibration_data': [...],
    'drift_detected': False,
    'performance_baseline': {...}
}
```

##### `export_monitoring_data(output_path=None)`
Exports monitoring data for analysis.

#### Drift Detection

**Method:** Kolmogorov-Smirnov (KS) Test

**Process:**
1. Establish reference distribution from initial predictions
2. Periodically compare current distribution to reference
3. Trigger alert if drift score > threshold

**Monitored Features:**
- `has_reentrancy`
- `has_unchecked_call`
- `num_external_calls`
- `cei_violations`
- `lines_of_code`
- `num_functions`
- `cfg_num_nodes`
- `dfg_num_sensitive_sinks`

**Configuration:**
```yaml
monitoring:
  drift_detection:
    enabled: true
    window_size: 1000
    check_interval: 100
    drift_threshold: 0.05
  log_dir: "logs"
```

#### Performance Degradation Detection

Monitors accuracy degradation:
- Establishes baseline from first 100 predictions with ground truth
- Alerts if recent accuracy drops > 10% from baseline

#### Alert System

Alerts are saved to monthly log files:
```
logs/alerts_2025-12.jsonl
```

Alert structure:
```json
{
  "type": "data_drift",
  "timestamp": "2025-12-29T14:30:00",
  "severity": "warning",
  "details": {
    "drift_score": 0.08,
    "samples_analyzed": 1000
  }
}
```

---

## API Reference

### Quick Start

```python
from chainguardian.ml.core import (
    ConfigManager,
    HyperparameterTuner,
    HeterogeneousEnsemble,
    SmartContractAugmenter,
    ModelRegistry,
    MLMonitor
)

# 1. Load configuration
config_manager = ConfigManager()
config = config_manager.load_config()

# 2. Augment data (optional)
augmenter = SmartContractAugmenter(config)
X_aug, y_aug = augmenter.augment(X_train, y_train, strategy='smote')

# 3. Optimize hyperparameters
tuner = HyperparameterTuner(config, feature_names)
results = tuner.optimize(X_aug, y_aug, n_trials=50)

# 4. Train ensemble
ensemble = HeterogeneousEnsemble(config, feature_names)
ensemble.fit(X_aug, y_aug)

# 5. Optimize ensemble weights
ensemble.optimize_weights(X_val, y_val)

# 6. Register model
registry = ModelRegistry()
version = registry.register_model({
    'model': ensemble,
    'scaler': scaler,
    'feature_names': feature_names,
    'config': config.to_dict(),
    'performance_metrics': metrics,
    'training_info': training_info
})

# 7. Setup monitoring
monitor = MLMonitor(config)

# 8. Make predictions with monitoring
predictions, probas, confidence = ensemble.predict_with_uncertainty(X_test)
for i, pred in enumerate(predictions):
    monitor.log_prediction(
        features=X_test[i],
        prediction={'prediction': pred, 'confidence': probas[i][1]},
        ground_truth=y_test[i] if available else None
    )
```

---

## Configuration

### Complete Configuration Example

```yaml
# config/hybrid_config.yaml

hyperparameter_tuning:
  enable_optuna: true
  n_trials: 50
  timeout_seconds: 3600
  study_name: "chainguardian_optimization"

  search_spaces:
    xgboost:
      n_estimators: [100, 300]
      max_depth: [3, 8]
      learning_rate: [0.01, 0.2]
      subsample: [0.6, 1.0]
      colsample_bytree: [0.6, 1.0]
      gamma: [0, 5]
      reg_alpha: [0, 10]
      reg_lambda: [1, 10]

    random_forest:
      n_estimators: [100, 300]
      max_depth: [5, 15]
      min_samples_split: [2, 10]
      min_samples_leaf: [1, 4]

    lightgbm:
      n_estimators: [100, 300]
      num_leaves: [20, 100]
      learning_rate: [0.01, 0.2]
      feature_fraction: [0.6, 1.0]

ensemble:
  enabled: true
  voting_method: "soft"
  calibration_method: "sigmoid"

  initial_weights:
    xgboost: 0.4
    random_forest: 0.3
    lightgbm: 0.2
    logistic_regression: 0.1

  uncertainty:
    enable_bootstrap: true
    n_bootstrap_samples: 100
    confidence_level: 0.95

augmentation:
  enabled: true
  strategy: "smote"
  max_augmentation_factor: 2.0
  mixup_alpha: 0.2
  gaussian_std: 0.05

model_registry:
  registry_path: "config/models/registry"
  auto_cleanup: true
  keep_last_n_versions: 10

monitoring:
  log_dir: "logs"

  drift_detection:
    enabled: true
    window_size: 1000
    check_interval: 100
    drift_threshold: 0.05

  performance_tracking:
    enabled: true
    baseline_samples: 100
    degradation_threshold: 0.1

thresholds:
  classification_threshold: 0.5
  confidence_threshold: 0.7
  data_quality_threshold: 0.8
```

---

## Usage Examples

### Example 1: Complete Training Pipeline

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from chainguardian.ml.core import *

# Load data
df = pd.read_csv('data/smart_contracts.csv')
X = df.drop('is_vulnerable', axis=1)
y = df['is_vulnerable']
feature_names = list(X.columns)

# Split data
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Load config
config_manager = ConfigManager()
config = config_manager.load_config()

# Augment training data
augmenter = SmartContractAugmenter(config)
X_aug, y_aug = augmenter.augment(
    pd.DataFrame(X_train_scaled, columns=feature_names),
    pd.Series(y_train),
    strategy='smote'
)

# Hyperparameter optimization
tuner = HyperparameterTuner(config, feature_names)
tuning_results = tuner.optimize(X_aug.values, y_aug.values, n_trials=100)
print(f"Best model: {tuning_results['best_params']['model_type']}")
print(f"Best AUC: {tuning_results['best_score']:.4f}")

# Train ensemble
ensemble = HeterogeneousEnsemble(config, feature_names)
ensemble.fit(X_aug.values, y_aug.values)

# Optimize weights on validation set
optimized_weights = ensemble.optimize_weights(X_val_scaled, y_val)
print(f"Optimized weights: {optimized_weights}")

# Evaluate on test set
predictions, probas, confidence = ensemble.predict_with_uncertainty(X_test_scaled)

# Calculate metrics
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
print(f"Test Accuracy: {accuracy_score(y_test, predictions):.4f}")
print(f"Test AUC: {roc_auc_score(y_test, probas[:, 1]):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, predictions))

# Register model
registry = ModelRegistry()
version = registry.register_model(
    model_info={
        'model': ensemble,
        'scaler': scaler,
        'feature_names': feature_names,
        'config': config.to_dict(),
        'performance_metrics': {
            'auc': roc_auc_score(y_test, probas[:, 1]),
            'accuracy': accuracy_score(y_test, predictions)
        },
        'training_info': {
            'date': '2025-12-29',
            'training_samples': len(X_aug),
            'validation_samples': len(X_val),
            'test_samples': len(X_test)
        }
    },
    description="SMOTE-augmented ensemble with optimized weights"
)
print(f"Model registered as version: {version}")
```

### Example 2: Model Deployment and Monitoring

```python
from chainguardian.ml.core import ModelRegistry, MLMonitor

# Load production model
registry = ModelRegistry()
production_model = registry.get_model()  # Gets latest version

model = production_model['model']
scaler = production_model['scaler']
feature_names = production_model['metadata']['feature_names']

# Setup monitoring
monitor = MLMonitor(config)

# Production inference
def predict_contract(contract_features):
    """Predict vulnerability with monitoring."""
    # Scale features
    features_scaled = scaler.transform([contract_features])

    # Predict
    pred, proba, conf_interval = model.predict_with_uncertainty(features_scaled)

    # Create prediction result
    result = {
        'prediction': bool(pred[0]),
        'calibrated_confidence': float(proba[0][1]),
        'confidence_interval': conf_interval[0].tolist(),
        'data_quality': {'quality_score': 0.95},  # From data quality check
        'processing_time_ms': 15.2
    }

    # Log to monitor
    monitor.log_prediction(
        features=dict(zip(feature_names, contract_features)),
        prediction=result,
        ground_truth=None  # Update when feedback available
    )

    return result

# Use in production
contract_data = [...]  # Contract features
prediction_result = predict_contract(contract_data)
print(f"Vulnerable: {prediction_result['prediction']}")
print(f"Confidence: {prediction_result['calibrated_confidence']:.2%}")

# Generate monitoring report
report = monitor.get_performance_report(window_size=1000)
print(f"Drift detected: {report['drift_detected']}")
print(f"Average confidence: {report['average_confidence']:.3f}")
```

### Example 3: Model Comparison and Rollback

```python
from chainguardian.ml.core import ModelRegistry

registry = ModelRegistry()

# List all models
models = registry.list_models(detailed=True)
for model_info in models:
    print(f"Version: {model_info['version']}")
    print(f"  AUC: {model_info['performance'].get('auc', 'N/A')}")
    print(f"  Timestamp: {model_info['timestamp']}")
    print()

# Compare two versions
comparison = registry.compare_models('1.0.0', '1.1.0')
print("Performance Comparison:")
for metric, values in comparison['performance_comparison'].items():
    print(f"  {metric}: {values}")

# Promote new version to staging
registry.promote_model('1.1.0', environment='staging')

# After validation, promote to production
registry.promote_model('1.1.0', environment='production')

# If issues arise, rollback
registry.rollback_model(environment='production', target_version='1.0.0')

# Cleanup old versions
removed = registry.cleanup_old_versions(keep_last_n=5)
print(f"Removed versions: {removed}")
```

---

## Development Guidelines

### Adding a New Algorithm to Ensemble

1. Add search space to configuration:
```yaml
hyperparameter_tuning:
  search_spaces:
    new_algorithm:
      param1: [min, max]
      param2: [min, max]
```

2. Add parameter extraction method in `HyperparameterTuner`:
```python
def _get_new_algorithm_params(self, trial: optuna.Trial) -> Dict[str, Any]:
    search_space = self.config.hyperparameter_tuning.search_spaces.get('new_algorithm', {})
    return {
        'param1': trial.suggest_int('new_param1', ...),
        'param2': trial.suggest_float('new_param2', ...)
    }
```

3. Add model to ensemble in `HeterogeneousEnsemble._train_individual_models()`:
```python
from new_package import NewAlgorithm

new_model = NewAlgorithm(**params)
new_model.fit(X, y, sample_weight=sample_weight)
self.models['new_algorithm']['model'] = new_model
```

### Adding a New Augmentation Strategy

1. Add strategy to configuration:
```yaml
augmentation:
  strategy: "new_strategy"
  new_strategy_param: value
```

2. Implement method in `SmartContractAugmenter`:
```python
def _new_strategy_augmentation(self, X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
    """Implement new augmentation strategy."""
    # Implementation
    return X_augmented, y_augmented
```

3. Add to `augment()` method:
```python
elif strategy == 'new_strategy':
    return self._new_strategy_augmentation(X, y)
```

### Testing Guidelines

```python
import pytest
from chainguardian.ml.core import *

def test_config_loading():
    """Test configuration loading."""
    config_manager = ConfigManager()
    config = config_manager.load_config()
    assert config.hyperparameter_tuning.n_trials > 0

def test_ensemble_training():
    """Test ensemble training."""
    X = np.random.rand(100, 10)
    y = np.random.randint(0, 2, 100)

    ensemble = HeterogeneousEnsemble(config, feature_names)
    ensemble.fit(X, y)

    assert ensemble.is_fitted
    predictions, uncertainties = ensemble.predict_proba(X)
    assert len(predictions) == len(X)

def test_model_registry():
    """Test model registration and retrieval."""
    registry = ModelRegistry()

    # Register model
    version = registry.register_model(model_info)
    assert version is not None

    # Retrieve model
    loaded = registry.get_model(version)
    assert loaded['version'] == version
```

### Performance Optimization Tips

1. **Hyperparameter Tuning:**
   - Use `n_jobs=-1` for parallel CV
   - Enable pruning to stop unpromising trials early
   - Start with fewer trials and increase gradually

2. **Ensemble Training:**
   - Use `n_jobs=-1` in all estimators
   - Consider disabling uncertainty estimation in production for speed
   - Cache calibrated models

3. **Monitoring:**
   - Batch log predictions instead of one-by-one
   - Use async logging for high-throughput scenarios
   - Periodically export and clear logs

4. **Model Registry:**
   - Enable auto-cleanup to manage disk space
   - Use symlinks instead of copies for large models
   - Compress old versions

---

## Troubleshooting

### Common Issues

**Issue:** Configuration not found
```
Solution: Ensure pyproject.toml exists in project root
Check: path_resolver.project_root
```

**Issue:** Optuna optimization very slow
```
Solution:
- Reduce n_trials
- Enable pruning
- Use fewer CV folds
- Reduce search space
```

**Issue:** Ensemble predictions inconsistent
```
Solution:
- Ensure models are calibrated
- Check ensemble weights sum to 1.0
- Verify all models are fitted
```

**Issue:** Drift detection too sensitive
```
Solution:
- Increase drift_threshold
- Increase window_size
- Adjust check_interval
```

**Issue:** Model registry paths not found
```
Solution:
- Verify path_resolver.registry_dir exists
- Check absolute vs relative paths
- Ensure proper permissions
```

---

## Additional Resources

- [Optuna Documentation](https://optuna.readthedocs.io/)
- [Scikit-learn Calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [SMOTE Paper](https://arxiv.org/abs/1106.1813)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-29
**Maintainer:** ChainGuardian AI Team
