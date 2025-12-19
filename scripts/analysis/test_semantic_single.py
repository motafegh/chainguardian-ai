"""
Test semantic feature extraction on single contract
"""

import sys
from pathlib import Path
import tempfile
import shutil
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

# Test on false_positive_trap (should show CEI safe)
test_file = Path('test_contracts/12_false_positive_trap.sol')

print("\n🧪 TESTING SEMANTIC FEATURES")
print("="*60)
print(f"Contract: {test_file.name}\n")

with tempfile.TemporaryDirectory() as tmpdir:
    tmp_file = Path(tmpdir) / test_file.name
    shutil.copy(test_file, tmp_file)
    
    pipeline = FeaturePipeline()
    success = pipeline.analyze_contract(
        tmp_file,
        'FalsePositiveTrap',
        {'address': f"0x{uuid.uuid4().hex[:40]}", 'data_source': 'test'}
    )
    
    if not success:
        print("❌ Extraction failed")
        sys.exit(1)
    
    df = pipeline.to_dataframe()
    row = df.iloc[-1]
    
    print("📊 SEMANTIC FEATURES:")
    print("-" * 60)
    semantic_features = [
        'cei_violations',
        'cei_safe_functions', 
        'cei_pattern_score',
        'has_reentrancy_guard',
        'functions_with_reentrancy_guard',
        'state_before_call_count',
        'state_after_call_count',
        'unchecked_calls_in_critical_context',
    ]
    
    for feat in semantic_features:
        if feat in row.index:
            val = row[feat]
            emoji = "✅" if feat in ['cei_safe_functions', 'has_reentrancy_guard', 'state_before_call_count'] and val > 0 else "📊"
            emoji = "⚠️" if feat in ['cei_violations', 'state_after_call_count', 'unchecked_calls_in_critical_context'] and val > 0 else emoji
            print(f"  {emoji} {feat:45s}: {val}")
        else:
            print(f"  ❌ {feat:45s}: NOT FOUND")
    
    print("\n" + "="*60)
    print("\n💡 INTERPRETATION:")
    
    cei_score = row.get('cei_pattern_score', 0)
    cei_violations = row.get('cei_violations', 0)
    has_guard = row.get('has_reentrancy_guard', False)
    
    if cei_score > 0.8:
        print("  ✅ Contract follows CEI pattern well")
    elif cei_violations > 0:
        print(f"  ⚠️  Found {cei_violations} CEI violations")
    
    if has_guard:
        print("  ✅ Has reentrancy protection")
    else:
        print("  ⚠️  No explicit reentrancy guard")
    
    print("="*60)
