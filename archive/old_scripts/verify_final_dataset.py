"""
Verify final database after rebuild.
"""
from chainguardian.database.manager import DatabaseManager
import pandas as pd

db = DatabaseManager()

print("="*70)
print("FINAL DATABASE VERIFICATION")
print("="*70)

# Get connection and all data
conn = db._get_connection()
try:
    df_contracts = pd.read_sql("SELECT * FROM contracts", conn)
    df_features = pd.read_sql("SELECT * FROM features WHERE failure_reason IS NULL", conn)
    df_labels = pd.read_sql("SELECT * FROM labels", conn)
finally:
    conn.close()

print(f"\n📊 DATABASE CONTENTS:")
print(f"  Total contracts: {len(df_contracts)}")
print(f"  Successful features: {len(df_features)}")
print(f"  Ground truth labels: {len(df_labels)}")

# Data source breakdown
print(f"\n📁 DATA SOURCES:")
source_counts = df_contracts['data_source'].value_counts()
for source, count in source_counts.items():
    print(f"  {source}: {count}")

# Label distribution
print(f"\n🏷️  LABEL DISTRIBUTION:")
label_dist = df_labels['has_vulnerability'].value_counts()
vulnerable = label_dist.get(True, 0)
safe = label_dist.get(False, 0)
total = vulnerable + safe

if total > 0:
    print(f"  Vulnerable: {vulnerable} ({vulnerable/total*100:.1f}%)")
    print(f"  Safe: {safe} ({safe/total*100:.1f}%)")
else:
    print(f"  No labels found in database")

# Vulnerability types
print(f"\n🔍 VULNERABILITY TYPES:")
if 'vulnerability_type' in df_labels.columns and len(df_labels) > 0:
    vuln_types = df_labels[df_labels['has_vulnerability']==True]['vulnerability_type'].value_counts()
    if len(vuln_types) > 0:
        for vtype, count in vuln_types.head(10).items():
            print(f"  {vtype}: {count}")
    else:
        print("  No vulnerabilities found in labels")
else:
    print("  No vulnerability_type column found")

# Feature completeness
print(f"\n📈 FEATURE QUALITY:")
if len(df_features) > 0:
    feature_cols = [col for col in df_features.columns 
                   if col not in ['id', 'contract_id', 'failure_reason', 
                                 'error_message', 'extracted_at']]

    non_zero_features = (df_features[feature_cols] != 0).sum(axis=1)
    avg_non_zero = non_zero_features.mean()

    print(f"  Total feature columns: {len(feature_cols)}")
    print(f"  Avg non-zero features per contract: {avg_non_zero:.1f}")
    print(f"  Contracts with >10 non-zero features: {(non_zero_features > 10).sum()}")
else:
    print("  No features found in database")

print("\n" + "="*70)
print("✅ DATABASE IS READY FOR EDA!")
print("="*70)

# Export to CSV (if we have data)
if len(df_features) > 0 and len(df_contracts) > 0:
    print("\nExporting to CSV...")
    export_df = df_features.merge(df_contracts[['id', 'name', 'data_source']], 
                                   left_on='contract_id', right_on='id')
    
    # Only merge labels if we have them
    if len(df_labels) > 0:
        export_df = export_df.merge(df_labels[['contract_id', 'vulnerability_type', 'has_vulnerability']], 
                                     on='contract_id', how='left')
    else:
        # Add placeholder columns if no labels
        export_df['vulnerability_type'] = None
        export_df['has_vulnerability'] = None
    
    export_df.to_csv('data/chainguardian_ml_ready_v2.csv', index=False)
    print(f"✅ Exported {len(export_df)} contracts to: data/chainguardian_ml_ready_v2.csv")
else:
    print("\n⚠️  No data to export!")