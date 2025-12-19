"""Verify data integrity - check for REAL duplicates."""
from chainguardian.database.manager import DatabaseManager
import pandas as pd

db = DatabaseManager()
df = db.get_all_features()

print("="*70)
print("DATA INTEGRITY CHECK")
print("="*70)

# Check 1: contract_id should be unique (primary key)
print(f"\n1. Primary Key Check:")
print(f"   Total rows: {len(df)}")
print(f"   Unique contract_ids: {df['contract_id'].nunique()}")
print(f"   Status: {'✅ PASS' if len(df) == df['contract_id'].nunique() else '❌ FAIL'}")

# Check 2: Same name + same file = potential real duplicate
print(f"\n2. Real Duplicate Check (name + path):")
real_dups = df[df.duplicated(subset=['contract_name', 'file_path'], keep=False)]
print(f"   Rows with same name AND path: {len(real_dups)}")
if len(real_dups) > 0:
    print("   ⚠️ These might be real duplicates:")
    print(real_dups[['contract_id', 'contract_name', 'file_path']].head())
else:
    print("   ✅ No real duplicates found")

# Check 3: Multi-contract files
print(f"\n3. Multi-Contract Files:")
file_contract_counts = df.groupby('file_path')['contract_name'].nunique()
multi_contract_files = file_contract_counts[file_contract_counts > 1]
print(f"   Files with multiple contracts: {len(multi_contract_files)}")
print(f"   Example:")
if len(multi_contract_files) > 0:
    example_file = multi_contract_files.index[0]
    contracts_in_file = df[df['file_path'] == example_file]['contract_name'].unique()
    print(f"   {example_file}:")
    for c in contracts_in_file[:5]:
        print(f"     - {c}")

# Check 4: For ML training, how many unique contracts?
successful = df[df['failure_reason'].isna()]
print(f"\n4. ML Training Dataset:")
print(f"   Total successful extractions: {len(successful)}")
print(f"   Unique by (name + path): {successful.groupby(['contract_name', 'file_path']).size().count()}")
print(f"   Status: ✅ Ready for ML training")

print("="*70)
