"""
Extract with semantic features - Direct CSV save (no database conflicts)
"""

import sys
from pathlib import Path
import pandas as pd
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

print("\n" + "="*70)
print("🔄 EXTRACTING WITH SEMANTIC FEATURES (Direct CSV)")
print("="*70)

# Find contracts
contract_dirs = [
    Path('data/safe_contracts'),
    Path('data/vulnerable_contracts'),
]

contracts = []
for dir_path in contract_dirs:
    if dir_path.exists():
        for sol_file in dir_path.rglob('*.sol'):
            contracts.append({
                'file_path': str(sol_file),
                'contract_name': sol_file.stem,
                'is_vulnerable': 'vulnerable' in str(sol_file),
            })

if not contracts:
    print("❌ No contracts found!")
    sys.exit(1)

df_contracts = pd.DataFrame(contracts)
print(f"\n✅ Found {len(df_contracts)} contracts")
print(f"⚡ Processing first 50 only (quick test)\n")

df_contracts = df_contracts.head(50)

# Extract WITHOUT database saves
all_features = []

for idx, row in df_contracts.iterrows():
    contract_path = Path(row['file_path'])
    contract_name = row['contract_name']
    
    if not contract_path.exists():
        continue
    
    try:
        # Use temporary pipeline to avoid database conflicts
        from chainguardian.feature_extraction.contract_analyzer import SlitherAnalyzer
        from chainguardian.feature_extraction.ast_analyzer import ASTFeatureExtractor
        from chainguardian.feature_extraction.graph_extractor import GraphFeatureExtractor
        from chainguardian.feature_extraction.semantic_analyzer import extract_semantic_features
        from slither import Slither
        import slither.detectors.all_detectors as detector_module
        import re
        import subprocess
        
        # Detect version
        content = contract_path.read_text(encoding='utf-8')
        pragma_match = re.search(r'pragma\s+solidity\s+([^;]+);', content)
        if pragma_match:
            pragma = pragma_match.group(1).strip()
            if '^' in pragma:
                version = re.search(r'([\d.]+)', pragma).group(1)
            else:
                version = re.search(r'([\d.]+)', pragma).group(1) if re.search(r'([\d.]+)', pragma) else '0.8.20'
        else:
            version = '0.8.20'
        
        # Set version and compile
        subprocess.run(['solc-select', 'use', version], capture_output=True)
        slither = Slither(str(contract_path), solc='solc', solc_disable_warnings=True)
        
        # Register detectors
        for name in dir(detector_module):
            if name[0].isupper():
                slither.register_detector(getattr(detector_module, name))
        
        # Extract features
        vuln_analyzer = SlitherAnalyzer(slither)
        vuln_features = vuln_analyzer.extract_features(contract_name)
        
        ast_extractor = ASTFeatureExtractor(contract_path, slither_obj=slither)
        ast_features = ast_extractor.extract_features(contract_name)
        
        graph_extractor = GraphFeatureExtractor(slither)
        graph_features = graph_extractor.extract_features(contract_name)
        
        # Semantic features - CRITICAL!
        target_contract = None
        for c in slither.contracts:
            if c.name == contract_name:
                target_contract = c
                break
        
        semantic_features = {}
        if target_contract:
            semantic_features = extract_semantic_features(target_contract)
        else:
            semantic_features = {
                'cei_violations': 0,
                'cei_safe_functions': 0,
                'cei_pattern_score': 1.0,
                'has_reentrancy_guard': False,
                'functions_with_reentrancy_guard': 0,
                'state_before_call_count': 0,
                'state_after_call_count': 0,
                'unchecked_calls_in_critical_context': 0,
            }
        
        # Combine all features
        combined = {
            'contract_name': contract_name,
            'file_path': str(contract_path),
            'address': f"0x{uuid.uuid4().hex[:40]}",
            'is_vulnerable': row['is_vulnerable'],
            
            # Vuln features
            'has_reentrancy': vuln_features.has_reentrancy,
            'has_unchecked_call': vuln_features.has_unchecked_call,
            'has_tx_origin': vuln_features.has_tx_origin,
            'has_controlled_delegatecall': vuln_features.has_controlled_delegatecall,
            'high_severity_count': vuln_features.high_severity_count,
            'medium_severity_count': vuln_features.medium_severity_count,
            'low_severity_count': vuln_features.low_severity_count,
            
            **ast_features,
            **graph_features,
            **semantic_features,
        }
        
        all_features.append(combined)
        
        if (idx + 1) % 10 == 0:
            print(f"✓ [{idx+1}/50] - {len(all_features)} successful")
    
    except Exception as e:
        if (idx + 1) % 10 == 0:
            print(f"❌ [{idx+1}/50] - {str(e)[:40]}")
        continue

# Save directly to CSV
if all_features:
    df_result = pd.DataFrame(all_features)
    output = Path('data/semantic_test_50.csv')
    df_result.to_csv(output, index=False)
    
    print("\n" + "="*70)
    print(f"✅ SAVED {len(df_result)} contracts")
    print(f"📁 {output}")
    print("="*70)
    print(f"\n📊 SEMANTIC STATS:")
    print(f"  CEI violations: {df_result['cei_violations'].sum()}")
    print(f"  Perfect CEI: {(df_result['cei_pattern_score'] == 1.0).sum()}")
    print(f"  Has guard: {df_result['has_reentrancy_guard'].sum()}")
    print(f"  Vulnerable: {df_result['is_vulnerable'].sum()}")
    print("="*70 + "\n")
else:
    print("\n❌ No contracts extracted")
