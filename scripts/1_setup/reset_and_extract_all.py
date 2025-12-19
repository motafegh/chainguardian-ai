"""
COMPLETE DATABASE RESET + FULL FEATURE EXTRACTION
==================================================
1. Backup existing database
2. Drop and recreate clean database
3. Extract ALL contracts with 89 features (including semantic)
4. Validate completeness
5. Export clean CSV for training

Estimated time: 30-60 minutes depending on contract count
"""

import sys
from pathlib import Path
import pandas as pd
import subprocess
from datetime import datetime
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

print("\n" + "="*80)
print("🔄 COMPLETE DATABASE RESET + FULL EXTRACTION")
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
else:
    print("⚠️  No CSV files to backup")

# Backup database file
db_file = Path('data/chainguardian.db')
if db_file.exists():
    shutil.copy(db_file, backup_dir / 'chainguardian.db')
    print(f"✅ Backed up database to {backup_dir}")
else:
    print("⚠️  No database file found")

# ============================================================================
# STEP 2: DROP AND RECREATE DATABASE
# ============================================================================
print("\n🗄️  STEP 2: RECREATING CLEAN DATABASE")
print("-" * 80)

# Remove old database
if db_file.exists():
    db_file.unlink()
    print("✅ Removed old database")

# Recreate database with fresh schema
from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()
print("✅ Created clean database with schema")

# ============================================================================
# STEP 3: FIND ALL CONTRACTS
# ============================================================================
print("\n🔍 STEP 3: SCANNING FOR CONTRACTS")
print("-" * 80)

contract_dirs = [
    Path('data/safe_contracts'),
    Path('data/vulnerable_contracts'),
    Path('test_contracts'),  # Include our adversarial tests
]

contracts = []
for dir_path in contract_dirs:
    if not dir_path.exists():
        print(f"⚠️  Directory not found: {dir_path}")
        continue
    
    for sol_file in dir_path.rglob('*.sol'):
        # Skip generated/test files
        if any(skip in str(sol_file) for skip in ['node_modules', '.venv', '__pycache__']):
            continue
        
        is_vulnerable = 'vulnerable' in str(sol_file)
        is_adversarial = 'test_contracts' in str(sol_file)
        
        contracts.append({
            'file_path': str(sol_file),
            'contract_name': sol_file.stem,
            'is_vulnerable': is_vulnerable,
            'data_source': 'adversarial' if is_adversarial else 'smartbugs',
        })

if not contracts:
    print("❌ NO CONTRACTS FOUND!")
    print("\n📁 Please ensure contract files exist in:")
    for d in contract_dirs:
        print(f"   - {d}")
    sys.exit(1)

df_contracts = pd.DataFrame(contracts)
print(f"\n✅ Found {len(df_contracts)} contracts:")
print(f"   - SmartBugs safe: {len(df_contracts[df_contracts['data_source']=='smartbugs'][~df_contracts['is_vulnerable']])}")
print(f"   - SmartBugs vulnerable: {len(df_contracts[(df_contracts['data_source']=='smartbugs') & (df_contracts['is_vulnerable'])])}")
print(f"   - Adversarial tests: {len(df_contracts[df_contracts['data_source']=='adversarial'])}")

# Ask for confirmation
print(f"\n⏱️  ESTIMATED TIME: {len(df_contracts) * 2 / 60:.0f}-{len(df_contracts) * 3 / 60:.0f} minutes")
print(f"\n⚠️  This will extract ALL {len(df_contracts)} contracts with 89 features")

response = input("\nContinue? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("❌ Cancelled by user")
    sys.exit(0)

# ============================================================================
# STEP 4: EXTRACT ALL FEATURES WITH SEMANTIC ANALYSIS
# ============================================================================
print("\n🚀 STEP 4: EXTRACTING FEATURES (89 total)")
print("-" * 80)
print("Features: 23 vuln flags + 17 AST + 25 graph + 8 semantic + 9 stats + 4 risk + 2 error")
print("")

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
                'address': f"0x{hash(str(contract_path)) % (10**40):040d}",  # Deterministic unique address
                'data_source': row['data_source'],
                'is_vulnerable': row['is_vulnerable'],
            }
        )
        
        successful += 1
        
        # Progress updates
        if (idx + 1) % 25 == 0:
            progress = (idx + 1) / len(df_contracts) * 100
            print(f"✓ [{idx+1}/{len(df_contracts)}] {progress:.1f}% - Success: {successful}, Failed: {failed}")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  INTERRUPTED BY USER")
        print(f"   Extracted: {successful}/{idx+1}")
        break
    
    except Exception as e:
        failed += 1
        error_msg = str(e)[:50]
        failed_details.append({
            'contract': contract_name,
            'error': error_msg
        })
        
        if failed % 25 == 0:
            print(f"❌ [{idx+1}/{len(df_contracts)}] Failures: {failed} (latest: {error_msg})")

