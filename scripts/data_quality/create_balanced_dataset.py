#!/usr/bin/env python3
"""Create balanced ML dataset - FINAL VERSION"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
from pathlib import Path

db = DatabaseManager()

print("🔄 Creating BALANCED dataset...")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            f.*,
            CASE WHEN l.contract_id IS NOT NULL THEN TRUE ELSE FALSE END as ground_truth_vulnerable
        FROM features f
        LEFT JOIN (
            SELECT DISTINCT contract_id 
            FROM labels 
            WHERE has_vulnerability = TRUE
        ) l ON f.contract_id = l.contract_id
        WHERE f.failure_reason IS NULL
        ORDER BY f.contract_id
    """)
    df = pd.DataFrame(cursor.fetchall())

print(f"✅ Loaded {len(df):,} successful contracts")

# Split balanced
vuln = df[df['ground_truth_vulnerable'] == True]
safe = df[df['ground_truth_vulnerable'] == False]

print(f"🔴 Vulnerable: {len(vuln):,}")
print(f"🟢 Safe:      {len(safe):,}")

# Balance
n_samples = min(len(vuln), len(safe))
vuln_sample = vuln.sample(n=n_samples, random_state=42)
safe_sample = safe.sample(n=n_samples, random_state=42)

balanced_df = pd.concat([vuln_sample, safe_sample])
print(f"✅ Balanced: {len(balanced_df):,} samples (50% vuln / 50% safe)")

# FIXED: Numeric columns selection
print("\n🔧 Selecting numeric ML features...")
numeric_cols = balanced_df.select_dtypes(include=['number']).columns.tolist()
ml_features = [col for col in numeric_cols if col not in ['contract_id']]

print(f"📊 ML features: {len(ml_features)}")

# Create final dataset
final_dataset = balanced_df[ml_features + ['ground_truth_vulnerable']].fillna(0)
print(f"✅ Final shape: {final_dataset.shape}")

# Save
Path("data/ml_balanced").mkdir(exist_ok=True)
final_dataset.to_csv("data/ml_balanced/train_balanced.csv", index=False)
print(f"💾 SAVED: data/ml_balanced/train_balanced.csv ({final_dataset.shape[0]} × {final_dataset.shape[1]})")
print(f"🎯 50/50 BALANCED ML DATASET READY!")
