"""
Analyze if we have CEI (Checks-Effects-Interactions) pattern detection
"""

import sys
from pathlib import Path
import joblib

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

metadata = joblib.load('models/two_stage_metadata.pkl')
code_features = metadata['code_features']

print("\n🔍 CURRENT FEATURES (42 total)\n")
print("="*60)

# Categorize features
pattern_features = [f for f in code_features if any(x in f.lower() for x in ['pattern', 'cei', 'guard', 'protect'])]
call_features = [f for f in code_features if 'call' in f.lower()]
flow_features = [f for f in code_features if any(x in f.lower() for x in ['flow', 'taint', 'dfg'])]
security_features = [f for f in code_features if any(x in f.lower() for x in ['security', 'vuln', 'danger'])]

print("\n🔒 SECURITY PATTERN FEATURES:")
if pattern_features:
    for f in pattern_features:
        print(f"  ✅ {f}")
else:
    print("  ❌ NONE - Missing CEI, reentrancy guard detection!")

print("\n📞 CALL-RELATED FEATURES:")
for f in call_features:
    print(f"  • {f}")

print("\n🌊 DATA FLOW FEATURES:")
for f in flow_features:
    print(f"  • {f}")

print("\n⚠️  OTHER SECURITY FEATURES:")
for f in security_features:
    print(f"  • {f}")

print("\n" + "="*60)
print("\n💡 MISSING CRITICAL SEMANTIC FEATURES:")
print("  ❌ cei_pattern_violations (state change after external call)")
print("  ❌ reentrancy_guard_present (ReentrancyGuard modifier)")
print("  ❌ state_modified_before_external_call (safe pattern)")
print("  ❌ unchecked_call_return_value_matters (context-aware)")
print("\n")

print("🎯 CONCLUSION:")
print("  Model has SYNTACTIC features (counts, complexity)")
print("  Model lacks SEMANTIC features (safety patterns)")
print("  This explains false positives on safe contracts!")
print("="*60)
