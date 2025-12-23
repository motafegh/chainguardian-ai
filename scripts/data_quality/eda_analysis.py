#!/usr/bin/env python3
"""
🚀 ChainGuardian DATA EDA - BULLETPROOF VERSION
Handles strings, categoricals, ALL data types
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("\n" + "="*80)
print("📊 CHAINGUARDIAN PRODUCTION DATASET EDA (BULLETPROOF)")
print("="*80)

# Load dataset
df = pd.read_csv("data/ml_final_train_dataset.csv")
print(f"✅ Loaded {len(df):,} samples × {df.shape[1]-1} features")
print(f"🔴 Vulnerable: {df['ground_truth_vulnerable'].mean():.1%}")

X = df.drop(columns=['ground_truth_vulnerable'])
y = df['ground_truth_vulnerable']

print(f"📊 Dataset balance: {y.value_counts().to_dict()}")

# =====================================================
# 1. DATA CLEANING - SEPARATE NUMERIC FEATURES
# =====================================================
print("\n🔧 1. CLEANING NUMERIC FEATURES ONLY")
numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

print(f"   📊 Numeric features: {len(numeric_cols)}")
print(f"   🔤  Categorical:    {len(categorical_cols)}")
print(f"   🔤  Categorical examples: {categorical_cols[:3]}")

X_numeric = X[numeric_cols]

# =====================================================
# 2. TOP PREDICTORS (Numeric variance)
# =====================================================
print("\n🏆 2. TOP 10 ML PREDICTORS")
if len(X_numeric.columns) > 0:
    top_features = X_numeric.var().sort_values(ascending=False).head(10)
    print(top_features.round(3))
    
    # Vulnerable averages
    print("\n🔴 Vulnerable Averages (Top 5):")
    vuln_means = X_numeric[y==1].mean().sort_values(ascending=False).head(5)
    print(vuln_means.round(3))
else:
    print("⚠️  No numeric features found!")

# =====================================================
# 3. VULNERABILITY FLAGS
# =====================================================
print("\n🔍 3. VULNERABILITY FLAGS")
vuln_flags = [col for col in X.columns if col.startswith('has_')]
bool_flags = [col for col in vuln_flags if col in X_numeric.columns]

if bool_flags:
    flag_stats = X_numeric[bool_flags].sum().sort_values(ascending=False).head(10)
    print("Top 10 flags:")
    print(flag_stats.round(0).astype(int))
    
    plt.figure(figsize=(12, 6))
    flag_stats.head(12).plot(kind='barh')
    plt.title('Top Vulnerability Flags (Affected Contracts)')
    plt.xlabel('Count')
    plt.tight_layout()
    plt.savefig('data/eda_vuln_flags.png', dpi=300, bbox_inches='tight')
    plt.show()
else:
    print("No boolean vulnerability flags found")

# =====================================================
# 4. FEATURE PYRAMID (Count-based)
# =====================================================
print("\n🏗️  4. 5-LAYER PYRAMID")
layers = {
    'Slither': len([col for col in X.columns if 'has_' in col or '_count' in col]),
    'AST': len([col for col in X.columns if 'num_' in col or 'lines_of_code' in col]),
    'Graph': len([col for col in X_numeric.columns if any(g in col for g in ['cfg_', 'cg_', 'dfg_'])]),
    'Semantic': len([col for col in X_numeric.columns if any(s in col for s in ['cei_', 'reentrancy_guard'])]),
    'Risk': len([col for col in X_numeric.columns if 'risk_score' in col or 'is_high_risk' in col])
}

plt.figure(figsize=(10, 6))
plt.pie(layers.values(), labels=layers.keys(), autopct='%1.1f%%')
plt.title('Feature Pyramid Distribution')
plt.savefig('data/eda_pyramid.png', dpi=300)
plt.show()

print("Layer counts:", layers)

# =====================================================
# 5. TOP DISTRIBUTIONS (Safe/Vuln if possible)
# =====================================================
print("\n📊 5. TOP DISTRIBUTIONS")
if len(X_numeric.columns) > 0:
    top_predictors = X_numeric.std().sort_values(ascending=False).head(6).index.tolist()
    
    n_cols = 3
    n_rows = (len(top_predictors) + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
    axes = axes.flat if n_rows * n_cols > 1 else [axes]
    
    for i, feature in enumerate(top_predictors):
        ax = axes[i]
        X_numeric[feature].hist(bins=20, alpha=0.7, ax=ax, color='skyblue', label='All')
        
        # Add vuln overlay if not 100% vuln
        if y.nunique() > 1:
            X_numeric[y==1][feature].hist(bins=20, alpha=0.7, ax=ax, color='red')
            ax.legend(['All', 'Vulnerable'])
        
        ax.set_title(f'{feature}\n(μ={X_numeric[feature].mean():.2f})')
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('Top 6 Most Variable Features', fontsize=16)
    plt.tight_layout()
    plt.savefig('data/eda_distributions.png', dpi=300, bbox_inches='tight')
    plt.show()
else:
    print("No numeric features for distributions")

# =====================================================
# 6. CORRELATION HEATMAP (Top numeric)
# =====================================================
if len(X_numeric.columns) >= 10:
    print("\n🔗 6. CORRELATION HEATMAP")
    top_corr_features = X_numeric.std().sort_values(ascending=False).head(15).index
    corr_matrix = X_numeric[top_corr_features].corr()
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=False, cmap='RdBu_r', center=0, square=True)
    plt.title('Feature Correlation Heatmap (Top 15 Numeric)')
    plt.tight_layout()
    plt.savefig('data/eda_correlation.png', dpi=300, bbox_inches='tight')
    plt.show()
else:
    print("Not enough numeric features for correlation")

# =====================================================
# 7. SUMMARY TABLE
# =====================================================
print("\n📋 7. SUMMARY")
print(f"\n✅ Dataset: {len(df):,} samples, {len(numeric_cols)} numeric features")
print(f"✅ Charts saved:")
print("   📊 data/eda_vuln_flags.png")
print("   🏗️  data/eda_pyramid.png")
print("   📈 data/eda_distributions.png")
if len(X_numeric.columns) >= 10:
    print("   🔗 data/eda_correlation.png")

print("\n🎯 EDA COMPLETE - Dataset ready for ML training!")
