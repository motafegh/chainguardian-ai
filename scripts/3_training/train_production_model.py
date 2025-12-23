"""
ChainGuardian AI - Production Model Training
============================================
ONE SCRIPT that does everything with proper data validation.

Author: Ali
Date: December 22, 2024
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import json

# ML imports
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    roc_auc_score, roc_curve, brier_score_loss
)
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

# MLflow
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from mlflow.models.signature import infer_signature

# Database
from sqlalchemy import create_engine, text

print("\n" + "="*80)
print("🚀 CHAINGUARDIAN AI - PRODUCTION MODEL TRAINING")
print("="*80)

# ============================================================================
# STEP 1: EXPORT DATA FROM DATABASE
# ============================================================================
print("\n📤 STEP 1: EXPORTING DATA FROM DATABASE")
print("-" * 80)

DATABASE_URL = "postgresql://chainguardian_user:2220128@localhost:5432/chainguardian"
engine = create_engine(DATABASE_URL)

query = text("""
    SELECT 
        c.name as contract_name,
        c.data_source,
        f.*
    FROM contracts c
    INNER JOIN features f ON c.id = f.contract_id
    WHERE f.failure_reason IS NULL
    ORDER BY c.data_source, c.name;
""")

with engine.connect() as conn:
    df = pd.read_sql(query, conn)

print(f"✅ Loaded {len(df)} contracts")

# Create labels
df['is_vulnerable'] = df['data_source'].isin([
    'smartbugs_curated', 'production_vulnerable', 'trail_of_bits'
]).astype(int)

vulnerable = df['is_vulnerable'].sum()
safe = len(df) - vulnerable

print(f"   Vulnerable: {vulnerable} ({100*vulnerable/len(df):.1f}%)")
print(f"   Safe:       {safe} ({100*safe/len(df):.1f}%)")

# ============================================================================
# STEP 2: PREPARE FEATURES (WITH VALIDATION)
# ============================================================================
print("\n🔧 STEP 2: PREPARING FEATURES")
print("-" * 80)

# Exclude metadata columns
exclude_cols = [
    'id', 'contract_id', 'contract_name', 'data_source',
    'failure_reason', 'error_message', 'is_vulnerable'
]

# Get all potential feature columns
all_feature_cols = [col for col in df.columns if col not in exclude_cols]

print(f"   Found {len(all_feature_cols)} potential feature columns")

# CRITICAL: Filter out non-numeric columns
# EDUCATIONAL NOTE: ML models need numeric features only
# String/object columns will cause "could not convert string to float" error
numeric_cols = []
non_numeric_cols = []

for col in all_feature_cols:
    dtype = df[col].dtype
    # Keep only numeric types (int, float, bool)
    if dtype in ['int64', 'int32', 'float64', 'float32', 'bool']:
        numeric_cols.append(col)
    else:
        non_numeric_cols.append(col)
        # Show what's in this column for debugging
        sample_values = df[col].dropna().unique()[:3]
        print(f"   ⚠️ Excluding non-numeric column: {col} (dtype: {dtype})")
        print(f"      Sample values: {sample_values}")

feature_cols = numeric_cols
print(f"\n✅ Selected {len(feature_cols)} numeric features")

# Fill missing values with 0
# EDUCATIONAL NOTE: NaN/NULL breaks ML training
df[feature_cols] = df[feature_cols].fillna(0)

# Replace infinite values
# EDUCATIONAL NOTE: np.inf also breaks ML training
df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], 999999)

# Convert boolean to int (0/1)
# EDUCATIONAL NOTE: Some ML libraries prefer int over bool
for col in feature_cols:
    if df[col].dtype == 'bool':
        df[col] = df[col].astype(int)

# Final validation: Ensure all features are numeric
print(f"\n🔍 Final validation:")
for col in feature_cols:
    dtype = df[col].dtype
    if dtype not in ['int64', 'int32', 'float64', 'float32']:
        print(f"   ❌ ERROR: {col} still not numeric (dtype: {dtype})")
        # Convert to numeric, coercing errors to NaN
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        print(f"      → Converted to numeric")

print(f"✅ All features validated as numeric")

# Create feature matrix
X = df[feature_cols].copy()
y = df['is_vulnerable'].copy()

# Final check: No strings in X
assert X.select_dtypes(include=['object']).shape[1] == 0, "Still have object columns!"
print(f"✅ Feature matrix ready: {X.shape}")

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

print(f"   Training: {len(X_train)} ({100*len(X_train)/len(df):.0f}%)")
print(f"   Test:     {len(X_test)} ({100*len(X_test)/len(df):.0f}%)")

pos_weight = len(y_train) / (2 * y_train.sum())
print(f"   Class weight: {pos_weight:.2f}")

# ============================================================================
# STEP 4: SCALE FEATURES (ROBUSTSCALER)
# ============================================================================
print("\n🔄 STEP 4: SCALING FEATURES (RobustScaler)")
print("-" * 80)

scaler = RobustScaler()

# Convert to numpy arrays to avoid pandas issues
X_train_scaled = scaler.fit_transform(X_train.values)
X_test_scaled = scaler.transform(X_test.values)

print(f"✅ Features scaled using median + IQR (outlier-resistant)")
print(f"   Shape: {X_train_scaled.shape}")

# ============================================================================
# STEP 5: TRAIN MODEL WITH CALIBRATION
# ============================================================================
print("\n🚀 STEP 5: TRAINING XGBOOST WITH CALIBRATION")
print("-" * 80)

# Setup MLflow
EXPERIMENT_NAME = "chainguardian_production"
mlflow.set_experiment(EXPERIMENT_NAME)

with mlflow.start_run(run_name=f"production_{datetime.now().strftime('%Y%m%d_%H%M')}"):
    
    # Log configuration
    mlflow.log_params({
        "model_type": "XGBoost_Calibrated",
        "scaler": "RobustScaler",
        "calibration": "isotonic",
        "n_estimators": 300,
        "max_depth": 6,
        "learning_rate": 0.05,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "num_features": len(feature_cols),
        "class_weight": pos_weight
    })
    
    # Train base model
    print(f"\n📊 Training base XGBoost...")
    base_model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=pos_weight,
        random_state=42,
        eval_metric='logloss'
    )
    
    base_model.fit(X_train_scaled, y_train)
    
    # Evaluate uncalibrated
    y_pred_proba_base = base_model.predict_proba(X_test_scaled)[:, 1]
    auc_base = roc_auc_score(y_test, y_pred_proba_base)
    brier_base = brier_score_loss(y_test, y_pred_proba_base)
    
    print(f"   Uncalibrated AUC:    {auc_base:.4f}")
    print(f"   Uncalibrated Brier:  {brier_base:.4f}")
    
    # Calibrate model
    print(f"\n🔧 Applying isotonic calibration...")
    calibrated_model = CalibratedClassifierCV(
        base_model,
        method='isotonic',
        cv=5,
        n_jobs=-1
    )
    
    calibrated_model.fit(X_train_scaled, y_train)
    
    # Evaluate calibrated
    y_pred_calib = calibrated_model.predict(X_test_scaled)
    y_pred_proba_calib = calibrated_model.predict_proba(X_test_scaled)[:, 1]
    
    auc_calib = roc_auc_score(y_test, y_pred_proba_calib)
    brier_calib = brier_score_loss(y_test, y_pred_proba_calib)
    
    print(f"   Calibrated AUC:      {auc_calib:.4f}")
    print(f"   Calibrated Brier:    {brier_calib:.4f}")
    print(f"   Improvement:         {brier_base - brier_calib:.4f}")
    
    # Log metrics
    mlflow.log_metrics({
        "test_auc": auc_calib,
        "test_brier": brier_calib,
        "brier_improvement": brier_base - brier_calib
    })
    
    # Classification report
    report = classification_report(y_test, y_pred_calib, output_dict=True)
    mlflow.log_metrics({
        "test_accuracy": report['accuracy'],
        "test_precision": report['1']['precision'],
        "test_recall": report['1']['recall'],
        "test_f1": report['1']['f1-score']
    })
    
    print(f"\n📊 Classification Metrics:")
    print(f"   Accuracy:  {report['accuracy']:.3f}")
    print(f"   Precision: {report['1']['precision']:.3f}")
    print(f"   Recall:    {report['1']['recall']:.3f}")
    print(f"   F1-Score:  {report['1']['f1-score']:.3f}")
    
    # ========================================================================
    # STEP 6: CREATE VISUALIZATIONS
    # ========================================================================
    print(f"\n📈 Creating visualizations...")
    
    # Calibration curve
    plt.figure(figsize=(10, 8))
    
    fraction_base, mean_pred_base = calibration_curve(
        y_test, y_pred_proba_base, n_bins=10
    )
    plt.plot(mean_pred_base, fraction_base, 's-', 
             label='Uncalibrated', linewidth=2, markersize=8)
    
    fraction_calib, mean_pred_calib = calibration_curve(
        y_test, y_pred_proba_calib, n_bins=10
    )
    plt.plot(mean_pred_calib, fraction_calib, 'o-',
             label='Calibrated', linewidth=2, markersize=8)
    
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect')
    plt.xlabel('Predicted Probability')
    plt.ylabel('Actual Frequency')
    plt.title('Calibration Curve')
    plt.legend()
    plt.grid(alpha=0.3)
    
    calib_path = 'calibration_curve.png'
    plt.savefig(calib_path, dpi=150, bbox_inches='tight')
    mlflow.log_artifact(calib_path)
    plt.close()
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred_calib)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Safe', 'Vulnerable'],
                yticklabels=['Safe', 'Vulnerable'])
    plt.title('Confusion Matrix')
    plt.ylabel('True')
    plt.xlabel('Predicted')
    
    cm_path = 'confusion_matrix.png'
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    mlflow.log_artifact(cm_path)
    plt.close()
    
    # ROC curve
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba_calib)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, label=f'AUC = {auc_calib:.3f}', linewidth=2)
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend()
    plt.grid(alpha=0.3)
    
    roc_path = 'roc_curve.png'
    plt.savefig(roc_path, dpi=150, bbox_inches='tight')
    mlflow.log_artifact(roc_path)
    plt.close()
    
    print(f"   ✅ Saved 3 visualizations")
    
    # ========================================================================
    # STEP 7: SAVE TO PRODUCTION
    # ========================================================================
    print(f"\n💾 STEP 7: SAVING TO PRODUCTION")
    print("-" * 80)
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Backup old models
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    if (models_dir / "production_model.pkl").exists():
        backup_dir = models_dir / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        import shutil
        shutil.copy(models_dir / "production_model.pkl", 
                   backup_dir / "production_model.pkl")
        shutil.copy(models_dir / "production_scaler.pkl",
                   backup_dir / "production_scaler.pkl")
        print(f"   📦 Backed up old models")
    
    # Save new models
    joblib.dump(calibrated_model, models_dir / "production_model.pkl")
    joblib.dump(scaler, models_dir / "production_scaler.pkl")
    
    print(f"   ✅ Saved model:  {models_dir / 'production_model.pkl'}")
    print(f"   ✅ Saved scaler: {models_dir / 'production_scaler.pkl'}")
    
    # Save feature names and metadata
    feature_metadata = {
        "feature_names": feature_cols,
        "feature_count": len(feature_cols),
        "model_type": "XGBoost_Calibrated",
        "scaler_type": "RobustScaler",
        "trained_date": datetime.now().isoformat(),
        "training_data": {
            "total_contracts": int(len(df)),
            "train_size": int(len(X_train)),
            "test_size": int(len(X_test)),
            "vulnerable": int(vulnerable),
            "safe": int(safe)
        },
        "metrics": {
            "test_auc": float(auc_calib),
            "test_accuracy": float(report['accuracy']),
            "test_precision": float(report['1']['precision']),
            "test_recall": float(report['1']['recall']),
            "test_f1": float(report['1']['f1-score']),
            "brier_score": float(brier_calib)
        }
    }
    
    with open(models_dir / "feature_metadata.json", 'w') as f:
        json.dump(feature_metadata, f, indent=2)
    
    print(f"   ✅ Saved metadata: {models_dir / 'feature_metadata.json'}")
    
    # Log to MLflow
    signature = infer_signature(X_train_scaled, y_pred_proba_calib)
    mlflow.sklearn.log_model(calibrated_model, "model", signature=signature)
    mlflow.log_artifact(str(models_dir / "feature_metadata.json"))
    
    run_id = mlflow.active_run().info.run_id
    print(f"\n   📊 MLflow Run ID: {run_id}")

# ============================================================================
# STEP 8: QUICK TEST
# ============================================================================
print("\n🧪 STEP 8: QUICK TEST")
print("-" * 80)

# Test predictions directly (no hybrid predictor needed)
test_idx = np.random.randint(0, len(X_test))
test_features = X_test_scaled[test_idx:test_idx+1]
test_pred = calibrated_model.predict_proba(test_features)[0, 1]
test_label = y_test.iloc[test_idx]

print(f"   Sample prediction:")
print(f"   True label:  {'VULNERABLE' if test_label == 1 else 'SAFE'}")
print(f"   Predicted:   {test_pred:.1%} confidence")
print(f"   Result:      {'✅ Correct' if (test_pred > 0.5) == test_label else '❌ Wrong'}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("🎉 TRAINING COMPLETE!")
print("="*80)

print(f"\n📊 FINAL METRICS:")
print(f"   Test AUC:       {auc_calib:.4f}")
print(f"   Test Accuracy:  {report['accuracy']:.4f}")
print(f"   Test Recall:    {report['1']['recall']:.4f}")
print(f"   Brier Score:    {brier_calib:.4f}")

print(f"\n📁 SAVED FILES:")
print(f"   ✅ models/production_model.pkl ({len(feature_cols)} features)")
print(f"   ✅ models/production_scaler.pkl")
print(f"   ✅ models/feature_metadata.json")

print(f"\n🔍 VIEW RESULTS:")
print(f"   MLflow UI: http://localhost:5000")
print(f"   Experiment: {EXPERIMENT_NAME}")

print(f"\n💡 NEXT STEPS:")
print(f"   1. Check MLflow UI for detailed visualizations")
print(f"   2. Test model on custom contracts")
print(f"   3. Deploy to production API")

print("\n" + "="*80 + "\n")