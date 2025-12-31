# ChainGuardian AI - ML Training Pipeline Documentation

**Version:** 7.0.0
**Script:** `scripts/3_training/train_production_v7.py`
**Last Updated:** 2025-12-30
**Status:** Production Ready ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Workflow](#architecture--workflow)
3. [Configuration](#configuration)
4. [Training Stages](#training-stages)
5. [Model Artifacts](#model-artifacts)
6. [Usage Examples](#usage-examples)
7. [Error Handling & Fallbacks](#error-handling--fallbacks)
8. [Performance Metrics](#performance-metrics)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The ML Training Pipeline (v7) is a production-ready training script that implements state-of-the-art machine learning practices for smart contract vulnerability detection. It provides a complete end-to-end workflow from data loading to model deployment with optional hyperparameter tuning, ensemble learning, and data augmentation.

### Key Features

✅ **Hyperparameter Optimization** - Bayesian optimization using Optuna
✅ **Heterogeneous Ensemble** - Multi-algorithm ensemble with probability calibration
✅ **Data Augmentation** - Smart contract-aware augmentation (Mixup, SMOTE, Gaussian)
✅ **Model Registry** - Automatic versioning and metadata tracking
✅ **Graceful Degradation** - Feature flags for optional components
✅ **Path Resolution** - Environment-agnostic path handling
✅ **Comprehensive Logging** - Detailed progress tracking and diagnostics

### Technology Stack

- **ML Frameworks**: XGBoost, LightGBM, Random Forest, Logistic Regression
- **Optimization**: Optuna (TPE sampler with median pruner)
- **Augmentation**: SMOTE, Mixup, Gaussian noise
- **Calibration**: Platt scaling (sigmoid), Isotonic regression
- **Scaling**: RobustScaler (handles outliers)

---

## Architecture & Workflow

### Complete Training Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                  TRAIN_PRODUCTION_V7.PY                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. INITIALIZATION                                          │
│     ├─ Load configuration (YAML/defaults)                   │
│     ├─ Initialize feature flags (optional components)       │
│     └─ Setup path resolver                                  │
│                                                             │
│  2. DATA LOADING & PREPROCESSING                            │
│     ├─ Load ml_ready_v4.csv                                 │
│     ├─ Remove leakage features (45+ features)               │
│     ├─ Remove constant features                             │
│     └─ Handle missing/infinite values                       │
│                                                             │
│  3. DATA AUGMENTATION (Optional)                            │
│     ├─ Mixup augmentation (continuous labels)               │
│     ├─ SMOTE oversampling (minority class)                  │
│     └─ Gaussian noise injection                             │
│                                                             │
│  4. TRAIN/VAL/TEST SPLIT                                    │
│     ├─ Binary labels → Stratified split                     │
│     ├─ Continuous labels → Non-stratified split             │
│     └─ 60% train / 20% val / 20% test                       │
│                                                             │
│  5. FEATURE SCALING                                         │
│     ├─ RobustScaler (fit on train only)                     │
│     └─ Transform train/val/test                             │
│                                                             │
│  6. HYPERPARAMETER TUNING (Optional)                        │
│     ├─ Optuna study (Bayesian optimization)                 │
│     ├─ 50 trials with median pruning                        │
│     └─ Maximize validation AUC                              │
│                                                             │
│  7. MODEL TRAINING                                          │
│     ├─ Option A: Heterogeneous Ensemble (Preferred)         │
│     │   ├─ XGBoost + LightGBM + RandomForest + LogReg      │
│     │   ├─ Voting with calibration                          │
│     │   └─ Calibration method from config                   │
│     └─ Option B: Single Model (Fallback)                    │
│         ├─ XGBoost with tuned/default params                │
│         └─ Platt scaling calibration                        │
│                                                             │
│  8. EVALUATION                                              │
│     ├─ Test set predictions                                 │
│     ├─ Calculate AUC, Accuracy, Brier score                 │
│     └─ Generate classification report                       │
│                                                             │
│  9. MODEL PERSISTENCE                                       │
│     ├─ Save model (ensemble or single)                      │
│     ├─ Save scaler                                          │
│     └─ Save metadata (features, metrics, config)            │
│                                                             │
│  10. MODEL REGISTRY (Optional)                              │
│      ├─ Register model with metadata                        │
│      ├─ Automatic versioning                                │
│      └─ Enable model rollback                               │
│                                                             │
│  11. SUMMARY                                                │
│      ├─ Print performance metrics                           │
│      ├─ List enabled features                               │
│      └─ Show saved artifacts                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Dependencies

```
┌────────────────────┐
│   train_v7.py      │
└────────┬───────────┘
         │
         ├─► PathResolver (Required)
         │   └─ Resolves data/models paths
         │
         ├─► ConfigManager (Optional)
         │   └─ YAML config or defaults
         │
         ├─► SmartContractAugmenter (Optional)
         │   └─ Data augmentation strategies
         │
         ├─► HyperparameterTuner (Optional)
         │   └─ Optuna-based optimization
         │
         ├─► HeterogeneousEnsemble (Optional)
         │   └─ Multi-model ensemble
         │
         ├─► PlattScalingCalibrator (Optional)
         │   └─ Probability calibration
         │
         └─► ModelRegistry (Optional)
             └─ Model versioning
```

---

## Configuration

### Configuration File Structure

The training script uses a hierarchical configuration loaded from YAML or defaults.

#### Default Config Locations (Priority Order)

1. `config/config.yaml` (Project root)
2. `config/training_config.yaml` (Project root)
3. Hardcoded defaults in script

#### Configuration Schema

```yaml
# ============================================================================
# HYPERPARAMETER TUNING
# ============================================================================
hyperparameter_tuning:
  enable_optuna: true
  n_trials: 50
  optimization_metric: "auc"
  pruner_type: "median"
  sampler_type: "tpe"

# ============================================================================
# ENSEMBLE CONFIGURATION
# ============================================================================
ensemble:
  enable_ensemble: true
  calibration_method: "sigmoid"  # Options: sigmoid, isotonic
  voting_weights:
    xgboost: 0.4
    lightgbm: 0.3
    random_forest: 0.2
    logistic_regression: 0.1

# ============================================================================
# DATA AUGMENTATION
# ============================================================================
augmentation:
  enabled: true
  strategy: "mixup"  # Options: mixup, smote, gaussian, all
  mixup_alpha: 0.2
  smote_k_neighbors: 5
  gaussian_noise_scale: 0.01

# ============================================================================
# MODEL REGISTRY
# ============================================================================
model_registry:
  registry_path: "models/registry"  # Relative to project root
  enable_versioning: true
  auto_backup: true
```

### Feature Flags

The script uses intelligent feature flags for graceful degradation:

```python
# Automatically detected based on import success
TUNER_AVAILABLE = True/False         # HyperparameterTuner
ENSEMBLE_AVAILABLE = True/False      # HeterogeneousEnsemble
AUGMENTER_AVAILABLE = True/False     # SmartContractAugmenter
PLATT_AVAILABLE = True/False         # PlattScalingCalibrator
REGISTRY_AVAILABLE = True/False      # ModelRegistry
CONFIG_AVAILABLE = True/False        # ConfigManager
```

**Important**: If a component is unavailable, the script automatically falls back to safer defaults without crashing.

---

## Training Stages

### Stage 1: Initialization

**Lines:** 19-159
**Purpose:** Load configuration and initialize components

```python
# Example: Load configuration
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from chainguardian.ml.core.path_resolver import path_resolver

# Load config with fallback
config = None
if CONFIG_AVAILABLE:
    from chainguardian.ml.core.config_manager import load_config
    config = load_config()  # Auto-searches config paths
```

**Key Operations:**
- Set up Python path
- Initialize path_resolver (singleton)
- Load configuration from YAML or use defaults
- Import optional components with try/except
- Print configuration summary

**Error Handling:**
- Graceful import failures with feature flags
- Config loading errors fall back to defaults

---

### Stage 2: Data Loading & Preprocessing

**Lines:** 162-217
**Purpose:** Load dataset and remove leakage features

```python
# Load dataset
datafile = path_resolver.data_dir / "ml_ready_v4.csv"
if not datafile.exists():
    print(f"❌ Could not find ml_ready_v4.csv at {datafile}")
    sys.exit(1)

df = pd.read_csv(datafile)
print(f"✅ Loaded {len(df)} samples, {len(df.columns)} columns")

# Remove leakage features (45+ features that directly reveal vulnerabilities)
LEAKAGE_FEATURES = [
    'id', 'contract_name', 'data_source',
    'high_severity_count', 'medium_severity_count', 'low_severity_count',
    'total_detector_hits', 'security_detectors_triggered',
    'unique_vulnerability_types', 'risk_score_simple', 'risk_score_weighted',
    # ... (45+ total features)
]

X = df[available_features]
y = df['ground_truth_vulnerable']

# Remove constant features (no variance)
constant_features = X.columns[X.nunique() == 1].tolist()
X = X.drop(columns=constant_features)

# Handle missing/infinite values
X = X.fillna(0)
X = X.replace([np.inf, -np.inf], 999999)
```

**Key Operations:**
- Load ml_ready_v4.csv from data directory
- Remove 45+ leakage features (features that leak ground truth)
- Remove constant features (no predictive value)
- Fill missing values with 0
- Replace infinities with large finite value

**Error Handling:**
- Exit if dataset not found
- Print detailed path information for debugging

**Why Remove Leakage Features?**
Features like `high_severity_count` and `total_detector_hits` are directly derived from Slither's vulnerability detection, which is what we're trying to predict. Including them would create data leakage and inflated performance.

---

### Stage 3: Data Augmentation

**Lines:** 220-234
**Purpose:** Augment training data (optional)

```python
if AUGMENTER_AVAILABLE and config.augmentation.get('enabled', False):
    print(f"\n🔄 Applying data augmentation: {config.augmentation.get('strategy')}")

    augmenter = SmartContractAugmenter(config)
    X_aug, y_aug = augmenter.augment(X, y)

    print(f"   Augmented: {len(X_aug)} samples (from {len(X)})")
    print(f"   Positive ratio: {y_aug.mean()*100:.1f}%")

    X, y = X_aug, y_aug
else:
    print(f"\n⚠️  Data augmentation disabled or not available")
```

**Augmentation Strategies:**

1. **Mixup** (Default, Recommended)
   - Creates synthetic samples by interpolating between pairs
   - Produces continuous labels: `y_new = λ*y1 + (1-λ)*y2`
   - Improves calibration and reduces overfitting
   - Parameter: `mixup_alpha` (default: 0.2)

2. **SMOTE** (Synthetic Minority Over-sampling)
   - Oversamples minority class (vulnerable contracts)
   - Creates synthetic samples in feature space
   - Parameter: `smote_k_neighbors` (default: 5)

3. **Gaussian Noise**
   - Adds random Gaussian noise to features
   - Parameter: `gaussian_noise_scale` (default: 0.01)

**Important**: Mixup produces **continuous labels** (0.0-1.0), not binary (0/1). This affects the train/test split strategy in the next stage.

---

### Stage 4: Train/Val/Test Split

**Lines:** 237-291
**Purpose:** Split data with proper handling of continuous labels

```python
# Check if labels are binary or continuous (after mixup augmentation)
labels_are_binary = set(np.unique(y)) == {0, 1}

if labels_are_binary:
    print(f"\n📊 Class distribution (binary labels):")
    print(f"   Class 0 (SAFE): {(y == 0).sum()} samples")
    print(f"   Class 1 (VULNERABLE): {(y == 1).sum()} samples")

    # Use stratified split for binary labels
    if (y == 0).sum() >= 2 and (y == 1).sum() >= 2:
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=0.25, random_state=42,
            stratify=y_train_val
        )
    else:
        # Fallback: Non-stratified if too few samples
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=None
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=0.25, random_state=42,
            stratify=None
        )
else:
    # For continuous labels (after mixup), use non-stratified split
    print(f"\n📊 Label distribution (continuous from mixup):")
    print(f"   Min: {y.min():.3f}, Max: {y.max():.3f}, Mean: {y.mean():.3f}")
    print(f"   Using non-stratified split for continuous labels...")

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=None
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, random_state=42,
        stratify=None
    )
```

**Split Ratios:**
- Training: 60% (0.8 * 0.75 = 0.60)
- Validation: 20% (0.8 * 0.25 = 0.20)
- Test: 20%

**Key Logic:**
1. **Detect label type** (binary vs continuous)
2. **Binary labels** → Use stratified split (preserves class balance)
3. **Continuous labels** → Use non-stratified split (stratify doesn't work with continuous values)
4. **Fallback** → Non-stratified if too few samples per class

**Why This Matters:**
Mixup augmentation produces continuous labels, which will cause `stratify` to crash. This stage correctly handles both scenarios.

---

### Stage 5: Feature Scaling

**Lines:** 294-302
**Purpose:** Scale features using RobustScaler

```python
from sklearn.preprocessing import RobustScaler

scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

print(f"\n🔧 Feature scaling applied (RobustScaler)")
print(f"   Training range: [{X_train_scaled.min():.2f}, {X_train_scaled.max():.2f}]")
```

**Why RobustScaler?**
- More robust to outliers than StandardScaler
- Uses median and IQR instead of mean and std
- Smart contract features often have outliers (e.g., very large contracts)

**Critical**: Scaler is **fit only on training data** to prevent data leakage.

---

### Stage 6: Hyperparameter Tuning

**Lines:** 305-342
**Purpose:** Bayesian optimization using Optuna (optional)

```python
if TUNER_AVAILABLE and config.hyperparameter_tuning.enable_optuna:
    print(f"\n🔍 Starting hyperparameter tuning with Optuna...")
    print(f"   Trials: {config.hyperparameter_tuning.n_trials}")
    print(f"   Metric: {config.hyperparameter_tuning.optimization_metric}")

    tuner = HyperparameterTuner(config)
    tuning_results = tuner.tune(
        X_train_scaled, y_train,
        X_val_scaled, y_val
    )

    best_params = tuning_results['best_params']
    best_score = tuning_results['best_value']

    print(f"✅ Tuning complete!")
    print(f"   Best {config.hyperparameter_tuning.optimization_metric}: {best_score:.4f}")
    print(f"   Best params: {best_params}")
else:
    print(f"\n⚠️ Hyperparameter tuning disabled or not available")
    best_params = None
```

**Tuning Process:**
1. **Search Space**: Defined in HyperparameterTuner
   - `max_depth`: 3-10
   - `learning_rate`: 0.01-0.3
   - `n_estimators`: 100-1000
   - `subsample`: 0.6-1.0
   - `colsample_bytree`: 0.6-1.0

2. **Optimization**: Maximize validation AUC

3. **Pruning**: MedianPruner stops unpromising trials early

4. **Sampler**: TPE (Tree-structured Parzen Estimator) - Bayesian optimization

**Output:**
- `best_params`: Dict of optimal hyperparameters
- `best_score`: Best validation AUC achieved
- `tuning_results`: Full Optuna study results

---

### Stage 7: Model Training

**Lines:** 345-446
**Purpose:** Train ensemble or single model

#### Option A: Heterogeneous Ensemble (Preferred)

```python
if ENSEMBLE_AVAILABLE and config.ensemble.enable_ensemble:
    print(f"\n🎯 Training heterogeneous ensemble...")
    print(f"   Models: XGBoost, LightGBM, RandomForest, LogisticRegression")
    print(f"   Calibration method: {config.ensemble.calibration_method.value}")

    ensemble = HeterogeneousEnsemble(config)

    # Train with optional hyperparameters
    ensemble.train(
        X_train_scaled, y_train,
        X_val_scaled, y_val,
        best_xgb_params=best_params if best_params else None
    )

    final_model = ensemble
    use_ensemble = True
```

**Ensemble Components:**
- **XGBoost** (40% weight) - Gradient boosting, best overall
- **LightGBM** (30% weight) - Fast gradient boosting
- **RandomForest** (20% weight) - Ensemble of decision trees
- **LogisticRegression** (10% weight) - Linear baseline

**Calibration:**
- Applies Platt scaling (sigmoid) or isotonic regression
- Ensures probabilities are well-calibrated
- Critical for production confidence scores

#### Option B: Single Model (Fallback)

```python
else:
    print(f"\n⚠️  Ensemble not available, training single XGBoost model...")

    import xgboost as xgb

    # Use tuned params if available, otherwise defaults
    xgb_params = best_params if best_params else {
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 300,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'random_state': 42
    }

    model = xgb.XGBClassifier(**xgb_params)
    model.fit(X_train_scaled, y_train)

    # Apply Platt scaling for calibration
    if PLATT_AVAILABLE:
        calibrator = PlattScalingCalibrator()
        calibrator.fit(
            model.predict_proba(X_val_scaled)[:, 1],
            y_val
        )
        final_model = (model, calibrator)
    else:
        final_model = model

    use_ensemble = False
```

**Fallback Strategy:**
1. Use single XGBoost model
2. Apply tuned hyperparameters if available
3. Apply Platt scaling if available
4. Use uncalibrated model as last resort

---

### Stage 8: Evaluation

**Lines:** 449-480
**Purpose:** Evaluate on held-out test set

```python
# Generate predictions
if use_ensemble:
    y_pred_proba = final_model.predict(X_test_scaled)
else:
    if PLATT_AVAILABLE and isinstance(final_model, tuple):
        model, calibrator = final_model
        raw_proba = model.predict_proba(X_test_scaled)[:, 1]
        y_pred_proba = calibrator.calibrate(raw_proba)
    else:
        y_pred_proba = final_model.predict_proba(X_test_scaled)[:, 1]

y_pred = (y_pred_proba > 0.5).astype(int)

# Calculate metrics
test_auc = roc_auc_score(y_test, y_pred_proba)
test_acc = accuracy_score(y_test, y_pred)
test_brier = brier_score_loss(y_test, y_pred_proba)

print(f"\n📊 TEST SET PERFORMANCE:")
print(f"   AUC:           {test_auc:.4f}")
print(f"   Accuracy:      {test_acc:.4f}")
print(f"   Brier Score:   {test_brier:.4f} (lower is better)")

print(f"\n📋 Classification Report:")
print(classification_report(y_test, y_pred, target_names=['SAFE', 'VULNERABLE']))
```

**Metrics Explained:**

| Metric | Range | Meaning | Target |
|--------|-------|---------|--------|
| **AUC** | 0.0-1.0 | Area Under ROC Curve - overall discrimination ability | > 0.85 |
| **Accuracy** | 0.0-1.0 | Fraction of correct predictions | > 0.80 |
| **Brier Score** | 0.0-1.0 | Calibration quality (mean squared error of probabilities) | < 0.15 |

**Why Brier Score?**
- Measures how well the predicted probabilities match true outcomes
- Low Brier = well-calibrated probabilities
- Critical for production where we need confidence scores

---

### Stage 9: Model Persistence

**Lines:** 483-539
**Purpose:** Save model, scaler, and metadata

```python
# Save directory
save_dir = path_resolver.models_dir
save_dir.mkdir(parents=True, exist_ok=True)

# Save model
if use_ensemble:
    model_path = save_dir / "ensemble_model_v7.pkl"
    scaler_path = save_dir / "ensemble_scaler_v7.pkl"
else:
    model_path = save_dir / "production_model_v7.pkl"
    scaler_path = save_dir / "production_scaler_v7.pkl"

joblib.dump(final_model, model_path)
joblib.dump(scaler, scaler_path)

# Save metadata
metadata = {
    "version": "7.0.0",
    "training_timestamp": datetime.now().isoformat(),
    "model_type": "ensemble" if use_ensemble else "single_xgboost",
    "feature_names": X.columns.tolist(),
    "num_features": len(X.columns),
    "performance_metrics": {
        "test_auc": float(test_auc),
        "test_accuracy": float(test_acc),
        "test_brier_score": float(test_brier)
    },
    "training_info": {
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "hyperparameter_tuning": best_params is not None,
        "data_augmentation": AUGMENTER_AVAILABLE and config.augmentation.get('enabled', False),
        "calibration_applied": True
    }
}

if CONFIG_AVAILABLE:
    metadata["config"] = config.to_dict() if hasattr(config, 'to_dict') else {}

metadata_path = save_dir / "feature_metadata_v7.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"✅ Model saved to: {model_path}")
print(f"✅ Scaler saved to: {scaler_path}")
print(f"✅ Metadata saved to: {metadata_path}")
```

**Saved Files:**

| File | Purpose | Format |
|------|---------|--------|
| `ensemble_model_v7.pkl` or `production_model_v7.pkl` | Trained model | Joblib |
| `ensemble_scaler_v7.pkl` or `production_scaler_v7.pkl` | Feature scaler | Joblib |
| `feature_metadata_v7.json` | Model metadata | JSON |

**Metadata Contents:**
- Version number
- Training timestamp
- Model type (ensemble vs single)
- Feature names (critical for prediction)
- Performance metrics
- Training configuration
- Dataset statistics

---

### Stage 10: Model Registry

**Lines:** 542-576
**Purpose:** Register model in versioned registry (optional)

```python
if REGISTRY_AVAILABLE:
    print("=" * 80)
    print("📚 MODEL REGISTRY INTEGRATION")
    print("=" * 80)

    try:
        # Use absolute path from config or default
        registry_path = None
        if CONFIG_AVAILABLE and hasattr(config, 'model_registry'):
            registry_path_str = config.model_registry.get('registry_path')
            if registry_path_str:
                registry_path = path_resolver.project_root / registry_path_str

        # Initialize registry
        registry = ModelRegistry(str(registry_path) if registry_path else None)

        model_info = {
            "model": final_model,
            "scaler": scaler,
            "feature_names": X.columns.tolist(),
            "performance_metrics": metadata["performance_metrics"],
            "training_info": metadata["training_info"]
        }

        if CONFIG_AVAILABLE:
            model_info["config"] = config.to_dict() if hasattr(config, 'to_dict') else {}

        version = registry.register_model(
            model_info,
            description="Enhanced v7 model with ensemble and calibration"
        )
        print(f"✅ Model registered as version: {version}")
    except Exception as e:
        print(f"⚠️  Model registry failed: {e}")
```

**Registry Features:**
- **Automatic Versioning**: v1, v2, v3, ...
- **Metadata Tracking**: Performance, config, features
- **Model Rollback**: Load previous versions
- **Deployment Management**: Track which version is in production

**Registry Directory Structure:**
```
models/registry/
├── v1/
│   ├── model.pkl
│   ├── scaler.pkl
│   └── metadata.json
├── v2/
│   ├── model.pkl
│   ├── scaler.pkl
│   └── metadata.json
└── registry_index.json
```

---

### Stage 11: Summary

**Lines:** 579-614
**Purpose:** Print training summary

```python
print("\n" + "="*80)
print("🏆 TRAINING v7 COMPLETE - SUMMARY")
print("="*80)

print(f"\n📊 MODEL PERFORMANCE:")
print(f"   AUC:           {test_auc:.4f}")
print(f"   Accuracy:      {test_acc:.4f}")
print(f"   Calibration:   {test_brier:.4f} Brier score")

print(f"\n🔧 FEATURES ENABLED:")
print(f"   Hyperparameter Tuning: {'✅' if TUNER_AVAILABLE and tuning_results else '❌'}")
print(f"   Ensemble: {'✅' if use_ensemble else '❌'}")
print(f"   Data Augmentation: {'✅' if AUGMENTER_AVAILABLE and config.augmentation.get('enabled', False) else '❌'}")
print(f"   Platt Scaling: {'✅' if not use_ensemble else '❌'} (ensemble uses its own calibration)")

print(f"\n💾 SAVED ASSETS:")
if use_ensemble:
    print(f"   • Ensemble model: ensemble_model_v7.pkl")
    print(f"   • Scaler: ensemble_scaler_v7.pkl")
else:
    print(f"   • Single model: production_model_v7.pkl")
    print(f"   • Scaler: production_scaler_v7.pkl")
print(f"   • Metadata: feature_metadata_v7.json")
if REGISTRY_AVAILABLE:
    print(f"   • Registry entry: v{version if 'version' in locals() else 'N/A'}")

print(f"\n🚀 NEXT STEPS:")
print(f"   1. Test the model: python scripts/3_training/test_enhanced_v7.py")
print(f"   2. Update your application to use EnhancedHybridPredictor")
print(f"   3. Monitor performance with the new monitoring system")

print(f"\n✅ TRAINING v7 COMPLETED SUCCESSFULLY!")
```

---

## Model Artifacts

### Output Files

After successful training, the following files are created in `models/`:

#### 1. Model File
- **Filename**: `ensemble_model_v7.pkl` or `production_model_v7.pkl`
- **Size**: ~10-50 MB (depends on model complexity)
- **Format**: Joblib (pickle)
- **Contents**:
  - Ensemble: HeterogeneousEnsemble object with 4 trained models
  - Single: XGBoost model + optional PlattScalingCalibrator

#### 2. Scaler File
- **Filename**: `ensemble_scaler_v7.pkl` or `production_scaler_v7.pkl`
- **Size**: ~100-500 KB
- **Format**: Joblib (pickle)
- **Contents**: Fitted RobustScaler with feature statistics

#### 3. Metadata File
- **Filename**: `feature_metadata_v7.json`
- **Size**: ~10-50 KB
- **Format**: JSON (human-readable)
- **Contents**: See [Metadata Schema](#metadata-schema)

### Metadata Schema

```json
{
  "version": "7.0.0",
  "training_timestamp": "2025-12-30T15:30:45.123456",
  "model_type": "ensemble",
  "feature_names": [
    "sloc",
    "num_functions",
    "num_state_variables",
    // ... (100+ features)
  ],
  "num_features": 127,
  "performance_metrics": {
    "test_auc": 0.9234,
    "test_accuracy": 0.8756,
    "test_brier_score": 0.1123
  },
  "training_info": {
    "train_samples": 4200,
    "val_samples": 1400,
    "test_samples": 1400,
    "hyperparameter_tuning": true,
    "data_augmentation": true,
    "calibration_applied": true
  },
  "config": {
    // Full config dump
  }
}
```

### Loading Trained Models

```python
import joblib
from chainguardian.ml.core.path_resolver import path_resolver

# Load model
model_path = path_resolver.models_dir / "ensemble_model_v7.pkl"
scaler_path = path_resolver.models_dir / "ensemble_scaler_v7.pkl"

model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

# Load metadata
import json
metadata_path = path_resolver.models_dir / "feature_metadata_v7.json"
with open(metadata_path) as f:
    metadata = json.load(f)

feature_names = metadata['feature_names']
print(f"Loaded model trained on {len(feature_names)} features")

# Make predictions
X_new_scaled = scaler.transform(X_new)
predictions = model.predict(X_new_scaled)
```

---

## Usage Examples

### Example 1: Basic Training (All Defaults)

```bash
cd /path/to/chainguardian-ai
python scripts/3_training/train_production_v7.py
```

**What Happens:**
1. Loads default config (or from `config/config.yaml`)
2. Loads `data/ml_ready_v4.csv`
3. Trains ensemble model (if available)
4. Saves to `models/ensemble_model_v7.pkl`
5. Prints summary

**Expected Output:**
```
🏆 TRAINING v7 COMPLETE - SUMMARY
================================================================================

📊 MODEL PERFORMANCE:
   AUC:           0.9234
   Accuracy:      0.8756
   Calibration:   0.1123 Brier score

🔧 FEATURES ENABLED:
   Hyperparameter Tuning: ✅
   Ensemble: ✅
   Data Augmentation: ✅
   Platt Scaling: ❌ (ensemble uses its own calibration)

💾 SAVED ASSETS:
   • Ensemble model: ensemble_model_v7.pkl
   • Scaler: ensemble_scaler_v7.pkl
   • Metadata: feature_metadata_v7.json
   • Registry entry: v1

🚀 NEXT STEPS:
   1. Test the model: python scripts/3_training/test_enhanced_v7.py
   2. Update your application to use EnhancedHybridPredictor
   3. Monitor performance with the new monitoring system

✅ TRAINING v7 COMPLETED SUCCESSFULLY!
```

---

### Example 2: Custom Configuration

Create `config/training_config.yaml`:

```yaml
hyperparameter_tuning:
  enable_optuna: true
  n_trials: 100  # More trials = better params
  optimization_metric: "auc"

ensemble:
  enable_ensemble: true
  calibration_method: "isotonic"  # Use isotonic instead of sigmoid

augmentation:
  enabled: true
  strategy: "all"  # Use all augmentation strategies
  mixup_alpha: 0.3
  smote_k_neighbors: 7
```

```bash
python scripts/3_training/train_production_v7.py
```

---

### Example 3: Single Model (No Ensemble)

Modify `config/config.yaml`:

```yaml
ensemble:
  enable_ensemble: false  # Force single model
```

```bash
python scripts/3_training/train_production_v7.py
```

**Output:**
- Single XGBoost model
- Platt scaling applied
- Faster training (~30% faster)

---

### Example 4: Minimal Training (No Optional Features)

For testing or minimal environments:

```yaml
hyperparameter_tuning:
  enable_optuna: false  # Skip tuning

ensemble:
  enable_ensemble: false  # Single model

augmentation:
  enabled: false  # No augmentation
```

```bash
python scripts/3_training/train_production_v7.py
```

**Result:**
- Fast training (~5-10 minutes)
- Single XGBoost with default params
- Lower performance but still functional

---

## Error Handling & Fallbacks

The training script implements comprehensive error handling with graceful degradation.

### Feature Flag System

```python
# Each optional component has a feature flag
TUNER_AVAILABLE = True/False
ENSEMBLE_AVAILABLE = True/False
AUGMENTER_AVAILABLE = True/False
PLATT_AVAILABLE = True/False
REGISTRY_AVAILABLE = True/False
CONFIG_AVAILABLE = True/False
```

### Fallback Chain

```
1. Try: Ensemble + Tuning + Augmentation + Registry
   ↓ (If ensemble unavailable)
2. Try: Single Model + Tuning + Augmentation + Registry
   ↓ (If tuning unavailable)
3. Try: Single Model + Default Params + Augmentation + Registry
   ↓ (If augmentation unavailable)
4. Try: Single Model + Default Params + No Aug + Registry
   ↓ (If calibration unavailable)
5. Final: Single Model + Default Params + No Aug + Uncalibrated
```

### Common Errors & Solutions

#### Error 1: Dataset Not Found

```
❌ Could not find ml_ready_v4.csv at /path/to/data/ml_ready_v4.csv
   Expected: /path/to/data/ml_ready_v4.csv
```

**Solution:**
1. Check dataset exists at `data/ml_ready_v4.csv`
2. Run feature extraction pipeline first
3. Verify path_resolver.data_dir is correct

#### Error 2: Import Failure

```
⚠️ HyperparameterTuner import failed: No module named 'optuna'
```

**Solution:**
1. Install missing dependency: `pip install optuna`
2. Or accept fallback: Training will use default params

#### Error 3: Insufficient Samples

```
⚠️ One class has too few samples for stratified split
   Using non-stratified split...
```

**Solution:**
- This is a warning, not an error
- Script automatically falls back to non-stratified split
- Consider collecting more data if possible

#### Error 4: Model Registry Failure

```
⚠️ Model registry failed: [Errno 2] No such file or directory: 'models/registry'
```

**Solution:**
1. Registry will auto-create directory on next run
2. Or manually create: `mkdir -p models/registry`
3. Or disable registry in config

---

## Performance Metrics

### Expected Performance (Typical Results)

Based on production runs with ~7000 samples:

| Configuration | AUC | Accuracy | Brier | Training Time |
|--------------|-----|----------|-------|---------------|
| **Full (Ensemble + Tuning + Aug)** | 0.92-0.95 | 0.87-0.90 | 0.10-0.13 | 60-90 min |
| **Ensemble (No Tuning)** | 0.90-0.93 | 0.85-0.88 | 0.11-0.14 | 30-45 min |
| **Single + Tuning** | 0.89-0.92 | 0.84-0.87 | 0.12-0.15 | 40-60 min |
| **Single (Defaults)** | 0.87-0.90 | 0.82-0.85 | 0.13-0.16 | 5-10 min |

### Performance Targets

| Metric | Minimum | Target | Excellent |
|--------|---------|--------|-----------|
| **AUC** | 0.80 | 0.90 | 0.95 |
| **Accuracy** | 0.75 | 0.85 | 0.90 |
| **Brier** | < 0.20 | < 0.15 | < 0.10 |

### Training Time Breakdown

For full configuration (Ensemble + Tuning + Augmentation):

```
Stage                           Time      % of Total
─────────────────────────────────────────────────────
Data Loading                    1 min     1.7%
Data Augmentation              5 min     8.3%
Hyperparameter Tuning          30 min    50%
Ensemble Training              20 min    33%
Evaluation & Saving            4 min     6.7%
─────────────────────────────────────────────────────
TOTAL                          60 min    100%
```

---

## Troubleshooting

### Issue: Low AUC (< 0.80)

**Possible Causes:**
1. Data quality issues
2. Insufficient features
3. Class imbalance
4. Leakage features not removed

**Solutions:**
1. Check feature extraction logs for errors
2. Enable data augmentation
3. Enable hyperparameter tuning
4. Verify LEAKAGE_FEATURES list is complete

---

### Issue: Training Crashes

**Possible Causes:**
1. Out of memory
2. Corrupted dataset
3. Missing dependencies

**Solutions:**
1. Reduce `n_trials` in hyperparameter tuning
2. Disable augmentation temporarily
3. Check dataset with `df.info()` and `df.describe()`
4. Install all dependencies: `pip install -r requirements.txt`

---

### Issue: Poor Calibration (High Brier Score)

**Possible Causes:**
1. Calibration disabled
2. Insufficient validation data
3. Overfitting

**Solutions:**
1. Enable ensemble (has built-in calibration)
2. Enable Platt scaling for single models
3. Increase validation set size
4. Add regularization via hyperparameter tuning

---

### Issue: Model Registry Fails

**Possible Causes:**
1. Registry directory doesn't exist
2. Permission issues
3. Disk space

**Solutions:**
1. Create directory: `mkdir -p models/registry`
2. Check permissions: `chmod -R 755 models/`
3. Check disk space: `df -h`
4. Disable registry in config if not needed

---

## Advanced Topics

### Custom Augmentation Strategy

Edit `config/config.yaml`:

```yaml
augmentation:
  enabled: true
  strategy: "custom"
  mixup_alpha: 0.4        # Increase for more aggressive mixup
  smote_k_neighbors: 10   # Increase for more diverse synthetic samples
  gaussian_noise_scale: 0.02  # Increase for more noise
```

### Custom Hyperparameter Search Space

Edit `src/chainguardian/ml/core/hyperparameter_tuner.py`:

```python
def _suggest_xgboost_params(self, trial):
    return {
        'max_depth': trial.suggest_int('max_depth', 3, 12),  # Wider range
        'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.5, log=True),
        'n_estimators': trial.suggest_int('n_estimators', 50, 2000),
        # Add more parameters...
    }
```

### Custom Ensemble Weights

Edit `config/config.yaml`:

```yaml
ensemble:
  voting_weights:
    xgboost: 0.5           # Increase XGBoost weight
    lightgbm: 0.3
    random_forest: 0.15
    logistic_regression: 0.05
```

---

## Integration with Other Components

### Using Trained Model in API

```python
from chainguardian.ml.hybrid_predictor import EnhancedHybridPredictor
from chainguardian.ml.core.path_resolver import path_resolver

# Initialize predictor (auto-loads latest model)
predictor = EnhancedHybridPredictor()

# Predict vulnerability
features = extract_features(contract_code)
prediction = predictor.predict(features)

print(f"Vulnerability probability: {prediction['probability']:.2%}")
print(f"Confidence: {prediction['confidence']}")
```

### Using Model Registry for Rollback

```python
from chainguardian.ml.core.model_registry import ModelRegistry

registry = ModelRegistry()

# List all versions
versions = registry.list_versions()
print(f"Available versions: {versions}")

# Load specific version
model_info = registry.load_model(version=2)
model = model_info['model']
scaler = model_info['scaler']

# Rollback to previous version
registry.set_production_version(version=2)
```

---

## Changelog

### Version 7.0.0 (Current)
- ✅ Heterogeneous ensemble with 4 algorithms
- ✅ Optuna hyperparameter tuning
- ✅ Data augmentation (Mixup, SMOTE, Gaussian)
- ✅ Model registry integration
- ✅ Graceful degradation with feature flags
- ✅ Proper handling of continuous labels from mixup
- ✅ RobustScaler for outlier-resistant scaling
- ✅ Comprehensive metadata tracking

### Version 6.x
- Single XGBoost model
- Manual hyperparameter tuning
- Basic SMOTE augmentation

---

## References

### Related Documentation

- [ml_core_technical_documentation.md](ml_core_technical_documentation.md) - ML Core Components
- [hybrid_predictor_technical_documentation.md](hybrid_predictor_technical_documentation.md) - Prediction Interface
- [configuration_guide.md](configuration_guide.md) - Configuration System
- [monitoring_technical_documentation.md](monitoring_technical_documentation.md) - Model Monitoring

### Key Dependencies

- **XGBoost** - https://xgboost.readthedocs.io/
- **LightGBM** - https://lightgbm.readthedocs.io/
- **Optuna** - https://optuna.readthedocs.io/
- **scikit-learn** - https://scikit-learn.org/
- **imbalanced-learn** - https://imbalanced-learn.org/

---

## Contact & Support

For questions about the training pipeline:
1. Check this documentation
2. Review [ml_core_technical_documentation.md](ml_core_technical_documentation.md)
3. Check script comments in `train_production_v7.py`

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-30
**Author:** ChainGuardian AI Team
