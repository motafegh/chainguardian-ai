#!/usr/bin/env python3
"""🔍 What columns ACTUALLY work?"""

from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

print("🔍 TEST RAW SELECT (no aliases)...")
try:
    with db._get_cursor() as cursor:  # No dict_cursor
        cursor.execute("""
            SELECT c.id, c.source_code
            FROM contracts c 
            JOIN features f ON c.id = f.contract_id
            JOIN labels l ON c.id = l.contract_id
            WHERE f.failure_reason IS NULL
              AND f.cei_violations = 0
              AND l.has_vulnerability = TRUE
            LIMIT 1
        """)
        row = cursor.fetchone()
        print(f"✅ RAW SELECT: id={row[0]}, source_len={len(row[1])}")
        print("✅ c.id + c.source_code WORKS!")
except Exception as e:
    print(f"❌ RAW SELECT ERROR: {e}")

print("\n🔍 CONTRACTS COLUMNS:")
with db._get_cursor() as cursor:
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='contracts'")
    print("  " + ", ".join([row[0] for row in cursor.fetchall()]))

print("\n🎯 Use RAW cursor → No dict_cursor!")
