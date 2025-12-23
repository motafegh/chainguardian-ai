"""
Complete Feature Audit
=====================
Check ALL columns in database and see what we're excluding.

Author: Ali
Date: December 22, 2024
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.database.manager import DatabaseManager
import pandas as pd
import numpy as np

print("\n" + "="*80)
print("�� COMPLETE FEATURE AUDIT")
print("="*80)

# Load complete dataset from database
db = DatabaseManager()

# Get raw SQL query to see EVERYTHING
from sqlalchemy import text
with db.engine.connect() as conn:
    query = text("""
        SELECT 
            c.id,
            c.name as contract_name,
            c.data_source,
            c.ground_truth_label,
            c.ground_truth_vuln_type,
            f.*
        FROM contracts c
        JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL
        LIMIT 5;
    """)
    
    sample = pd.read_sql(query, conn)

print(f"\n📊 TOTAL COLUMNS IN DATABASE: {len(sample.columns)}")
print(f"   Sample size: {len(sample)} rows")

# Categorize ALL columns
print("\n" + "="*80)
print("COLUMN CATEGORIZATION")
print("="*80)

# Group by data type
column_types = {}
for col in sample.columns:
    dtype = str(sample[col].dtype)
    if dtype not in column_types:
        column_types[dtype] = []
    column_types[dtype].append(col)

for dtype, cols in sorted(column_types.items()):
    print(f"\n📁 {dtype.upper()} ({len(cols)} columns):")
    for col in sorted(cols):
        # Show sample values
        unique_count = sample[col].nunique()
        sample_vals = sample[col].unique()[:3]
        print(f"   • {col:40s} | Unique: {unique_count:3d} | Sample: {sample_vals}")

# Check what we're currently using vs excluding
print("\n" + "="*80)
print("WHAT WE'RE USING vs EXCLUDING")
print("="*80)

# Load our current dataset
current_data = pd.read_csv("data/ml_ready_v3.csv")
current_features = set(current_data.columns)

all_db_features = set(sample.columns)

# What's in DB but NOT in our dataset?
excluded = all_db_features - current_features

print(f"\n❌ EXCLUDED COLUMNS ({len(excluded)}):")
for col in sorted(excluded):
    dtype = str(sample[col].dtype)
    unique = sample[col].nunique()
    print(f"   • {col:40s} | Type: {dtype:10s} | Unique: {unique}")

# Specifically check for categorical columns
print("\n" + "="*80)
print("CATEGORICAL COLUMNS ANALYSIS")
print("="*80)

categorical_cols = []
for col in sample.columns:
    dtype = str(sample[col].dtype)
    unique_count = sample[col].nunique()
    
    # Potential categorical: object, string, or low cardinality numeric
    if dtype == 'object' or (dtype in ['int64', 'float64'] and unique_count < 20):
        categorical_cols.append({
            'column': col,
            'dtype': dtype,
            'unique_count': unique_count,
            'samples': list(sample[col].unique()[:5]),
            'in_current_dataset': col in current_features
        })

print(f"\nFound {len(categorical_cols)} potential categorical features:\n")

for cat in categorical_cols:
    status = "✅ USING" if cat['in_current_dataset'] else "❌ EXCLUDED"
    print(f"{status} | {cat['column']:40s}")
    print(f"       Type: {cat['dtype']}, Unique: {cat['unique_count']}")
    print(f"       Values: {cat['samples']}")
    print()

# Check for useful categorical features we might have excluded
print("\n" + "="*80)
print("POTENTIALLY USEFUL EXCLUDED FEATURES")
print("="*80)

# Load full dataset to check excluded columns
with db.engine.connect() as conn:
    full_query = text("""
        SELECT *
        FROM contracts c
        JOIN features f ON c.id = f.contract_id
        WHERE f.failure_reason IS NULL;
    """)
    full_df = pd.read_sql(full_query, conn)

print(f"\n🔍 Checking {len(excluded)} excluded columns for usefulness...")

useful_excluded = []
for col in excluded:
    if col in full_df.columns:
        dtype = str(full_df[col].dtype)
        unique_count = full_df[col].nunique()
        null_pct = full_df[col].isna().sum() / len(full_df) * 100
        
        # Criteria for "potentially useful"
        is_useful = (
            unique_count > 1 and  # Not constant
            unique_count < len(full_df) * 0.9 and  # Not too unique (like ID)
            null_pct < 50  # Not mostly null
        )
        
        if is_useful:
            # Check correlation with target (if numeric)
            correlation = None
            if dtype in ['int64', 'float64', 'bool']:
                try:
                    correlation = full_df[col].corr(full_df['ground_truth_vulnerable'])
                except:
                    correlation = None
            
            useful_excluded.append({
                'column': col,
                'dtype': dtype,
                'unique_count': unique_count,
                'null_pct': null_pct,
                'correlation': correlation,
                'can_encode': dtype == 'object' and unique_count < 50
            })

# Sort by potential usefulness
useful_excluded.sort(key=lambda x: abs(x['correlation']) if x['correlation'] else 0, reverse=True)

print(f"\n⚠️  POTENTIALLY USEFUL EXCLUDED FEATURES: {len(useful_excluded)}")
print("="*80)

for feat in useful_excluded:
    print(f"\n📌 {feat['column']}")
    print(f"   Type: {feat['dtype']}")
    print(f"   Unique values: {feat['unique_count']}")
    print(f"   Null %: {feat['null_pct']:.1f}%")
    if feat['correlation']:
        print(f"   Correlation with target: {feat['correlation']:.4f}")
    if feat['can_encode']:
        print(f"   ✅ Can be one-hot encoded ({feat['unique_count']} categories)")
    
    # Show sample values
    sample_vals = full_df[feat['column']].value_counts().head(5)
    print(f"   Sample values:")
    for val, count in sample_vals.items():
        print(f"      • {val}: {count} ({count/len(full_df)*100:.1f}%)")

# Summary
print("\n" + "="*80)
print("📋 SUMMARY")
print("="*80)
print(f"Total columns in database: {len(all_db_features)}")
print(f"Currently using: {len(current_features)}")
print(f"Excluded: {len(excluded)}")
print(f"Potentially useful excluded: {len(useful_excluded)}")

if useful_excluded:
    print(f"\n⚠️  RECOMMENDATION:")
    print(f"   Consider adding these {len(useful_excluded)} features:")
    for feat in useful_excluded[:10]:
        print(f"      • {feat['column']}")
    if len(useful_excluded) > 10:
        print(f"      ... and {len(useful_excluded) - 10} more")

print("\n" + "="*80)
