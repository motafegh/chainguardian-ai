#!/usr/bin/env python3
"""Retrain WITHOUT data leaks."""

import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
import xgboost as xgb
import joblib
from datetime import datetime

df = pd.read_csv('data/training_with_semantic_20251222.csv')

# CRITICAL: Remove data leaks
drop_leaks = ['contract_id', 'contract_name', 'file_path']
df = df.drop(columns=[c for c in drop_leaks if c in df.columns])

print(f"✅ Cleaned {len(df)} contracts")

X = df.drop(columns=['label'])
y = df['label']

# Convert bool/object
for col in X.columns:
    if X[col].dtype == 'bool':
        X[col] = X[col].astype(int)
    elif X[col].dtype == 'object':
        X[col] = pd.Categorical(X[col]).codes

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

scaler = RobustScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

model = xgb.XGBClassifier(
    n_estimators=100,  # Reduced
    max_depth=4,       # Reduced
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train_s, y_train)

# Test
probs = model.predict_proba(X_test_s)[:,1]
print(f"✅ Test AUC: {roc_auc_score(y_test, probs):.4f}")

# Save
output_dir = Path("models")
output_dir.mkdir(exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M")
joblib.dump(model, output_dir / f"xgboost_clean_{ts}.pkl")
joblib.dump(scaler, output_dir / f"robust_scaler_clean_{ts}.pkl")
with open(output_dir / f"feature_names_clean_{ts}.txt", 'w') as f:
    f.write('\n'.join(X.columns))

print("✅ Clean model saved!")
