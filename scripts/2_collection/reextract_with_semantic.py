"""
Re-extract SmartBugs dataset with semantic features (89 total)
Uses existing CSV metadata, no custom loaders needed
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from chainguardian.feature_extraction.pipeline import FeaturePipeline

print("\n" + "="*70)
print("🔄 RE-EXTRACTING SMARTBUGS WITH SEMANTIC FEATURES")
print("="*70)

# Load existing metadata CSV
metadata_files = [
    'data/smartbugs_metadata.csv',
    'data/contracts_metadata.csv',
    'data/smartbugs_features.csv',
    'data/ml_features.csv',
]

df_contracts = None
for csv_file in metadata_files:
    if Path(csv_file).exists():
        df_contracts = pd.read_csv(csv_file)
        print(f"\n✅ Loaded metadata from: {csv_file}")
        break

if df_contracts is None:
    print("\n❌ No metadata CSV found. Looking for contract files directly...")
    
    # Fallback: Find contracts in data/safe_contracts and data/vulnerable_contracts
    contract_dirs = [
        Path('data/safe_contracts'),
        Path('data/vulnerable_contracts'),
    ]
    
    contracts = []
    for dir_path in contract_dirs:
        if dir_path.exists():
            for sol_file in dir_path.rglob('*.sol'):
                # Extract contract name from file
                contract_name = sol_file.stem
                contracts.append({
                    'file_path': str(sol_file),
                    'contract_name': contract_name,
                    'is_vulnerable': 'vulnerable' in str(sol_file),
                    'data_source': 'smartbugs',
                })
    
    if contracts:
        df_contracts = pd.DataFrame(contracts)
        print(f"\n✅ Found {len(df_contracts)} contract files")
    else:
        print("\n❌ No contracts found! Check data/ directory structure")
        sys.exit(1)

print(f"\n📦 Processing {len(df_contracts)} contracts")
print(f"⏱️  Estimated time: {len(df_contracts) * 2 / 60:.0f}-{len(df_contracts) * 3 / 60:.0f} minutes")

# Limit for quick test (remove this line for full extraction)
print(f"\n⚡ QUICK TEST MODE: Processing first 100 contracts only")
df_contracts = df_contracts.head(100)

print(f"\n🚀 Starting extraction...\n")

# Initialize pipeline
pipeline = FeaturePipeline()

# Process contracts
successful = 0
failed = 0

for idx, row in df_contracts.iterrows():
    contract_path = Path(row['file_path'])
    contract_name = row.get('contract_name', contract_path.stem)
    
    if not contract_path.exists():
        failed += 1
        continue
    
    try:
        # Extract features (now with semantic analysis)
        features = pipeline.analyze_contract(
            contract_path,
            contract_name,
            {
                'address': row.get('address', f"0x{'0'*40}"),
                'data_source': row.get('data_source', 'smartbugs'),
                'vulnerability_type': row.get('vulnerability_type', ''),
                'is_vulnerable': row.get('is_vulnerable', False),
            }
        )
        
        successful += 1
        
        # Progress update every 10 contracts
        if (idx + 1) % 10 == 0:
            progress = (idx + 1) / len(df_contracts) * 100
            print(f"✓ [{idx+1}/{len(df_contracts)}] {progress:.1f}% - "
                  f"Success: {successful}, Failed: {failed}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Saving progress...")
        break
    except Exception as e:
        failed += 1
        if failed % 10 == 0:
            print(f"❌ [{idx+1}/{len(df_contracts)}] {contract_name}: {str(e)[:50]}")

print("\n" + "="*70)
print(f"✅ EXTRACTION COMPLETE")
print("="*70)
print(f"  Successful: {successful}/{len(df_contracts)} ({successful/len(df_contracts)*100:.1f}%)")
print(f"  Failed: {failed}/{len(df_contracts)} ({failed/len(df_contracts)*100:.1f}%)")

# Save to CSV
output_path = Path('data/smartbugs_with_semantic.csv')
pipeline.save_dataset(output_path)

print(f"\n📁 Saved: {output_path}")

# Show semantic feature stats
try:
    df = pd.read_csv(output_path)
    print(f"\n📊 SEMANTIC FEATURE STATS:")
    print("="*70)
    print(f"  Total features: {len(df.columns)}")
    print(f"  Contracts analyzed: {len(df)}")
    print(f"  Contracts with CEI violations: {df['cei_violations'].sum()}")
    print(f"  Contracts with reentrancy guard: {df['has_reentrancy_guard'].sum()}")
    print(f"  Average CEI score: {df['cei_pattern_score'].mean():.3f}")
    print(f"  Contracts with vulnerabilities: {df['is_vulnerable'].sum() if 'is_vulnerable' in df else 'N/A'}")
    print("="*70 + "\n")
except Exception as e:
    print(f"\n⚠️  Could not load stats: {e}")
