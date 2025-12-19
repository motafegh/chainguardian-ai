"""Check for duplicate contracts in database."""
from chainguardian.database.manager import DatabaseManager
import pandas as pd

db = DatabaseManager()
df = db.get_all_features()

print("="*70)
print("DUPLICATE CHECK")
print("="*70)

# Check by contract_name
name_dups = df[df.duplicated(subset=['contract_name'], keep=False)]
print(f"\nDuplicate contract names: {len(name_dups)}")
if len(name_dups) > 0:
    print(name_dups[['contract_id', 'contract_name', 'file_path']].head(10))

# Check by file_path
path_dups = df[df.duplicated(subset=['file_path'], keep=False)]
print(f"\nDuplicate file paths: {len(path_dups)}")

# Check by address
addr_dups = df[df.duplicated(subset=['address'], keep=False)]
print(f"\nDuplicate addresses: {len(addr_dups)}")

# Show unique counts
print(f"\nUnique contracts by:")
print(f"  contract_id: {df['contract_id'].nunique()}")
print(f"  contract_name: {df['contract_name'].nunique()}")
print(f"  file_path: {df['file_path'].nunique()}")
print(f"  address: {df['address'].nunique()}")

print("="*70)
