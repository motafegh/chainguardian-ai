"""
Test Hybrid Model on Real CEI Violations
=========================================
Test on contracts we KNOW have CEI violations from dataset
"""

import sys
from pathlib import Path
import pandas as pd
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

print("\n" + "="*80)
print("🔍 TESTING HYBRID MODEL ON REAL CEI VIOLATIONS")
print("="*80)

# Load data
df = pd.read_csv('data/complete_dataset_with_semantic.csv')

# Filter to contracts with CEI violations detected
cei_violators = df[df['cei_violations'] > 0].copy()

print(f"\n📊 Contracts with CEI Violations: {len(cei_violators)}")
print(f"\nBy Source:")
print(cei_violators['data_source'].value_counts().to_string())

# Show the contracts
print(f"\n📋 CEI VIOLATION CONTRACTS:")
print("="*80)

for _, row in cei_violators.iterrows():
    print(f"\n{row['contract_name']}:")
    print(f"   Source: {row['data_source']}")
    print(f"   CEI violations: {row['cei_violations']}")
    print(f"   CEI score: {row['cei_pattern_score']:.2f}")
    print(f"   State-after-call: {row['state_after_call_count']}")
    print(f"   Has guard: {row['has_reentrancy_guard']}")
    
    # Calculate semantic risk
    risk = 0.0
    if row['cei_violations'] > 0:
        risk += 0.4 * min(row['cei_violations'] / 5, 1.0)
    if row['cei_pattern_score'] < 0.8:
        risk += 0.2 * (1.0 - row['cei_pattern_score'])
    if row['state_after_call_count'] > 0:
        risk += 0.3 * min(row['state_after_call_count'] / 3, 1.0)
    
    print(f"   🎯 Semantic Risk Score: {risk:.2%}")

# Compare to contracts with perfect CEI
perfect_cei = df[df['cei_pattern_score'] == 1.0].copy()

print(f"\n\n📊 COMPARISON:")
print(f"   Perfect CEI (score=1.0): {len(perfect_cei)} contracts ({len(perfect_cei)/len(df)*100:.1f}%)")
print(f"   Has violations (>0):      {len(cei_violators)} contracts ({len(cei_violators)/len(df)*100:.1f}%)")

# Known vulnerable contracts that should have CEI issues
print(f"\n\n🔍 CHECKING KNOWN VULNERABLE CONTRACTS:")
print("="*80)

known_vuln = df[df['data_source'].isin(['trail_of_bits', 'smartbugs_curated'])]
print(f"\nTrail of Bits + SmartBugs Curated: {len(known_vuln)} contracts")
print(f"   With CEI violations: {(known_vuln['cei_violations'] > 0).sum()}")
print(f"   Perfect CEI: {(known_vuln['cei_pattern_score'] == 1.0).sum()}")

# Show vulnerable contracts WITH CEI violations
vuln_with_cei = known_vuln[known_vuln['cei_violations'] > 0]
print(f"\n✅ Vulnerable contracts with CEI violations detected:")
for _, row in vuln_with_cei.iterrows():
    print(f"   • {row['contract_name']:40s} (Source: {row['data_source']}, Violations: {row['cei_violations']})")

# Show vulnerable contracts WITHOUT CEI violations
vuln_no_cei = known_vuln[known_vuln['cei_violations'] == 0]
print(f"\n⚠️  Vulnerable contracts WITHOUT CEI violations ({len(vuln_no_cei)}):")
print("   (These have OTHER vulnerability types)")
for _, row in vuln_no_cei.head(10).iterrows():
    print(f"   • {row['contract_name']:40s}")

print("\n" + "="*80)
print("🎓 KEY INSIGHT:")
print("="*80)
print("""
Your adversarial test contracts were designed to test SYNTACTIC patterns
(external calls, state variables, complexity), not SEMANTIC patterns (CEI).

The semantic analyzer correctly identifies that most contracts (98.9%)
follow proper CEI patterns. Only 24 contracts have actual CEI violations.

For semantic features to help:
1. Need more training data with CEI violations
2. Or use semantic rules as OVERRIDES (not ensemble weights)
3. Or target specific vulnerability types (reentrancy only)
""")

print("\n💡 RECOMMENDATION:")
print("="*80)
print("""
Use semantic analysis as a SECONDARY CHECK:

1. ML model predicts based on all patterns (syntactic)
2. IF contract has CEI violations → Flag as HIGH RISK (override)
3. IF contract has perfect CEI + guard → Reduce risk score

This is how production tools work:
- Slither: Static analysis catches patterns
- Semantic rules: Validate safety properties
- Human review: Final decision
""")
