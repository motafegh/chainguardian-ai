"""
Diagnose why contracts 22-25 fail feature extraction
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

print("\n" + "="*70)
print("🔍 DIAGNOSING FEATURE EXTRACTION FAILURES")
print("="*70)

# Problem contracts
problem_contracts = [
    'test_contracts/22_empty_contract.sol',
    'test_contracts/23_only_events.sol',
    'test_contracts/24_intentional_honeypot.sol',
    'test_contracts/25_gas_optimization_extreme.sol'
]

for contract_file in problem_contracts:
    print(f"\n{'='*70}")
    print(f"📄 TESTING: {contract_file}")
    print('='*70)
    
    contract_path = Path(contract_file)
    
    if not contract_path.exists():
        print(f"❌ File not found!")
        continue
    
    # Read contract
    with open(contract_path, 'r') as f:
        code = f.read()
    
    print(f"\n📝 CONTRACT CODE:")
    print(code[:300] + "..." if len(code) > 300 else code)
    
    # Try to extract features
    print(f"\n🔬 ATTEMPTING FEATURE EXTRACTION:")
    
    pipeline = FeaturePipeline()
    
    metadata = {
        'address': f'0xtest{contract_path.stem}',
        'data_source': 'diagnostic',
        'compiler_version': None
    }
    
    success = pipeline.analyze_contract(
        contract_path=contract_path,
        contract_name=contract_path.stem,
        metadata=metadata
    )
    
    print(f"\nSuccess: {success}")
    
    if success:
        df = pipeline.to_dataframe()
        if len(df) > 0:
            print(f"✅ Features extracted: {len(df.columns)} columns")
            
            # Show some key features
            row = df.iloc[-1]
            print(f"\nKey features:")
            print(f"  has_reentrancy: {row.get('has_reentrancy', 'N/A')}")
            print(f"  has_unchecked_call: {row.get('has_unchecked_call', 'N/A')}")
            print(f"  security_detectors_triggered: {row.get('security_detectors_triggered', 'N/A')}")
        else:
            print(f"❌ DataFrame is empty!")
    else:
        print(f"❌ Feature extraction failed!")

print("\n" + "="*70)
print("🎯 DIAGNOSIS COMPLETE")
print("="*70 + "\n")
