"""
COMPLETE DATABASE RESET + FULL FEATURE EXTRACTION (ALL SOURCES)
================================================================
Scans ALL contract directories in data/ for comprehensive extraction
"""

import sys
from pathlib import Path
import pandas as pd
import subprocess
from datetime import datetime
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

print("\n" + "="*80)
print("🔄 COMPLETE DATABASE RESET + FULL EXTRACTION (ALL SOURCES)")
print("="*80)

# ============================================================================
# STEP 1: BACKUP EXISTING DATABASE
# ============================================================================
print("\n📦 STEP 1: BACKING UP EXISTING DATA")
print("-" * 80)

backup_dir = Path('backups') / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)

# Backup CSV files
csv_files = list(Path('data').glob('*.csv'))
if csv_files:
    for csv_file in csv_files:
        dest = backup_dir / csv_file.name
        shutil.copy(csv_file, dest)
    print(f"✅ Backed up {len(csv_files)} CSV files to {backup_dir}")

print(f"✅ Backup complete: {backup_dir}")

# ============================================================================
# STEP 2: CLEAR DATABASE COMPLETELY
# ============================================================================
print("\n🗄️  STEP 2: CLEARING DATABASE COMPLETELY")
print("-" * 80)

from chainguardian.database.manager import DatabaseManager
import psycopg2

# Connect and drop/recreate tables
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'chainguardian',
    'user': 'chainguardian_user',
    'password': '2220128'
}

try:
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    # Drop tables in correct order (respecting foreign keys)
    print("🗑️  Dropping existing tables...")
    cursor.execute("DROP TABLE IF EXISTS labels CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS features CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS contracts CASCADE;")
    conn.commit()
    print("✅ All tables dropped")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"⚠️  Error dropping tables: {e}")

# Recreate schema
print("🏗️  Recreating schema...")
subprocess.run(['poetry', 'run', 'python', 'scripts/1_setup/create_tables.py'], check=False)
print("✅ Schema recreated with all features")

# ============================================================================
# STEP 3: FIND ALL CONTRACTS (COMPREHENSIVE!)
# ============================================================================
print("\n🔍 STEP 3: SCANNING FOR CONTRACTS (ALL SOURCES)")
print("-" * 80)

contract_dirs = [
    # OpenZeppelin (safe) - EXPLICIT!
    ('data/safe_contracts/openzeppelin-contracts/contracts', 'openzeppelin', False),
    ('data/safe_contracts/openzeppelin_all', 'openzeppelin', False),
    
    # SmartBugs (mix - determine by folder structure)
    ('data/safe_contracts', 'smartbugs', False),  # Will scan but exclude openzeppelin subdirs
    
    # Production contracts
    ('data/production/safe', 'production_safe', False),
    ('data/production/vulnerable', 'production_vulnerable', True),
    
    # SmartBugs Curated (vulnerable)
    ('data/smartbugs_curated/dataset', 'smartbugs_curated', True),
    
    # Vulnerable complex sources
    ('data/vulnerable_complex/defi_hacks', 'defi_hacks', True),
    ('data/vulnerable_complex/rekt_news', 'rekt_news', True),
    ('data/vulnerable_complex/swc_registry', 'swc_registry', True),
    ('data/vulnerable_complex/trail_of_bits', 'trail_of_bits', True),
    ('data/vulnerable_complex/etherscan_exploits', 'etherscan_exploits', True),
    ('data/vulnerable_complex/slowmist_hacked', 'slowmist_hacked', True),
    
    # Adversarial tests
    ('test_contracts', 'adversarial_test', False),  # Mix of safe/vulnerable
]

contracts = []
dir_stats = {}

for dir_path_str, data_source, is_vulnerable_dir in contract_dirs:
    dir_path = Path(dir_path_str)
    
    if not dir_path.exists():
        print(f"⚠️  Not found: {dir_path}")
        dir_stats[data_source] = 0
        continue
    
    dir_count = 0
    for sol_file in dir_path.rglob('*.sol'):
        # Skip generated/test/mock files
        if any(skip in str(sol_file) for skip in ['node_modules', '.venv', '__pycache__']):
            continue
        
        # Skip if this is smartbugs dir but file is in openzeppelin subdirectory
        # (we'll catch it in the explicit openzeppelin scan)
        if data_source == 'smartbugs':
            if 'openzeppelin' in str(sol_file):
                continue
        
        # For adversarial, parse filename for vulnerability status
        if data_source == 'adversarial_test':
            is_vulnerable = any(v in sol_file.stem.lower() for v in [
                'reentrancy', 'vulnerable', 'danger', 'exploit', 'honeypot', 'obvious'
            ])
        else:
            is_vulnerable = is_vulnerable_dir
        
        contracts.append({
            'file_path': str(sol_file),
            'contract_name': sol_file.stem,
            'is_vulnerable': is_vulnerable,
            'data_source': data_source,
        })
        dir_count += 1
    
    dir_stats[data_source] = dir_count
    print(f"   ✅ {data_source:30s}: {dir_count} files")

