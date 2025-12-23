#!/usr/bin/env python3
"""Manual test of adversarial contract semantic extraction."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from chainguardian.feature_extraction.semantic_analyzer import SemanticAnalyzer
import logging

logging.basicConfig(level=logging.DEBUG)

# Test the most obvious reentrancy
contract_path = Path("data/adversarial_test_set/01_obvious_reentrancy.sol")

if not contract_path.exists():
    print(f"❌ Contract not found: {contract_path}")
    sys.exit(1)

print("="*80)
print(f"🧪 TESTING: {contract_path.name}")
print("="*80)

analyzer = SemanticAnalyzer()

try:
    features = analyzer.extract_features(str(contract_path))
    
    print(f"\n✅ EXTRACTION RESULT:")
    print(f"   CEI violations: {features.get('cei_violations', 'NOT FOUND')}")
    print(f"   CEI score: {features.get('cei_pattern_score', 'NOT FOUND')}")
    print(f"   Has reentrancy: {features.get('has_reentrancy', 'NOT FOUND')}")
    print(f"   State changes after calls: {features.get('state_changes_after_calls', 'NOT FOUND')}")
    print(f"   Reentrancy guard: {features.get('has_reentrancy_guard', 'NOT FOUND')}")
    
    print(f"\n📊 ALL FEATURES:")
    for k, v in sorted(features.items()):
        print(f"   {k}: {v}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
