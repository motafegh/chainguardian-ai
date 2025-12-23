"""
Test Feature Engineering Pipeline
=================================
Verify feature engineering works with real ChainGuardian data.

Author: Ali
Date: December 22, 2024
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

import pandas as pd
import numpy as np
from chainguardian.ml.data_engineering.feature_engineer import FeatureEngineer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("🧪 TESTING FEATURE ENGINEERING PIPELINE")
print("="*80)

# ============================================================================
# LOAD REAL DATA
# ============================================================================
print("\n📥 Loading dataset...")
data_path = Path("data/ml_ready_v3.csv")

if not data_path.exists():
    print(f"❌ Dataset not found: {data_path}")
    print(f"   Run: poetry run python scripts/data_quality/data_quality_report_v3.py")
    exit(1)

df = pd.read_csv(data_path)
print(f"   Loaded: {len(df)} samples × {len(df.columns)} features")

# Separate features from labels/metadata
exclude_cols = ['ground_truth_vulnerable', 'contract_name', 'data_source']
feature_cols = [col for col in df.columns if col not in exclude_cols]

# Get original numeric features
X_original = df[feature_cols].select_dtypes(include=[np.number])
print(f"   Original numeric features: {len(X_original.columns)}")

# ============================================================================
# INITIALIZE FEATURE ENGINEER
# ============================================================================
print("\n🔧 Initializing Feature Engineer...")
engineer = FeatureEngineer(degree=2)

# ============================================================================
# STEP 1: INTERACTION FEATURES
# ============================================================================
print("\n" + "-"*80)
print("STEP 1: Creating Interaction Features")
print("-"*80)

X_with_interactions = engineer.create_interaction_features(X_original.copy())

print(f"\n📊 Results:")
print(f"   Before: {len(X_original.columns)} features")
print(f"   After:  {len(X_with_interactions.columns)} features")
print(f"   Added:  {len(X_with_interactions.columns) - len(X_original.columns)}")

# Show sample of new features
interaction_features = [
    col for col in X_with_interactions.columns 
    if col not in X_original.columns
]
print(f"\n   New interaction features:")
for feat in interaction_features[:5]:
    print(f"      • {feat}")
    # Show statistics
    stats = X_with_interactions[feat].describe()
    print(f"        Range: [{stats['min']:.2f}, {stats['max']:.2f}], "
          f"Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}")

# ============================================================================
# STEP 2: RATIO FEATURES
# ============================================================================
print("\n" + "-"*80)
print("STEP 2: Creating Ratio Features")
print("-"*80)

X_with_ratios = engineer.create_ratio_features(X_with_interactions.copy())

print(f"\n📊 Results:")
print(f"   Before: {len(X_with_interactions.columns)} features")
print(f"   After:  {len(X_with_ratios.columns)} features")
print(f"   Added:  {len(X_with_ratios.columns) - len(X_with_interactions.columns)}")

# Show sample of ratio features
ratio_features = [
    col for col in X_with_ratios.columns 
    if col not in X_with_interactions.columns
]
print(f"\n   New ratio features:")
for feat in ratio_features[:5]:
    print(f"      • {feat}")
    stats = X_with_ratios[feat].describe()
    print(f"        Range: [{stats['min']:.2f}, {stats['max']:.2f}], "
          f"Mean: {stats['mean']:.2f}")

# ============================================================================
# STEP 3: DOMAIN FEATURES
# ============================================================================
print("\n" + "-"*80)
print("STEP 3: Creating Domain Features")
print("-"*80)

X_with_domain = engineer.create_domain_features(X_with_ratios.copy())

print(f"\n📊 Results:")
print(f"   Before: {len(X_with_ratios.columns)} features")
print(f"   After:  {len(X_with_domain.columns)} features")
print(f"   Added:  {len(X_with_domain.columns) - len(X_with_ratios.columns)}")

# Show domain features
domain_features = [
    col for col in X_with_domain.columns 
    if col not in X_with_ratios.columns
]
print(f"\n   New domain features:")
for feat in domain_features:
    print(f"      • {feat}")
    stats = X_with_domain[feat].describe()
    print(f"        Range: [{stats['min']:.2f}, {stats['max']:.2f}], "
          f"Mean: {stats['mean']:.2f}")

# ============================================================================
# STEP 4: POLYNOMIAL FEATURES (Key features only)
# ============================================================================
print("\n" + "-"*80)
print("STEP 4: Creating Polynomial Features")
print("-"*80)

# Select key features for polynomial expansion
key_features = [
    'cei_violations',
    'lines_of_code', 
    'num_functions',
    'max_cyclomatic_complexity',
    'total_detector_hits'
]

# Check if all key features exist
available_key_features = [f for f in key_features if f in X_with_domain.columns]
print(f"   Key features for polynomial expansion: {len(available_key_features)}")
for feat in available_key_features:
    print(f"      • {feat}")

X_final = engineer.create_polynomial_features(
    X_with_domain.copy(),
    available_key_features
)

print(f"\n📊 Results:")
print(f"   Before: {len(X_with_domain.columns)} features")
print(f"   After:  {len(X_final.columns)} features")
print(f"   Added:  {len(X_final.columns) - len(X_with_domain.columns)}")

# Show sample polynomial features
poly_features = [
    col for col in X_final.columns 
    if col not in X_with_domain.columns
]
print(f"\n   Sample polynomial features:")
for feat in poly_features[:5]:
    print(f"      • {feat}")

# ============================================================================
# STEP 5: COMPLETE PIPELINE TEST
# ============================================================================
print("\n" + "="*80)
print("COMPLETE PIPELINE TEST")
print("="*80)

# Reset engineer
engineer_full = FeatureEngineer(degree=2)

# Run complete pipeline
X_engineered = engineer_full.engineer_features(
    X_original.copy(),
    poly_features=available_key_features
)

print(f"\n✅ Pipeline Complete:")
print(f"   Original features:   {len(X_original.columns)}")
print(f"   Engineered features: {len(X_engineered.columns)}")
print(f"   Total added:         {len(X_engineered.columns) - len(X_original.columns)}")
print(f"   Growth factor:       {len(X_engineered.columns) / len(X_original.columns):.2f}x")

# ============================================================================
# DATA QUALITY CHECKS
# ============================================================================
print("\n" + "-"*80)
print("DATA QUALITY CHECKS")
print("-"*80)

# Check for NaN values
nan_counts = X_engineered.isna().sum()
if nan_counts.sum() > 0:
    print(f"⚠️  NaN values found:")
    for col in nan_counts[nan_counts > 0].index:
        print(f"      {col}: {nan_counts[col]} NaNs")
else:
    print(f"✅ No NaN values")

# Check for infinite values
inf_counts = np.isinf(X_engineered.select_dtypes(include=[np.number])).sum()
if inf_counts.sum() > 0:
    print(f"⚠️  Infinite values found:")
    for col in inf_counts[inf_counts > 0].index:
        print(f"      {col}: {inf_counts[col]} infs")
else:
    print(f"✅ No infinite values")

# Check for constant features
constant_features = X_engineered.columns[X_engineered.nunique() == 1]
if len(constant_features) > 0:
    print(f"⚠️  Constant features (no variance):")
    for col in constant_features:
        print(f"      {col}: {X_engineered[col].unique()}")
else:
    print(f"✅ No constant features")

# ============================================================================
# EXPORT ENGINEERED DATASET
# ============================================================================
print("\n" + "-"*80)
print("EXPORT ENGINEERED DATASET")
print("-"*80)

output_path = Path("data/ml_engineered_features_v1.csv")
output_path.parent.mkdir(exist_ok=True)

# Combine with labels
X_engineered['ground_truth_vulnerable'] = df['ground_truth_vulnerable']
X_engineered['contract_name'] = df['contract_name']
X_engineered['data_source'] = df['data_source']

X_engineered.to_csv(output_path, index=False)

print(f"✅ Exported to: {output_path}")
print(f"   Shape: {X_engineered.shape}")
print(f"   Features: {len(X_engineered.columns) - 3} (+ 3 metadata)")

# ============================================================================
# FEATURE IMPORTANCE PREVIEW (Simple Correlation)
# ============================================================================
print("\n" + "-"*80)
print("FEATURE CORRELATION PREVIEW")
print("-"*80)

# Calculate correlation with target
numeric_features = X_engineered.select_dtypes(include=[np.number]).columns
correlations = X_engineered[numeric_features].corrwith(
    X_engineered['ground_truth_vulnerable']
).abs().sort_values(ascending=False)

print(f"\n🎯 Top 10 Most Correlated Features:")
for i, (feat, corr) in enumerate(correlations.head(10).items(), 1):
    if feat != 'ground_truth_vulnerable':
        print(f"   {i:2d}. {feat:40s} {corr:.4f}")

# Compare new vs original features in top 10
new_features_in_top10 = [
    feat for feat in correlations.head(10).index 
    if feat not in X_original.columns and feat != 'ground_truth_vulnerable'
]

if new_features_in_top10:
    print(f"\n✅ {len(new_features_in_top10)} engineered features in top 10!")
    print(f"   New features are predictive:")
    for feat in new_features_in_top10:
        print(f"      • {feat}")
else:
    print(f"\n⚠️  No engineered features in top 10")
    print(f"   Original features still dominate")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("✅ FEATURE ENGINEERING TEST COMPLETE")
print("="*80)

summary = {
    'Original Features': len(X_original.columns),
    'Interaction Features': len(interaction_features),
    'Ratio Features': len(ratio_features),
    'Domain Features': len(domain_features),
    'Polynomial Features': len(poly_features),
    'Total Features': len(X_engineered.columns) - 3,  # Exclude metadata
    'Growth Factor': f"{len(X_engineered.columns) / len(X_original.columns):.2f}x",
    'Dataset Size': f"{len(X_engineered)} samples",
    'Output File': str(output_path)
}

print("\n📊 SUMMARY:")
for key, value in summary.items():
    print(f"   {key:25s}: {value}")

print("\n🎯 NEXT STEPS:")
print("   1. Review feature correlations above")
print("   2. Proceed to feature selection (RFECV)")
print("   3. Train model with engineered features")

print("\n" + "="*80)