if not contracts:
    print("\n❌ NO CONTRACTS FOUND!")
    sys.exit(1)

df_contracts = pd.DataFrame(contracts)

print(f"\n📊 TOTAL FOUND: {len(df_contracts)} contracts")
print(f"   Safe: {(~df_contracts['is_vulnerable']).sum()}")
print(f"   Vulnerable: {df_contracts['is_vulnerable'].sum()}")

# Show source breakdown
print(f"\n📊 BY SOURCE:")
for source, count in sorted(dir_stats.items(), key=lambda x: x[1], reverse=True):
    if count > 0:
        print(f"   {source:30s}: {count}")

# Ask for confirmation
print(f"\n⏱️  ESTIMATED TIME: {len(df_contracts) * 2 / 60:.0f}-{len(df_contracts) * 3 / 60:.0f} minutes")

response = input("\nContinue with extraction? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("❌ Cancelled by user")
    sys.exit(0)

# ============================================================================
# STEP 4: EXTRACT ALL FEATURES WITH SEMANTIC ANALYSIS
# ============================================================================
print("\n🚀 STEP 4: EXTRACTING FEATURES (93 total, including 8 semantic)")
print("-" * 80)

from chainguardian.feature_extraction.pipeline import FeaturePipeline

pipeline = FeaturePipeline()

successful = 0
failed = 0
failed_details = []

for idx, row in df_contracts.iterrows():
    contract_path = Path(row['file_path'])
    contract_name = row['contract_name']
    
    if not contract_path.exists():
        failed += 1
        continue
    
    try:
        # Extract with metadata
        features = pipeline.analyze_contract(
            contract_path,
            contract_name,
            {
                'address': f"0x{hash(str(contract_path)) % (10**40):040d}",
                'data_source': row['data_source'],
                'is_vulnerable': row['is_vulnerable'],
            }
        )
        
        successful += 1
        
        # Progress updates
        if (idx + 1) % 50 == 0:
            progress = (idx + 1) / len(df_contracts) * 100
            print(f"✓ [{idx+1}/{len(df_contracts)}] {progress:.1f}% - Success: {successful}, Failed: {failed}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  INTERRUPTED BY USER")
        print(f"   Extracted: {successful}/{idx+1}")
        break
    
    except Exception as e:
        failed += 1
        error_msg = str(e)[:50]
        failed_details.append({'contract': contract_name, 'error': error_msg})
        
        if failed % 50 == 0:
            print(f"❌ [{idx+1}/{len(df_contracts)}] Failures: {failed}")

# ============================================================================
# STEP 5: EXPORT & VALIDATE
# ============================================================================
print("\n" + "="*80)
print("✅ EXTRACTION COMPLETE")
print("="*80)

total = successful + failed
print(f"\n📊 RESULTS:")
print(f"   Total contracts processed: {total}")
print(f"   ✅ Successful: {successful} ({successful/total*100:.1f}%)")
print(f"   ❌ Failed: {failed} ({failed/total*100:.1f}%)")

# Export
db = DatabaseManager()
df_final = db.get_all_features()

output_csv = Path('data/complete_dataset_with_semantic.csv')
df_final.to_csv(output_csv, index=False)

print(f"\n✅ Exported {len(df_final)} contracts to {output_csv}")
print(f"   Features: {len(df_final.columns)}")

# Validation
print(f"\n📊 SEMANTIC FEATURE STATS:")
if 'cei_violations' in df_final.columns:
    print(f"   CEI violations: {df_final['cei_violations'].sum()}")
    print(f"   Perfect CEI: {(df_final['cei_pattern_score'] == 1.0).sum()}")
    print(f"   With guard: {df_final['has_reentrancy_guard'].sum()}")
    print(f"   Avg CEI score: {df_final['cei_pattern_score'].mean():.3f}")

print(f"\n📊 DATA SOURCE DISTRIBUTION:")
print(df_final['data_source'].value_counts().to_string())

print(f"\n📊 VULNERABILITY DISTRIBUTION:")
if 'is_vulnerable' in df_final.columns:
    vuln_by_source = df_final.groupby('data_source')['is_vulnerable'].agg(['sum', 'count'])
    vuln_by_source.columns = ['Vulnerable', 'Total']
    vuln_by_source['Safe'] = vuln_by_source['Total'] - vuln_by_source['Vulnerable']
    print(vuln_by_source.to_string())

print("\n" + "="*80)
print("🎉 COMPLETE DATABASE EXTRACTION FINISHED")
print("="*80 + "\n")

# Save report
report = {
    'timestamp': datetime.now().isoformat(),
    'contracts_processed': total,
    'successful': successful,
    'failed': failed,
    'sources': dir_stats,
    'output': str(output_csv),
}

import json
report_file = backup_dir / 'extraction_report.json'
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f"📄 Report: {report_file}\n")
