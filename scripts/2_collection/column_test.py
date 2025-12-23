#!/usr/bin/env python3
"""🔍 Test EVERY column individually"""

from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

print("🔍 COUNT TEST (works):")
with db._get_cursor(dict_cursor=True) as cursor:
    cursor.execute("""
        SELECT COUNT(*) as cnt
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND l.has_vulnerability = TRUE
    """)
    print(f"✅ COUNT: {cursor.fetchone()['cnt']}")

print("\n🔍 TEST COLUMNS ONE BY ONE:")
tests = [
    "c.id",
    "f.contract_id", 
    "l.contract_id",
    "c.source_code",
    # NO c.name - that's the bug!
]

for col in tests:
    try:
        with db._get_cursor(dict_cursor=True) as cursor:
            cursor.execute(f"""
                SELECT {col} 
                FROM contracts c 
                JOIN features f ON c.id = f.contract_id
                JOIN labels l ON c.id = l.contract_id
                WHERE f.failure_reason IS NULL
                  AND f.cei_violations = 0
                  AND l.has_vulnerability = TRUE
                LIMIT 1
            """)
            row = cursor.fetchone()
            print(f"✅ {col}: {row[col] if row else 'NULL'}")
    except Exception as e:
        print(f"❌ {col}: ERROR {e}")

print("\n🎯 contracts.name DOESN'T EXIST → Use f.contract_id instead!")
