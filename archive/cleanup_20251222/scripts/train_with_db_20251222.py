#!/usr/bin/env python3
"""
Production ML Training - Database Export (Dec 22, 2025)
RobustScaler + Calibration on clean PostgreSQL dataset
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, brier_score_loss
)
from sklearn.preprocessing import RobustScaler
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import joblib

print("\n" + "="*80)
print("🎯 CHAINGUARDIAN PRODUCTION TRAINING - DATABASE EXPORT")
print("="*80)

# ============================================================================
# STEP 1: LOAD CLEAN DATABASE EXPORT
# ============================================================================
print("\n📊 STEP 1: LOADING DATABASE EXPORT")
print("-" * 80)

df = pd.read_csv('data/training_with_semantic_20251222.csv')
print(f"✅ Loaded {len(df)} contracts from PostgreSQL export")
print(f"   Columns: {len(df.columns)}")

# Drop metadata columns
drop_cols = [
    "contract_name", "file_path", "data_source",
    "compiler_version", "address",  # Missing values
]
df = df.drop(columns=[c for c in drop_cols if c in df.columns])

# Drop constant columns (identified in verification)
constant_cols = [
    'has_delegatecall_loop', 'has_msg_value_loop', 'has_shadowing_abstract',
    'has_incorrect_solc_version', 'has_outdated_compiler', 'num_dependencies',
    'num_unused_functions', 'low_confidence_detectors', 'detectors_per_function',
    'detectors_per_loc', 'unchecked_calls_in_critical_context'
]
constant_cols = [c for c in constant_cols if c in df.columns]
if constant_cols:
    print(f"\n🧹 Dropping {len(constant_cols)} constant columns")
    df = df.drop(columns=constant_cols)

print(f"\n✅ Clean dataset: {len(df)} rows, {len(df.columns)} columns")
print(f"   Features: {len(df.columns) - 1}")

# ============================================================================
# STEP 2: PREPARE FEATURES & LABELS
# ============================================================================
print("\n🔧 STEP 2: FEATURE PREPARATION")
print("-" * 80)

# Label already exists as 'label' column (0=safe, 1=vulnerable)
X = df.drop(columns=['label'])
y = df['label']

# Convert boolean to int
for col in X.columns:
    if X[col].dtype == 'bool':
        X[col] = X[col].astype(int)

# Handle remaining object columns
for col in X.columns:
    if X[col].dtype == 'object':
        X[col] = pd.Categorical(X[col]).codes

print(f"✅ Feature matrix: {X.shape}")
print(f"   Label distribution:")
print(f"     Safe (0): {sum(y==0)} ({sum(y==0)/len(y)*100:.1f}%)")
print(f"     Vulnerable (1): {sum(y==1)} ({sum(y==1)/len(y)*100:.1f}%)")

# ============================================================================
# STEP 3: TRAIN/TEST SPLIT
# ============================================================================
print("\n🔀 STEP 3: TRAIN/TEST SPLIT")
print("-" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"✅ Train: {len(X_train)} ({sum(y_train==1)} vulnerable)")
print(f"✅ Test:  {len(X_test)} ({sum(y_test==1)} vulnerable)")

pos_weight = len(y_train) / (2 * y_train.sum())
print(f"✅ Pos weight for XGBoost: {pos_weight:.2f}")

# ============================================================================
# STEP 4: ROBUST SCALING
# ============================================================================
print("\n🔄 STEP 4: ROBUST SCALING")
print("-" * 80)

scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"✅ RobustScaler applied")
print(f"   Method: (X - median) / IQR")
print(f"   Robust to outliers: Yes")

# ============================================================================
# STEP 5: TRAIN BASE MODEL
# ============================================================================
print("\n🚀 STEP 5: TRAINING BASE XGBOOST")
print("-" * 80)

xgb_model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=pos_weight,
    random_state=42,
    eval_metric='logloss',
    use_label_encoder=False
)

train_start = datetime.now()
xgb_model.fit(X_train_scaled, y_train)
train_time = (datetime.now() - train_start).total_seconds()

print(f"✅ Training complete: {train_time:.1f}s")

# Evaluate base model
y_pred_base = xgb_model.predict(X_test_scaled)
y_pred_proba_base = xgb_model.predict_proba(X_test_scaled)[:, 1]
base_auc = roc_auc_score(y_test, y_pred_proba_base)
base_brier = brier_score_loss(y_test, y_pred_proba_base)

print(f"\n📊 Base Model Performance:")
print(f"   AUC: {base_auc:.4f}")
print(f"   Brier Score: {base_brier:.4f}")

# ============================================================================
# STEP 6: CALIBRATION
# ============================================================================
print("\n🔧 STEP 6: APPLYING ISOTONIC CALIBRATION")
print("-" * 80)

calib_start = datetime.now()
calibrated_model = CalibratedClassifierCV(
    xgb_model,
    method='isotonic',
    cv=5,
    n_jobs=-1
)
calibrated_model.fit(X_train_scaled, y_train)
calib_time = (datetime.now() - calib_start).total_seconds()

print(f"✅ Calibration complete: {calib_time:.1f}s")

# Evaluate calibrated model
y_pred_calib = calibrated_model.predict(X_test_scaled)
y_pred_proba_calib = calibrated_model.predict_proba(X_test_scaled)[:, 1]
calib_auc = roc_auc_score(y_test, y_pred_proba_calib)
calib_brier = brier_score_loss(y_test, y_pred_proba_calib)

print(f"\n📊 Calibrated Model Performance:")
print(f"   AUC: {calib_auc:.4f}")
print(f"   Brier Score: {calib_brier:.4f}")
print(f"\n📈 Improvement:")
print(f"   Brier: {base_brier:.4f} → {calib_brier:.4f} (Δ {base_brier-calib_brier:.4f})")

# ============================================================================
# STEP 7: DETAILED METRICS
# ============================================================================
print("\n📊 STEP 7: CLASSIFICATION REPORT")
print("-" * 80)

print(classification_report(y_test, y_pred_calib,
                          target_names=["Safe", "Vulnerable"]))

cm = confusion_matrix(y_test, y_pred_calib)
print(f"Confusion Matrix:")
print(f"  [[TN={cm[0,0]:>3}, FP={cm[0,1]:>3}],")
print(f"   [FN={cm[1,0]:>3}, TP={cm[1,1]:>3}]]")

# ============================================================================
# STEP 8: FEATURE IMPORTANCE
# ============================================================================
print("\n🔍 STEP 8: TOP 20 FEATURES")
print("-" * 80)

feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)

for i, row in feature_importance.head(20).iterrows():
    print(f"  {row['feature']:<45} {row['importance']:.4f}")

# ============================================================================
# STEP 9: SAVE ARTIFACTS
# ============================================================================
print("\n💾 STEP 9: SAVING MODELS")
print("-" * 80)

output_dir = Path("models")
output_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M")

# Save calibrated model
model_path = output_dir / f"xgboost_calibrated_{timestamp}.pkl"
joblib.dump(calibrated_model, model_path)
print(f"✅ Model: {model_path}")

# Save scaler
scaler_path = output_dir / f"robust_scaler_{timestamp}.pkl"
joblib.dump(scaler, scaler_path)
print(f"✅ Scaler: {scaler_path}")

# Save feature names
feature_path = output_dir / f"feature_names_{timestamp}.txt"
with open(feature_path, 'w') as f:
    f.write('\n'.join(X.columns))
print(f"✅ Features: {feature_path}")

# Save feature importance
importance_path = output_dir / f"feature_importance_{timestamp}.csv"
feature_importance.to_csv(importance_path, index=False)
print(f"✅ Importance: {importance_path}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("🎉 TRAINING COMPLETE!")
print("="*80)
print(f"\n🏆 FINAL RESULTS:")
print(f"   Test AUC:       {calib_auc:.4f}")
print(f"   Brier Score:    {calib_brier:.4f}")
print(f"   Training Time:  {train_time:.1f}s (base) + {calib_time:.1f}s (calib)")
print(f"   Dataset Size:   {len(df)} contracts")
print(f"   Features Used:  {X.shape[1]}")
print("\n" + "="*80 + "\n")
