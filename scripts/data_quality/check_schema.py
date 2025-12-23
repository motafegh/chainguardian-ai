#!/usr/bin/env python3
"""Database Schema Checker - NATIVE DatabaseManager API"""

from chainguardian.database.manager import DatabaseManager
import pandas as pd

print("="*80)
print("🔍 CHAINGUARDIAN DATABASE SCHEMA")
print("="*80)

db = DatabaseManager()

# 1. TABLES
print("\n📋 TABLES:")
with db._get_cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        print(f"   • {table}")

# 2. CEI VIOLATIONS LOCATION
print("\n🔍 CEI VIOLATIONS COLUMN:")
with db._get_cursor() as cursor:
    # Check contracts table
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = 'contracts' AND column_name = 'cei_violations'
    """)
    contracts_cei = cursor.fetchone()[0] > 0
    
    # Check features table  
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = 'features' AND column_name = 'cei_violations'
    """)
    features_cei = cursor.fetchone()[0] > 0
    
    print(f"   contracts.cei_violations:  {'✅' if contracts_cei else '❌'}")
    print(f"   features.cei_violations:   {'✅' if features_cei else '❌'}")

# 3. CONTRACTS COLUMNS
print("\n📊 CONTRACTS TABLE:")
with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'contracts'
        ORDER BY ordinal_position
    """)
    cols = cursor.fetchall()
    for col in cols:
        null_status = 'NULL' if col[2] == 'YES' else 'NOT NULL'
        print(f"   {col[0]:25s} | {col[1]:15s} | {null_status}")

# 4. FEATURES COLUMNS (CEI location)
print("\n📊 FEATURES TABLE (CEI features):")
with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'features' 
          AND column_name LIKE '%cei%' 
           OR column_name LIKE '%reentrancy%' 
           OR column_name LIKE '%guard%'
        ORDER BY column_name
    """)
    semantic_cols = cursor.fetchall()
    for col in semantic_cols:
        print(f"   {col[0]:30s} | {col[1]}")

# 5. CEI STATS
print("\n📈 CEI VIOLATIONS STATS:")
with db._get_cursor(dict_cursor=True) as cursor:
    # ML-ready contracts
    cursor.execute("""
        SELECT 
            COUNT(*) as total_ml_ready,
            AVG(CASE WHEN f.cei_violations IS NOT NULL THEN f.cei_violations ELSE 0 END) as avg_cei,
            COUNT(*) FILTER (WHERE f.cei_violations = 0) as zero_cei,
            COUNT(*) FILTER (WHERE EXISTS(SELECT 1 FROM labels l WHERE l.contract_id = c.id AND l.has_vulnerability=TRUE)) as vuln_total
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id 
        WHERE f.failure_reason IS NULL
    """)
    stats = cursor.fetchone()
    
    print(f"   ML-ready contracts:      {stats['total_ml_ready']:,}")
    print(f"   Avg CEI violations:      {stats['avg_cei']:.2f}")
    print(f"   Zero CEI contracts:      {stats['zero_cei']:,} ({stats['zero_cei']/stats['total_ml_ready']*100:.1f}%)")
    print(f"   Vulnerable contracts:    {stats['vuln_total']:,}")

print("\n" + "="*80)
print("✅ SCHEMA ANALYSIS COMPLETE!")
