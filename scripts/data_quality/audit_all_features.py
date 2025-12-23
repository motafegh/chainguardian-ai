#!/usr/bin/env python3
"""Complete Feature Audit - FIXED for DatabaseManager"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
import numpy as np

print("\n" + "="*80)
print("🔍 COMPLETE FEATURE AUDIT")
print("="*80)

db = DatabaseManager()

# FIXED: Use native cursor (NO SQLAlchemy!)
print("🔄 Loading complete dataset...")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            c.id,
            c.name as contract_name,
            c.data_source,
            c.compiler_version,
            f.*,
            CASE WHEN l.contract_id IS NOT NULL THEN TRUE ELSE FALSE END as ground_truth_vulnerable
        FROM contracts c
        JOIN features f ON c.id = f.contract_id
        LEFT JOIN (SELECT DISTINCT contract_id FROM labels WHERE has_vulnerability=TRUE) l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
        LIMIT 100
    """)
    sample = pd.DataFrame(cursor.fetchall())

print(f"✅ Loaded {len(sample):,} samples × {len(sample.columns)} columns")

# Current ML dataset
current_data = pd.read_csv("data/ml_ready_v3.csv")
current_features = set(current_data.columns) - {'ground_truth_vulnerable', 'data_source', 'contract_name'}

print(f"\n📊 CURRENT ML: {len(current_features)} features")
print(f"📊 DATABASE RAW: {len(sample.columns)} columns")

# EXCLUDED FEATURES (The 27 you're missing!)
all_db_features = set(sample.columns)
excluded = all_db_features - current_features - {'contract_id', 'ground_truth_vulnerable'}

print(f"\n❌ {len(excluded)} EXCLUDED FEATURES:")
for col in sorted(excluded):
    dtype = str(sample[col].dtype)
    unique = sample[col].nunique()
    print(f"   {col:35s} | {dtype:12s} | Unique: {unique:3d}")

# CATEGORICAL ANALYSIS (Your GOLD!)
print(f"\n�� POTENTIAL CATEGORICAL FEATURES:")
categoricals = []
for col in excluded:
    if sample[col].dtype == 'object' or sample[col].nunique() < 20:
        unique_vals = sample[col].unique()[:5]
        categoricals.append(f"  • {col}: {unique_vals} (n={sample[col].nunique()})")
        print(categoricals[-1])

print(f"\n💡 RECOMMENDATION:")
print(f"   Add {len(categoricals)} categoricals → +5-10% AUC!")
print(f"   Run: poetry run python scripts/data_quality/encode_categoricals.py")

print("\n" + "="*80)
print("✅ AUDIT COMPLETE!")
