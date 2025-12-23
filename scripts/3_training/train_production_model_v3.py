"""
Production Model Training v3 - For 745 Contracts
================================================
Uses properly joined dataset with ground truth labels.

CHANGES FROM V2:
- Works with v3 dataset (proper SQL JOIN)
- 62 numeric features (filtered non-numeric)
- 745 samples (469 vuln, 276 safe)
- Class weighting for 63/37 imbalance

Author: Ali
Date: December 22, 2024
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import json
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, brier_score_loss,
    classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import mlflow

print("\n" + "="*80)
print("🚀 CHAINGUARDIAN PRODUCTION MODEL TRAINING v3")
print("📊 Dataset: 745 contracts | Features: 62 | Balance: 63/37")
print("="*80)

# ============================================================================
# CONFIGURATION
# ============================================================================
MODELS_DIR = Path("models")
DATA_PATH = Path("data/ml_ready_v3.csv")

if not DATA_PATH.exists():
    print(f"❌ Dataset not found: {DATA_PATH}")
    print(f"   Run: poetry run python scripts/data_quality/data_quality_report_v3.py")
    exit(1)

# Backup old models
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
backup_dir = MODELS_DIR / f"backup_{timestamp}"
if (MODELS_DIR / "production_model.pkl").exists():
    backup_dir.mkdir(exist_ok=True)
    import shutil
    for f in ["production_model.pkl", "production_scaler.pkl", "feature_metadata.json"]:
        src = MODELS_DIR / f
        if src.exists():
            shutil.copy(src, backup_dir / f)
    print(f"✅ Backed up old models to: {backup_dir}")

# ============================================================================
# LOAD DATA
# ============================================================================
print(f"\n📥 Loading dataset from {DATA_PATH}...")
df = pd.read_csv(DATA_PATH)

print(f"   Total samples: {len(df)}")
print(f"   Total columns: {len(df.columns)}")

# Check for label column
if 'ground_truth_vulnerable' not in df.columns:
    print(f"❌ Label column 'ground_truth_vulnerable' not found!")
    print(f"   Available columns: {list(df.columns)[:10]}")
    exit(1)

# ============================================================================
# PREPARE FEATURES & LABELS
# ============================================================================
print(f"\n🏷️  Preparing labels...")

# Label distribution
y = df['ground_truth_vulnerable'].astype(int)
vuln_count = y.sum()
safe_count = len(y) - vuln_count

print(f"   Vulnerable: {vuln_count} ({vuln_count/len(y)*100:.1f}%)")
print(f"   Safe:       {safe_count} ({safe_count/len(y)*100:.1f}%)")
print(f"   Balance ratio: {min(vuln_count, safe_count)/max(vuln_count, safe_count):.2f}")

# Get feature columns (exclude metadata)
exclude_cols = [
    'ground_truth_vulnerable', 'contract_name', 'data_source',
    'id', 'contract_id', 'failure_reason', 'error_message',
    'created_at', 'ground_truth_label', 'ground_truth_vuln_type'
]

feature_cols = [col for col in df.columns if col not in exclude_cols]

# Filter numeric only
numeric_features = []
for col in feature_cols:
    if df[col].dtype in ['int64', 'float64', 'bool']:
        numeric_features.append(col)
    else:
        print(f"   ⚠️ Excluding non-numeric: {col} ({df[col].dtype})")

# Convert bool to int
for col in numeric_features:
    if df[col].dtype == 'bool':
        df[col] = df[col].astype(int)

print(f"\n📊 Features prepared:")
print(f"   Total: {len(numeric_features)} numeric features")

X = df[numeric_features]

# Handle missing/infinite
X = X.fillna(0)
X = X.replace([np.inf, -np.inf], 999999)

# ============================================================================
# TRAIN/TEST SPLIT (STRATIFIED)
# ============================================================================
print(f"\n✂️ Splitting data (stratified)...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"   Training: {len(X_train)} samples")
print(f"   Test:     {len(X_test)} samples")
print(f"   Train: {y_train.sum()} vuln ({y_train.mean()*100:.1f}%)")
print(f"   Test:  {y_test.sum()} vuln ({y_test.mean()*100:.1f}%)")

# ============================================================================
# FEATURE SCALING (RobustScaler)
# ============================================================================
print(f"\n⚖️ Scaling with RobustScaler...")
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train.values)
X_test_scaled = scaler.transform(X_test.values)
print(f"   ✅ Scaled (median + IQR)")

# ============================================================================
# MODEL TRAINING (XGBoost + Calibration)
# ============================================================================
print(f"\n🤖 Training XGBoost with calibration...")

# Calculate class weight for imbalanced data
scale_pos_weight = safe_count / vuln_count
print(f"   Class weight (scale_pos_weight): {scale_pos_weight:.2f}")

base_model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,  # Handle imbalance
    random_state=42,
    eval_metric='logloss',
    tree_method='hist'
)

# Calibrate probabilities
calibrated_model = CalibratedClassifierCV(
    base_model,
    method='isotonic',
    cv=5,
    n_jobs=-1
)

print(f"   Training...")
calibrated_model.fit(X_train_scaled, y_train)
print(f"   ✅ Model trained!")

# ============================================================================
# EVALUATION
# ============================================================================
print(f"\n📈 Evaluating model...")

y_pred = calibrated_model.predict(X_test_scaled)
y_proba = calibrated_model.predict_proba(X_test_scaled)[:, 1]

# Metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_proba)
brier = brier_score_loss(y_test, y_proba)

print(f"\n🎯 Test Metrics:")
print(f"   AUC:       {auc:.4f} {'✅' if auc > 0.90 else '⚠️'}")
print(f"   Accuracy:  {accuracy:.4f}")
print(f"   Precision: {precision:.4f}")
print(f"   Recall:    {recall:.4f}")
print(f"   F1 Score:  {f1:.4f}")
print(f"   Brier:     {brier:.4f}")

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()

print(f"\n📊 Confusion Matrix:")
print(f"              Predicted")
print(f"              SAFE  VULN")
print(f"   Actual SAFE  {tn:3d}   {fp:3d}")
print(f"         VULN  {fn:3d}   {tp:3d}")

# Detailed report
print(f"\n📋 Classification Report:")
print(classification_report(y_test, y_pred, target_names=['SAFE', 'VULNERABLE']))

# ============================================================================
# SAVE MODEL
# ============================================================================
print(f"\n💾 Saving model...")

joblib.dump(calibrated_model, MODELS_DIR / "production_model.pkl")
joblib.dump(scaler, MODELS_DIR / "production_scaler.pkl")

metadata = {
    'feature_names': numeric_features,
    'n_features': len(numeric_features),
    'training_date': timestamp,
    'dataset_version': 'v3_expanded_745',
    'n_total': len(df),
    'n_train': len(X_train),
    'n_test': len(X_test),
    'class_balance': {
        'vulnerable': int(vuln_count),
        'safe': int(safe_count),
        'ratio': float(safe_count / vuln_count)
    },
    'metrics': {
        'test_auc': float(auc),
        'test_accuracy': float(accuracy),
        'test_precision': float(precision),
        'test_recall': float(recall),
        'test_f1': float(f1),
        'test_brier': float(brier)
    },
    'confusion_matrix': {
        'TN': int(tn), 'FP': int(fp),
        'FN': int(fn), 'TP': int(tp)
    }
}

with open(MODELS_DIR / "feature_metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"   ✅ Saved to {MODELS_DIR}/")

# ============================================================================
# MLFLOW LOGGING
# ============================================================================
print(f"\n📊 Logging to MLflow...")

mlflow.set_experiment("chainguardian_production_v3")

with mlflow.start_run():
    mlflow.log_param("model_type", "XGBoost_Calibrated")
    mlflow.log_param("scaler", "RobustScaler")
    mlflow.log_param("dataset_version", "v3_745_samples")
    mlflow.log_param("n_features", len(numeric_features))
    mlflow.log_param("class_balance", f"{vuln_count}/{safe_count}")
    mlflow.log_param("scale_pos_weight", scale_pos_weight)
    
    mlflow.log_metric("test_auc", auc)
    mlflow.log_metric("test_accuracy", accuracy)
    mlflow.log_metric("test_precision", precision)
    mlflow.log_metric("test_recall", recall)
    mlflow.log_metric("test_f1", f1)
    mlflow.log_metric("test_brier", brier)
    
    print(f"   ✅ Logged to MLflow")

print("\n" + "="*80)
print("✅ TRAINING COMPLETE!")
print("="*80)
print(f"\n�� Model files:")
print(f"   {MODELS_DIR / 'production_model.pkl'}")
print(f"   {MODELS_DIR / 'production_scaler.pkl'}")
print(f"   {MODELS_DIR / 'feature_metadata.json'}")

if auc > 0.90:
    print(f"\n🎉 EXCELLENT MODEL! AUC: {auc:.4f}")
elif auc > 0.85:
    print(f"\n✅ GOOD MODEL! AUC: {auc:.4f}")
else:
    print(f"\n⚠️ Model needs improvement. AUC: {auc:.4f}")
    print(f"   Consider: More data, feature engineering, hyperparameter tuning")

print(f"\n🚀 Ready for production deployment!")
