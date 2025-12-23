"""
Production Training v5 - NO LEAKAGE
===================================
Remove ALL potentially leaking features and test true performance.

REMOVED:
- id, contract_name, data_source (ordering leakage)
- high_severity_count, medium_severity_count, low_severity_count
- total_detector_hits, security_detectors_triggered
- Any other aggregate counts

KEPT:
- Boolean flags (has_reentrancy, has_access_control, etc.)
- Code metrics (LOC, complexity, functions)
- Graph features (CFG, DFG, call graph)
- Semantic features (CEI violations, pattern scores)

Author: Ali
Date: December 22, 2024
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import RobustScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report
from datetime import datetime

print("\n" + "="*80)
print("🧪 PRODUCTION TRAINING v5 - ZERO LEAKAGE TEST")
print("="*80)

# Load data
df = pd.read_csv("data/ml_ready_v4.csv")
print(f"\n📥 Loaded: {len(df)} samples × {len(df.columns)} columns")

# Define leakage features to REMOVE
LEAKAGE_FEATURES = [
    # Ordering leakage
    'id',
    'contract_name',
    'data_source',
    
    # Severity counts (potential circular dependency)
    'high_severity_count',
    'medium_severity_count', 
    'low_severity_count',
    'total_detector_hits',
    'security_detectors_triggered',
    'unique_vulnerability_types',
    
    # Aggregate risk scores (derived from severity)
    'risk_score_simple',
    'risk_score_weighted',
    
    # Any other detector counts
    'high_confidence_detectors',
    'medium_confidence_detectors',
    'low_confidence_detectors',
    
    # Constant features
    'has_delegatecall_loop',
    'has_msg_value_loop',
    'has_incorrect_solc_version',
    'has_outdated_compiler',
    'num_dependencies',
    'num_unused_functions',
    'low_confidence_detectors',
    'detectors_per_function',
    'detectors_per_loc',
    'unchecked_calls_in_critical_context'
]

# Separate features
exclude_cols = ['ground_truth_vulnerable'] + LEAKAGE_FEATURES
available_features = [col for col in df.columns if col not in exclude_cols and col in df.columns]

print(f"\n🔍 Feature Filtering:")
print(f"   Original: {len(df.columns) - 1} features")  # -1 for target
print(f"   Removed:  {len([f for f in LEAKAGE_FEATURES if f in df.columns])} leakage features")
print(f"   Final:    {len(available_features)} clean features")

X = df[available_features]
y = df['ground_truth_vulnerable']

# Remove any remaining constant features
constant_features = X.columns[X.nunique() == 1].tolist()
if constant_features:
    print(f"\n⚠️  Removing {len(constant_features)} additional constant features")
    X = X.drop(columns=constant_features)

print(f"\n📊 Final Dataset:")
print(f"   Features: {len(X.columns)}")
print(f"   Samples:  {len(X)}")
print(f"   Labels:   {y.sum()} vuln ({y.mean()*100:.1f}%)")

# List feature categories
boolean_features = [col for col in X.columns if X[col].nunique() == 2]
numeric_features = [col for col in X.columns if col not in boolean_features]

print(f"\n📋 Feature Breakdown:")
print(f"   Boolean flags:    {len(boolean_features)}")
print(f"   Numeric features: {len(numeric_features)}")

# Handle missing/infinite
X = X.fillna(0)
X = X.replace([np.inf, -np.inf], 999999)

# 5-Fold Cross-Validation FIRST (most reliable test)
print("\n" + "="*80)
print("🔬 CROSS-VALIDATION TEST (5-Fold)")
print("="*80)

scaler = RobustScaler()
X_scaled = scaler.fit_transform(X)

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='logloss'
)

cv_scores = cross_val_score(
    model, X_scaled, y,
    cv=5,
    scoring='roc_auc',
    n_jobs=-1
)

print(f"\n📊 Cross-Validation AUC:")
for i, score in enumerate(cv_scores, 1):
    print(f"   Fold {i}: {score:.4f}")
print(f"   Mean:    {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Single train/test split for comparison
print("\n" + "="*80)
print("🔬 TRAIN/TEST SPLIT (80/20)")
print("="*80)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train with calibration
base_model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=(len(y_train) - y_train.sum()) / y_train.sum(),
    random_state=42,
    eval_metric='logloss'
)

calibrated_model = CalibratedClassifierCV(
    base_model,
    method='isotonic',
    cv=5,
    n_jobs=-1
)

print(f"\n🤖 Training...")
calibrated_model.fit(X_train_scaled, y_train)

# Evaluate
y_proba = calibrated_model.predict_proba(X_test_scaled)[:, 1]
y_pred = calibrated_model.predict(X_test_scaled)

test_auc = roc_auc_score(y_test, y_proba)
test_acc = accuracy_score(y_test, y_pred)

print(f"\n📈 Test Results:")
print(f"   AUC:      {test_auc:.4f}")
print(f"   Accuracy: {test_acc:.4f}")

# Save model
MODELS_DIR = Path("models")
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

joblib.dump(calibrated_model, MODELS_DIR / f"production_model_v5_clean.pkl")
joblib.dump(scaler, MODELS_DIR / f"production_scaler_v5_clean.pkl")

# Feature importance
base_estimator = calibrated_model.calibrated_classifiers_[0].estimator
importance_df = pd.DataFrame({
    'feature': X.columns,
    'importance': base_estimator.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n🎯 TOP 15 FEATURES:")
for i, row in importance_df.head(15).iterrows():
    is_bool = row['feature'] in boolean_features
    marker = "🎯" if is_bool else "📊"
    print(f"   {marker} {row['feature']:40s} {row['importance']:.4f}")

# Final comparison
print("\n" + "="*80)
print("📊 RESULTS COMPARISON")
print("="*80)
print(f"v4 (with potential leakage):  AUC = 0.9998")
print(f"v5 (clean features):          AUC = {test_auc:.4f}")
print(f"v5 (CV mean):                 AUC = {cv_scores.mean():.4f}")
print(f"\nDifference:                   {(0.9998 - test_auc)*100:.2f}%")

if test_auc > 0.95:
    print(f"\n✅ HIGH PERFORMANCE MAINTAINED ({test_auc:.4f})")
    print(f"   Your meta-classifier is legitimate!")
elif test_auc > 0.90:
    print(f"\n✅ GOOD PERFORMANCE ({test_auc:.4f})")
    print(f"   Confirms: Boolean flags are predictive")
elif test_auc > 0.85:
    print(f"\n⚠️  MODERATE PERFORMANCE ({test_auc:.4f})")
    print(f"   Previous 0.9998 was partially inflated by leakage")
else:
    print(f"\n❌ LOW PERFORMANCE ({test_auc:.4f})")
    print(f"   Previous 0.9998 was mostly leakage!")

print("\n✅ Clean model saved!")
