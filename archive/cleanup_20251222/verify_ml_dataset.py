import pandas as pd
import numpy as np

df = pd.read_csv("data/training_with_semantic_20251222.csv")

print("="*80)
print("ML DATASET VERIFICATION")
print("="*80)

# 1. Check for missing values
print(f"\n1. MISSING VALUES")
missing = df.isnull().sum()
missing = missing[missing > 0].sort_values(ascending=False)
if len(missing) > 0:
    print(missing.head(10))
else:
    print("   ✅ No missing values!")

# 2. Check label distribution by data source
print(f"\n2. LABEL BY DATA SOURCE")
print(df.groupby("data_source")["label"].value_counts().unstack(fill_value=0))

# 3. Check key semantic features
print(f"\n3. SEMANTIC FEATURES STATS")
semantic_cols = [c for c in df.columns if "cei" in c.lower() or "reentrancy" in c.lower()]
for col in semantic_cols[:8]:  # Show first 8
    if df[col].dtype in ['int64', 'float64']:
        print(f"   {col}: mean={df[col].mean():.3f}, max={df[col].max():.1f}, non-zero={sum(df[col] > 0)}")
    else:
        print(f"   {col}: True={sum(df[col])}/{len(df)}")

# 4. Check feature types
print(f"\n4. FEATURE TYPES")
print(f"   Boolean: {sum(df.dtypes == 'bool')}")
print(f"   Numeric: {sum(df.dtypes.isin(['int64', 'float64']))}")
print(f"   Object: {sum(df.dtypes == 'object')}")

# 5. Check for constant columns (useless for ML)
print(f"\n5. CONSTANT COLUMNS (zero variance)")
for col in df.columns:
    if df[col].dtype in ['int64', 'float64', 'bool']:
        if df[col].nunique() == 1:
            print(f"   ⚠️  {col}: always {df[col].iloc[0]}")

print("\n" + "="*80)
