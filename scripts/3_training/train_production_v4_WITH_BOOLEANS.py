"""
Production Training v4 - WITH BOOLEAN FLAGS
===========================================
Train on 93 features including 30 boolean vulnerability flags.

CHANGES FROM V3:
- 93 features (was 62)
- 30 boolean vulnerability flags included
- Expected: +5-10% AUC improvement

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
from datetime import datetime
import mlflow

print("\n" + "="*80)
print("🚀 PRODUCTION TRAINING v4 - WITH BOOLEAN VULNERABILITY FLAGS")
print("="*80)

# Load dataset
data_path = Path("data/ml_ready_v4.csv")
df = pd.read_csv(data_path)

print(f"\n📥 Dataset: {len(df)} samples × {len(df.columns)} columns")

# Separate features from metadata
exclude_cols = ['ground_truth_vulnerable', 'contract_name', 'data_source']
feature_cols = [col for col in df.columns if col not in exclude_cols]

print(f"   Features: {len(feature_cols)}")

# Remove constant features
X = df[feature_cols]
y = df['ground_truth_vulnerable']

# Find and remove constant features
constant_features = X.columns[X.nunique() == 1].tolist()
if constant_features:
    print(f"\n⚠️  Removing {len(constant_features)} constant features:")
    for feat in constant_features:
        print(f"      • {feat} = {X[feat].unique()[0]}")
    X = X.drop(columns=constant_features)

# Handle missing/infinite
X = X.fillna(0)
X = X.replace([np.inf, -np.inf], 999999)

print(f"\n📊 Final features: {len(X.columns)}")
print(f"   Labels: {y.sum()} vulnerable ({y.mean()*100:.1f}%)")

# Backup old model
MODELS_DIR = Path("models")
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
backup_dir = MODELS_DIR / f"backup_v3_{timestamp}"

if (MODELS_DIR / "production_model.pkl").exists():
    backup_dir.mkdir(exist_ok=True)
    import shutil
    for f in ["production_model.pkl", "production_scaler.pkl", "feature_metadata.json"]:
        src = MODELS_DIR / f
        if src.exists():
            shutil.copy(src, backup_dir / f)
    print(f"\n✅ Backed up v3 model to: {backup_dir}")

# Train/test split (stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n✂️  Split:")
print(f"   Train: {len(X_train)} ({y_train.mean()*100:.1f}% vuln)")
print(f"   Test:  {len(X_test)} ({y_test.mean()*100:.1f}% vuln)")

# Scale features
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train.values)
X_test_scaled = scaler.transform(X_test.values)

# Train model
scale_pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()

base_model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    eval_metric='logloss'
)

calibrated_model = CalibratedClassifierCV(
    base_model,
    method='isotonic',
    cv=5,
    n_jobs=-1
)

print(f"\n🤖 Training XGBoost + Calibration...")
print(f"   Class weight: {scale_pos_weight:.2f}")
calibrated_model.fit(X_train_scaled, y_train)
print(f"   ✅ Training complete!")

# Evaluate
y_pred = calibrated_model.predict(X_test_scaled)
y_proba = calibrated_model.predict_proba(X_test_scaled)[:, 1]

auc = roc_auc_score(y_test, y_proba)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
brier = brier_score_loss(y_test, y_proba)

print(f"\n📈 RESULTS:")
print(f"   AUC:       {auc:.4f} {'✅' if auc > 0.985 else '⚠️'}")
print(f"   Accuracy:  {accuracy:.4f}")
print(f"   Precision: {precision:.4f}")
print(f"   Recall:    {recall:.4f}")
print(f"   F1:        {f1:.4f}")
print(f"   Brier:     {brier:.4f}")

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()

print(f"\n📊 Confusion Matrix:")
print(f"              SAFE  VULN")
print(f"   SAFE        {tn:3d}   {fp:3d}")
print(f"   VULN        {fn:3d}   {tp:3d}")

# Save model
joblib.dump(calibrated_model, MODELS_DIR / "production_model.pkl")
joblib.dump(scaler, MODELS_DIR / "production_scaler.pkl")

metadata = {
    'feature_names': X.columns.tolist(),
    'n_features': len(X.columns),
    'training_date': timestamp,
    'dataset_version': 'v4_with_booleans',
    'boolean_flags_included': True,
    'n_train': len(X_train),
    'n_test': len(X_test),
    'metrics': {
        'test_auc': float(auc),
        'test_accuracy': float(accuracy),
        'test_precision': float(precision),
        'test_recall': float(recall),
        'test_f1': float(f1),
        'test_brier': float(brier)
    }
}

with open(MODELS_DIR / "feature_metadata.json", 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n💾 Saved: models/production_model.pkl")

# MLflow
mlflow.set_experiment("chainguardian_v4_with_booleans")

with mlflow.start_run():
    mlflow.log_param("n_features", len(X.columns))
    mlflow.log_param("boolean_flags", True)
    mlflow.log_param("dataset_version", "v4")
    
    mlflow.log_metric("test_auc", auc)
    mlflow.log_metric("test_accuracy", accuracy)
    mlflow.log_metric("test_precision", precision)
    mlflow.log_metric("test_recall", recall)

# Comparison with v3
print("\n" + "="*80)
print("📊 COMPARISON: v3 vs v4")
print("="*80)
print(f"v3 (62 features, no booleans):  AUC = 0.9822")
print(f"v4 (93 features, 30 booleans):  AUC = {auc:.4f}")
print(f"Improvement:                     {(auc - 0.9822)*100:+.2f}%")

if auc > 0.9822:
    print(f"\n🎉 SUCCESS! Boolean flags improved model!")
else:
    print(f"\n⚠️  No improvement - investigate feature importance")

print("\n✅ Training complete!")