# ============================================================================
# STEP 5: VALIDATE EXTRACTION
# ============================================================================
print("\n" + "="*80)
print("✅ EXTRACTION COMPLETE")
print("="*80)

total = successful + failed
print(f"\n📊 RESULTS:")
print(f"   Total contracts: {total}")
print(f"   ✅ Successful: {successful} ({successful/total*100:.1f}%)")
print(f"   ❌ Failed: {failed} ({failed/total*100:.1f}%)")

# Show failure breakdown if any
if failed > 0 and failed_details:
    print(f"\n�� FAILURE SUMMARY (last 10):")
    for detail in failed_details[-10:]:
        print(f"   - {detail['contract']}: {detail['error']}")

# ============================================================================
# STEP 6: EXPORT FROM DATABASE
# ============================================================================
print("\n📁 STEP 6: EXPORTING CLEAN DATASET")
print("-" * 80)

df_final = db.get_all_features()

if df_final.empty:
    print("❌ No data in database!")
    sys.exit(1)

# Export to CSV
output_csv = Path('data/complete_dataset_with_semantic.csv')
df_final.to_csv(output_csv, index=False)

print(f"✅ Exported {len(df_final)} contracts to {output_csv}")
print(f"   Features: {len(df_final.columns)}")

# ============================================================================
# STEP 7: VALIDATION CHECKS
# ============================================================================
print("\n✅ STEP 7: VALIDATION")
print("-" * 80)

# Check semantic features present
semantic_features = [
    'cei_violations',
    'cei_pattern_score',
    'has_reentrancy_guard',
    'state_before_call_count',
]

missing_semantic = [f for f in semantic_features if f not in df_final.columns]

if missing_semantic:
    print(f"❌ MISSING SEMANTIC FEATURES:")
    for f in missing_semantic:
        print(f"   - {f}")
else:
    print(f"✅ All semantic features present")

# Show semantic stats
print(f"\n📊 SEMANTIC FEATURE STATS:")
if 'cei_violations' in df_final.columns:
    print(f"   CEI violations detected: {df_final['cei_violations'].sum()}")
    print(f"   Contracts with perfect CEI: {(df_final['cei_pattern_score'] == 1.0).sum()}")
    print(f"   Contracts with reentrancy guard: {df_final['has_reentrancy_guard'].sum()}")
    print(f"   Average CEI score: {df_final['cei_pattern_score'].mean():.3f}")

# Show vulnerability distribution
if 'is_vulnerable' in df_final.columns:
    print(f"\n📊 VULNERABILITY DISTRIBUTION:")
    print(f"   Vulnerable: {df_final['is_vulnerable'].sum()}")
    print(f"   Safe: {(~df_final['is_vulnerable']).sum()}")

# Show data source distribution
if 'data_source' in df_final.columns:
    print(f"\n�� DATA SOURCE DISTRIBUTION:")
    print(df_final['data_source'].value_counts().to_string())

# Database stats
stats = db.get_stats()
print(f"\n📊 DATABASE STATS:")
print(f"   Total contracts: {stats.get('total_contracts', 0)}")
print(f"   Total features: {stats.get('total_features', 0)}")

# ============================================================================
# STEP 8: FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("🎉 DATABASE RESET COMPLETE")
print("="*80)

print(f"\n📁 OUTPUT FILES:")
print(f"   ✅ Database: data/chainguardian.db ({len(df_final)} contracts)")
print(f"   ✅ CSV: {output_csv} ({len(df_final.columns)} features)")
print(f"   ✅ Backup: {backup_dir}")

print(f"\n🎯 READY FOR:")
print(f"   - Model training with {len(df_final.columns)} features")
print(f"   - Semantic analysis validation")
print(f"   - Production deployment")

print("\n" + "="*80 + "\n")

# Save extraction report
report = {
    'timestamp': datetime.now().isoformat(),
    'total_contracts': len(df_final),
    'features': len(df_final.columns),
    'successful': successful,
    'failed': failed,
    'backup_location': str(backup_dir),
    'output_csv': str(output_csv),
}

import json
report_file = backup_dir / 'extraction_report.json'
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f"📄 Extraction report saved: {report_file}\n")
