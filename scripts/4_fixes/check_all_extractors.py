"""
Check all extractor files for contract name matching issues
"""

from pathlib import Path
import re

print("\n" + "="*70)
print("🔍 CHECKING ALL FEATURE EXTRACTORS")
print("="*70)

extractor_files = [
    'src/chainguardian/feature_extraction/contract_analyzer.py',
    'src/chainguardian/feature_extraction/ast_analyzer.py',
    'src/chainguardian/feature_extraction/graph_extractor.py',
]

for filepath in extractor_files:
    file = Path(filepath)
    
    print(f"\n📄 {file.name}")
    print("-" * 70)
    
    if not file.exists():
        print("  ❌ File not found!")
        continue
    
    content = file.read_text()
    
    # Check for contract name matching patterns
    patterns = [
        (r'if contract\.name == contract_name', 'Exact match (OLD)'),
        (r'if c\.name == contract_name', 'Exact match (OLD)'),
        (r'contract_name\.lower\(\)\.replace', 'Fuzzy match (NEW ✅)'),
        (r'name_clean = contract_name\.lower', 'Fuzzy match (NEW ✅)'),
    ]
    
    found_patterns = []
    
    for pattern, description in patterns:
        matches = re.findall(pattern, content)
        if matches:
            found_patterns.append((description, len(matches)))
    
    if found_patterns:
        print("  Found patterns:")
        for desc, count in found_patterns:
            print(f"    - {desc}: {count} occurrence(s)")
    else:
        print("  ⚠️  No contract matching patterns found!")
    
    # Check if file has fuzzy matching
    has_fuzzy = 'name_clean' in content or 'Fuzzy match' in content
    
    if has_fuzzy:
        print("  ✅ Has fuzzy matching!")
    else:
        print("  ❌ Needs fuzzy matching patch!")

print("\n" + "="*70)
print("📊 SUMMARY")
print("="*70)

# Count how many need fixing
for filepath in extractor_files:
    file = Path(filepath)
    if file.exists():
        content = file.read_text()
        has_fuzzy = 'name_clean' in content
        status = "✅" if has_fuzzy else "❌"
        print(f"{status} {file.name}")

print("="*70 + "\n")
