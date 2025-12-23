#!/usr/bin/env python3
"""
Dataset Integrity Check
Verify training data before model rebuild
"""
import pandas as pd
import numpy as np

print("="*80)
print("📊 DATASET VERIFICATION")
print("="*80)

df = pd.read_csv('data/complete_dataset_with_semantic.csv')

print(f"\n1️⃣ BASIC STATS")
print(f"   Total contracts: {len(df)}")
print(f"   Data sources: {df['data_source'].nunique()}")
print(f"   Date range: {df.get('created_at', ['N/A'])[0] if 'created_at' in df.columns else 'N/A'}")

print(f"\n2️⃣ DATA SOURCES")
for source in df['data_source'].unique():
    count = (df['data_source'] == source).sum()
    vuln = df[df['data_source'] == source]['is_vulnerable'].sum() if 'is_vulnerable' in df.columns else 0
    print(f"   {source:25s}: {count:4d} contracts ({vuln:3d} vulnerable)")

print(f"\n3️⃣ LABEL DISTRIBUTION")
if 'is_vulnerable' in df.columns:
    vuln = df['is_vulnerable'].sum()
    safe = len(df) - vuln
    print(f"   Vulnerable: {vuln:4d} ({vuln/len(df)*100:.1f}%)")
    print(f"   Safe:       {safe:4d} ({safe/len(df)*100:.1f}%)")
else:
    print("   ⚠️  WARNING: No 'is_vulnerable' column found!")

print(f"\n4️⃣ FEATURE GROUPS")
feature_groups = {
    'Vulnerability flags': [c for c in df.columns if c.startswith('has_')],
    'Severity': [c for c in df.columns if 'severity' in c.lower()],
    'AST features': ['num_functions', 'lines_of_code', 'cyclomatic_complexity'],
    'Graph features': [c for c in df.columns if c.startswith('cfg_') or c.startswith('cg_') or c.startswith('dfg_')],
    'Semantic features': [c for c in df.columns if c.startswith('cei_') or 'reentrancy_guard' in c]
}

total_features = 0
for group, features in feature_groups.items():
    available = [f for f in features if f in df.columns]
    total_features += len(available)
    print(f"   {group:20s}: {len(available):3d} features")

print(f"   {'TOTAL':20s}: {total_features:3d} features")

print(f"\n5️⃣ MISSING VALUES")
missing = df.isnull().sum()
if missing.sum() > 0:
    print(f"   Columns with missing: {(missing > 0).sum()}")
    top_missing = missing[missing > 0].sort_values(ascending=False).head(5)
    for col, count in top_missing.items():
        print(f"   - {col}: {count} ({count/len(df)*100:.1f}%)")
else:
    print(f"   ✅ No missing values")

print(f"\n6️⃣ ADVERSARIAL SET")
adv = df[df['data_source'] == 'adversarial_test']
if len(adv) > 0:
    print(f"   Count: {len(adv)} contracts")
    print(f"   Contracts: {', '.join(adv['contract_name'].head(5).tolist())}...")
    
    # Check semantic features on adversarial
    if 'cei_violations' in adv.columns:
        print(f"   CEI violations: min={adv['cei_violations'].min()}, max={adv['cei_violations'].max()}, mean={adv['cei_violations'].mean():.2f}")
    if 'cei_pattern_score' in adv.columns:
        print(f"   CEI score: min={adv['cei_pattern_score'].min():.2f}, max={adv['cei_pattern_score'].max():.2f}, mean={adv['cei_pattern_score'].mean():.2f}")
else:
    print(f"   ⚠️  WARNING: No adversarial_test contracts found!")

print(f"\n7️⃣ TRAIN/TEST SPLIT")
train = df[df['data_source'] != 'adversarial_test']
print(f"   Training pool: {len(train)} contracts")
print(f"   Test set (20%): ~{int(len(train)*0.2)} contracts")
print(f"   Adversarial holdout: {len(adv)} contracts")

print("\n" + "="*80)
print("✅ VERIFICATION COMPLETE")
print("="*80 + "\n")
