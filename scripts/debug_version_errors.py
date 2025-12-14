"""
Debug VERSION_MISMATCH Errors with Full Details
================================================

Shows complete error messages and suggests fixes.
"""

import pandas as pd
from pathlib import Path
import re
from collections import Counter

# Load dataset
csv_path = Path("data/collected_dataset.csv")
df = pd.read_csv(csv_path)

# Filter VERSION_MISMATCH errors
version_errors = df[df['failure_reason'] == 'VERSION_MISMATCH'].copy()

print("="*70)
print(f"DEBUGGING {len(version_errors)} VERSION_MISMATCH ERRORS")
print("="*70)

# Show first 5 COMPLETE error messages
print("\n📋 Complete Error Messages (first 5):")
print("-"*70)

for i, (idx, row) in enumerate(version_errors.head(5).iterrows()):
    contract = row['contract_name']
    file_path = row['file_path']
    error = row['error_message']
    
    print(f"\n{i+1}. CONTRACT: {contract}")
    print(f"   File: {file_path}")
    print(f"   Error: {error}")
    print("-"*70)

# Try to extract specific version requirements from errors
print("\n\n🔍 Analyzing Error Patterns:")
print("-"*70)

patterns_found = {
    'full_errors_available': 0,
    'truncated_errors': 0,
    'mentions_pragma': 0,
    'mentions_version_number': 0,
}

pragma_versions = []
required_versions = []

for error_msg in version_errors['error_message'].dropna():
    # Check if truncated
    if error_msg.endswith('versio'):
        patterns_found['truncated_errors'] += 1
    else:
        patterns_found['full_errors_available'] += 1
    
    # Check for pragma mentions
    if 'pragma' in error_msg.lower():
        patterns_found['mentions_pragma'] += 1
        
        # Extract version from pragma
        pragma_match = re.search(r'pragma\s+solidity\s+[^\d]*([\d.]+)', error_msg)
        if pragma_match:
            pragma_versions.append(pragma_match.group(1))
    
    # Check for "requires X" patterns
    requires_match = re.search(r'requires?\s+(?:compiler\s+)?version\s+[^\d]*([\d.]+)', error_msg, re.IGNORECASE)
    if requires_match:
        required_versions.append(requires_match.group(1))
        patterns_found['mentions_version_number'] += 1

print("\nPattern Statistics:")
for pattern, count in patterns_found.items():
    percentage = count / len(version_errors) * 100 if len(version_errors) > 0 else 0
    print(f"  {pattern}: {count} ({percentage:.1f}%)")

if pragma_versions:
    print(f"\n📊 Pragma Versions Found in Errors:")
    version_counter = Counter(pragma_versions)
    for version, count in version_counter.most_common(10):
        print(f"  {version}: {count} contracts")

if required_versions:
    print(f"\n📊 Required Versions Mentioned:")
    version_counter = Counter(required_versions)
    for version, count in version_counter.most_common(10):
        print(f"  {version}: {count} contracts")

# Analyze actual contract files to see their pragmas
print("\n\n📄 Analyzing Contract Files Directly:")
print("-"*70)

pragma_analysis = []

for idx, row in version_errors.head(10).iterrows():
    contract_name = row['contract_name']
    file_path = Path(row['file_path'])
    
    if file_path.exists():
        try:
            if file_path.is_dir():
                # Multi-file - find main file
                sol_files = list(file_path.glob("*.sol"))
                if sol_files:
                    file_path = sol_files[0]
            
            content = file_path.read_text(encoding='utf-8')
            
            # Extract pragma
            pragma_match = re.search(r'pragma\s+solidity\s+([^;]+);', content)
            if pragma_match:
                pragma = pragma_match.group(1)
                pragma_analysis.append({
                    'contract': contract_name,
                    'pragma': pragma,
                    'file': file_path.name
                })
                
        except Exception as e:
            pass

if pragma_analysis:
    print("\nPragmas from failing contracts:")
    for item in pragma_analysis:
        print(f"  {item['contract']:20} → pragma solidity {item['pragma']:20} ({item['file']})")

print("\n" + "="*70)
print("💡 RECOMMENDATIONS:")
print("="*70)

if patterns_found['truncated_errors'] > len(version_errors) * 0.5:
    print("""
1. ⚠️ CRITICAL: 50%+ error messages are truncated!
   
   Fix in pipeline.py:
   - Change: 'error_message': str(e)[:500]
   - To:     'error_message': str(e)[:1000]
   
   Then re-run feature extraction.
""")

if pragma_analysis:
    print("""
2. 🔍 SPECIFIC PRAGMAS DETECTED:
   
   The contracts are using specific pragma formats that may not be
   handled correctly. Check the pragma patterns above.
   
   Common issues:
   - Range pragmas (>=0.6.0 <0.8.0) not fully implemented
   - Caret pragmas (^0.8.0) not selecting highest version
   - Exact versions not installed
""")

print("""
3. 🔧 IMMEDIATE ACTIONS:

   a) Increase error message length (see above)
   
   b) Run with verbose logging:
      poetry run python scripts/extract_features_only.py 2>&1 | grep -A 5 "COMPILATION ERROR"
   
   c) Test on one failing contract:
      poetry run python -c "
from pathlib import Path
from chainguardian.feature_extraction.pipeline import FeaturePipeline
import logging
logging.basicConfig(level=logging.DEBUG)

pipeline = FeaturePipeline()
path = Path('blockchain/contracts/collected/DSToken_0x9f8f72aa.sol')
if path.exists():
    features = pipeline.analyze_contract(path, 'DSToken')
    print(f'Result: {features.get(\"failure_reason\", \"SUCCESS\")}')
"
""")
