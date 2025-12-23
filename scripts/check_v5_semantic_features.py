"""
Check if semantic features are in v5 model
"""
import json
from pathlib import Path

# Load v5 metadata
with open("models/feature_metadata_v5.json", 'r') as f:
    metadata = json.load(f)

features = metadata['feature_names']

print(f"📋 v5 Model has {len(features)} features\n")

# Check for semantic features
semantic_features = [
    'cei_violations',
    'cei_pattern_score',
    'state_after_call_count',
    'has_reentrancy_guard',
    'unchecked_calls_in_critical_context'
]

print("🔍 Checking for semantic features:")
for feat in semantic_features:
    if feat in features:
        idx = features.index(feat)
        print(f"   ✅ {feat:40s} at position {idx}")
    else:
        print(f"   ❌ {feat:40s} MISSING")

print(f"\n📊 First 20 features in v5:")
for i, f in enumerate(features[:20], 1):
    marker = "⭐" if f in semantic_features else "  "
    print(f"   {marker} {i:2d}. {f}")

print(f"\n💡 RECOMMENDATION:")
missing = [f for f in semantic_features if f not in features]
if missing:
    print(f"   ❌ {len(missing)} semantic features missing!")
    print(f"   These were probably removed as 'leakage' in v5")
    print(f"\n   OPTIONS:")
    print(f"   A) Retrain v5 keeping semantic features")
    print(f"   B) Use v4 model (has semantic features)")
    print(f"   C) Accept lower confidence without semantic layer")
else:
    print(f"   ✅ All semantic features present!")
