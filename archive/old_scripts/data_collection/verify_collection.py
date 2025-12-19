"""
Collection Verification Script
Verifies collected contracts match expected complexity
"""

import re
from pathlib import Path
from typing import Dict

def estimate_complexity(source_code: str) -> Dict:
    """Estimate contract complexity from source code"""
    
    # Count lines (exclude comments and empty)
    lines = [l for l in source_code.split('\n') 
             if l.strip() and not l.strip().startswith('//')]
    loc = len(lines)
    
    # Count functions
    functions = len(re.findall(r'function\s+\w+', source_code))
    
    # Count external calls
    external_calls = len(re.findall(
        r'\.call\(|\.delegatecall\(|\.transfer\(|\.send\(', 
        source_code
    ))
    
    # Count state variables
    state_vars = len(re.findall(
        r'^\s+(uint|int|address|bool|string|bytes|mapping)', 
        source_code, 
        re.MULTILINE
    ))
    
    # Complexity estimate
    if loc > 500 or functions > 20:
        complexity = "COMPLEX"
    elif loc > 200 or functions > 10:
        complexity = "MEDIUM"
    else:
        complexity = "SIMPLE"
    
    return {
        'lines_of_code': loc,
        'num_functions': functions,
        'external_calls': external_calls,
        'state_variables': state_vars,
        'complexity': complexity
    }

def verify_collection():
    """Verify collected contracts"""
    
    print("="*70)
    print("COLLECTION VERIFICATION")
    print("="*70)
    
    base_dir = Path('../data/real_world_collection')
    
    categories = [
        ('vulnerable_complex', 'COMPLEX'),
        ('safe_complex', 'COMPLEX'),
    ]
    
    total_contracts = 0
    
    for category, expected_complexity in categories:
        category_path = base_dir / category
        contracts = list(category_path.glob('*.sol'))
        
        if not contracts:
            print(f"\n📂 {category.upper()}: No contracts yet")
            continue
        
        print(f"\n{'='*70}")
        print(f"📂 {category.upper()} ({len(contracts)} contracts)")
        print(f"   Expected complexity: {expected_complexity}")
        print("="*70)
        
        total_contracts += len(contracts)
        
        for contract_file in contracts:
            with open(contract_file, 'r', encoding='utf-8') as f:
                source = f.read()
            
            stats = estimate_complexity(source)
            
            # Check if matches expected
            matches = (
                (expected_complexity == 'COMPLEX' and stats['complexity'] in ['COMPLEX', 'MEDIUM']) or
                (expected_complexity == 'SIMPLE' and stats['complexity'] == 'SIMPLE')
            )
            
            status = "✅" if matches else "⚠️"
            
            print(f"\n   {status} {contract_file.name}")
            print(f"      LOC: {stats['lines_of_code']}")
            print(f"      Functions: {stats['num_functions']}")
            print(f"      External calls: {stats['external_calls']}")
            print(f"      State vars: {stats['state_variables']}")
            print(f"      Complexity: {stats['complexity']}")
    
    print(f"\n{'='*70}")
    print(f"✅ VERIFICATION COMPLETE")
    print(f"   Total contracts collected: {total_contracts}")
    print(f"   Ready for tomorrow's full collection!")
    print("="*70)

if __name__ == "__main__":
    verify_collection()
