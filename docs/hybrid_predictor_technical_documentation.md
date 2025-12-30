# ChainGuardian AI - Hybrid Predictor Technical Documentation

**Version:** 2.0 (Enhanced)
**Last Updated:** 2025-12-29
**Module Path:** `src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py`

**Related Documentation:**

- [ML Core Technical Documentation](ml_core_technical_documentation.md)
- [API Technical Documentation](api_technical_documentation.md)
- [Monitoring Technical Documentation](monitoring_technical_documentation.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Prediction Pipeline](#prediction-pipeline)
5. [API Reference](#api-reference)
6. [Configuration](#configuration)
7. [Performance Optimization](#performance-optimization)
8. [Usage Examples](#usage-examples)
9. [Advanced Features](#advanced-features)

---

## Overview

The Enhanced Hybrid Predictor V2 is the **core inference engine** for ChainGuardian AI. It combines **ML ensemble predictions** with **semantic rule-based analysis** to achieve industry-leading vulnerability detection accuracy.

### Key Features

**V2 Enhancements:**

1. **YAML Configuration Support**: All parameters configurable via external YAML
2. **Ensemble Integration**: Supports heterogeneous ensemble models (XGBoost, RF, LightGBM, LogReg)
3. **Batch Prediction**: Vectorized batch processing for high throughput
4. **Bootstrap Uncertainty**: True uncertainty quantification via confidence intervals
5. **Monitoring Hooks**: Integration with MLMonitor for drift detection
6. **Performance Optimization**: LRU caching, warmup, vectorization

**Core Capabilities:**

- **Hybrid Scoring**: Combines ML probabilities with semantic risk analysis
- **Dynamic Weighting**: Adjusts ML vs semantic weights based on data quality
- **Confidence Calibration**: Multi-factor confidence adjustment
- **SHAP Explanations**: Model interpretability via SHAP values
- **Data Quality Assessment**: Validates feature completeness and quality

### Performance Metrics

- **Test AUC**: 99.78%
- **Prediction Latency**: 66ms (single), 15ms (batch avg)
- **Calibration**: Brier score 0.0146
- **Feature Count**: 89 features

---

## Architecture

### Hybrid Prediction Architecture

```
┌─────────────────────────────────────────────────────────────┐
│        EnhancedHybridPredictorV2 (Main Class)               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Initialization                                      │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  1. Load Config (YAML)                    │     │  │
│  │  │  2. Load Model (Ensemble or Single)       │     │  │
│  │  │  3. Load Scaler (StandardScaler)          │     │  │
│  │  │  4. Load Feature Metadata                 │     │  │
│  │  │  5. Initialize SHAP Explainer (optional)  │     │  │
│  │  │  6. Initialize ML Monitor (optional)      │     │  │
│  │  │  7. Warmup Prediction                     │     │  │
│  │  └────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Single Prediction Flow (predict_single)            │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  INPUT: Feature Dictionary (89 features)  │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  1. Assess Data Completeness               │     │  │
│  │  │     • Source code availability             │     │  │
│  │  │     • Semantic analysis completeness       │     │  │
│  │  │     • Static analysis completeness         │     │  │
│  │  │     • Graph features availability          │     │  │
│  │  │     → DataQualityLevel (EXCELLENT-POOR)    │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  2. Feature Extraction & Scaling           │     │  │
│  │  │     • Convert dict → numpy array (cached)  │     │  │
│  │  │     • Apply StandardScaler                 │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  3. ML Prediction                          │     │  │
│  │  │     if ensemble:                           │     │  │
│  │  │       • predict_with_uncertainty()         │     │  │
│  │  │       • Returns: pred, proba, CI           │     │  │
│  │  │     else:                                  │     │  │
│  │  │       • predict_proba()                    │     │  │
│  │  │       • Returns: proba only                │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  4. Semantic Risk Calculation              │     │  │
│  │  │     • CEI violations analysis              │     │  │
│  │  │     • Static vulnerability checks          │     │  │
│  │  │     • Reentrancy guard detection           │     │  │
│  │  │     → semantic_score + reasons             │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  5. Dynamic Weight Calculation             │     │  │
│  │  │     Based on DataQualityLevel:             │     │  │
│  │  │     • EXCELLENT → (0.8 ML, 0.2 semantic)   │     │  │
│  │  │     • GOOD      → (0.7 ML, 0.3 semantic)   │     │  │
│  │  │     • FAIR      → (0.6 ML, 0.4 semantic)   │     │  │
│  │  │     • POOR      → (0.5 ML, 0.5 semantic)   │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  6. Hybrid Score Computation               │     │  │
│  │  │     final_score =                          │     │  │
│  │  │       (ml_weight × ml_proba) +             │     │  │
│  │  │       (semantic_weight × semantic_score)   │     │  │
│  │  │     prediction = 1 if final > threshold    │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  7. Confidence Calibration                 │     │  │
│  │  │     • ML certainty alignment boost         │     │  │
│  │  │     • Static signal boost                  │     │  │
│  │  │     • Data quality multiplier              │     │  │
│  │  │     • Contradiction penalty                │     │  │
│  │  │     → calibrated_confidence                │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  8. SHAP Explanation (optional)            │     │  │
│  │  │     • Calculate SHAP values                │     │  │
│  │  │     • Rank features by importance          │     │  │
│  │  │     • Return top-k contributors            │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  9. Monitoring & Logging                   │     │  │
│  │  │     • Log to MLMonitor                     │     │  │
│  │  │     • Track processing time                │     │  │
│  │  └──────────┬─────────────────────────────────┘     │  │
│  │             ▼                                        │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │  OUTPUT: Prediction Dictionary             │     │  │
│  │  └────────────────────────────────────────────┘     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Batch Prediction Flow (predict_batch)              │  │
│  │  • Vectorized feature extraction                    │  │
│  │  • Batch ML inference                               │  │
│  │  • Parallel semantic analysis                       │  │
│  │  • 10x faster than sequential                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Data Quality Assessment

**Class:** `DataCompletenessMetrics`
**Location:** [Line 63](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L63)

```python
@dataclass
class DataCompletenessMetrics:
    source_code_available: bool = False
    semantic_analysis_complete: bool = False
    static_analysis_complete: bool = False
    graph_features_available: bool = False
    cei_analysis_quality: float = 0.0
```

**Purpose**: Assesses the completeness and quality of input features to determine confidence.

**Quality Score Calculation:**

```python
score = (
    0.3 × source_code_available +
    0.3 × semantic_analysis_complete +
    0.2 × static_analysis_complete +
    0.1 × graph_features_available +
    0.1 × cei_analysis_quality
)
```

**Quality Levels:**

| Score Range | Quality Level | ML Weight | Semantic Weight |
| ----------- | ------------- | --------- | --------------- |
| ≥ 0.9 | EXCELLENT | 0.8 | 0.2 |
| 0.7 - 0.9 | GOOD | 0.7 | 0.3 |
| 0.5 - 0.7 | FAIR | 0.6 | 0.4 |
| 0.3 - 0.5 | POOR | 0.5 | 0.5 |
| < 0.3 | UNKNOWN | 0.5 | 0.5 |

---

### 2. Confidence Levels

**Enum:** `ConfidenceLevel`
**Location:** [Line 55](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L55)

```python
class ConfidenceLevel(Enum):
    VERY_HIGH = "VERY_HIGH"  # ≥ 0.9
    HIGH = "HIGH"            # 0.7 - 0.9
    MODERATE = "MODERATE"    # 0.5 - 0.7
    LOW = "LOW"              # 0.3 - 0.5
    VERY_LOW = "VERY_LOW"    # < 0.3
```

**Usage in Results:**

```python
result = {
    'calibrated_confidence': 0.92,
    'confidence_level': 'VERY_HIGH'
}
```

---

### 3. Model Loading

**Method:** `_load_models()`
**Location:** [Line 251](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L251)

**Supported Model Types:**

1. **Ensemble Model** (preferred):
   - Path: `config/models/ensemble_model_v7.pkl`
   - Contains: HeterogeneousEnsemble with 4 base models
   - Features: Uncertainty quantification, calibrated probabilities

2. **Single Model** (fallback):
   - Path: `config/models/production_model_v7.pkl`
   - Contains: Single XGBoost classifier
   - Features: Standard predictions without uncertainty

**Auto-detection Logic:**

```python
if ensemble_path.exists():
    self.use_ensemble = True
    # Load with uncertainty support
elif single_path.exists():
    self.use_ensemble = False
    # Load standard model
else:
    # Fallback to v6
```

---

### 4. Feature Caching

**Method:** `_get_feature_vector()`
**Location:** [Line 337](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L337)

**Implementation:**

```python
@lru_cache(maxsize=1000)
def _get_feature_vector(self, features: Dict) -> np.ndarray:
    """Convert features dict to numpy array with caching."""
    feature_vector = np.zeros(len(self.feature_names))

    for i, feature_name in enumerate(self.feature_names):
        feature_vector[i] = features.get(feature_name, 0)

    return feature_vector
```

**Benefits:**
- **Cache Hit Rate**: ~80% in typical workloads
- **Speedup**: 3-5x for repeated similar contracts
- **Memory**: ~100KB for 1000 cached vectors

---

### 5. Warmup Prediction

**Method:** `_warmup_prediction()`
**Location:** [Line 201](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L201)

**Purpose**: Eliminate cold start latency by warming up JIT compilation and caches.

**Process:**

```python
1. Create dummy features (all zeros)
2. Run fast path prediction (no details)
3. Run full path prediction (with calibration)
4. Run cached path (verify caching works)
5. Report warmup times
```

**Typical Warmup Times:**
- Fast path: ~50ms
- Full path: ~100ms
- Cached path: ~15ms
- Total: ~165ms (one-time cost at startup)

---

## Prediction Pipeline

### Single Prediction Flow

**Method:** `predict_single(features, return_details=True, explain=True)`
**Location:** [Line 381](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L381)

**Step-by-Step Breakdown:**

#### Step 1: Data Quality Assessment

```python
data_completeness = self.assess_data_completeness(features)
data_quality = data_completeness.get_quality_level()
```

**Checks:**
- Source code presence
- Semantic analysis (CEI) completeness
- Static analysis (Slither) completeness
- Graph features (CFG, DFG, CG) availability

#### Step 2: Feature Extraction

```python
feature_vector = self._get_feature_vector(frozenset(features.items()))
X_scaled = self.scaler.transform(feature_vector.reshape(1, -1))
```

**Process:**
- Convert dict to ordered numpy array (89 features)
- Apply StandardScaler (zero mean, unit variance)
- Use LRU cache for repeated contracts

#### Step 3: ML Prediction

```python
if self.use_ensemble:
    ml_prediction, ml_proba, ml_ci = self.ml_model.predict_with_uncertainty(X_scaled)
    ml_uncertainty = ml_ci[0, 1] - ml_ci[0, 0]
else:
    ml_proba = self.ml_model.predict_proba(X_scaled)[0, 1]
    ml_uncertainty = 0.0
```

**Ensemble Prediction:**
- Returns probability + confidence interval
- Uncertainty = CI width (higher = more uncertain)

**Single Model:**
- Returns probability only
- No uncertainty quantification

#### Step 4: Semantic Risk Calculation

```python
semantic_score, semantic_reasons, metadata = self.calculate_semantic_risk(features)
```

**Risk Components:**

| Component | Weight | Condition |
| --------- | ------ | --------- |
| CEI Violations | 0.4 | cei_violations > 0 |
| Low CEI Score | 0.2 | cei_pattern_score < 0.8 |
| State After Call | 0.3 | state_after_call_count > 0 |
| Unchecked Critical Calls | 0.2 | unchecked_calls_in_critical_context > 0 |
| Reentrancy Guard | -0.5 | has_reentrancy_guard = True |

**Example Semantic Reasons:**

```python
[
    "🚨 CEI violations: 3 (+24% risk)",
    "⚠️ Low CEI score: 0.65 (+7% risk)",
    "✅ Reentrancy guard detected (-50% risk)"
]
```

#### Step 5: Dynamic Weight Calculation

```python
ml_weight, semantic_weight = self.calculate_dynamic_weights(data_quality)
```

**Weight Profiles:**

```yaml
EXCELLENT:
  ml: 0.8
  semantic: 0.2

GOOD:
  ml: 0.7
  semantic: 0.3

FAIR:
  ml: 0.6
  semantic: 0.4

POOR:
  ml: 0.5
  semantic: 0.5
```

**Rationale:**
- High-quality data → Trust ML more
- Low-quality data → Rely on semantic rules

#### Step 6: Hybrid Scoring

```python
final_score = (ml_weight × ml_proba) + (semantic_weight × semantic_score)
prediction = 1 if final_score > threshold else 0
```

**Example:**

```python
# EXCELLENT quality data
ml_proba = 0.95
semantic_score = 0.30
ml_weight = 0.8
semantic_weight = 0.2

final_score = (0.8 × 0.95) + (0.2 × 0.30) = 0.76 + 0.06 = 0.82
prediction = 1  # VULNERABLE
```

#### Step 7: Confidence Calibration

```python
calibrated_confidence, notes = self.calibrate_confidence(
    ml_proba, semantic_score, features, data_completeness
)
```

**Calibration Factors:**

| Factor | Condition | Adjustment |
| ------ | --------- | ---------- |
| ML Certainty Alignment | ml > 0.9 AND static_risk > 0.7 | +0.4 (boost) |
| Moderate ML Boost | ml > 0.6 AND static_risk > 0.5 | +0.25 (boost) |
| Static Signal Boost | static_risk > 0.7 AND ml > 0.4 | +0.15 (boost) |
| Data Quality Multiplier | quality > 0.8 | ×1.3 (multiply) |
| Data Quality Penalty | quality < 0.4 | ×quality (reduce) |
| Contradiction Penalty | Conflicting signals | -0.2 (reduce) |

**Example Calibration:**

```python
base_confidence = (0.95 + 0.30) / 2 = 0.625

# Apply boosts
+ ML certainty alignment: +0.4 → 1.025 (capped at 1.0)
+ Data quality multiplier: ×1.3 → 1.0
- No contradictions

calibrated_confidence = 1.0
notes = [
    "⬆️ High confidence: ML certainty aligns with strong static signals",
    "⬆️ High data quality increases confidence"
]
```

#### Step 8: SHAP Explanation (Optional)

```python
if explain and self.shap_explainer is not None:
    result['shap_explanation'] = self.explain_with_shap(X_scaled)
```

**Returns:**

```python
{
    'top_features': [
        {
            'feature': 'has_reentrancy',
            'value': 1.0,
            'shap_value': 0.42,
            'abs_shap': 0.42
        },
        {
            'feature': 'cei_violations',
            'value': 3.0,
            'shap_value': 0.38,
            'abs_shap': 0.38
        }
    ],
    'base_value': 0.15
}
```

#### Step 9: Result Compilation

```python
result = {
    'prediction': 1,
    'prediction_label': 'VULNERABLE',
    'raw_score': 0.82,
    'calibrated_confidence': 0.92,
    'confidence_level': 'VERY_HIGH',
    'ml_score': 0.95,
    'semantic_score': 0.30,
    'ml_uncertainty': 0.05,
    'weights_applied': {
        'ml_weight': 0.8,
        'semantic_weight': 0.2
    },
    'data_quality': {
        'quality_score': 0.95,
        'quality_level': 'EXCELLENT'
    },
    'semantic_reasons': [...],
    'calibration_notes': [...],
    'processing_time_ms': 66
}
```

---

### Batch Prediction Flow

**Method:** `predict_batch(features_list, max_workers=4, return_details=True)`
**Location:** [Line 458](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L458)

**Optimization Strategies:**

#### 1. Vectorized Processing (Default)

**Method:** `_process_batch_vectorized()`
**Location:** [Line 494](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L494)

**Process:**

```python
1. Extract features in batch → [batch_size, 89] matrix
2. ML prediction in batch → [batch_size] probabilities
3. Semantic analysis pre-computation → cached for reuse
4. Fast path if return_details=False
5. Full path with calibration if return_details=True
```

**Performance:**
- **Throughput**: ~60 predictions/second
- **Latency**: ~15ms per prediction (in batch)
- **Speedup**: 4-5x vs sequential

#### 2. Parallel Processing (Alternative)

**Method:** `_process_batch_parallel()`
**Location:** [Line 580](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L580)

**Process:**

```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(predict_single, f) for f in batch]
    results = [f.result() for f in futures]
```

**Use Case:** When vectorization is not possible (different feature sets)

---

## API Reference

### EnhancedHybridPredictorV2

**Constructor:**

```python
def __init__(
    self,
    model_path: str = None,
    scaler_path: str = None,
    metadata_path: str = None,
    enable_shap: bool = True,
    models_dir: str = None,
    config_path: str = None,
    enable_monitoring: bool = True
):
```

**Parameters:**

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `model_path` | str | None | Path to model file (auto-detect if None) |
| `scaler_path` | str | None | Path to scaler file (auto-detect if None) |
| `metadata_path` | str | None | Path to feature metadata JSON |
| `enable_shap` | bool | True | Enable SHAP explanations |
| `models_dir` | str | None | Directory containing models |
| `config_path` | str | None | Path to YAML config file |
| `enable_monitoring` | bool | True | Enable MLMonitor integration |

**Example:**

```python
predictor = EnhancedHybridPredictorV2(
    models_dir="config/models",
    enable_shap=True,
    enable_monitoring=True
)
```

---

### predict_single()

**Signature:**

```python
def predict_single(
    self,
    features: Dict,
    return_details: bool = True,
    explain: bool = True
) -> Dict:
```

**Parameters:**

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `features` | Dict | Required | Feature dictionary (89 keys) |
| `return_details` | bool | True | Return detailed metrics and calibration |
| `explain` | bool | True | Include SHAP explanations |

**Returns:**

```python
{
    # Prediction
    'prediction': int,              # 0 (SAFE) or 1 (VULNERABLE)
    'prediction_label': str,        # "SAFE" or "VULNERABLE"
    'raw_score': float,             # 0.0 - 1.0
    'calibrated_confidence': float, # 0.0 - 1.0
    'confidence_level': str,        # "VERY_HIGH", "HIGH", etc.

    # Component Scores
    'ml_score': float,              # ML model probability
    'semantic_score': float,        # Semantic risk score
    'ml_uncertainty': float,        # Confidence interval width

    # Weights
    'weights_applied': {
        'ml_weight': float,
        'semantic_weight': float
    },

    # Data Quality
    'data_quality': {
        'quality_score': float,
        'quality_level': str
    },

    # Explanations
    'semantic_reasons': List[str],
    'calibration_notes': List[str],
    'shap_explanation': Dict,       # If explain=True

    # Metadata
    'processing_time_ms': float
}
```

**Example:**

```python
features = {
    'has_reentrancy': 1,
    'cei_violations': 3,
    'num_external_calls': 5,
    # ... 86 more features
}

result = predictor.predict_single(features, return_details=True, explain=True)

print(f"Prediction: {result['prediction_label']}")
print(f"Confidence: {result['calibrated_confidence']:.2%}")
print(f"Processing Time: {result['processing_time_ms']:.1f}ms")
```

---

### predict_batch()

**Signature:**

```python
def predict_batch(
    self,
    features_list: List[Dict],
    max_workers: int = None,
    return_details: bool = True
) -> List[Dict]:
```

**Parameters:**

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `features_list` | List[Dict] | Required | List of feature dictionaries |
| `max_workers` | int | 4 | Max parallel workers (if not vectorized) |
| `return_details` | bool | True | Return detailed metrics |

**Returns:** List of prediction dictionaries (same format as predict_single)

**Example:**

```python
contracts = [
    {'has_reentrancy': 1, 'cei_violations': 3, ...},
    {'has_reentrancy': 0, 'cei_violations': 0, ...},
    # ... more contracts
]

results = predictor.predict_batch(contracts, return_details=False)

for i, result in enumerate(results):
    print(f"Contract {i}: {result['prediction_label']} ({result['confidence']:.2%})")
```

---

## Configuration

### YAML Configuration

**File:** `config/hybrid_config.yaml`

**Relevant Sections:**

```yaml
# Thresholds
thresholds:
  vulnerability_prediction: 0.2  # Hybrid score threshold
  confidence_threshold: 0.7
  data_quality_threshold: 0.8

# Dynamic Weights
weights:
  data_quality_profiles:
    EXCELLENT:
      ml: 0.8
      semantic: 0.2
    GOOD:
      ml: 0.7
      semantic: 0.3
    FAIR:
      ml: 0.6
      semantic: 0.4
    POOR:
      ml: 0.5
      semantic: 0.5
    UNKNOWN:
      ml: 0.5
      semantic: 0.5

  # Semantic Risk Weights
  semantic_risk:
    cei_violation: 0.4
    cei_score_low: 0.2
    state_after_call: 0.3
    unchecked_critical: 0.2
    reentrancy_guard_bonus: -0.5

  # Confidence Calibration
  confidence_calibration:
    ml_certainty_alignment: 0.4
    moderate_ml_boost: 0.25
    static_signal_boost: 0.15
    data_quality_multiplier: 1.3
    contradiction_penalty: -0.2

# Batch Processing
batch_processing:
  batch_size: 32
  max_workers: 4
  enable_vectorization: true
```

---

## Performance Optimization

### 1. Feature Vector Caching

**Implementation:**

```python
@lru_cache(maxsize=1000)
def _get_feature_vector(self, features: Dict) -> np.ndarray:
    # Convert to frozenset for hashability
    # Cache hit = instant return
```

**Benefits:**
- **Cache Hit Rate**: 70-90% in production
- **Speedup**: 3-5x for similar contracts
- **Memory Overhead**: Minimal (~100KB)

---

### 2. Batch Vectorization

**Implementation:**

```python
# Instead of:
for features in batch:
    pred = model.predict(features)  # Slow

# Use:
X_batch = np.vstack([extract(f) for f in batch])
preds = model.predict(X_batch)  # Fast
```

**Benefits:**
- **Throughput**: 60 predictions/sec vs 12/sec
- **Latency**: 15ms per prediction vs 80ms
- **Speedup**: 5x for batches > 10

---

### 3. Warmup Prediction

**Purpose:** Pre-compile JIT code and warm caches

**Implementation:**

```python
# At startup
predictor._warmup_prediction()

# First user request now served from hot cache
# Eliminates 200ms+ cold start
```

---

### 4. Conditional Processing

**Fast Path (return_details=False):**

```python
# Skip calibration, SHAP, detailed metrics
# Return only: prediction, probability, confidence
# Latency: ~30ms vs ~66ms
```

**Use Case:** High-throughput batch processing where details aren't needed

---

### 5. Pre-computed Semantic Analysis

**In Batch Mode:**

```python
# Pre-compute semantic scores for ALL samples
semantic_data = [calc_semantic(f) for f in batch]

# Reuse in loop (no recalculation)
for i in range(len(batch)):
    semantic_score = semantic_data[i]['score']  # Cached!
```

**Benefits:**
- Avoid duplicate calculation
- 2x faster batch processing

---

## Usage Examples

### Example 1: Basic Prediction

```python
from chainguardian.ml.models.hybrid_predictor_enhanced_v2 import EnhancedHybridPredictorV2

# Initialize
predictor = EnhancedHybridPredictorV2(
    models_dir="config/models",
    enable_shap=True
)

# Create features
features = {
    'has_reentrancy': 1,
    'cei_violations': 3,
    'num_external_calls': 5,
    'has_reentrancy_guard': 0,
    'lines_of_code': 150,
    # ... 84 more features
}

# Predict
result = predictor.predict_single(features)

print(f"Prediction: {result['prediction_label']}")
print(f"Confidence: {result['calibrated_confidence']:.2%}")
print(f"ML Score: {result['ml_score']:.3f}")
print(f"Semantic Score: {result['semantic_score']:.3f}")
print(f"Quality: {result['data_quality']['quality_level']}")

print("\nReasons:")
for reason in result['semantic_reasons']:
    print(f"  {reason}")

print("\nTop SHAP Features:")
for feat in result['shap_explanation']['top_features'][:5]:
    print(f"  {feat['feature']}: {feat['shap_value']:.3f}")
```

---

### Example 2: Batch Processing

```python
# Load multiple contracts
contracts = [
    extract_features(contract1),
    extract_features(contract2),
    extract_features(contract3),
    # ... more contracts
]

# Batch predict (vectorized)
results = predictor.predict_batch(
    contracts,
    return_details=False  # Fast path
)

# Process results
vulnerable_count = sum(1 for r in results if r['prediction'] == 1)
avg_confidence = sum(r['confidence'] for r in results) / len(results)

print(f"Analyzed {len(contracts)} contracts")
print(f"Vulnerable: {vulnerable_count} ({vulnerable_count/len(contracts):.1%})")
print(f"Average Confidence: {avg_confidence:.2%}")
```

---

### Example 3: Integration with API

```python
from chainguardian.api.dependencies.model_loader import get_predictor
from chainguardian.feature_extraction.pipeline import FeaturePipeline

# In API endpoint
@router.post("/api/v1/analyze")
async def analyze_contract(request: ContractAnalysisRequest):
    # Get cached predictor
    predictor = get_predictor()

    # Extract features
    pipeline = FeaturePipeline()
    features = pipeline.analyze_contract(
        contract_path=temp_path,
        contract_name=request.contract_name
    )

    # Predict with hybrid predictor
    result = predictor.predict_single(
        features=features,
        return_details=True,
        explain=request.include_explanations
    )

    # Convert to API response
    return ContractAnalysisResponse(
        is_safe=(result['prediction'] == 0),
        risk_score=result['raw_score'],
        confidence=result['calibrated_confidence'],
        vulnerabilities=convert_semantic_reasons(result['semantic_reasons']),
        ...
    )
```

---

## Advanced Features

### 1. Uncertainty Quantification

**Ensemble Models Only:**

```python
# Ensemble returns confidence intervals
predictions, probabilities, confidence_intervals = ensemble.predict_with_uncertainty(X)

# Uncertainty = CI width
ml_uncertainty = confidence_intervals[0, 1] - confidence_intervals[0, 0]

# Use in decision making
if ml_uncertainty > 0.2:
    # High uncertainty - review manually
    print("⚠️ High uncertainty - manual review recommended")
```

---

### 2. SHAP Explanations

**Feature Importance:**

```python
result = predictor.predict_single(features, explain=True)

for feat in result['shap_explanation']['top_features']:
    print(f"{feat['feature']:30} "
          f"Value: {feat['value']:6.2f} "
          f"SHAP: {feat['shap_value']:+7.3f}")
```

**Output:**

```
has_reentrancy                 Value:   1.00 SHAP: +0.420
cei_violations                 Value:   3.00 SHAP: +0.380
state_after_call_count         Value:   2.00 SHAP: +0.250
num_external_calls             Value:   5.00 SHAP: +0.180
has_unchecked_call             Value:   1.00 SHAP: +0.150
```

---

### 3. Monitoring Integration

**Automatic Logging:**

```python
# If enable_monitoring=True
predictor = EnhancedHybridPredictorV2(enable_monitoring=True)

# Every prediction automatically logged to MLMonitor
result = predictor.predict_single(features)

# Access monitoring data
monitor = predictor.monitor
report = monitor.get_performance_report(window_size=1000)

print(f"Drift detected: {report['drift_detected']}")
print(f"Average confidence: {report['average_confidence']:.3f}")
```

---

### 4. Custom Thresholds

**Override Default Threshold:**

```python
# Default threshold: 0.2
result = predictor.predict_single(features)

# Custom threshold
custom_threshold = 0.5
custom_prediction = 1 if result['raw_score'] > custom_threshold else 0

print(f"Default prediction: {result['prediction']}")
print(f"Custom prediction: {custom_prediction}")
```

---

## Integration with Other Modules

### ML Core Integration

| Component | Usage in Hybrid Predictor |
| --------- | ------------------------- |
| ConfigManager | Load YAML configuration |
| HeterogeneousEnsemble | ML prediction with uncertainty |
| MLMonitor | Log predictions for drift detection |
| PathResolver | Resolve model file paths |

---

### API Integration

**Used By:**

- [predict.py](../src/chainguardian/api/routers/predict.py) - `/api/v1/analyze` and `/api/v1/predict-from-features`
- [reports.py](../src/chainguardian/api/routers/reports.py) - `/api/v1/reports/generate`
- [model_loader.py](../src/chainguardian/api/dependencies/model_loader.py) - Singleton model loading

---

## Backward Compatibility

**Wrapper Class:** `EnhancedHybridPredictor`
**Location:** [Line 974](../src/chainguardian/ml/models/hybrid_predictor_enhanced_v2.py#L974)

```python
class EnhancedHybridPredictor(EnhancedHybridPredictorV2):
    """Backward compatibility wrapper."""

    def predict(self, features: Dict, **kwargs) -> Dict:
        """Original method name."""
        return self.predict_single(features, **kwargs)
```

**Legacy Code Still Works:**

```python
# Old API
predictor = EnhancedHybridPredictor()
result = predictor.predict(features, llm_ready=True)

# Internally calls predict_single()
```

---

## Additional Resources

- [ML Core Documentation](ml_core_technical_documentation.md)
- [API Documentation](api_technical_documentation.md)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-29
**Maintainer:** ChainGuardian AI Team
