"""
ChainGuardian AI - Dataset Inspection
Run before Day 1 to understand data structure
"""

import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv('data/chainguardian_features_clean.csv')

print("="*70)
print("CHAINGUARDIAN AI - DATASET INSPECTION")
print("="*70)

# ════════════════════════════════════════════════════════════════════
# 1. COLUMN BREAKDOWN
# ════════════════════════════════════════════════════════════════════

# Identify column types
meta_cols = ['contract_id', 'contract_name', 'address', 'file_path', 'compiler_version']
vuln_cols = [c for c in df.columns if c.startswith('has_')]
feature_cols = [c for c in df.columns if c not in meta_cols + vuln_cols]

print(f"\n📊 COLUMN TYPES:")
print(f"   Total columns: {len(df.columns)}")
print(f"   ├─ Metadata: {len(meta_cols)} columns")
print(f"   ├─ Features: {len(feature_cols)} columns")
print(f"   └─ Vulnerabilities: {len(vuln_cols)} labels")

# ════════════════════════════════════════════════════════════════════
# 2. FEATURE COLUMNS (What we'll analyze on Day 1)
# ════════════════════════════════════════════════════════════════════

print(f"\n🔢 FEATURE COLUMNS ({len(feature_cols)}):")
for i, col in enumerate(feature_cols, 1):
    sample_val = df[col].iloc[0] if len(df) > 0 else 'N/A'
    dtype = df[col].dtype
    print(f"   {i:2d}. {col:40s} (type: {dtype}, sample: {sample_val})")

# ════════════════════════════════════════════════════════════════════
# 3. VULNERABILITY DISTRIBUTION (Class Imbalance Analysis)
# ════════════════════════════════════════════════════════════════════

print(f"\n⚠️  VULNERABILITY DISTRIBUTION:")
print(f"   {'Vulnerability':<40s} {'Count':>6s} {'%':>6s} {'Ratio':>10s}")
print(f"   {'-'*40} {'-'*6} {'-'*6} {'-'*10}")

vuln_stats = []
for vuln in vuln_cols:
    count = df[vuln].sum()
    pct = (count / len(df)) * 100
    ratio = len(df) / (count + 0.001)  # Avoid division by zero
    vuln_stats.append({
        'vulnerability': vuln,
        'count': int(count),
        'pct': pct,
        'ratio': ratio
    })
    print(f"   {vuln:<40s} {int(count):>6d} {pct:>6.1f}% {ratio:>9.1f}:1")

# Identify most/least common
vuln_stats_df = pd.DataFrame(vuln_stats)
most_common = vuln_stats_df.nlargest(3, 'count')
least_common = vuln_stats_df.nsmallest(3, 'count')

print(f"\n   Most common vulnerabilities:")
for _, row in most_common.iterrows():
    print(f"      • {row['vulnerability']}: {row['count']} contracts")

print(f"\n   Least common (hardest to detect):")
for _, row in least_common.iterrows():
    print(f"      • {row['vulnerability']}: {row['count']} contracts")

# ════════════════════════════════════════════════════════════════════
# 4. DATA QUALITY CHECKS
# ════════════════════════════════════════════════════════════════════

print(f"\n❓ DATA QUALITY:")

# Missing values
missing = df[feature_cols].isnull().sum()
if missing.sum() == 0:
    print("   ✅ No missing values in features!")
else:
    print(f"   ⚠️ Missing values found:")
    for col in missing[missing > 0].index:
        print(f"      {col}: {missing[col]} missing ({missing[col]/len(df)*100:.1f}%)")

# Zero variance features (useless for ML)
zero_var = [col for col in feature_cols if df[col].nunique() <= 1]
if zero_var:
    print(f"\n   ⚠️ Zero-variance features (consider removing):")
    for col in zero_var:
        print(f"      {col}: {df[col].unique()}")
else:
    print("   ✅ All features have variance")

# Duplicate rows
duplicates = df.duplicated(subset=feature_cols).sum()
if duplicates > 0:
    print(f"   ⚠️ {duplicates} duplicate rows found")
else:
    print("   ✅ No duplicate rows")

# ════════════════════════════════════════════════════════════════════
# 5. FEATURE STATISTICS (Basic)
# ════════════════════════════════════════════════════════════════════

print(f"\n📈 FEATURE STATISTICS (Sample - Top 5 Features):")
print(df[feature_cols[:5]].describe().round(2))

# ════════════════════════════════════════════════════════════════════
# 6. SAMPLE CONTRACTS
# ════════════════════════════════════════════════════════════════════

print(f"\n📄 SAMPLE CONTRACTS:")
print("\nVulnerable Contract Example:")
vuln_contract = df[df[vuln_cols].sum(axis=1) > 0].iloc[0]
print(f"   Address: {vuln_contract.get('address', 'N/A')}")
print(f"   Name: {vuln_contract.get('contract_name', 'N/A')}")
print(f"   Vulnerabilities: {[v.replace('has_', '') for v in vuln_cols if vuln_contract[v] == 1]}")
print(f"   Sample features: {dict(vuln_contract[feature_cols[:3]])}")

print("\nClean Contract Example:")
clean_contract = df[df[vuln_cols].sum(axis=1) == 0].iloc[0]
print(f"   Address: {clean_contract.get('address', 'N/A')}")
print(f"   Name: {clean_contract.get('contract_name', 'N/A')}")
print(f"   Sample features: {dict(clean_contract[feature_cols[:3]])}")

# ════════════════════════════════════════════════════════════════════
# 7. RECOMMENDATIONS FOR DAY 1
# ════════════════════════════════════════════════════════════════════

print(f"\n💡 RECOMMENDATIONS FOR DAY 1:")

# Severe imbalance?
severe_imbalance = [v for v, s in zip(vuln_cols, vuln_stats) if s['ratio'] > 20]
if severe_imbalance:
    print(f"   • Focus on class imbalance for: {', '.join([v.replace('has_', '') for v in severe_imbalance[:3]])} (ratio > 20:1)")

# Feature count
if len(feature_cols) < 20:
    print(f"   • {len(feature_cols)} features is good for baseline, but aim for 30+ with graph features")
elif len(feature_cols) > 50:
    print(f"   • {len(feature_cols)} features - consider feature selection to remove redundancy")

# Vulnerability prioritization
print(f"   • Prioritize these 10 critical vulnerabilities:")
critical = [
    'has_reentrancy', 'has_access_control_issues', 'has_unchecked_call',
    'has_timestamp_dependency', 'has_controlled_delegatecall',
    'has_uninitialized_state', 'has_tx_origin', 'has_delegatecall_loop',
    'has_reentrancy_unlimited', 'has_reentrancy_events'
]
for vuln in critical:
    if vuln in vuln_cols:
        stats = next(s for s in vuln_stats if s['vulnerability'] == vuln)
        print(f"      • {vuln.replace('has_', '')}: {stats['count']} samples")

print("\n" + "="*70)
print("✅ INSPECTION COMPLETE - READY FOR DAY 1!")
print("="*70)
print("\nNext step: Run Day 1, Session 1A - Load this data and start deep EDA!")
