"""
Contract Collection Script
Collects first batch of contracts for proof of concept
"""

import json
from pathlib import Path
from etherscan_fetcher import EtherscanFetcher

def collect_initial_batch():
    """Collect first 5-10 contracts as proof of concept"""
    
    print("="*70)
    print("INITIAL CONTRACT COLLECTION (PROOF OF CONCEPT)")
    print("="*70)
    
    # Initialize fetcher
    fetcher = EtherscanFetcher()
    
    # Load targets
    base_dir = Path('../data/real_world_collection')
    with open(base_dir / 'sources' / 'target_contracts.json', 'r') as f:
        targets = json.load(f)
    
    # Track results
    results = {
        'vulnerable_complex': [],
        'safe_complex': []
    }
    
    # ================================================================
    # VULNERABLE COMPLEX (First 3)
    # ================================================================
    
    print(f"\n{'='*70}")
    print("COLLECTING VULNERABLE COMPLEX CONTRACTS")
    print("="*70)
    
    for i, contract in enumerate(targets['VULNERABLE_COMPLEX'][:3], 1):
        print(f"\n[{i}/3] {contract['name']}")
        print(f"   Address: {contract['address']}")
        print(f"   Vulnerability: {contract['vulnerability']}")
        print(f"   Impact: {contract['impact']}")
        
        data = fetcher.get_contract_source(contract['address'])
        
        if data:
            metadata = {
                'category': 'vulnerable_complex',
                'vulnerability_type': contract['vulnerability'],
                'exploit_date': str(contract['year']),
                'complexity_estimate': contract['complexity'],
                'source': 'historical_exploit',
                'verification_status': 'verified_exploit',
                'impact': contract['impact'],
                'notes': f"Historical exploit from {contract['year']}"
            }
            
            file_path = fetcher.save_contract(data, 'vulnerable_complex', metadata)
            results['vulnerable_complex'].append({
                'name': contract['name'],
                'address': contract['address'],
                'file': file_path.name,
                'vulnerability': contract['vulnerability']
            })
    
    # ================================================================
    # SAFE COMPLEX (First 2)
    # ================================================================
    
    print(f"\n{'='*70}")
    print("COLLECTING SAFE COMPLEX CONTRACTS")
    print("="*70)
    
    for i, contract in enumerate(targets['SAFE_COMPLEX'][:2], 1):
        print(f"\n[{i}/2] {contract['name']}")
        print(f"   Address: {contract['address']}")
        print(f"   Type: {contract['type']}")
        
        data = fetcher.get_contract_source(contract['address'])
        
        if data:
            metadata = {
                'category': 'safe_complex',
                'vulnerability_type': 'none',
                'complexity_estimate': contract['complexity'],
                'source': 'production_audited',
                'verification_status': 'audited_production',
                'audits': ', '.join(contract['audits']),
                'contract_type': contract['type'],
                'notes': f"Production {contract['type']} contract with multiple audits"
            }
            
            file_path = fetcher.save_contract(data, 'safe_complex', metadata)
            results['safe_complex'].append({
                'name': contract['name'],
                'address': contract['address'],
                'file': file_path.name,
                'type': contract['type']
            })
    
    # ================================================================
    # SUMMARY
    # ================================================================
    
    print(f"\n{'='*70}")
    print("COLLECTION COMPLETE")
    print("="*70)
    
    print(f"\n✅ COLLECTED:")
    print(f"\n   Vulnerable Complex ({len(results['vulnerable_complex'])}):")
    for r in results['vulnerable_complex']:
        print(f"      • {r['name']} - {r['vulnerability']}")
    
    print(f"\n   Safe Complex ({len(results['safe_complex'])}):")
    for r in results['safe_complex']:
        print(f"      • {r['name']} - {r['type']}")
    
    fetcher.print_stats()
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Run: python3 verify_collection.py")
    print(f"   2. If good → Tomorrow run: python3 batch_collect.py")
    print(f"   3. Goal: 50+ contracts per category")
    
    # Save results
    results_path = base_dir / 'sources' / 'collection_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved: {results_path}")
    print("="*70)
    
    return results

if __name__ == "__main__":
    collect_initial_batch()
