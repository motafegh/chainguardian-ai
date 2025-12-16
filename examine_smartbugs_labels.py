"""
Examine SmartBugs Curated labels

🎓 Goal: Understand what labels we have for training
"""

import json
from pathlib import Path
from collections import Counter

def examine_labels():
    """Look at vulnerabilities.json to understand label structure."""
    
    labels_file = Path("data/smartbugs_curated/vulnerabilities.json")
    
    if not labels_file.exists():
        print(f"❌ File not found: {labels_file}")
        return
    
    print("="*70)
    print("📋 SMARTBUGS CURATED LABELS")
    print("="*70)
    print()
    
    # Load labels
    with open(labels_file) as f:
        data = json.load(f)
    
    # Show structure
    print("🔍 JSON Structure:")
    if isinstance(data, dict):
        print(f"  Type: Dictionary with {len(data)} keys")
        print(f"  Keys: {list(data.keys())[:5]}...")
    elif isinstance(data, list):
        print(f"  Type: List with {len(data)} items")
        if data:
            print(f"  First item keys: {list(data[0].keys())}")
    print()
    
    # Count vulnerabilities by type
    print("📊 Vulnerability Counts:")
    
    vuln_counts = Counter()
    contract_count = 0
    
    # Parse based on actual structure
    if isinstance(data, dict):
        for contract_name, vuln_info in data.items():
            contract_count += 1
            if isinstance(vuln_info, dict) and 'vulnerabilities' in vuln_info:
                for vuln_type in vuln_info['vulnerabilities']:
                    vuln_counts[vuln_type] += 1
            elif isinstance(vuln_info, list):
                for vuln_type in vuln_info:
                    vuln_counts[vuln_type] += 1
    
    for vuln_type, count in vuln_counts.most_common():
        print(f"  • {vuln_type:30s}: {count:3d} contracts")
    
    print()
    print(f"📈 Total: {contract_count} contracts with labels")
    print()
    
    # Show example
    print("📄 Example Entry:")
    print("-"*70)
    if isinstance(data, dict):
        first_key = list(data.keys())[0]
        print(f"Contract: {first_key}")
        print(f"Data: {json.dumps(data[first_key], indent=2)}")
    elif isinstance(data, list) and data:
        print(json.dumps(data[0], indent=2))
    print()

if __name__ == "__main__":
    examine_labels()