"""
Re-extract features for adversarial contracts WITH semantic analysis
"""

import sys
from pathlib import Path
import pandas as pd
import tempfile
import shutil
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.feature_extraction.pipeline import FeaturePipeline
import re


def extract_contract_names(source_code: str) -> list:
    """Extract contract names from Solidity source."""
    pattern = r'(?:abstract\s+)?(?:contract|library|interface)\s+([A-Z][a-zA-Z0-9_]*)'
    return re.findall(pattern, source_code)


print("\n" + "="*70)
print("🔬 EXTRACTING FEATURES WITH SEMANTIC ANALYSIS")
print("="*70)

test_dir = Path('test_contracts')
test_files = sorted(test_dir.glob('*.sol'))

print(f"\n📂 Found {len(test_files)} contracts\n")

pipeline = FeaturePipeline()
results = []

for test_file in test_files:
    print(f"📄 {test_file.name}")
    
    try:
        source = test_file.read_text()
        names = extract_contract_names(source)
        
        if not names:
            print(f"   ⚠️  No contract found\n")
            continue
        
        contract_name = names[0]
        
        # Create temp copy
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / test_file.name
            shutil.copy(test_file, tmp_file)
            
            # Extract features
            features = pipeline.analyze_contract(
                tmp_file,
                contract_name,
                {'address': f"0x{uuid.uuid4().hex[:40]}", 'data_source': 'adversarial'}
            )
            
            # Show key semantic features
            print(f"   CEI violations: {features.get('cei_violations', 0)}")
            print(f"   CEI score: {features.get('cei_pattern_score', 0):.2f}")
            print(f"   Has guard: {features.get('has_reentrancy_guard', False)}")
            print(f"   External calls: {features.get('num_external_calls', 0)}")
            print(f"   State vars: {features.get('num_state_vars', 0)}\n")
            
            results.append(features)
    
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

# Save to CSV
if results:
    df = pd.DataFrame(results)
    df.to_csv('data/adversarial_with_semantic.csv', index=False)
    
    print("="*70)
    print(f"✅ SAVED {len(df)} contracts with {len(df.columns)} features")
    print(f"📁 Output: data/adversarial_with_semantic.csv")
    print("="*70)
    
    # Show semantic feature summary
    print("\n📊 SEMANTIC FEATURE SUMMARY:")
    print("-" * 70)
    print(f"  CEI violations detected: {df['cei_violations'].sum()}")
    print(f"  Contracts with perfect CEI: {(df['cei_pattern_score'] == 1.0).sum()}")
    print(f"  Contracts with reentrancy guard: {df['has_reentrancy_guard'].sum()}")
    print(f"  Average CEI score: {df['cei_pattern_score'].mean():.2f}")
    print("="*70 + "\n")
else:
    print("\n❌ No features extracted")
