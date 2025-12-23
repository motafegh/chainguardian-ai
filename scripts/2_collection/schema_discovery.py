#!/usr/bin/env python3
"""🔍 EXACT SCHEMA + REAL COUNTS"""

from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

print("🔍 TABLE NAMES:")
with db._get_cursor() as cursor:
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")

print("\n🔍 FEATURES COLUMNS:")
with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'features'
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

print("\n🔍 LABELS COLUMNS:")
with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'labels'
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

print("\n🔍 RAW COUNTS (no assumptions):")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("SELECT COUNT(*) as total_contracts FROM contracts")
    print(f"Contracts: {cursor.fetchone()['total_contracts']:,}")
    
    cursor.execute("SELECT COUNT(*) as total_features FROM features")
    print(f"Features:  {cursor.fetchone()['total_features']:,}")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT contract_id) as unique_contracts 
        FROM features WHERE failure_reason IS NULL
    """)
    print(f"ML-ready:  {cursor.fetchone()['unique_contracts']:,}")

print("\n🔍 VULN COUNTS (try all possible names):")
with db._get_cursor(dict_cursor=True) as cursor:
    # Try different vuln column names
    vuln_cols = ['has_vulnerability', 'is_vulnerable', 'vulnerable', 'has_vuln']
    for col in vuln_cols:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) as cnt, '{col}' as col 
                FROM labels WHERE {col}=TRUE
            """)
            cnt = cursor.fetchone()
            if cnt and cnt['cnt'] > 0:
                print(f"✅ labels.{col}: {cnt['cnt']:,}")
        except:
            pass

print("\n🔍 CEI SAMPLE:")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT contract_id, cei_violations, failure_reason
        FROM features 
        WHERE cei_violations = 0 
        LIMIT 3
    """)
    for row in cursor.fetchall():
        print(f"ID {row['contract_id']}: CEI={row['cei_violations']}, fail={row['failure_reason']}")

print("\n🎯 SCHEMA REVEALED!")
