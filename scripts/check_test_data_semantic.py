"""
Check if test data has semantic features
"""
import pandas as pd

df = pd.read_csv("data/ml_ready_v4.csv")

# Get one vulnerable contract
vuln = df[df['ground_truth_vulnerable'] == 1].iloc[0]

print("📋 Semantic features in test data:")
semantic_features = [
    'cei_violations',
    'cei_pattern_score', 
    'state_after_call_count',
    'has_reentrancy_guard'
]

for feat in semantic_features:
    if feat in df.columns:
        value = vuln[feat]
        print(f"   ✅ {feat:30s} = {value}")
    else:
        print(f"   ❌ {feat:30s} MISSING!")

print(f"\n📊 Sample vulnerable contract:")
print(f"   Name: {vuln['contract_name']}")
print(f"   Ground Truth: {vuln['ground_truth_vulnerable']}")

# Check all vulnerable contracts
print(f"\n📊 CEI violations across vulnerable contracts:")
vuln_contracts = df[df['ground_truth_vulnerable'] == 1]
if 'cei_violations' in df.columns:
    cei_stats = vuln_contracts['cei_violations'].describe()
    print(f"   Mean: {cei_stats['mean']:.2f}")
    print(f"   Max:  {cei_stats['max']:.0f}")
    print(f"   Min:  {cei_stats['min']:.0f}")
    print(f"   Zero CEI: {(vuln_contracts['cei_violations'] == 0).sum()} / {len(vuln_contracts)}")
else:
    print("   ❌ cei_violations column missing!")
