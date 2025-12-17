"""
Analyze why contracts failed feature extraction
"""
import pandas as pd
from pathlib import Path
import re

# Load both datasets
df_full = pd.read_csv('data/ml_dataset_fixed.csv')
df_clean = pd.read_csv('data/ml_dataset_clean.csv')

# Find contracts with all zeros
numeric_cols = [col for col in df_full.columns 
               if col not in ['contract_name', 'file_path', 'has_reentrancy']]
failed_contracts = df_full[(df_full[numeric_cols] == 0).all(axis=1)]

print("="*70)
print(f"FAILED CONTRACTS ANALYSIS")
print("="*70)
print(f"Total contracts: {len(df_full)}")
print(f"Successful: {len(df_clean)}")
print(f"Failed: {len(failed_contracts)}")

# Read actual contract files to check for patterns
contracts_dir = Path('blockchain/contracts/collected')
failure_reasons = {
    'missing_pragma': [],
    'double_brace': [],
    'proxy_contract': [],
    'compiler_mismatch': [],
    'unknown': []
}

for _, row in failed_contracts.iterrows():
    contract_name = row['contract_name']
    # Find the file
    files = list(contracts_dir.glob(f"{contract_name}_*.sol"))
    
    if files:
        content = files[0].read_text(errors='ignore')
        
        # Check for issues
        if 'pragma solidity' not in content:
            failure_reasons['missing_pragma'].append(contract_name)
        elif content.strip().startswith('{{'):
            failure_reasons['double_brace'].append(contract_name)
        elif 'Proxy' in contract_name or 'proxy' in content.lower()[:500]:
            failure_reasons['proxy_contract'].append(contract_name)
        else:
            # Check pragma version
            match = re.search(r'pragma solidity\s+[\^>=<]*([0-9.]+)', content)
            if match:
                failure_reasons['compiler_mismatch'].append(contract_name)
            else:
                failure_reasons['unknown'].append(contract_name)

print("\n" + "="*70)
print("FAILURE REASONS")
print("="*70)
for reason, contracts in failure_reasons.items():
    if contracts:
        print(f"\n{reason.upper()}: {len(contracts)} contracts")
        for c in contracts[:5]:
            print(f"  - {c}")
        if len(contracts) > 5:
            print(f"  ... and {len(contracts)-5} more")

