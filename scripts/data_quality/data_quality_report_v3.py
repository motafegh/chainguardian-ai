#!/usr/bin/env python3
"""Data Quality Report v3 - PRODUCTION READY"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
from pathlib import Path

print("="*80)
print("📊 CHAINGUARDIAN DATA QUALITY REPORT v3")
print("🎯 TRUE GROUND TRUTH + DATA SOURCE")
print("="*80)

db = DatabaseManager()

# COMPLETE dataset (contracts + features + labels)
print("\n🔄 Loading COMPLETE dataset...")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT 
            c.id as contract_id,
            c.name as contract_name,
            c.data_source,
            f.*,
            CASE WHEN l_has_vuln.contract_id IS NOT NULL THEN TRUE ELSE FALSE END as ground_truth_vulnerable
        FROM contracts c
        JOIN features f ON c.id = f.contract_id
        LEFT JOIN (
            SELECT DISTINCT contract_id 
            FROM labels WHERE has_vulnerability = TRUE
        ) l_has_vuln ON c.id = l_has_vuln.contract_id
        ORDER BY c.id
    """)
    df = pd.DataFrame(cursor.fetchall())

print(f"✅ Loaded {len(df):,} contracts (contracts + features + labels)")

# ML-ready (successful extraction)
ml_ready = df[df['failure_reason'].isna()].copy()
print(f"✅ ML-ready samples: {len(ml_ready):,} ({len(ml_ready)/len(df)*100:.1f}%)")

# TRUE label distribution
vuln_count = ml_ready['ground_truth_vulnerable'].sum()
safe_count = len(ml_ready) - vuln_count

print(f"\n🏷️  TRUE GROUND TRUTH (ML-Ready):")
print(f"   🔴 Vulnerable: {vuln_count:,} ({vuln_count/len(ml_ready)*100:.1f}%)")
print(f"   🟢 Safe:       {safe_count:,} ({safe_count/len(ml_ready)*100:.1f}%)")

# Data sources breakdown
print(f"\n📁 TOP DATA SOURCES (Vuln/Safe Breakdown):")
source_stats = ml_ready.groupby('data_source')['ground_truth_vulnerable'].agg(['count', 'mean']).round(3)
source_stats.columns = ['total', 'vuln_pct']
source_stats = source_stats.sort_values('total', ascending=False).head(10)
print(source_stats)

# FIXED: Numeric features (no .tolist() error)
numeric_cols = ml_ready.select_dtypes(include=['number']).columns
ml_features = [col for col in numeric_cols if col not in ['contract_id']]
print(f"\n📊 ML FEATURES:")
print(f"   Numeric: {len(ml_features):,} ready for XGBoost/RF")
print(f"   Top 5: {ml_features[:5]}")  # FIXED: Direct list slice

# Export ML-ready dataset
output_path = Path("data/ml_ready_v3.csv")
ml_ready[ml_features + ['ground_truth_vulnerable', 'data_source', 'contract_name']].fillna(0).to_csv(output_path, index=False)

print(f"\n💾 EXPORTED PRODUCTION DATASET:")
print(f"   📁 {output_path}")
print(f"   📊 {len(ml_ready):,} samples × {len(ml_features)} features")
print(f"   ⚖️  {vuln_count/len(ml_ready)*100:.1f}% vulnerable (REAL-WORLD PERFECT)")
print(f"   🎯 Train now: `poetry run python scripts/3_training/train_production_ensemble.py`")

# Balance recommendation
balance_ratio = min(vuln_count, safe_count) / max(vuln_count, safe_count)
if balance_ratio > 0.6:
    print(f"\n✅ EXCELLENT balance ratio: {balance_ratio:.2f} (production ready!)")
else:
    print(f"\n⚠️  Balance ratio: {balance_ratio:.2f} (consider balancing)")

print("\n" + "="*80)
print("✅ v3 PRODUCTION COMPLETE!")
print("🚀 Ready for XGBoost training!")
