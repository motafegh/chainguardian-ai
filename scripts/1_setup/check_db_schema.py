"""
Check if database schema needs updates for semantic features
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

print("\n🔍 CHECKING DATABASE SCHEMA COMPATIBILITY")
print("="*70)

# Check current schema
from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

# Get current table schema
import sqlite3
conn = sqlite3.connect('data/chainguardian.db')
cursor = conn.cursor()

# Check contracts table
cursor.execute("PRAGMA table_info(contracts);")
contracts_cols = cursor.fetchall()

print(f"\n📊 CONTRACTS TABLE: {len(contracts_cols)} columns")
for col in contracts_cols[:10]:  # Show first 10
    print(f"   - {col[1]} ({col[2]})")
if len(contracts_cols) > 10:
    print(f"   ... and {len(contracts_cols) - 10} more")

# Check features table
cursor.execute("PRAGMA table_info(features);")
features_cols = cursor.fetchall()

print(f"\n📊 FEATURES TABLE: {len(features_cols)} columns")
for col in features_cols[:10]:  # Show first 10
    print(f"   - {col[1]} ({col[2]})")
if len(features_cols) > 10:
    print(f"   ... and {len(features_cols) - 10} more")

conn.close()

# Check if semantic features are in schema
semantic_features = [
    'cei_violations',
    'cei_safe_functions',
    'cei_pattern_score',
    'has_reentrancy_guard',
    'functions_with_reentrancy_guard',
    'state_before_call_count',
    'state_after_call_count',
    'unchecked_calls_in_critical_context',
]

feature_col_names = [col[1] for col in features_cols]

print(f"\n🔍 SEMANTIC FEATURES IN SCHEMA:")
missing = []
for feat in semantic_features:
    if feat in feature_col_names:
        print(f"   ✅ {feat}")
    else:
        print(f"   ❌ {feat} - MISSING!")
        missing.append(feat)

if missing:
    print(f"\n⚠️  SCHEMA NEEDS UPDATE!")
    print(f"   Missing {len(missing)} semantic features")
    print(f"\n💡 SOLUTION: Update schema.sql or use dynamic columns")
else:
    print(f"\n✅ ALL SEMANTIC FEATURES IN SCHEMA")

print("="*70 + "\n")
