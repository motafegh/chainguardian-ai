"""
Export Calibrated Model from MLflow to models/ directory
========================================================
Copies the best calibrated model to production location.

WHY THIS SCRIPT:
- hybrid_predictor.py expects models in models/ directory
- MLflow stores models in mlruns/ directory
- This script bridges the gap

Author: Ali
Date: December 21, 2024
"""

import mlflow
import joblib
from pathlib import Path
import shutil

print("\n" + "="*80)
print("📦 EXPORTING CALIBRATED MODEL TO PRODUCTION")
print("="*80)

# Get latest run from calibrated experiment
client = mlflow.tracking.MlflowClient()
experiment = client.get_experiment_by_name("smart_contract_robust_calibrated")

if not experiment:
    print("❌ Experiment 'smart_contract_robust_calibrated' not found")
    exit(1)

# Get latest run
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["start_time DESC"],
    max_results=1
)

if not runs:
    print("❌ No runs found in experiment")
    exit(1)

run = runs[0]
run_id = run.info.run_id

print(f"\n✅ Found latest run:")
print(f"   Run ID: {run_id}")
print(f"   Start Time: {run.info.start_time}")
print(f"   Test AUC: {run.data.metrics.get('test_auc_calibrated', 'N/A'):.4f}")

# Load calibrated model from MLflow
print(f"\n📥 Loading calibrated model from MLflow...")
model_uri = f"runs:/{run_id}/calibrated_model"
calibrated_model = mlflow.sklearn.load_model(model_uri)
print(f"✅ Model loaded")

# Load robust scaler from artifacts
print(f"\n📥 Loading RobustScaler from artifacts...")
artifact_path = client.download_artifacts(run_id, "robust_scaler_XGBoost.pkl")
scaler = joblib.load(artifact_path)
print(f"✅ Scaler loaded")

# Save to production directory
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

# Backup old models
backup_dir = Path("models/backup_20251221")
backup_dir.mkdir(exist_ok=True)

if (models_dir / "production_model.pkl").exists():
    shutil.copy(
        models_dir / "production_model.pkl",
        backup_dir / "production_model_old.pkl"
    )
    print(f"\n📦 Backed up old model to {backup_dir}")

if (models_dir / "production_scaler.pkl").exists():
    shutil.copy(
        models_dir / "production_scaler.pkl",
        backup_dir / "production_scaler_old.pkl"
    )
    print(f"📦 Backed up old scaler to {backup_dir}")

# Save new models
print(f"\n💾 Saving calibrated model to production...")
joblib.dump(calibrated_model, models_dir / "production_model.pkl")
joblib.dump(scaler, models_dir / "production_scaler.pkl")

print(f"✅ Saved to {models_dir / 'production_model.pkl'}")
print(f"✅ Saved to {models_dir / 'production_scaler.pkl'}")

# Save metadata
import json
from datetime import datetime

metadata = {
    "model_type": "XGBoost_Calibrated",
    "calibration_method": "isotonic",
    "scaler_type": "RobustScaler",
    "mlflow_run_id": run_id,
    "mlflow_experiment": "smart_contract_robust_calibrated",
    "test_auc": run.data.metrics.get('test_auc_calibrated', None),
    "brier_score": run.data.metrics.get('brier_score_calibrated', None),
    "exported_date": datetime.now().isoformat(),
    "notes": "Calibrated model with RobustScaler for outlier robustness"
}

with open(models_dir / "PRODUCTION_MODEL_README.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"✅ Saved metadata to {models_dir / 'PRODUCTION_MODEL_README.json'}")

print("\n" + "="*80)
print("🎉 EXPORT COMPLETE!")
print("="*80)
print("\n💡 Next steps:")
print("   1. Test with: poetry run python scripts/3_training/test_shap_explanations.py")
print("   2. Verify adversarial accuracy improved")
print("\n" + "="*80 + "\n")