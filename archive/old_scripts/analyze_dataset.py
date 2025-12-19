"""
Analyze our combined dataset quality

🎓 Goal: Understand what we have before ML training
"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd
from collections import Counter

def analyze_dataset():
    """Analyze the combined dataset."""
    
    db = DatabaseManager()
    df = db.get_all_features()
    
    print("="*70)
    print("📊 DATASET QUALITY ANALYSIS")
    print("="*70)
    print()
    
    # Basic stats
    print("📈 OVERALL STATISTICS:")
    print(f"  Total contracts: {len(df)}")
    print(f"  Successful extractions: {df['failure_reason'].isna().sum()}")
    print(f"  Failed extractions: {df['failure_reason'].notna().sum()}")
    print()
    
    # Source breakdown
    print("📁 CONTRACTS BY SOURCE:")
    
    # Count by source prefix
    source_counts = Counter()
    for source in df['address'].fillna(''):
        if 'smartbugs' in source.lower() or source == '':
            source_counts['SmartBugs'] += 1
        else:
            source_counts['Your Collection'] += 1
    
    for source, count in source_counts.most_common():
        print(f"  {source:20s}: {count:3d} contracts")
    print()
    
    # Success rate by source
    successful = df[df['failure_reason'].isna()]
    
    print("✅ SUCCESSFUL EXTRACTIONS:")
    print(f"  Total successful: {len(successful)}")
    print(f"  With reentrancy: {successful['has_reentrancy'].sum()}")
    print(f"  With access control issues: {successful['has_access_control_issues'].sum()}")
    print(f"  With timestamp dependency: {successful['has_timestamp_dependency'].sum()}")
    print(f"  With unchecked calls: {successful['has_unchecked_call'].sum()}")
    print()
    
    # Vulnerability distribution
    print("🐛 VULNERABILITY DISTRIBUTION (Successful Contracts):")
    vuln_contracts = successful[
        (successful['has_reentrancy'] == True) |
        (successful['has_access_control_issues'] == True) |
        (successful['has_timestamp_dependency'] == True) |
        (successful['has_unchecked_call'] == True)
    ]
    safe_contracts = successful[
        (successful['has_reentrancy'] == False) &
        (successful['has_access_control_issues'] == False) &
        (successful['has_timestamp_dependency'] == False) &
        (successful['has_unchecked_call'] == False)
    ]
    
    print(f"  Vulnerable: {len(vuln_contracts)} ({len(vuln_contracts)/len(successful)*100:.1f}%)")
    print(f"  Safe: {len(safe_contracts)} ({len(safe_contracts)/len(successful)*100:.1f}%)")
    print()
    
    # Feature completeness
    print("📊 FEATURE COMPLETENESS:")
    feature_cols = [
        'num_functions', 'num_external_calls', 'num_state_vars',
        'num_modifiers', 'max_cyclomatic_complexity', 'num_low_level_calls'
    ]
    
    for col in feature_cols:
        non_zero = (successful[col] > 0).sum()
        print(f"  {col:30s}: {non_zero:3d} contracts ({non_zero/len(successful)*100:.1f}%)")
    print()
    
    # Failure reasons
    failed = df[df['failure_reason'].notna()]
    if len(failed) > 0:
        print("❌ FAILURE REASONS:")
        failure_counts = failed['failure_reason'].value_counts()
        for reason, count in failure_counts.items():
            print(f"  {reason:30s}: {count:3d} contracts")
        print()
    
    # ML readiness
    print("="*70)
    print("🎯 ML TRAINING READINESS")
    print("="*70)
    print()
    print(f"✅ Usable for training: {len(successful)} contracts")
    print(f"✅ Vulnerable samples: {len(vuln_contracts)} ({len(vuln_contracts)/len(successful)*100:.1f}%)")
    print(f"✅ Safe samples: {len(safe_contracts)} ({len(safe_contracts)/len(successful)*100:.1f}%)")
    print()
    
    # Class balance check
    balance_ratio = len(vuln_contracts) / len(safe_contracts) if len(safe_contracts) > 0 else 0
    print(f"📊 Class balance ratio: {balance_ratio:.2f}")
    
    if balance_ratio < 0.3:
        print("   ⚠️  Imbalanced (need SMOTE for ML)")
    elif balance_ratio > 0.7:
        print("   ✅ Well balanced!")
    else:
        print("   ✅ Acceptable (can use SMOTE if needed)")
    print()
    
    print("="*70)
    print("🎉 DATASET IS READY FOR ML TRAINING!")
    print("="*70)
    print()
    print("Next steps:")
    print("  1. Train baseline model on SmartBugs (labeled data)")
    print("  2. Evaluate model performance")
    print("  3. Predict on your 166 contracts")
    print("  4. Retrain on combined dataset")
    print()

if __name__ == "__main__":
    analyze_dataset()