"""
Extract v5 model's actual feature names
"""
import joblib
from pathlib import Path

# Load v5 model
model = joblib.load("models/production_model_v5_clean.pkl")
scaler = joblib.load("models/production_scaler_v5_clean.pkl")

# Get base estimator
if hasattr(model, 'calibrated_classifiers_'):
    base = model.calibrated_classifiers_[0].estimator
else:
    base = model

# Get feature names
if hasattr(base, 'feature_names_in_'):
    features = list(base.feature_names_in_)
elif hasattr(scaler, 'feature_names_in_'):
    features = list(scaler.feature_names_in_)
else:
    print("❌ No feature names found in model!")
    exit(1)

print(f"✅ v5 Model has {len(features)} features:")
print(f"\nFirst 10:")
for i, f in enumerate(features[:10], 1):
    print(f"   {i:2d}. {f}")

print(f"\nLast 10:")
for i, f in enumerate(features[-10:], len(features)-9):
    print(f"   {i:2d}. {f}")

# Save to file
import json
v5_metadata = {
    'feature_names': features,
    'n_features': len(features),
    'model_version': 'v5_clean_no_leakage',
    'training_date': '2024-12-22'
}

output_path = Path("models/feature_metadata_v5.json")
with open(output_path, 'w') as f:
    json.dump(v5_metadata, f, indent=2)

print(f"\n✅ Saved to: {output_path}")
