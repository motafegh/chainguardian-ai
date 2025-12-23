#!/usr/bin/env python3
"""🔍 Why LENGTH(source_code)>100 kills all 396?"""

from chainguardian.database.manager import DatabaseManager

db = DatabaseManager()

print("🔍 SOURCE CODE LENGTHS (zero-CEI vuln contracts):")
with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT c.id, LENGTH(COALESCE(c.source_code, '')) as code_len,
               CASE WHEN LENGTH(COALESCE(c.source_code, '')) > 100 THEN 'PASS' ELSE 'FAIL' END as filter
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND l.has_vulnerability = TRUE
        ORDER BY code_len DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"ID {row[0]}: {row[1]} chars ({row[2]})")

print("\n🔍 REMOVE LENGTH FILTER → Get ALL contracts!")
with db._get_cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) 
        FROM contracts c 
        JOIN features f ON c.id = f.contract_id
        JOIN labels l ON c.id = l.contract_id
        WHERE f.failure_reason IS NULL
          AND f.cei_violations = 0
          AND l.has_vulnerability = TRUE
    """)
    print(f"TOTAL without length filter: {cursor.fetchone()[0]}")

print("\n�� REMOVE LENGTH FILTER!")
